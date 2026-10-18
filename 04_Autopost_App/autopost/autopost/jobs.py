"""Background posting worker (run with: python manage.py autopost_worker)."""
import logging

from django.db import transaction
from django.utils import timezone

from . import conf
from .chat import get_adapter
from .models import Clip, PlatformPost, SocialAccount
from .publishers import PublishError, get_publisher

log = logging.getLogger("autopost")
ICON = {"youtube": "▶️ YouTube", "facebook": "📘 Facebook", "tiktok": "🎵 TikTok"}


def reset_stuck(minutes=30):
    cutoff = timezone.now() - timezone.timedelta(minutes=minutes)
    return PlatformPost.objects.filter(status=PlatformPost.Status.RUNNING, updated_at__lt=cutoff).update(
        status=PlatformPost.Status.QUEUED)


def claim_next():
    """Atomically take one due post (safe with several workers)."""
    now = timezone.now()
    for post in PlatformPost.objects.filter(status=PlatformPost.Status.QUEUED,
                                            next_attempt_at__lte=now).order_by("next_attempt_at")[:5]:
        n = PlatformPost.objects.filter(pk=post.pk, status=PlatformPost.Status.QUEUED).update(
            status=PlatformPost.Status.RUNNING, attempts=post.attempts + 1, updated_at=now)
        if n:
            post.refresh_from_db()
            return post
    return None


def run_one(post):
    account = SocialAccount.objects.filter(platform=post.platform, enabled=True).first()
    try:
        if account is None:
            raise PublishError(f"{post.platform} account not connected", retryable=False)
        result = get_publisher(post.platform).publish(post.clip, account)
    except Exception as e:  # noqa: BLE001
        retryable = getattr(e, "retryable", True)
        log.warning("publish %s failed (attempt %s): %s", post, post.attempts, e)
        post.error = str(e)[:2000]
        if retryable and post.attempts < conf.get("MAX_ATTEMPTS"):
            post.status = PlatformPost.Status.QUEUED
            post.next_attempt_at = timezone.now() + timezone.timedelta(minutes=2 ** post.attempts)
        else:
            post.status = PlatformPost.Status.FAILED
        post.save()
    else:
        post.status = PlatformPost.Status.DONE
        post.remote_id, post.url, post.note, post.error = result.remote_id, result.url, result.note, ""
        post.save()
    finish_clip(post.clip)
    return post


def finish_clip(clip):
    with transaction.atomic():
        clip = Clip.objects.select_for_update().get(pk=clip.pk)
        posts = list(clip.posts.all())
        if any(p.status in (PlatformPost.Status.QUEUED, PlatformPost.Status.RUNNING) for p in posts):
            return False
        if clip.status != Clip.Status.POSTING:
            return False  # already finalised
        ok = [p for p in posts if p.status == PlatformPost.Status.DONE]
        clip.status = (Clip.Status.POSTED if len(ok) == len(posts)
                       else Clip.Status.PARTIAL if ok else Clip.Status.FAILED)
        clip.save(update_fields=["status"])
    notify(clip, posts)
    return True


def summary(clip, posts):
    lines = [f"{'✅' if clip.status == Clip.Status.POSTED else '⚠️'} ຜົນການໂພສ \"{clip}\":"]
    for p in posts:
        if p.status == PlatformPost.Status.DONE:
            extra = p.url or p.note or "ສຳເລັດ"
            if p.note and p.url:
                extra += f"\n   ({p.note})"
            lines.append(f"{ICON.get(p.platform, p.platform)}: {extra}")
        else:
            lines.append(f"{ICON.get(p.platform, p.platform)}: ❌ {p.error[:160]}")
    return "\n".join(lines)


def notify(clip, posts):
    op = clip.requested_by
    if not op or not op.is_active:
        return
    try:
        get_adapter(op.channel).send_text(op.external_id, summary(clip, posts))
    except Exception:  # noqa: BLE001
        log.exception("could not notify operator %s", op)
