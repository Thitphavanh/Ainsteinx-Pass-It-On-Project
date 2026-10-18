"""YouTube Shorts upload via YouTube Data API v3 (resumable upload)."""
import json

from django.utils import timezone

from .. import conf
from .base import PublishError, PublishResult, TIMEOUT, check, file_size, session

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
CAPTIONS_URL = "https://www.googleapis.com/upload/youtube/v3/captions"
CHUNK = 8 * 1024 * 1024  # must be a multiple of 256 KiB


def refresh(account):
    if account.access_token and not account.token_expired:
        return account.access_token
    if not account.refresh_token:
        raise PublishError("YouTube: no refresh token, connect the account again", retryable=False)
    r = session.post(TOKEN_URL, data={
        "client_id": conf.get("GOOGLE_CLIENT_ID"),
        "client_secret": conf.get("GOOGLE_CLIENT_SECRET"),
        "refresh_token": account.refresh_token,
        "grant_type": "refresh_token",
    }, timeout=TIMEOUT)
    if r.status_code == 400:
        raise PublishError(f"YouTube token refresh rejected: {r.text[:300]} — connect the account again", retryable=False)
    check(r, "YouTube token refresh")
    data = r.json()
    account.access_token = data["access_token"]
    account.expires_at = timezone.now() + timezone.timedelta(seconds=int(data.get("expires_in", 3600)))
    account.save(update_fields=["access_token", "expires_at"])
    return account.access_token


class YouTubePublisher:
    platform = "youtube"

    def publish(self, clip, account):
        token = refresh(account)
        path = clip.video.path
        size = file_size(path)
        title = (clip.title or "Short")[:100]
        tags = [t.lstrip("#") for t in clip.hashtags.split() if t.startswith("#")][:15]
        meta = {
            "snippet": {
                "title": title,
                "description": "\n\n".join(p for p in (clip.description, clip.hashtags) if p)[:5000],
                "tags": tags,
                "categoryId": conf.get("YOUTUBE_CATEGORY_ID"),
            },
            "status": {
                "privacyStatus": conf.get("YOUTUBE_PRIVACY"),
                "selfDeclaredMadeForKids": False,
            },
        }
        r = session.post(UPLOAD_URL, params={"uploadType": "resumable", "part": "snippet,status"}, json=meta,
                         headers={"Authorization": f"Bearer {token}",
                                  "X-Upload-Content-Type": "video/mp4",
                                  "X-Upload-Content-Length": str(size)}, timeout=TIMEOUT)
        check(r, "YouTube upload init")
        location = r.headers.get("Location")
        if not location:
            raise PublishError("YouTube upload init returned no Location header")

        video = None
        with open(path, "rb") as fh:
            offset = 0
            while offset < size:
                chunk = fh.read(CHUNK)
                end = offset + len(chunk) - 1
                r = session.put(location, data=chunk, headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Length": str(len(chunk)),
                    "Content-Range": f"bytes {offset}-{end}/{size}",
                }, timeout=TIMEOUT)
                if r.status_code == 308:            # chunk accepted, more to come
                    rng = r.headers.get("Range")      # e.g. "bytes=0-8388607"
                    offset = int(rng.split("-")[1]) + 1 if rng else end + 1
                    fh.seek(offset)
                    continue
                check(r, "YouTube upload")
                video = r.json()
                break
        if not video or "id" not in video:
            raise PublishError("YouTube upload finished without a video id")

        note = ""
        if clip.subtitle_th:
            # The video is already live: a caption failure must not fail (and so re-upload) the post.
            try:
                upload_caption(token, video["id"], clip.subtitle_th, language="th", name="ไทย")
                note = "ໃສ່ຊັບໄຕເຕີ້ລ໌ໄທແລ້ວ"
            except PublishError as e:
                note = f"ວິດີໂອຂຶ້ນແລ້ວ ແຕ່ຊັບໄຕເຕີ້ລ໌ໄທບໍ່ຂຶ້ນ: {str(e)[:200]}"
        return PublishResult(video["id"], f"https://youtube.com/shorts/{video['id']}", note)


def upload_caption(token, video_id, srt_file, language, name):
    """Attach an SRT track (needs the youtube.force-ssl scope)."""
    srt_file.open("rb")
    try:
        body = srt_file.read()
    finally:
        srt_file.close()
    meta = {"snippet": {"videoId": video_id, "language": language, "name": name, "isDraft": False}}
    r = session.post(CAPTIONS_URL, params={"uploadType": "multipart", "part": "snippet"},
                     headers={"Authorization": f"Bearer {token}"},
                     files={"metadata": (None, json.dumps(meta), "application/json; charset=UTF-8"),
                            "media": ("subtitle.srt", body, "application/octet-stream")},
                     timeout=TIMEOUT)
    if r.status_code == 403:
        raise PublishError("YouTube ປະຕິເສດ (403) — ກົດເຊື່ອມຕໍ່ YouTube ໃໝ່ ເພື່ອໃຫ້ສິດໃສ່ຊັບໄຕເຕີ້ລ໌", retryable=False)
    check(r, "YouTube caption upload")
