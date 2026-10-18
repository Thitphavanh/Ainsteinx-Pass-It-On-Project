"""WhatsApp Cloud API adapter."""
import hashlib
import hmac
import json

import requests
from django.utils import timezone

from .. import conf
from .base import BadSignature, ChatAdapter, Incoming, daily_text

TIMEOUT = (10, 60)


def graph(path):
    return f"https://graph.facebook.com/{conf.get('GRAPH_VERSION')}/{path.lstrip('/')}"


def verify(body: bytes, header: str):
    secret = conf.get("META_APP_SECRET").encode()
    expected = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
    if not header or not hmac.compare_digest(expected, header):
        raise BadSignature("WhatsApp signature mismatch")


class WhatsAppAdapter(ChatAdapter):
    channel = "whatsapp"

    def _headers(self):
        return {"Authorization": f"Bearer {conf.get('WA_ACCESS_TOKEN')}", "Content-Type": "application/json"}

    def parse(self, request):
        verify(request.body, request.headers.get("X-Hub-Signature-256", ""))
        out = []
        for entry in json.loads(request.body or b"{}").get("entry", []):
            for change in entry.get("changes", []):
                v = change.get("value", {})
                names = {c.get("wa_id"): c.get("profile", {}).get("name", "") for c in v.get("contacts", [])}
                for m in v.get("messages", []):
                    base = dict(channel="whatsapp", user_id=m.get("from", ""), message_id=m.get("id", ""),
                                name=names.get(m.get("from"), ""))
                    t = m.get("type")
                    if t == "text":
                        out.append(Incoming(kind="text", text=m["text"].get("body", ""), **base))
                    elif t == "interactive":
                        it = m["interactive"]
                        rep = it.get("button_reply") or it.get("list_reply") or {}
                        out.append(Incoming(kind="postback", payload=rep.get("id", ""), **base))
                    elif t == "button":  # quick-reply button on a template message
                        out.append(Incoming(kind="postback", payload=m["button"].get("payload", ""), **base))
                    elif t == "video":
                        out.append(Incoming(kind="video", media_id=m["video"]["id"], **base))
                    elif t == "document" and (m["document"].get("mime_type", "").startswith("video/")
                                              or m["document"].get("filename", "").lower().endswith((".mp4", ".mov"))):
                        out.append(Incoming(kind="video", media_id=m["document"]["id"], **base))
                    else:
                        out.append(Incoming(kind="other", **base))
        return out

    def download(self, msg, dest_path):
        r = requests.get(graph(msg.media_id), headers=self._headers(), timeout=TIMEOUT)
        r.raise_for_status()
        url = r.json()["url"]
        with requests.get(url, headers={"Authorization": f"Bearer {conf.get('WA_ACCESS_TOKEN')}"},
                          stream=True, timeout=TIMEOUT) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as fh:
                for part in r.iter_content(1 << 20):
                    fh.write(part)
        return dest_path

    def _send(self, body):
        body = {"messaging_product": "whatsapp", **body}
        r = requests.post(graph(f"{conf.get('WA_PHONE_NUMBER_ID')}/messages"), headers=self._headers(),
                          json=body, timeout=TIMEOUT)
        r.raise_for_status()
        return r

    def send_text(self, to, text, reply_token=None):
        return self._send({"to": to, "type": "text", "text": {"body": text[:4096]}})

    def send_buttons(self, to, text, buttons, reply_token=None):
        btns = [{"type": "reply", "reply": {"id": payload[:256], "title": label[:20]}} for label, payload in buttons[:3]]
        return self._send({"to": to, "type": "interactive", "interactive": {
            "type": "button", "body": {"text": text[:1024]}, "action": {"buttons": btns}}})

    def send_daily_prompt(self, operator, clip, buttons):
        # Free-form messages only work within 24 h of the user's last message; otherwise use a template.
        recent = operator.last_inbound_at and operator.last_inbound_at > timezone.now() - timezone.timedelta(hours=23)
        tpl = conf.get("WA_DAILY_TEMPLATE")
        if recent or not tpl:
            return self.send_buttons(operator.external_id, daily_text(clip), buttons)
        comps = [{"type": "body", "parameters": [{"type": "text", "text": str(clip)[:60]}]}]
        for i, (_label, payload) in enumerate(buttons[:3]):
            comps.append({"type": "button", "sub_type": "quick_reply", "index": str(i),
                          "parameters": [{"type": "payload", "payload": payload}]})
        return self._send({"to": operator.external_id, "type": "template", "template": {
            "name": tpl, "language": {"code": conf.get("WA_TEMPLATE_LANG")}, "components": comps}})
