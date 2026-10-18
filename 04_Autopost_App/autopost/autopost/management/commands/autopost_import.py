"""Queue the episodes of an Ainsteinx-Pass-It-On-Project folder.

    python manage.py autopost_import /path/to/Ainsteinx-Pass-It-On-Project [--dry-run] [--update]

Reads:
  01_Episodes/<EPnn_Name>/   videos, *_social_post.txt / *_title_description.txt, *_voiceover.srt
  05_Plan/episode_log.json   category of each episode
  06_Subtitles_TH_upload/    the Thai subtitle chosen for upload, one per episode

The Thai subtitle decides which cut gets posted: of the voiced videos, the one
whose length is closest to (and not shorter than) the subtitle wins, so EP.4
gets its 43 s 3D cut and EP.7 its v2. Without a subtitle the best-ranked
voiced cut is used. Clips found without a title are queued as drafts.

Each folder is imported once (matched by folder name, or by episode number for
clips added earlier by hand). --update refreshes text and subtitle of clips
that are still waiting in the queue; their video is never replaced.
"""
import json
import re
import struct
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from autopost.models import Clip

CTA = "ຖ້າຮູ້ແລ້ວ ຢ່າລືມ"          # closing line of every voice-over
CHANNEL_TAG = "#ບອກຕໍ່ຄວາມຮູ້"
SECTION = re.compile(r"^\s*(youtube title|title|description|tiktok)\b[^:]*:\s*$", re.I)
EP_DIR = re.compile(r"^EP(\d+)_", re.I)


# ---------- small readers ----------
def mp4_duration(path):
    """Seconds from the moov/mvhd box, or None. Avoids needing ffprobe on the server."""
    try:
        with open(path, "rb") as fh:
            return _find_mvhd(fh, 0, Path(path).stat().st_size)
    except (OSError, struct.error):
        return None


def _find_mvhd(fh, start, end):
    pos = start
    while pos + 8 <= end:
        fh.seek(pos)
        size, kind = struct.unpack(">I4s", fh.read(8))
        header = 8
        if size == 1:
            size, header = struct.unpack(">Q", fh.read(8))[0], 16
        elif size == 0:
            size = end - pos
        if size < header:
            return None
        if kind == b"moov":
            return _find_mvhd(fh, pos + header, pos + size)
        if kind == b"mvhd":
            version = fh.read(1)[0]
            fh.read(3)
            if version == 1:
                fh.read(16)
                scale, duration = struct.unpack(">IQ", fh.read(12))
            else:
                fh.read(8)
                scale, duration = struct.unpack(">II", fh.read(8))
            return duration / scale if scale else None
        pos += size
    return None


def srt_lines(path):
    text = Path(path).read_text(encoding="utf-8-sig")
    return [ln.strip() for ln in text.splitlines()
            if ln.strip() and "-->" not in ln and not ln.strip().isdigit()]


def srt_end(path):
    stamps = re.findall(r"--> (\d+):(\d+):(\d+)[,.](\d+)", Path(path).read_text(encoding="utf-8-sig"))
    if not stamps:
        return None
    h, m, s, ms = (int(x) for x in stamps[-1])
    return h * 3600 + m * 60 + s + ms / 1000


def split_hashtags(text):
    tags = [w for w in text.split() if w.startswith("#")]
    rest = " ".join(w for w in text.split() if not w.startswith("#"))
    return rest, tags


def parse_post(path):
    """Title / description / hashtags from a *_social_post.txt or *_title_description.txt."""
    sections, current = {}, None
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        m = SECTION.match(line)
        if m:
            current = m.group(1).lower().split()[-1]      # "youtube title" -> "title"
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line.rstrip())

    title_lines = [ln for ln in sections.get("title", []) if ln.strip()]
    title, tags = split_hashtags(title_lines[0]) if title_lines else ("", [])
    body = []
    for line in sections.get("description", []):
        words = line.split()
        if words and all(w.startswith("#") for w in words):
            tags += words
        else:
            body.append(line)
    tags = [t for t in tags if t.lower() != "#shorts"] + (["#shorts"] if any(t.lower() == "#shorts" for t in tags) else [])
    return title.strip(), "\n".join(body).strip(), tags


# ---------- picking files ----------
def rank(video):
    """Lower is better: voiced cuts with music first, silent masters never."""
    name = video.stem.lower()
    if "noaudio" in name:
        return None
    if name.endswith("voice_music"):
        return 0
    if name.endswith("voice"):
        return 1
    if "smooth" in name:
        return 2
    return 3


def pick_video(videos, target=None):
    candidates = [v for v in videos if rank(v) is not None]
    if not candidates:
        return None
    if target:
        durations = {v: mp4_duration(v) for v in candidates}
        fitting = [v for v in candidates if durations[v] and durations[v] >= target - 0.5]
        if fitting:
            best = min(durations[v] - target for v in fitting)
            candidates = [v for v in fitting if durations[v] - target <= best + 0.5]
    # Name descending as the tie-break favours "Real3D"/"v2"/"male" over the older cuts.
    candidates.sort(key=lambda v: v.name, reverse=True)
    return min(candidates, key=rank)


def version_tag(path):
    m = re.search(r"(v\d+)", path.stem)
    return m.group(1) if m else ""


def closest(files, seconds):
    if not files:
        return None
    if seconds is None:
        return files[0]
    return min(files, key=lambda f: abs((srt_end(f) or 0) - seconds))


class Command(BaseCommand):
    help = "Queue every episode of an Ainsteinx-Pass-It-On-Project folder for autoposting."

    def add_arguments(self, parser):
        parser.add_argument("folder", help="Ainsteinx-Pass-It-On-Project (holds 01_Episodes)")
        parser.add_argument("--dry-run", action="store_true", help="Only show what would be queued")
        parser.add_argument("--update", action="store_true",
                            help="Refresh text and subtitle of clips that are still in the queue")

    def handle(self, folder, dry_run=False, update=False, **options):
        root = Path(folder).expanduser()
        episodes_dir = root / "01_Episodes"
        if not episodes_dir.is_dir():
            raise CommandError(f"No 01_Episodes folder in {root}")

        categories = self.load_categories(root / "05_Plan" / "episode_log.json")
        upload_subs = sorted((root / "06_Subtitles_TH_upload").glob("*.srt"))
        added = updated = skipped = 0

        for ep_dir in sorted(p for p in episodes_dir.iterdir() if p.is_dir()):
            m = EP_DIR.match(ep_dir.name)
            number = int(m.group(1)) if m else None
            plan = self.plan(ep_dir, number, categories, upload_subs)
            if plan is None:
                self.stdout.write(self.style.WARNING(f"skip {ep_dir.name}: no usable video"))
                skipped += 1
                continue

            existing = Clip.objects.filter(
                Q(source=ep_dir.name) | (Q(episode=number) if number else Q(video__icontains=ep_dir.name.split("_")[-1]))
            ).first()
            self.report(ep_dir.name, plan, existing)
            if dry_run:
                continue

            if existing is None:
                self.create(ep_dir.name, plan)
                added += 1
            elif update and existing.status in (Clip.Status.DRAFT, Clip.Status.READY):
                self.refresh(existing, ep_dir.name, plan)
                updated += 1
            else:
                skipped += 1

        if dry_run:
            self.stdout.write("dry run — nothing saved")
        else:
            self.stdout.write(self.style.SUCCESS(f"added {added}, updated {updated}, unchanged {skipped}"))

    # ----- planning -----
    def load_categories(self, path):
        try:
            done = json.loads(path.read_text(encoding="utf-8")).get("done", [])
        except (OSError, ValueError):
            return {}
        return {row["ep"]: row.get("cat", "") for row in done if "ep" in row}

    def plan(self, ep_dir, number, categories, upload_subs):
        prefix = f"EP{number:02d}" if number else None
        sub = next((s for s in upload_subs if prefix and s.name.upper().startswith(prefix)), None)
        if sub is None and prefix:
            local = sorted(ep_dir.glob("*_subtitle_TH.srt"))
            sub = local[0] if len(local) == 1 else None    # ambiguous without the upload pick

        video = pick_video(sorted(ep_dir.glob("*.mp4")), srt_end(sub) if sub else None)
        if video is None:
            return None
        length = mp4_duration(video)

        title, description, tags = self.text_for(ep_dir, video, length)
        category = categories.get(number, "")
        if not tags and title:
            tags = [CHANNEL_TAG] + ([f"#ຮູ້ບໍ່EP{number}"] if number else []) + \
                   ([f"#{category.replace(' ', '')}"] if category else []) + ["#shorts"]
        hashtags = " ".join(dict.fromkeys(tags))          # de-duplicate, keep order
        return dict(video=video, subtitle=sub, length=length, number=number, category=category,
                    title=title[:100], description=description, hashtags=hashtags[:500])

    def text_for(self, ep_dir, video, length):
        posts = sorted(ep_dir.glob("*_social_post.txt")) + sorted(ep_dir.glob("*_title_description.txt"))
        tag = version_tag(video)
        posts.sort(key=lambda p: version_tag(p) != tag)    # same version (e.g. v2) first
        for post in posts:
            title, description, tags = parse_post(post)
            if title:
                return title, description, tags

        # No post copy: the Lao voice-over is the clip's own text.
        voiceovers = [p for p in ep_dir.glob("*voiceover.srt") if version_tag(p) == tag]
        vo = closest(sorted(voiceovers), length)
        if vo is None:
            return "", "", []
        lines = [ln for ln in srt_lines(vo) if not ln.startswith(CTA)]
        if not lines:
            return "", "", []
        return lines[0], "\n".join(lines[1:]), []

    # ----- output / saving -----
    def report(self, name, plan, existing):
        state = "new" if existing is None else f"exists (#{existing.pk}, {existing.get_status_display()})"
        length = f"{plan['length']:.1f}s" if plan["length"] else "?"
        sub = plan["subtitle"].name if plan["subtitle"] else "—"
        self.stdout.write(f"{name}: {plan['video'].name} [{length}] · TH {sub} · {state}\n"
                          f"    {plan['title'] or '(no title → draft)'}")

    def create(self, name, plan):
        clip = Clip(source=name, episode=plan["number"], category=plan["category"], title=plan["title"],
                    description=plan["description"], hashtags=plan["hashtags"],
                    status=Clip.Status.READY if plan["title"] else Clip.Status.DRAFT,
                    queue_position=(plan["number"] or 900) * 10)
        with open(plan["video"], "rb") as fh:
            clip.video.save(plan["video"].name, File(fh), save=False)
        self.attach_subtitle(clip, plan)
        clip.save()

    def refresh(self, clip, name, plan):
        clip.source = name
        for field in ("category", "title", "description", "hashtags"):
            if plan[field]:
                setattr(clip, field, plan[field])
        if clip.status == Clip.Status.DRAFT and clip.title:
            clip.status = Clip.Status.READY
        if clip.subtitle_th:
            clip.subtitle_th.delete(save=False)
        self.attach_subtitle(clip, plan)
        clip.save()

    def attach_subtitle(self, clip, plan):
        if plan["subtitle"]:
            with open(plan["subtitle"], "rb") as fh:
                clip.subtitle_th.save(plan["subtitle"].name, File(fh), save=False)
