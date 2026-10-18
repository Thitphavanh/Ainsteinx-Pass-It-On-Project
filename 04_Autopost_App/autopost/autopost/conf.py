"""All settings are read from Django settings with the AUTOPOST_ prefix (see .env.example)."""
from django.conf import settings

DEFAULTS = {
    "PUBLIC_BASE_URL": "",               # e.g. https://ainsteinx.com  (used for OAuth redirect URIs)
    "FERNET_KEY": "",                    # encrypts stored tokens; generate with: python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"
    "PAIR_CODE": "",                     # chat users send "pair <code>" once to become an operator
    "PLATFORMS": ["youtube", "facebook", "tiktok"],
    "MAX_ATTEMPTS": 3,
    # YouTube (Google Cloud OAuth client, type "Web application")
    "GOOGLE_CLIENT_ID": "",
    "GOOGLE_CLIENT_SECRET": "",
    "YOUTUBE_PRIVACY": "public",         # public | unlisted | private
    "YOUTUBE_CATEGORY_ID": "27",         # 27 = Education
    # Facebook Page (Meta app with Facebook Login)
    "META_APP_ID": "",
    "META_APP_SECRET": "",
    "GRAPH_VERSION": "v25.0",
    "FB_PAGE_ID": "",                    # optional: which Page to post to if you manage several
    # TikTok (TikTok for Developers app with Content Posting API)
    "TIKTOK_CLIENT_KEY": "",
    "TIKTOK_CLIENT_SECRET": "",
    "TIKTOK_PRIVACY": "SELF_ONLY",       # unaudited apps can only post SELF_ONLY; switch to PUBLIC_TO_EVERYONE after audit
    # LINE Messaging API
    "LINE_CHANNEL_SECRET": "",
    "LINE_CHANNEL_ACCESS_TOKEN": "",
    # WhatsApp Cloud API
    "WA_PHONE_NUMBER_ID": "",
    "WA_ACCESS_TOKEN": "",
    "WA_VERIFY_TOKEN": "",
    "WA_DAILY_TEMPLATE": "",             # approved template name for the daily prompt (needed outside the 24 h window)
    "WA_TEMPLATE_LANG": "lo",
}


def get(name):
    return getattr(settings, f"AUTOPOST_{name}", DEFAULTS[name])
