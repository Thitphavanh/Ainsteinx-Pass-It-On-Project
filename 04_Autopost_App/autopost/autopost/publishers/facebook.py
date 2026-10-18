"""Facebook Page Reels via Graph API (video_reels: start → rupload → finish)."""
from .. import conf
from .base import PublishError, PublishResult, TIMEOUT, check, file_size, poll, session


def graph(path):
    return f"https://graph.facebook.com/{conf.get('GRAPH_VERSION')}/{path.lstrip('/')}"


class FacebookPublisher:
    platform = "facebook"

    def publish(self, clip, account):
        page_id, token = account.external_id, account.access_token
        if not (page_id and token):
            raise PublishError("Facebook: Page not connected", retryable=False)

        r = session.post(graph(f"{page_id}/video_reels"), data={"upload_phase": "start", "access_token": token},
                         timeout=TIMEOUT)
        if r.status_code in (400, 401, 403):
            raise PublishError(f"Facebook start rejected: {r.text[:400]}", retryable=False)
        check(r, "Facebook reel start")
        video_id = r.json()["video_id"]

        size = file_size(clip.video.path)
        with open(clip.video.path, "rb") as fh:
            r = session.post(f"https://rupload.facebook.com/video-upload/{conf.get('GRAPH_VERSION')}/{video_id}",
                             data=fh, headers={"Authorization": f"OAuth {token}", "offset": "0",
                                               "file_size": str(size), "Content-Type": "application/octet-stream"},
                             timeout=TIMEOUT)
        check(r, "Facebook reel upload")

        r = session.post(graph(f"{page_id}/video_reels"), data={
            "access_token": token, "video_id": video_id, "upload_phase": "finish",
            "video_state": "PUBLISHED", "description": clip.caption(limit=2200),
        }, timeout=TIMEOUT)
        if r.status_code == 400:
            raise PublishError(f"Facebook publish rejected: {r.text[:400]}", retryable=False)
        check(r, "Facebook reel publish")

        def done():
            s = session.get(graph(video_id), params={"fields": "status", "access_token": token}, timeout=TIMEOUT)
            check(s, "Facebook status")
            st = s.json().get("status", {})
            for phase in ("uploading_phase", "processing_phase", "publishing_phase"):
                ph = st.get(phase) or {}
                if ph.get("status") == "error":
                    raise PublishError(f"Facebook {phase} error: {ph.get('error')}", retryable=False)
            pub = (st.get("publishing_phase") or {}).get("status")
            return pub == "complete" or st.get("video_status") == "ready"

        poll(done, timeout=900, every=10)
        return PublishResult(video_id, f"https://www.facebook.com/reel/{video_id}")
