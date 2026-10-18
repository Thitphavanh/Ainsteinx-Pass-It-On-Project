from dataclasses import dataclass, field


@dataclass
class Incoming:
    channel: str                 # "line" | "whatsapp"
    user_id: str
    kind: str                    # "text" | "video" | "postback" | "other"
    message_id: str = ""
    text: str = ""
    payload: str = ""
    media_id: str = ""
    name: str = ""
    reply_token: str = ""
    extra: dict = field(default_factory=dict)


class BadSignature(Exception):
    pass


class ChatAdapter:
    channel = ""

    def __init__(self):
        self._reply_token = None

    # incoming
    def parse(self, request):          # -> list[Incoming]
        raise NotImplementedError

    def download(self, msg, dest_path):
        raise NotImplementedError

    # outgoing — buttons: list of (label, payload); adapters trim labels to platform limits
    def send_text(self, to, text, reply_token=None):
        raise NotImplementedError

    def send_buttons(self, to, text, buttons, reply_token=None):
        raise NotImplementedError

    def send_daily_prompt(self, operator, clip, buttons):
        """Proactive message (no inbound to reply to)."""
        return self.send_buttons(operator.external_id, daily_text(clip), buttons)


def daily_text(clip):
    return f"📅 ຄລິບຕໍ່ໄປພ້ອມໂພສແລ້ວ:\n{clip}\n\nໂພສລົງ YouTube, Facebook, TikTok ດຽວນີ້ບໍ?"


def get_adapter(channel):
    if channel == "line":
        from .line import LineAdapter
        return LineAdapter()
    if channel == "whatsapp":
        from .whatsapp import WhatsAppAdapter
        return WhatsAppAdapter()
    raise ValueError(channel)
