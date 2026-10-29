"""ທົດລອງສຽງ Google AI Studio (Gemini TTS) ສຳລັບ EP.15.
ໃຊ້: cd ~/My-Project/Ainsteinx-Pass-It-On-Project && python3 tools/gemini_tts_test.py
ອ່ານ GOOGLE_STUDIO_API_KEY ຈາກ .env (ບໍ່ພິມ key ອອກມາ). ຜົນ: 01_Episodes/EP15_SpaceX/gemini_tts_test/*.wav"""
import json, os, sys, base64, urllib.request, urllib.error, wave
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
key = None
for l in open(os.path.join(ROOT, ".env")):
    if l.strip().startswith("GOOGLE_STUDIO_API_KEY"):
        key = l.split("=", 1)[1].strip().strip('"').strip("'")
if not key: sys.exit("ບໍ່ພົບ GOOGLE_STUDIO_API_KEY ໃນ .env")
OUT = os.path.join(ROOT, "01_Episodes/EP15_SpaceX/gemini_tts_test"); os.makedirs(OUT, exist_ok=True)
MODELS = ["gemini-2.5-flash-preview-tts", "gemini-2.5-pro-preview-tts"]
VOICES = ["Charon", "Orus", "Puck"]
STYLE = "ອ່ານເປັນພາສາລາວ ດ້ວຍນ້ຳສຽງຜູ້ບັນຍາຍສາລະຄະດີ ອົບອຸ່ນ ຊັດເຈນ ຕື່ນເຕັ້ນເລັກນ້ອຍ: "
TEXT = ("ຮູ້ບໍ່? ບໍລິສັດຈະຫຼວດທີ່ດັງທີ່ສຸດໃນໂລກ ເລີ່ມຕົ້ນຈາກຈະຫຼວດທີ່ຜິດຫວັງ! "
        "ບໍລິສັດນີ້ຊື່ SpaceX ກໍ່ຕັ້ງໃນປີ ສອງພັນສອງ ໂດຍ Elon Musk. "
        "ມັນເປັນຈະຫຼວດເຊື້ອໄຟແຫຼວລຳທຳອິດ ທີ່ບໍລິສັດເອກະຊົນສ້າງເອງ ແລ້ວໄປຮອດວົງໂຄຈອນ. "
        "ຖ້າຮູ້ແລ້ວ ຢ່າລືມບອກຕໍ່ ໃຫ້ໝູ່ເດີ້!")
def tts(model, voice):
    body = {"contents": [{"parts": [{"text": STYLE + TEXT}]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                                 data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key})
    r = json.load(urllib.request.urlopen(req, timeout=180))
    pcm = base64.b64decode(r["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
    p = os.path.join(OUT, f"{model.split('-preview')[0]}_{voice}.wav")
    w = wave.open(p, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm); w.close()
    print("OK", os.path.basename(p), round(len(pcm) / 48000, 1), "s")
for m in MODELS:
    for v in VOICES:
        try: tts(m, v)
        except urllib.error.HTTPError as e: print("ERR", m, v, e.code, e.read().decode()[:300])
        except Exception as e: print("ERR", m, v, e)
