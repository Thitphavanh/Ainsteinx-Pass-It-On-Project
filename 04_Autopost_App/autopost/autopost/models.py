from django.db import models
from django.utils import timezone

from . import conf

PLATFORM_CHOICES = [("youtube", "YouTube"), ("facebook", "Facebook"), ("tiktok", "TikTok")]
CHAT_CHOICES = [("line", "LINE"), ("whatsapp", "WhatsApp")]


# ---------- token encryption ----------
def _fernet():
    key = conf.get("FERNET_KEY")
    if not key:
        return None
    from cryptography.fernet import Fernet
    return Fernet(key.encode() if isinstance(key, str) else key)


class EncryptedTextField(models.TextField):
    """Stores text encrypted with AUTOPOST_FERNET_KEY (plain text if no key is set)."""
    PREFIX = "enc:"

    def from_db_value(self, value, expression, connection):
        if value and value.startswith(self.PREFIX):
            f = _fernet()
            if f is None:
                raise RuntimeError("AUTOPOST_FERNET_KEY is required to read stored tokens")
            return f.decrypt(value[len(self.PREFIX):].encode()).decode()
        return value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        f = _fernet()
        if value and f and not value.startswith(self.PREFIX):
            return self.PREFIX + f.encrypt(value.encode()).decode()
        return value


# ---------- accounts ----------
class SocialAccount(models.Model):
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, unique=True)
    name = models.CharField(max_length=200, blank=True)            # channel / page / TikTok username
    external_id = models.CharField(max_length=200, blank=True)     # channel id / page id / open_id
    access_token = EncryptedTextField(blank=True)
    refresh_token = EncryptedTextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    enabled = models.BooleanField(default=True)
    connected_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_platform_display()}: {self.name or self.external_id}"

    @property
    def token_expired(self):
        return bool(self.expires_at and self.expires_at <= timezone.now() + timezone.timedelta(minutes=5))


class ChatOperator(models.Model):
    """A LINE / WhatsApp user who may order posts."""
    channel = models.CharField(max_length=20, choices=CHAT_CHOICES)
    external_id = models.CharField(max_length=200)                 # LINE userId / WhatsApp phone (wa_id)
    name = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    receives_daily_prompt = models.BooleanField(default=True)
    state = models.CharField(max_length=40, blank=True)            # e.g. "await_caption:12"
    last_inbound_at = models.DateTimeField(null=True, blank=True)  # WhatsApp 24 h window
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("channel", "external_id")]

    def __str__(self):
        return f"{self.get_channel_display()} {self.name or self.external_id}"


class InboundMessage(models.Model):
    """De-duplicates webhook redeliveries."""
    channel = models.CharField(max_length=20, choices=CHAT_CHOICES)
    message_id = models.CharField(max_length=200)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("channel", "message_id")]


# ---------- content ----------
class Clip(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "ຮ່າງ (ລໍຖ້າຫົວຂໍ້)"
        READY = "ready", "ພ້ອມໂພສ (ໃນຄິວ)"
        POSTING = "posting", "ກຳລັງໂພສ"
        POSTED = "posted", "ໂພສແລ້ວ"
        PARTIAL = "partial", "ໂພສໄດ້ບາງບ່ອນ"
        FAILED = "failed", "ໂພສບໍ່ສຳເລັດ"
        SKIPPED = "skipped", "ຂ້າມ"

    title = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    hashtags = models.CharField(max_length=500, blank=True, help_text="ເຊັ່ນ #ຮູ້ບໍ່ #ອາວະກາດ #shorts")
    video = models.FileField(upload_to="autopost/videos/")
    subtitle_th = models.FileField(upload_to="autopost/subtitles/", blank=True,
                                   help_text="SRT ພາສາໄທ — ອັບຂຶ້ນ YouTube ເປັນຊັບໄຕເຕີ້ລ໌ຫຼັງໂພສ")
    source = models.CharField(max_length=200, blank=True, db_index=True,
                              help_text="ໂຟນເດີຕົ້ນທາງ (ໃຊ້ຕອນ autopost_import ເພື່ອບໍ່ໃຫ້ນຳເຂົ້າຊ້ຳ)")
    episode = models.PositiveIntegerField(null=True, blank=True)
    category = models.CharField(max_length=40, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.READY)
    queue_position = models.IntegerField(default=0, help_text="ນ້ອຍກວ່າ = ໂພສກ່ອນ")
    not_before = models.DateTimeField(null=True, blank=True, help_text="ເລື່ອນໄປຖາມອີກຄັ້ງຫຼັງເວລານີ້")
    requested_by = models.ForeignKey(ChatOperator, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["queue_position", "episode", "created_at"]

    def __str__(self):
        ep = f"EP.{self.episode} " if self.episode else ""
        return f"{ep}{self.title or self.video.name}"

    def caption(self, limit=None):
        parts = [p for p in (self.title, self.description, self.hashtags) if p]
        text = "\n\n".join(parts)
        return text[:limit] if limit else text

    @classmethod
    def next_ready(cls):
        now = timezone.now()
        return (cls.objects.filter(status=cls.Status.READY)
                .filter(models.Q(not_before__isnull=True) | models.Q(not_before__lte=now)).first())


class PlatformPost(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "ລໍຖ້າ"
        RUNNING = "running", "ກຳລັງອັບໂຫຼດ"
        DONE = "done", "ສຳເລັດ"
        FAILED = "failed", "ບໍ່ສຳເລັດ"

    clip = models.ForeignKey(Clip, on_delete=models.CASCADE, related_name="posts")
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    remote_id = models.CharField(max_length=200, blank=True)
    url = models.URLField(blank=True)
    note = models.CharField(max_length=300, blank=True)
    error = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("clip", "platform")]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.clip} → {self.platform}: {self.status}"
