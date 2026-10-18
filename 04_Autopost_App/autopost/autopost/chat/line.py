"""LINE Messaging API adapter."""
import base64
import hashlib
import hmac
import json
import time

import requests

from .. import conf
from .base import BadSignature, ChatAdapter, Incoming

API = "https://api.line.me/v2/bot"
DATA_API = "https://api-data.line.me/v2/bot"
TIMEOUT = (10, 60)


def verify(body: bytes, signature: str):
    secret = conf.get("LINE_CHANNEL_SECRET").encode()
    expected = base64.b64encode(hmac.new(secret, body, hashlib.sha256).digest()).decode()
    if not signature or not hmac.compare_digest(expected, signature):
        raise BadSignature("LINE signature mismatch")


class LineAdapter(ChatAdapter):
    channel = "line"

    def _headers(self):
        return {"Authorization": f"Bearer {conf.get('LINE_CHANNEL_ACCESS_TOKEN')}", "Content-Type": "application/json"}

    def parse(self, request):
        verify(request.body, request.headers.get("X-Line-Signature", ""))
        out = []
        for ev in json.loads(request.body or b"{}").get("events", []):
            src = ev.get("source", {})
            if src.get("type") != "user":
                continue  # ignore group / room events
            base = dict(channel="line", user_id=src.get("userId", ""), reply_token=ev.get("replyToken", ""),
                        message_id=ev.get("webhookEventId", ""))
            if ev.get("type") == "postback":
                out.append(Incoming(kind="postback", payload=ev["postback"].get("data", ""), **base))
            elif ev.get("type") == "message":
                m = ev["message"]
                base["message_id"] = m.get("id", base["message_id"])
                if m["type"] == "text":
                    out.append(Incoming(kind="text", text=m.get("text", ""), **base))
                elif m["type"] == "video" or (m["type"] == "file" and m.get("fileName", "").lower().endswith((".mp4", ".mov"))):
                    out.append(Incoming(kind="video", media_id=m["id"], extra={"line_type": m["type"]}, **base))
                else:
                    out.append(Incoming(kind="other", **base))
        return out

    def download(self, msg, dest_path):
        if msg.extra.get("line_type") == "video":  # wait until LINE finishes preparing the video
            for _ in range(30):
                r = requests.get(f"{DATA_API}/message/{msg.media_id}/content/transcoding",
                                 headers=self._headers(), timeout=TIMEOUT)
                if r.ok and r.json().get("status") == "succeeded":
                    break
                if r.ok and r.json().get("status") == "failed":
                    raise RuntimeError("LINE could not prepare the video")
                time.sleep(2)
        with requests.get(f"{DATA_API}/message/{msg.media_id}/content", headers=self._headers(),
                          stream=True, timeout=TIMEOUT) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as fh:
                for part in r.iter_content(1 << 20):
                    fh.write(part)
        return dest_path

    def _send(self, to, messages, reply_token=None):
        if reply_token:
            r = requests.post(f"{API}/message/reply", headers=self._headers(),
                              json={"replyToken": reply_token, "messages": messages}, timeout=TIMEOUT)
            if r.ok:
                return r
        r = requests.post(f"{API}/message/push", headers=self._headers(),
                          json={"to": to, "messages": messages}, timeout=TIMEOUT)
        r.raise_for_status()
        return r

    def send_text(self, to, text, reply_token=None):
        return self._send(to, [{"type": "text", "text": text[:5000]}], reply_token)

    def send_buttons(self, to, text, buttons, reply_token=None):
        items = [{"type": "action", "action": {"type": "postback", "label": label[:20], "data": payload,
                                                "displayText": label[:300]}} for label, payload in buttons[:13]]
        return self._send(to, [{"type": "text", "text": text[:5000], "quickReply": {"items": items}}], reply_token)
