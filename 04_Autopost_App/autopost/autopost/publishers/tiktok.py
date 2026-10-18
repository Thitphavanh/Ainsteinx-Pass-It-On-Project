"""TikTok Direct Post via Content Posting API (FILE_UPLOAD)."""
from django.utils import timezone

from .. import conf
from .base import PublishError, PublishResult, TIMEOUT, check, file_size, poll, session

API = "https://open.tiktokapis.com/v2"
MIN_CHUNK, MAX_CHUNK = 5 * 1024 * 1024, 64 * 1024 * 1024
CHUNK = 10 * 1024 * 1024


def refresh(account):
    if account.access_token and not account.token_expired:
        return account.access_token
    r = session.post(f"{API}/oauth/token/", data={
        "client_key": conf.get("TIKTOK_CLIENT_KEY"),
        "client_secret": conf.get("TIKTOK_CLIENT_SECRET"),
        "grant_type": "refresh_token",
        "refresh_token": account.refresh_token,
    }, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=TIMEOUT)
    check(r, "TikTok token refresh")
    data = r.json()
    if "access_token" not in data:
        raise PublishError(f"TikTok refresh failed: {data} — connect the account again", retryable=False)
    account.access_token = data["access_token"]
    account.refresh_token = data.get("refresh_token", account.refresh_token)
    account.expires_at = timezone.now() + timezone.timedelta(seconds=int(data.get("expires_in", 86400)))
    account.save(update_fields=["access_token", "refresh_token", "expires_at"])
    return account.access_token


def plan_chunks(size):
    """Return (chunk_size, total_chunk_count) following TikTok's media transfer rules."""
    if size < MIN_CHUNK:
        return size, 1
    chunk = min(CHUNK, MAX_CHUNK)
    return chunk, max(1, size // chunk)  # remainder joins the last chunk


def api_json(r, what):
    check(r, what)
    body = r.json()
    err = body.get("error") or {}
    if err.get("code") not in (None, "ok"):
        retryable = err.get("code") in ("rate_limit_exceeded", "internal_error")
        raise PublishError(f"{what}: {err.get('code')} {err.get('message')}", retryable=retryable)
    return body.get("data") or {}


class TikTokPublisher:
    platform = "tiktok"

    def publish(self, clip, account, duration_sec=None):
        token = refresh(account)
        hdr = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"}

        # 1. creator info is required before every post (privacy options, max duration)
        info = api_json(session.post(f"{API}/post/publish/creator_info/query/", headers=hdr, timeout=TIMEOUT),
                        "TikTok creator info")
        options = info.get("privacy_level_options") or []
        privacy = conf.get("TIKTOK_PRIVACY")
        if options and privacy not in options:
            privacy = "SELF_ONLY" if "SELF_ONLY" in options else options[0]
        max_d = info.get("max_video_post_duration_sec")
        if duration_sec and max_d and duration_sec > max_d:
            raise PublishError(f"TikTok: clip is {duration_sec:.0f}s, account allows {max_d}s", retryable=False)

        # 2. init
        size = file_size(clip.video.path)
        chunk, count = plan_chunks(size)
        data = api_json(session.post(f"{API}/post/publish/video/init/", headers=hdr, json={
            "post_info": {
                "title": clip.caption(limit=2200),
                "privacy_level": privacy,
                "disable_duet": False, "disable_comment": bool(info.get("comment_disabled")),
                "disable_stitch": False, "video_cover_timestamp_ms": 1600,
            },
            "source_info": {"source": "FILE_UPLOAD", "video_size": size,
                            "chunk_size": chunk, "total_chunk_count": count},
        }, timeout=TIMEOUT), "TikTok init")
        publish_id, upload_url = data["publish_id"], data["upload_url"]

        # 3. upload chunks in order; the last chunk carries the remainder
        with open(clip.video.path, "rb") as fh:
            for i in range(count):
                start = i * chunk
                end = size - 1 if i == count - 1 else start + chunk - 1
                fh.seek(start)
                body = fh.read(end - start + 1)
                r = session.put(upload_url, data=body, headers={
                    "Content-Type": "video/mp4", "Content-Length": str(len(body)),
                    "Content-Range": f"bytes {start}-{end}/{size}"}, timeout=TIMEOUT)
                if r.status_code not in (201, 206):
                    check(r, f"TikTok chunk {i + 1}/{count}")

        # 4. wait for the post
        def status():
            d = api_json(session.post(f"{API}/post/publish/status/fetch/", headers=hdr,
                                      json={"publish_id": publish_id}, timeout=TIMEOUT), "TikTok status")
            st = d.get("status")
            if st == "FAILED":
                raise PublishError(f"TikTok post failed: {d.get('fail_reason')}", retryable=False)
            return d if st == "PUBLISH_COMPLETE" else None

        d = poll(status, timeout=900, every=8)
        ids = d.get("publicaly_available_post_id") or d.get("publicly_available_post_id") or []
        url = f"https://www.tiktok.com/@{account.name}/video/{ids[0]}" if ids and account.name else ""
        note = "ສ່ວນຕົວ (SELF_ONLY) ຈົນກວ່າແອັບຜ່ານ TikTok audit" if privacy == "SELF_ONLY" else ""
        return PublishResult(str(ids[0]) if ids else publish_id, url, note)
