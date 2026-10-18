import base64
import hashlib
import hmac
import json
import os
import tempfile
from unittest import mock

from cryptography.fernet import Fernet
from django.core.files.base import ContentFile
from django.db import connection
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from autopost import jobs
from autopost.bot import Bot, parse_caption
from autopost.chat.base import ChatAdapter, Incoming
from autopost.chat.line import LineAdapter
from autopost.chat.whatsapp import WhatsAppAdapter
from autopost.models import ChatOperator, Clip, PlatformPost, SocialAccount
from autopost.publishers import PublishError, PublishResult
from autopost.publishers import tiktok as tt
from autopost.publishers import youtube as yt
from autopost.publishers import facebook as fb

MEDIA = tempfile.mkdtemp()
KEY = Fernet.generate_key().decode()
SETTINGS = dict(MEDIA_ROOT=MEDIA, AUTOPOST_FERNET_KEY=KEY, AUTOPOST_PAIR_CODE="1234",
                AUTOPOST_LINE_CHANNEL_SECRET="linesecret", AUTOPOST_META_APP_SECRET="metasecret",
                AUTOPOST_WA_VERIFY_TOKEN="verifyme")


class Resp:
    def __init__(self, status=200, body=None, headers=None):
        self.status_code, self._body, self.headers = status, body or {}, headers or {}
        self.text = json.dumps(self._body)
        self.ok = status < 400

    def json(self):
        return self._body


class FakeAdapter(ChatAdapter):
    channel = "line"

    def __init__(self):
        super().__init__()
        self.sent = []

    def send_text(self, to, text, reply_token=None):
        self.sent.append(("text", to, text, None))

    def send_buttons(self, to, text, buttons, reply_token=None):
        self.sent.append(("buttons", to, text, buttons))

    def download(self, msg, dest_path):
        with open(dest_path, "wb") as fh:
            fh.write(b"\x00" * 1000)


def make_clip(**kw):
    c = Clip(title="ມື້ໜຶ່ງເທິງດາວພະສຸກ", hashtags="#ຮູ້ບໍ່ #space", **kw)
    c.video.save("t.mp4", ContentFile(b"\x00" * 3000), save=False)
    c.save()
    return c


@override_settings(**SETTINGS)
class EncryptionTests(TestCase):
    def test_tokens_encrypted_at_rest(self):
        SocialAccount.objects.create(platform="youtube", access_token="secret-token", refresh_token="r")
        with connection.cursor() as cur:
            cur.execute("select access_token from autopost_socialaccount")
            raw = cur.fetchone()[0]
        self.assertTrue(raw.startswith("enc:"))
        self.assertNotIn("secret-token", raw)
        self.assertEqual(SocialAccount.objects.get().access_token, "secret-token")


@override_settings(**SETTINGS)
class LineTests(TestCase):
    def req(self, body, good=True):
        raw = json.dumps(body).encode()
        sig = base64.b64encode(hmac.new(b"linesecret", raw, hashlib.sha256).digest()).decode()
        return RequestFactory().post("/x", data=raw, content_type="application/json",
                                     HTTP_X_LINE_SIGNATURE=sig if good else "nope")

    def test_parse_and_signature(self):
        body = {"events": [
            {"type": "message", "replyToken": "rt", "source": {"type": "user", "userId": "U1"},
             "message": {"type": "text", "id": "m1", "text": "ຄິວ"}},
            {"type": "postback", "replyToken": "rt2", "webhookEventId": "e2", "source": {"type": "user", "userId": "U1"},
             "postback": {"data": "post:5"}},
            {"type": "message", "replyToken": "rt3", "source": {"type": "user", "userId": "U1"},
             "message": {"type": "file", "id": "m3", "fileName": "EP01.mp4"}},
            {"type": "message", "source": {"type": "group", "groupId": "G"}, "message": {"type": "text", "id": "g"}}]}
        msgs = LineAdapter().parse(self.req(body))
        self.assertEqual([m.kind for m in msgs], ["text", "postback", "video"])
        self.assertEqual(msgs[1].payload, "post:5")
        from autopost.chat import BadSignature
        with self.assertRaises(BadSignature):
            LineAdapter().parse(self.req(body, good=False))

    def test_webhook_rejects_bad_signature(self):
        r = self.client.post("/autopost/webhook/line/", data=b"{}", content_type="application/json",
                             HTTP_X_LINE_SIGNATURE="bad")
        self.assertEqual(r.status_code, 403)


@override_settings(**SETTINGS)
class WhatsAppTests(TestCase):
    def test_verify_handshake(self):
        r = self.client.get("/autopost/webhook/whatsapp/", {"hub.mode": "subscribe", "hub.verify_token": "verifyme",
                                                              "hub.challenge": "42"})
        self.assertEqual(r.content, b"42")
        r = self.client.get("/autopost/webhook/whatsapp/", {"hub.mode": "subscribe", "hub.verify_token": "x"})
        self.assertEqual(r.status_code, 403)

    def test_parse(self):
        body = {"entry": [{"changes": [{"value": {"contacts": [{"wa_id": "856201", "profile": {"name": "Thit"}}],
                "messages": [
                    {"from": "856201", "id": "w1", "type": "interactive",
                     "interactive": {"type": "button_reply", "button_reply": {"id": "post:3", "title": "ໂພສ"}}},
                    {"from": "856201", "id": "w2", "type": "document",
                     "document": {"id": "MEDIA", "mime_type": "video/mp4", "filename": "a.mp4"}},
                    {"from": "856201", "id": "w3", "type": "button", "button": {"payload": "skip:3"}}]}}]}]}
        raw = json.dumps(body).encode()
        sig = "sha256=" + hmac.new(b"metasecret", raw, hashlib.sha256).hexdigest()
        req = RequestFactory().post("/x", data=raw, content_type="application/json", HTTP_X_HUB_SIGNATURE_256=sig)
        msgs = WhatsAppAdapter().parse(req)
        self.assertEqual([(m.kind, m.payload or m.media_id) for m in msgs],
                         [("postback", "post:3"), ("video", "MEDIA"), ("postback", "skip:3")])
        self.assertEqual(msgs[0].name, "Thit")

    def test_daily_prompt_uses_template_outside_24h(self):
        op = ChatOperator.objects.create(channel="whatsapp", external_id="856201",
                                         last_inbound_at=timezone.now() - timezone.timedelta(days=2))
        clip = make_clip(status=Clip.Status.READY)
        a = WhatsAppAdapter()
        with override_settings(AUTOPOST_WA_DAILY_TEMPLATE="daily_post"), mock.patch.object(a, "_send") as send:
            a.send_daily_prompt(op, clip, [("ໂພສດຽວນີ້", f"post:{clip.pk}")])
        body = send.call_args[0][0]
        self.assertEqual(body["type"], "template")
        self.assertEqual(body["template"]["components"][1]["parameters"][0]["payload"], f"post:{clip.pk}")


@override_settings(**SETTINGS)
class BotTests(TestCase):
    def setUp(self):
        self.a = FakeAdapter()
        self.bot = Bot(self.a)

    def msg(self, **kw):
        kw.setdefault("message_id", os.urandom(6).hex())
        return Incoming(channel="line", user_id="U1", **kw)

    def test_unpaired_user_is_refused_then_pairs(self):
        self.bot.handle(self.msg(kind="text", text="ຄິວ"))
        self.assertIn("pair", self.a.sent[-1][2])
        self.bot.handle(self.msg(kind="text", text="pair 1234"))
        self.assertTrue(ChatOperator.objects.filter(external_id="U1", is_active=True).exists())

    def test_redelivery_ignored(self):
        ChatOperator.objects.create(channel="line", external_id="U1")
        m = self.msg(kind="text", text="ຊ່ວຍ")
        self.bot.handle(m)
        self.bot.handle(Incoming(channel="line", user_id="U1", kind="text", text="ຊ່ວຍ", message_id=m.message_id))
        self.assertEqual(len(self.a.sent), 1)

    def test_video_caption_then_post(self):
        ChatOperator.objects.create(channel="line", external_id="U1")
        SocialAccount.objects.create(platform="youtube", access_token="a")
        SocialAccount.objects.create(platform="tiktok", access_token="a")
        self.bot.handle(self.msg(kind="video", media_id="M"))
        clip = Clip.objects.get()
        self.assertEqual(clip.status, Clip.Status.DRAFT)
        self.bot.handle(self.msg(kind="text", text="EP.6 ດາວນິວຕຣອນ\nໜຶ່ງບ່ວງ ໜັກພັນລ້ານໂຕນ\n#ຮູ້ບໍ່ #space"))
        clip.refresh_from_db()
        self.assertEqual((clip.title, clip.episode, clip.hashtags), ("EP.6 ດາວນິວຕຣອນ", 6, "#ຮູ້ບໍ່ #space"))
        self.assertEqual(self.a.sent[-1][0], "buttons")
        self.bot.handle(self.msg(kind="postback", payload=f"post:{clip.pk}"))
        clip.refresh_from_db()
        self.assertEqual(clip.status, Clip.Status.POSTING)
        self.assertEqual(sorted(clip.posts.values_list("platform", flat=True)), ["tiktok", "youtube"])

    def test_post_without_accounts_warns(self):
        ChatOperator.objects.create(channel="line", external_id="U1")
        clip = make_clip(status=Clip.Status.READY)
        self.bot.handle(self.msg(kind="postback", payload=f"post:{clip.pk}"))
        self.assertIn("ຍັງບໍ່ໄດ້ເຊື່ອມຕໍ່", self.a.sent[-1][2])

    def test_parse_caption(self):
        p = parse_caption("ຫົວຂໍ້ #a\nລາຍລະອຽດ\n#b #a")
        self.assertEqual(p["title"], "ຫົວຂໍ້")
        self.assertEqual(p["description"], "ລາຍລະອຽດ")
        self.assertEqual(p["hashtags"], "#a #b")


@override_settings(**SETTINGS)
class WorkerTests(TestCase):
    def setUp(self):
        self.op = ChatOperator.objects.create(channel="line", external_id="U1")
        SocialAccount.objects.create(platform="youtube", access_token="a")
        SocialAccount.objects.create(platform="facebook", access_token="a", external_id="P")
        self.clip = make_clip(status=Clip.Status.READY)
        from autopost.bot import start_posting
        start_posting(self.clip, self.op)

    def run_all(self, publisher):
        fake = FakeAdapter()
        with mock.patch("autopost.jobs.get_publisher", return_value=publisher), \
                mock.patch("autopost.jobs.get_adapter", return_value=fake):
            while (p := jobs.claim_next()):
                jobs.run_one(p)
        return fake

    def test_success_notifies_with_links(self):
        pub = mock.Mock()
        pub.publish.side_effect = [PublishResult("yt1", "https://youtube.com/shorts/yt1"),
                                   PublishResult("fb1", "https://www.facebook.com/reel/fb1")]
        fake = self.run_all(pub)
        self.clip.refresh_from_db()
        self.assertEqual(self.clip.status, Clip.Status.POSTED)
        self.assertIn("youtube.com/shorts/yt1", fake.sent[-1][2])

    def test_retry_then_fail(self):
        pub = mock.Mock()
        pub.publish.side_effect = PublishError("HTTP 500", retryable=True)
        self.run_all(pub)
        p = PlatformPost.objects.first()
        self.assertEqual((p.status, p.attempts), (PlatformPost.Status.QUEUED, 1))
        self.assertGreater(p.next_attempt_at, timezone.now())
        PlatformPost.objects.update(next_attempt_at=timezone.now())
        self.run_all(pub)
        PlatformPost.objects.update(next_attempt_at=timezone.now())
        fake = self.run_all(pub)
        self.assertEqual(set(PlatformPost.objects.values_list("status", flat=True)), {"failed"})
        self.clip.refresh_from_db()
        self.assertEqual(self.clip.status, Clip.Status.FAILED)
        self.assertIn("❌", fake.sent[-1][2])

    def test_partial(self):
        pub = mock.Mock()
        pub.publish.side_effect = [PublishResult("yt1", "u"), PublishError("token revoked", retryable=False)]
        self.run_all(pub)
        self.clip.refresh_from_db()
        self.assertEqual(self.clip.status, Clip.Status.PARTIAL)


@override_settings(**SETTINGS)
class PublisherTests(TestCase):
    def setUp(self):
        self.clip = make_clip()

    def test_tiktok_chunk_plan(self):
        self.assertEqual(tt.plan_chunks(4_000_000), (4_000_000, 1))
        self.assertEqual(tt.plan_chunks(23 * 1024 * 1024), (10 * 1024 * 1024, 2))
        self.assertEqual(tt.plan_chunks(50_000_123)[1], 4)  # 10 MiB chunks, remainder in last

    def test_tiktok_flow(self):
        acc = SocialAccount.objects.create(platform="tiktok", name="boktor", access_token="t",
                                           expires_at=timezone.now() + timezone.timedelta(hours=5))
        posts = iter([
            Resp(200, {"data": {"privacy_level_options": ["PUBLIC_TO_EVERYONE", "SELF_ONLY"],
                                "max_video_post_duration_sec": 600}, "error": {"code": "ok"}}),
            Resp(200, {"data": {"publish_id": "pid", "upload_url": "https://up"}, "error": {"code": "ok"}}),
            Resp(200, {"data": {"status": "PUBLISH_COMPLETE", "publicaly_available_post_id": [777]},
                       "error": {"code": "ok"}}),
        ])
        with mock.patch.object(tt.session, "post", side_effect=lambda *a, **k: next(posts)) as post, \
                mock.patch.object(tt.session, "put", return_value=Resp(201)) as put:
            res = tt.TikTokPublisher().publish(self.clip, acc)
        init = post.call_args_list[1].kwargs["json"]
        self.assertEqual(init["post_info"]["privacy_level"], "SELF_ONLY")
        self.assertEqual(init["source_info"]["total_chunk_count"], 1)
        self.assertEqual(put.call_args.kwargs["headers"]["Content-Range"], "bytes 0-2999/3000")
        self.assertEqual(res.url, "https://www.tiktok.com/@boktor/video/777")
        self.assertIn("audit", res.note)

    def test_youtube_resumable(self):
        acc = SocialAccount.objects.create(platform="youtube", access_token="t",
                                           expires_at=timezone.now() + timezone.timedelta(hours=1))
        with mock.patch.object(yt, "CHUNK", 2048), \
                mock.patch.object(yt.session, "post", return_value=Resp(200, headers={"Location": "https://loc"})) as post, \
                mock.patch.object(yt.session, "put", side_effect=[Resp(308, headers={"Range": "bytes=0-2047"}),
                                                                  Resp(200, {"id": "abc"})]) as put:
            res = yt.YouTubePublisher().publish(self.clip, acc)
        self.assertEqual(res.url, "https://youtube.com/shorts/abc")
        self.assertEqual(post.call_args.kwargs["json"]["status"]["selfDeclaredMadeForKids"], False)
        self.assertEqual(put.call_args_list[1].kwargs["headers"]["Content-Range"], "bytes 2048-2999/3000")

    def _youtube_with_subtitle(self, caption_resp):
        acc = SocialAccount.objects.create(platform="youtube", access_token="t",
                                           expires_at=timezone.now() + timezone.timedelta(hours=1))
        self.clip.subtitle_th.save("ep.srt", ContentFile(b"1\n00:00:00,000 --> 00:00:01,000\nhi\n"))
        posts = iter([Resp(200, headers={"Location": "https://loc"}), caption_resp])
        with mock.patch.object(yt.session, "post", side_effect=lambda *a, **k: next(posts)) as post, \
                mock.patch.object(yt.session, "put", return_value=Resp(200, {"id": "abc"})):
            res = yt.YouTubePublisher().publish(self.clip, acc)
        return res, post

    def test_youtube_attaches_thai_subtitle(self):
        res, post = self._youtube_with_subtitle(Resp(200, {"id": "cap"}))
        call = post.call_args_list[1]
        self.assertEqual(call.args[0], yt.CAPTIONS_URL)
        meta = json.loads(call.kwargs["files"]["metadata"][1])
        self.assertEqual(meta["snippet"], {"videoId": "abc", "language": "th", "name": "ไทย", "isDraft": False})
        self.assertIn(b"hi", call.kwargs["files"]["media"][1])
        self.assertIn("ຊັບໄຕເຕີ້ລ໌ໄທແລ້ວ", res.note)

    def test_youtube_subtitle_failure_keeps_the_post(self):
        res, _ = self._youtube_with_subtitle(Resp(403, {"error": "insufficientPermissions"}))
        self.assertEqual(res.url, "https://youtube.com/shorts/abc")
        self.assertIn("ເຊື່ອມຕໍ່ YouTube ໃໝ່", res.note)

    def test_youtube_refreshes_expired_token(self):
        acc = SocialAccount.objects.create(platform="youtube", access_token="old", refresh_token="r",
                                           expires_at=timezone.now() - timezone.timedelta(minutes=1))
        with mock.patch.object(yt.session, "post", return_value=Resp(200, {"access_token": "new", "expires_in": 3600})):
            self.assertEqual(yt.refresh(acc), "new")
        acc.refresh_from_db()
        self.assertEqual(acc.access_token, "new")

    def test_facebook_reel(self):
        acc = SocialAccount.objects.create(platform="facebook", access_token="pt", external_id="PAGE")
        posts = iter([Resp(200, {"video_id": "V1"}), Resp(200, {"success": True}), Resp(200, {"success": True})])
        with mock.patch.object(fb.session, "post", side_effect=lambda *a, **k: next(posts)) as post, \
                mock.patch.object(fb.session, "get", return_value=Resp(200, {"status": {
                    "video_status": "ready", "publishing_phase": {"status": "complete"}}})):
            res = fb.FacebookPublisher().publish(self.clip, acc)
        self.assertEqual(res.url, "https://www.facebook.com/reel/V1")
        self.assertIn("rupload.facebook.com/video-upload", post.call_args_list[1].args[0])
        self.assertEqual(post.call_args_list[2].kwargs["data"]["video_state"], "PUBLISHED")


@override_settings(**SETTINGS)
class DashboardTests(TestCase):
    def test_dashboard_and_post_now(self):
        from django.contrib.auth.models import User
        User.objects.create_superuser("admin", "a@a.a", "pw")
        self.client.login(username="admin", password="pw")
        clip = make_clip(status=Clip.Status.READY)
        r = self.client.get("/autopost/")
        self.assertContains(r, "ບອກຕໍ່")
        self.assertContains(r, str(clip))
        SocialAccount.objects.create(platform="youtube", access_token="a")
        self.client.post(f"/autopost/clip/{clip.pk}/post/")
        clip.refresh_from_db()
        self.assertEqual(clip.status, Clip.Status.POSTING)

    def test_connect_redirects_with_state(self):
        from django.contrib.auth.models import User
        User.objects.create_superuser("admin", "a@a.a", "pw")
        self.client.login(username="admin", password="pw")
        with override_settings(AUTOPOST_TIKTOK_CLIENT_KEY="ck", AUTOPOST_PUBLIC_BASE_URL="https://ainsteinx.com"):
            r = self.client.get("/autopost/connect/tiktok/")
        self.assertIn("tiktok.com/v2/auth/authorize", r["Location"])
        self.assertIn("redirect_uri=https%3A%2F%2Fainsteinx.com%2Fautopost%2Foauth%2Ftiktok%2Fcallback%2F", r["Location"])
        r = self.client.get("/autopost/oauth/tiktok/callback/", {"code": "c", "state": "wrong"})
        self.assertEqual(r.status_code, 400)


def fake_mp4(path, seconds):
    """Smallest file mp4_duration() can read: ftyp + moov/mvhd (version 0)."""
    import struct
    mvhd_body = bytes(4) + bytes(8) + struct.pack(">II", 1000, int(seconds * 1000)) + bytes(80)
    mvhd = struct.pack(">I4s", 8 + len(mvhd_body), b"mvhd") + mvhd_body
    moov = struct.pack(">I4s", 8 + len(mvhd), b"moov") + mvhd
    ftyp = struct.pack(">I4s", 16, b"ftyp") + b"isom" + bytes(4)
    path.write_bytes(ftyp + moov)


def fake_srt(path, end, lines):
    blocks = [f"{i}\n00:00:00,000 --> 00:00:{end:06.3f}\n{text}\n".replace(".", ",", 1)
              for i, text in enumerate(lines, 1)]
    path.write_text("\n".join(blocks), encoding="utf-8")


@override_settings(**SETTINGS)
class ImportTests(TestCase):
    def setUp(self):
        from pathlib import Path
        self.root = Path(tempfile.mkdtemp())
        eps = self.root / "01_Episodes"
        ep4 = eps / "EP04_Eiffel"
        ep4.mkdir(parents=True)
        fake_mp4(ep4 / "EP04_Eiffel_3D_9x16_voice.mp4", 42.5)
        fake_mp4(ep4 / "EP04_Eiffel_60s_voice_music.mp4", 60)
        fake_mp4(ep4 / "EP04_Eiffel_3D_9x16_noaudio.mp4", 42.5)
        (ep4 / "EP04_social_post.txt").write_text(
            "YouTube Title:\nຍອດຫໍໄອເຟລ ເຄື່ອນທີ່ທຸກມື້! #shorts\n\nDescription:\nເຫຼັກຂະຫຍາຍຕົວ\n"
            "#ບອກຕໍ່ຄວາມຮູ້ #ຮູ້ບໍ່EP4\n\nTikTok:\nບໍ່ໃຊ້ #fyp\n", encoding="utf-8")
        ep1 = eps / "EP01_Venus"
        ep1.mkdir()
        fake_mp4(ep1 / "EP01_Venus_voice.mp4", 40)
        fake_srt(ep1 / "EP01_voiceover.srt", 38.6,
                 ["ຮູ້ບໍ່ວ່າ 1 ມື້ ຍາວກວ່າ 1 ປີ?", "ນັ້ນຄື ດາວພະສຸກ.", "ຖ້າຮູ້ແລ້ວ ຢ່າລືມ ບອກຕໍ່ ໃຫ້ໝູ່ເດີ້!"])
        extra = eps / "Extra_Mekong_MapStory"
        extra.mkdir()
        fake_mp4(extra / "Mekong_MapStory_9x16.mp4", 51)
        subs = self.root / "06_Subtitles_TH_upload"
        subs.mkdir()
        fake_srt(subs / "EP04_3D_43s_subtitle_TH.srt", 42.3, ["ยอดหอไอเฟล"])
        plan = self.root / "05_Plan"
        plan.mkdir()
        (plan / "episode_log.json").write_text(json.dumps({"done": [
            {"ep": 1, "cat": "ອາວະກາດ"}, {"ep": 4, "cat": "ວິສະວະກຳ"}]}), encoding="utf-8")

    def run_import(self, *args):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command("autopost_import", str(self.root), *args, stdout=out)
        return out.getvalue()

    def test_mp4_duration_reader(self):
        from autopost.management.commands.autopost_import import mp4_duration
        self.assertAlmostEqual(mp4_duration(self.root / "01_Episodes/EP04_Eiffel/EP04_Eiffel_3D_9x16_voice.mp4"), 42.5)

    def test_subtitle_picks_the_matching_cut(self):
        self.run_import()
        clip = Clip.objects.get(episode=4)
        self.assertIn("3D_9x16_voice", clip.video.name)             # 43 s cut, not the 60 s one
        self.assertIn("EP04_3D_43s_subtitle_TH", clip.subtitle_th.name)
        self.assertEqual(clip.title, "ຍອດຫໍໄອເຟລ ເຄື່ອນທີ່ທຸກມື້!")
        self.assertEqual(clip.description, "ເຫຼັກຂະຫຍາຍຕົວ")
        self.assertEqual(clip.hashtags, "#ບອກຕໍ່ຄວາມຮູ້ #ຮູ້ບໍ່EP4 #shorts")
        self.assertEqual((clip.category, clip.status, clip.source), ("ວິສະວະກຳ", Clip.Status.READY, "EP04_Eiffel"))

    def test_voiceover_fallback_and_draft(self):
        self.run_import()
        ep1 = Clip.objects.get(episode=1)
        self.assertEqual(ep1.title, "ຮູ້ບໍ່ວ່າ 1 ມື້ ຍາວກວ່າ 1 ປີ?")
        self.assertEqual(ep1.description, "ນັ້ນຄື ດາວພະສຸກ.")          # closing call-to-action dropped
        self.assertEqual(ep1.hashtags, "#ບອກຕໍ່ຄວາມຮູ້ #ຮູ້ບໍ່EP1 #ອາວະກາດ #shorts")
        self.assertFalse(ep1.subtitle_th)
        mekong = Clip.objects.get(source="Extra_Mekong_MapStory")
        self.assertEqual(mekong.status, Clip.Status.DRAFT)

    def test_import_is_idempotent_and_matches_manual_clips(self):
        manual = make_clip(episode=4, status=Clip.Status.READY)
        out = self.run_import()
        self.assertIn("exists", out)
        self.assertEqual(Clip.objects.filter(episode=4).count(), 1)
        self.run_import()
        self.assertEqual(Clip.objects.count(), 3)
        self.run_import("--update")
        manual.refresh_from_db()
        self.assertEqual(manual.source, "EP04_Eiffel")
        self.assertTrue(manual.subtitle_th)
        self.assertEqual(manual.video.name.rsplit("/", 1)[-1][:1], "t")  # video untouched

    def test_dry_run_saves_nothing(self):
        self.assertIn("dry run", self.run_import("--dry-run"))
        self.assertEqual(Clip.objects.count(), 0)
