# ບອກຕໍ່ຄວາມຮູ້ — Auto Post ສຳລັບ ainsteinx.com

Django app ທີ່ໃຫ້ກົດສັ່ງໂພສຄລິບລົງ **YouTube Shorts, Facebook Reels ແລະ TikTok** ພ້ອມກັນ ຜ່ານ **LINE** ຫຼື **WhatsApp** (ແລະຈາກໜ້າເວັບ `/autopost/`).

## ເຮັດວຽກແນວໃດ

```
LINE / WhatsApp ──webhook──▶ ainsteinx.com/autopost/webhook/…  ──▶ Bot (ຖາມ-ຕອບ, ປຸ່ມກົດ)
                                                                     │ ສ້າງວຽກໂພສ
                                                                     ▼
                                         autopost_worker (ແລ່ນຕະຫຼອດ) ──▶ YouTube / Facebook / TikTok
                                                                     │
                                                         ແຈ້ງຜົນ + ລິ້ງ ກັບໄປທາງແຊັດ
```

ສັ່ງໄດ້ 2 ແບບ:

1. **ຄິວ + ກົດອະນຸມັດ** — ອັບຄລິບ ແລະ ຫົວຂໍ້ ໄວ້ໃນໜ້າ `/autopost/` ລ່ວງໜ້າ. ທຸກມື້ບອດຈະສົ່ງຄລິບຕໍ່ໄປມາຖາມ ພ້ອມປຸ່ມ **ໂພສດຽວນີ້ / ພຸ່ງນີ້ / ຂ້າມ**.
2. **ສົ່ງຄລິບໃນແຊັດ** — ສົ່ງໄຟລ໌ MP4 ໃຫ້ບອດ → ບອດຖາມຫົວຂໍ້ → ພິມຫົວຂໍ້ → ກົດ **ໂພສດຽວນີ້** ຫຼື **ເຂົ້າຄິວ**.

ຄຳສັ່ງໃນແຊັດ: `ຄິວ` · `ສະຖານະ` · `ຊ່ວຍ` · `pair <ລະຫັດ>` (ຄັ້ງທຳອິດເທົ່ານັ້ນ)

ຮູບແບບຫົວຂໍ້ທີ່ພິມ:

```
EP.6 ໜຶ່ງບ່ວງ ໜັກພັນລ້ານໂຕນ!          ← ແຖວ 1 = Title (ມີ EP.x ຈະອ່ານເລກຕອນໃຫ້)
ດາວນິວຕຣອນມີມວນຫຼາຍກວ່າດວງອາທິດ...   ← ແຖວຕໍ່ໄປ = Description
#ຮູ້ບໍ່ #ອາວະກາດ #space #shorts       ← ຄຳທີ່ຂຶ້ນຕົ້ນດ້ວຍ # = Hashtags
```

---

## 1. ຕິດຕັ້ງໃນໂປຣເຈັກ Django

```bash
pip install requests cryptography
cp -r autopost /path/to/ainsteinx/          # ວາງຄູ່ກັບ app ອື່ນ
```

`settings.py`:

```python
import os
INSTALLED_APPS += ["autopost"]
MEDIA_ROOT = BASE_DIR / "media"            # ຖ້າຍັງບໍ່ມີ
DATA_UPLOAD_MAX_MEMORY_SIZE = 200 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

for k, v in os.environ.items():             # ອ່ານທຸກຄ່າ AUTOPOST_* ຈາກ .env
    if k.startswith("AUTOPOST_"):
        globals()[k] = v
AUTOPOST_PLATFORMS = ["youtube", "facebook", "tiktok"]
```

`urls.py`:

```python
path("autopost/", include("autopost.urls")),
```

```bash
python manage.py migrate
cp .env.example .env    # ແລ້ວໃສ່ຄ່າຕາມຂັ້ນຕອນລຸ່ມນີ້
```

ຖ້າໃຊ້ gunicorn ໃຫ້ຕັ້ງ `--timeout 90` ເພາະຕອນຮັບວິດີໂອຈາກແຊັດ ເວັບຕ້ອງດາວໂຫຼດໄຟລ໌ກ່ອນຕອບ.

ໜ້າ `/autopost/` ເຂົ້າໄດ້ສະເພາະ staff (ລັອກອິນຜ່ານ `/admin/`).

> ⚠️ ຕັ້ງ `AUTOPOST_FERNET_KEY` **ກ່ອນ** ເຊື່ອມຕໍ່ບັນຊີ — token ຈະຖືກເຂົ້າລະຫັດໃນຖານຂໍ້ມູນ. ຢ່າປ່ຽນ key ຫຼັງຈາກນັ້ນ (ຖ້າປ່ຽນ ຕ້ອງເຊື່ອມຕໍ່ບັນຊີໃໝ່).

## 2. ແລ່ນ worker ແລະ ຕັ້ງເວລາຖາມປະຈຳວັນ

Worker ອັບໂຫຼດວິດີໂອຢູ່ເບື້ອງຫຼັງ (webhook ຕອບກັບທັນທີ ບໍ່ຕ້ອງລໍ):

```ini
# /etc/systemd/system/autopost-worker.service
[Unit]
Description=ainsteinx autopost worker
After=network.target
[Service]
WorkingDirectory=/path/to/ainsteinx
EnvironmentFile=/path/to/ainsteinx/.env
ExecStart=/path/to/venv/bin/python manage.py autopost_worker
Restart=always
User=www-data
[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now autopost-worker
```

ຖາມປະຈຳວັນ (ຕົວຢ່າງ 11:30 ໂມງ ເວລາລາວ):

```cron
30 11 * * * cd /path/to/ainsteinx && /path/to/venv/bin/python manage.py autopost_daily_prompt
```

## 3. ເຊື່ອມຕໍ່ແພລັດຟອມໂພສ

Redirect URI ທີ່ຕ້ອງໃສ່ໃນແຕ່ລະ console:

| ແພລັດຟອມ | Redirect URI |
| --- | --- |
| YouTube | `https://ainsteinx.com/autopost/oauth/youtube/callback/` |
| Facebook | `https://ainsteinx.com/autopost/oauth/facebook/callback/` |
| TikTok | `https://ainsteinx.com/autopost/oauth/tiktok/callback/` |

ແລ້ວກົດ **ເຊື່ອມຕໍ່** ໃນໜ້າ `/autopost/` ທີລະອັນ.

### YouTube
1. [Google Cloud Console](https://console.cloud.google.com/) → ສ້າງ project → ເປີດ **YouTube Data API v3**.
2. **OAuth consent screen**: External, ໃສ່ scope `youtube.upload`. ⚠️ ກົດ **Publish app (In production)** — ຖ້າຢູ່ໂໝດ Testing, refresh token ຈະໝົດອາຍຸທຸກ 7 ມື້. ຕອນລັອກອິນຈະເຫັນ "unverified app" ໃຫ້ກົດ Advanced → ດຳເນີນການຕໍ່ (ໃຊ້ກັບບັນຊີຕົນເອງໄດ້).
3. **Credentials** → OAuth client ID → Web application → ໃສ່ Redirect URI ຂ້າງເທິງ.

### Facebook Page
1. [developers.facebook.com](https://developers.facebook.com/) → Create app → ເພີ່ມ **Facebook Login for Business**.
2. Permissions: `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`.
3. ແອັບໃນໂໝດ Development ໃຊ້ໄດ້ກັບ Page ຂອງຕົນເອງ (ບັນຊີທີ່ເປັນ admin ຂອງແອັບ). ຕອນລັອກອິນ ຕ້ອງຕິກເລືອກ Page **ບອກຕໍ່ຄວາມຮູ້**.

### TikTok
1. [developers.tiktok.com](https://developers.tiktok.com/) → Create app → ເພີ່ມ **Login Kit** ແລະ **Content Posting API** (ເປີດ Direct Post).
2. Scopes: `user.info.basic`, `video.publish`. ໃສ່ Redirect URI ຂ້າງເທິງ.
3. ⚠️ ກ່ອນແອັບຜ່ານ **audit** ຂອງ TikTok, ທຸກໂພສຈະເປັນ **ສ່ວນຕົວ (SELF_ONLY)** — ຕ້ອງເຂົ້າແອັບ TikTok ໄປເປີດເປັນສາທາລະນະເອງ. ພໍຜ່ານ audit ແລ້ວ ປ່ຽນ `AUTOPOST_TIKTOK_PRIVACY=PUBLIC_TO_EVERYONE`.

## 4. ເຊື່ອມຕໍ່ແອັບແຊັດ

### WhatsApp
1. ໃນ Meta app ດຽວກັນ → ເພີ່ມ **WhatsApp** → ຈະໄດ້ `Phone number ID` ແລະ access token (ໃຊ້ **System User token** ແບບຖາວອນ ບໍ່ແມ່ນ token ທົດລອງ 24 ຊມ).
2. Webhook: Callback URL `https://ainsteinx.com/autopost/webhook/whatsapp/`, Verify token = `AUTOPOST_WA_VERIFY_TOKEN`, subscribe field **messages**.
3. ທັກເບີ WhatsApp ຂອງບອດ ແລ້ວສົ່ງ `pair <ລະຫັດ>`.
4. **ຂໍ້ຄວາມຖາມປະຈຳວັນ**: WhatsApp ອະນຸຍາດໃຫ້ບອດສົ່ງຂໍ້ຄວາມເອງໄດ້ສະເພາະພາຍໃນ 24 ຊມ ຫຼັງເຈົ້າທັກມາລ່າສຸດ. ເພື່ອໃຫ້ຖາມໄດ້ທຸກມື້ ໃຫ້ສ້າງ **Message template** (ໝວດ Utility) ຊື່ເຊັ່ນ `daily_post`:
   - Body: `ຄລິບຕໍ່ໄປພ້ອມໂພສແລ້ວ: {{1}} ໂພສດຽວນີ້ບໍ?`
   - Quick reply buttons 3 ອັນ: `ໂພສດຽວນີ້`, `ພຸ່ງນີ້`, `ຂ້າມ`
   - ແລ້ວໃສ່ `AUTOPOST_WA_DAILY_TEMPLATE=daily_post`
5. ສົ່ງຄລິບເປັນ **Document (ໄຟລ໌)** ບໍ່ແມ່ນ Gallery — ຖ້າສົ່ງແບບວິດີໂອ WhatsApp ຈະບີບອັດຄຸນນະພາບ ແລະ ຈຳກັດ 16 MB.

### LINE
1. [LINE Developers](https://developers.line.biz/) → Provider → **Messaging API channel** (ຈະສ້າງ LINE Official Account ໃຫ້). ກວດກ່ອນວ່າປະເທດທີ່ລົງທະບຽນຮອງຮັບ.
2. ເອົາ **Channel secret** ແລະ **Channel access token (long-lived)** ໃສ່ .env.
3. Webhook URL `https://ainsteinx.com/autopost/webhook/line/` → Verify → ເປີດ **Use webhook**, ປິດ Auto-reply messages.
4. ເພີ່ມບອດເປັນໝູ່ → ສົ່ງ `pair <ລະຫັດ>`.
5. ສົ່ງຄລິບແບບ **ໄຟລ໌** (Keep/File) ຖ້າເຮັດໄດ້ ເພື່ອບໍ່ໃຫ້ LINE ບີບອັດ. ຂໍ້ຄວາມ push (ຖາມປະຈຳວັນ, ແຈ້ງຜົນ) ນັບໃນໂຄຕ້າລາຍເດືອນຂອງແພັກເກັດ LINE OA.

## 5. ຂໍ້ຈຳກັດຂອງແຕ່ລະແພລັດຟອມ (ກວດ ເດືອນ ຕ.ລ. 2026)

| | ຂໍ້ຈຳກັດ |
| --- | --- |
| YouTube | `videos.insert` ໄດ້ສູງສຸດ 100 ຄັ້ງ/ມື້ |
| Facebook Reels | 3–90 ວິນາທີ, 9:16, ສູງສຸດ 30 ໂພສ/24 ຊມ ຜ່ານ API |
| TikTok | ສ່ວນຕົວຈົນກວ່າຜ່ານ audit; ອັບໂຫຼດເປັນ chunk 5–64 MB |
| WhatsApp | ສົ່ງເອງໄດ້ພາຍໃນ 24 ຊມ, ນອກນັ້ນຕ້ອງໃຊ້ template |

ຖ້າໂພສລົ້ມ (ເຊັ່ນ server ຂອງແພລັດຟອມຂັດຂ້ອງ) worker ຈະລອງໃໝ່ອັດຕະໂນມັດ 3 ຄັ້ງ (ລໍ 2, 4 ນາທີ). ຖ້າ token ໝົດອາຍຸ/ຖືກຖອນ ຈະແຈ້ງໃນແຊັດໃຫ້ກົດ **ເຊື່ອມຕໍ່ໃໝ່** ໃນເວັບ.

## 6. ທົດສອບ

```bash
python manage.py test autopost       # 21 tests: webhook signatures, bot flow, worker retries, uploads (mocked)
```
