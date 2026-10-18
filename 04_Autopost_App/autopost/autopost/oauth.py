"""Connect YouTube, Facebook Page and TikTok accounts (OAuth 2.0, staff only)."""
import secrets
from urllib.parse import urlencode

import requests
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from . import conf
from .models import SocialAccount

TIMEOUT = (10, 60)


def callback_url(request, platform):
    path = reverse("autopost:oauth_callback", args=[platform])
    base = conf.get("PUBLIC_BASE_URL").rstrip("/")
    return f"{base}{path}" if base else request.build_absolute_uri(path)


def graph(path):
    return f"https://graph.facebook.com/{conf.get('GRAPH_VERSION')}/{path.lstrip('/')}"


@staff_member_required
def connect(request, platform):
    state = secrets.token_urlsafe(24)
    request.session[f"autopost_state_{platform}"] = state
    redirect_uri = callback_url(request, platform)
    if platform == "youtube":
        url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
            "client_id": conf.get("GOOGLE_CLIENT_ID"), "redirect_uri": redirect_uri, "response_type": "code",
            # force-ssl is needed to attach subtitle tracks (captions.insert).
            "scope": "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly "
                     "https://www.googleapis.com/auth/youtube.force-ssl",
            "access_type": "offline", "prompt": "consent", "state": state})
    elif platform == "facebook":
        url = f"https://www.facebook.com/{conf.get('GRAPH_VERSION')}/dialog/oauth?" + urlencode({
            "client_id": conf.get("META_APP_ID"), "redirect_uri": redirect_uri, "state": state,
            "scope": "pages_show_list,pages_read_engagement,pages_manage_posts"})
    elif platform == "tiktok":
        url = "https://www.tiktok.com/v2/auth/authorize/?" + urlencode({
            "client_key": conf.get("TIKTOK_CLIENT_KEY"), "redirect_uri": redirect_uri, "response_type": "code",
            "scope": "user.info.basic,video.publish", "state": state})
    else:
        return HttpResponseBadRequest("unknown platform")
    return redirect(url)


@staff_member_required
def oauth_callback(request, platform):
    if request.GET.get("state") != request.session.pop(f"autopost_state_{platform}", None):
        return HttpResponseBadRequest("state mismatch — start the connection again")
    if "error" in request.GET or "code" not in request.GET:
        messages.error(request, f"{platform}: {request.GET.get('error_description') or request.GET.get('error') or 'cancelled'}")
        return redirect("autopost:dashboard")
    code, redirect_uri = request.GET["code"], callback_url(request, platform)
    try:
        name = {"youtube": _youtube, "facebook": _facebook, "tiktok": _tiktok}[platform](code, redirect_uri)
        messages.success(request, f"✅ ເຊື່ອມຕໍ່ {platform}: {name}")
    except Exception as e:  # noqa: BLE001
        messages.error(request, f"{platform}: {e}")
    return redirect("autopost:dashboard")


def _save(platform, **fields):
    acc, _ = SocialAccount.objects.get_or_create(platform=platform)
    for k, v in fields.items():
        setattr(acc, k, v)
    acc.enabled = True
    acc.save()
    return acc


def _youtube(code, redirect_uri):
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "code": code, "client_id": conf.get("GOOGLE_CLIENT_ID"), "client_secret": conf.get("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": redirect_uri, "grant_type": "authorization_code"}, timeout=TIMEOUT)
    r.raise_for_status()
    tok = r.json()
    if "refresh_token" not in tok:
        raise RuntimeError("Google did not return a refresh token — remove the app at myaccount.google.com/permissions and connect again")
    ch = requests.get("https://www.googleapis.com/youtube/v3/channels", params={"part": "snippet", "mine": "true"},
                      headers={"Authorization": f"Bearer {tok['access_token']}"}, timeout=TIMEOUT)
    ch.raise_for_status()
    items = ch.json().get("items") or [{}]
    _save("youtube", name=items[0].get("snippet", {}).get("title", ""), external_id=items[0].get("id", ""),
          access_token=tok["access_token"], refresh_token=tok["refresh_token"],
          expires_at=timezone.now() + timezone.timedelta(seconds=int(tok.get("expires_in", 3600))))
    return items[0].get("snippet", {}).get("title", "YouTube")


def _facebook(code, redirect_uri):
    app = {"client_id": conf.get("META_APP_ID"), "client_secret": conf.get("META_APP_SECRET")}
    r = requests.get(graph("oauth/access_token"), params={**app, "redirect_uri": redirect_uri, "code": code}, timeout=TIMEOUT)
    r.raise_for_status()
    short = r.json()["access_token"]
    r = requests.get(graph("oauth/access_token"), params={**app, "grant_type": "fb_exchange_token",
                                                         "fb_exchange_token": short}, timeout=TIMEOUT)
    r.raise_for_status()
    long_user = r.json()["access_token"]
    r = requests.get(graph("me/accounts"), params={"fields": "id,name,access_token", "access_token": long_user},
                     timeout=TIMEOUT)
    r.raise_for_status()
    pages = r.json().get("data", [])
    want = conf.get("FB_PAGE_ID")
    page = next((p for p in pages if not want or p["id"] == want), None)
    if not page:
        raise RuntimeError("no Facebook Page found (did you tick the Page in the login dialog?)")
    # A Page token obtained from a long-lived user token does not expire.
    _save("facebook", name=page["name"], external_id=page["id"], access_token=page["access_token"],
          refresh_token="", expires_at=None)
    return page["name"]


def _tiktok(code, redirect_uri):
    r = requests.post("https://open.tiktokapis.com/v2/oauth/token/", data={
        "client_key": conf.get("TIKTOK_CLIENT_KEY"), "client_secret": conf.get("TIKTOK_CLIENT_SECRET"),
        "code": code, "grant_type": "authorization_code", "redirect_uri": redirect_uri},
        headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=TIMEOUT)
    r.raise_for_status()
    tok = r.json()
    if "access_token" not in tok:
        raise RuntimeError(str(tok))
    u = requests.get("https://open.tiktokapis.com/v2/user/info/", params={"fields": "open_id,display_name,username"},
                     headers={"Authorization": f"Bearer {tok['access_token']}"}, timeout=TIMEOUT)
    user = (u.json().get("data") or {}).get("user", {}) if u.ok else {}
    _save("tiktok", name=user.get("username") or user.get("display_name", ""), external_id=tok.get("open_id", ""),
          access_token=tok["access_token"], refresh_token=tok.get("refresh_token", ""),
          expires_at=timezone.now() + timezone.timedelta(seconds=int(tok.get("expires_in", 86400))))
    return user.get("display_name") or "TikTok"
