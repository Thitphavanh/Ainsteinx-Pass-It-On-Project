"""Chat conversation shared by LINE and WhatsApp."""
import logging
import os
import re
import uuid

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from . import conf
from .models import ChatOperator, Clip, InboundMessage, PlatformPost, SocialAccount

log = logging.getLogger("autopost")

HELP = ("🤖 ບອກຕໍ່ຄວາມຮູ້ — ບອດໂພສອັດຕະໂນມັດ\n\n"
        "• ສົ່ງໄຟລ໌ວິດີໂອ (MP4) ມາ → ບອດຈະຖາມຫົວຂໍ້ ແລ້ວໂພສໃຫ້\n"
        "• ພິມ \"ຄິວ\" → ເບິ່ງຄລິບທີ່ພ້ອມໂພສ\n"
        "• ພິມ \"ສະຖານະ\" → ເບິ່ງຜົນການໂພສລ່າສຸດ\n"
        "• ພິມ \"ຊ່ວຍ\" → ເບິ່ງຂໍ້ຄວາມນີ້\n\n"
        "ຮູບແບບຫົວຂໍ້: ແຖວທຳອິດ = Title, ແຖວຕໍ່ໄປ = Description, ຄຳທີ່ຂຶ້ນຕົ້ນດ້ວຍ # = Hashtags")


def post_buttons(clip):
    return [("ໂພສດຽວນີ້", f"post:{clip.pk}"), ("ພຸ່ງນີ້", f"later:{clip.pk}"), ("ຂ້າມ", f"skip:{clip.pk}")]


def parse_caption(text):
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    tags = [w for w in text.split() if w.startswith("#") and len(w) > 1]
    body = [" ".join(w for w in l.split() if not w.startswith("#")) for l in lines]
    body = [l for l in body if l]
    title = body[0] if body else ""
    ep = re.search(r"EP\.?\s*(\d+)", text, re.I)
    return {"title": title[:100], "description": "\n".join(body[1:]), "hashtags": " ".join(dict.fromkeys(tags)),
            "episode": int(ep.group(1)) if ep else None}


def enabled_platforms():
    wanted = conf.get("PLATFORMS")
    return list(SocialAccount.objects.filter(enabled=True, platform__in=wanted).values_list("platform", flat=True))


def start_posting(clip, operator=None):
    """Queue the clip for every connected platform. Returns list of platforms or [] if none connected."""
    platforms = enabled_platforms()
    if not platforms:
        return []
    with transaction.atomic():
        for p in platforms:
            PlatformPost.objects.update_or_create(clip=clip, platform=p, defaults={
                "status": PlatformPost.Status.QUEUED, "attempts": 0, "error": "", "note": "",
                "next_attempt_at": timezone.now()})
        clip.status = Clip.Status.POSTING
        clip.requested_by = operator or clip.requested_by
        clip.save(update_fields=["status", "requested_by"])
    return platforms


class Bot:
    def __init__(self, adapter):
        self.a = adapter

    # -------- helpers --------
    def say(self, msg, text):
        self.a.send_text(msg.user_id, text, reply_token=msg.reply_token)
        msg.reply_token = ""  # a LINE reply token works once

    def ask(self, msg, text, buttons):
        self.a.send_buttons(msg.user_id, text, buttons, reply_token=msg.reply_token)
        msg.reply_token = ""

    # -------- entry point --------
    def handle(self, msg):
        if msg.message_id:
            try:
                InboundMessage.objects.create(channel=msg.channel, message_id=msg.message_id)
            except IntegrityError:
                return  # redelivery
        op = ChatOperator.objects.filter(channel=msg.channel, external_id=msg.user_id, is_active=True).first()
        if op is None:
            return self.pair(msg)
        op.last_inbound_at = timezone.now()
        if msg.name and not op.name:
            op.name = msg.name
        op.save(update_fields=["last_inbound_at", "name"])

        if msg.kind == "video":
            return self.on_video(msg, op)
        if msg.kind == "postback":
            return self.on_postback(msg, op)
        if msg.kind == "text":
            return self.on_text(msg, op)
        self.say(msg, "ຮອງຮັບສະເພາະຂໍ້ຄວາມ ແລະ ໄຟລ໌ວິດີໂອ MP4 ເທົ່ານັ້ນ")

    def pair(self, msg):
        code = conf.get("PAIR_CODE")
        if msg.kind == "text" and code and msg.text.strip().lower() == f"pair {code}".lower():
            ChatOperator.objects.update_or_create(channel=msg.channel, external_id=msg.user_id,
                                                  defaults={"is_active": True, "name": msg.name})
            return self.say(msg, "✅ ເຊື່ອມຕໍ່ສຳເລັດ!\n\n" + HELP)
        self.say(msg, "🔒 ບັນຊີນີ້ຍັງບໍ່ມີສິດສັ່ງໂພສ. ສົ່ງ \"pair <ລະຫັດ>\" ເພື່ອເຊື່ອມຕໍ່.")

    def on_video(self, msg, op):
        folder = os.path.join(settings.MEDIA_ROOT, "autopost", "videos")
        os.makedirs(folder, exist_ok=True)
        name = f"chat_{timezone.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}.mp4"
        path = os.path.join(folder, name)
        try:
            self.a.download(msg, path)
        except Exception as e:  # noqa: BLE001
            log.exception("download failed")
            return self.say(msg, f"❌ ດາວໂຫຼດວິດີໂອບໍ່ໄດ້: {e}")
        clip = Clip.objects.create(video=f"autopost/videos/{name}", status=Clip.Status.DRAFT, requested_by=op)
        op.state = f"await_caption:{clip.pk}"
        op.save(update_fields=["state"])
        self.ask(msg, "📥 ໄດ້ຮັບວິດີໂອແລ້ວ!\nສົ່ງຫົວຂໍ້ມາເລີຍ:\nແຖວ 1 = Title\nແຖວຕໍ່ໄປ = Description\n#hashtag ໃສ່ທ້າຍ",
                 [("ຍົກເລີກ", f"cancel:{clip.pk}")])

    def on_text(self, msg, op):
        t = msg.text.strip()
        low = t.lower()
        if op.state.startswith("await_caption:") and low not in ("ຊ່ວຍ", "help", "ຄິວ", "queue", "ສະຖານະ", "status"):
            clip = Clip.objects.filter(pk=op.state.split(":")[1]).first()
            op.state = ""
            op.save(update_fields=["state"])
            if not clip:
                return self.say(msg, "ບໍ່ພົບຄລິບ ລອງສົ່ງວິດີໂອໃໝ່")
            for k, v in parse_caption(t).items():
                if v not in (None, ""):
                    setattr(clip, k, v)
            clip.save()
            return self.ask(msg, f"📝 {clip.caption()}\n\nຈະເຮັດແນວໃດກັບຄລິບນີ້?",
                            [("ໂພສດຽວນີ້", f"post:{clip.pk}"), ("ເຂົ້າຄິວ", f"queue:{clip.pk}"),
                             ("ຍົກເລີກ", f"cancel:{clip.pk}")])
        if low in ("ຄິວ", "queue"):
            clips = list(Clip.objects.filter(status=Clip.Status.READY)[:3])
            if not clips:
                return self.say(msg, "ຄິວຫວ່າງ — ສົ່ງວິດີໂອມາ ຫຼື ເພີ່ມໃນເວັບ")
            text = "📋 ຄິວ:\n" + "\n".join(f"{i + 1}. {c}" for i, c in enumerate(clips)) + "\n\nກົດເພື່ອໂພສ:"
            return self.ask(msg, text, [(f"ໂພສ {i + 1}", f"post:{c.pk}") for i, c in enumerate(clips)])
        if low in ("ສະຖານະ", "status"):
            posts = PlatformPost.objects.select_related("clip")[:6]
            if not posts:
                return self.say(msg, "ຍັງບໍ່ມີການໂພສ")
            return self.say(msg, "📊 ລ່າສຸດ:\n" + "\n".join(
                f"{p.get_platform_display()} · {p.clip} · {p.get_status_display()}" for p in posts))
        return self.say(msg, HELP)

    def on_postback(self, msg, op):
        action, _, pk = msg.payload.partition(":")
        clip = Clip.objects.filter(pk=pk).first() if pk.isdigit() else None
        if clip is None:
            return self.say(msg, "ບໍ່ພົບຄລິບນີ້ (ອາດຖືກລຶບແລ້ວ)")
        if op.state == f"await_caption:{clip.pk}":
            op.state = ""
            op.save(update_fields=["state"])

        if action == "post":
            if clip.status in (Clip.Status.POSTING, Clip.Status.POSTED):
                return self.say(msg, f"ຄລິບນີ້ {clip.get_status_display()} ຢູ່ແລ້ວ")
            platforms = start_posting(clip, op)
            if not platforms:
                return self.say(msg, "⚠️ ຍັງບໍ່ໄດ້ເຊື່ອມຕໍ່ບັນຊີ YouTube / Facebook / TikTok ໃນເວັບ")
            names = ", ".join(p.capitalize() for p in platforms)
            return self.say(msg, f"⏳ ກຳລັງໂພສ \"{clip}\" ລົງ {names}...\nຈະແຈ້ງຜົນເມື່ອສຳເລັດ")
        if action == "queue":
            clip.status = Clip.Status.READY
            clip.save(update_fields=["status"])
            pos = Clip.objects.filter(status=Clip.Status.READY).count()
            return self.say(msg, f"✅ ເຂົ້າຄິວແລ້ວ (ລຳດັບທີ {pos})")
        if action == "later":
            clip.status = Clip.Status.READY
            clip.not_before = timezone.now() + timezone.timedelta(hours=20)
            clip.save(update_fields=["status", "not_before"])
            return self.say(msg, "👌 ເລື່ອນໄປຖາມພຸ່ງນີ້")
        if action == "skip":
            clip.status = Clip.Status.SKIPPED
            clip.save(update_fields=["status"])
            return self.say(msg, "⏭️ ຂ້າມຄລິບນີ້ແລ້ວ")
        if action == "cancel":
            if clip.status == Clip.Status.DRAFT:
                clip.video.delete(save=False)
                clip.delete()
            return self.say(msg, "ຍົກເລີກແລ້ວ")
        return self.say(msg, HELP)
