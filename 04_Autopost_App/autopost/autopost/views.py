import logging

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import conf
from .bot import Bot, start_posting
from .chat import BadSignature, get_adapter
from .models import ChatOperator, Clip, PlatformPost, SocialAccount

log = logging.getLogger("autopost")


# ---------- webhooks ----------
def _handle(request, channel):
    adapter = get_adapter(channel)
    try:
        msgs = adapter.parse(request)
    except BadSignature:
        return HttpResponseForbidden("bad signature")
    bot = Bot(adapter)
    for m in msgs:
        try:
            bot.handle(m)
        except Exception:  # noqa: BLE001 — always 200 so the platform does not retry forever
            log.exception("bot failed on %s message", channel)
    return HttpResponse("ok")


@csrf_exempt
@require_POST
def line_webhook(request):
    return _handle(request, "line")


@csrf_exempt
def whatsapp_webhook(request):
    if request.method == "GET":  # Meta verification handshake
        if (request.GET.get("hub.mode") == "subscribe"
                and request.GET.get("hub.verify_token") == conf.get("WA_VERIFY_TOKEN") and conf.get("WA_VERIFY_TOKEN")):
            return HttpResponse(request.GET.get("hub.challenge", ""))
        return HttpResponseForbidden("verify token mismatch")
    if request.method != "POST":
        return HttpResponse(status=405)
    return _handle(request, "whatsapp")


# ---------- dashboard ----------
class ClipForm(forms.ModelForm):
    class Meta:
        model = Clip
        fields = ["video", "subtitle_th", "episode", "category", "title", "description", "hashtags", "queue_position"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3}),
                   "subtitle_th": forms.ClearableFileInput(attrs={"accept": ".srt"})}

    def clean_subtitle_th(self):
        f = self.cleaned_data.get("subtitle_th")
        if f and not f.name.lower().endswith(".srt"):
            raise forms.ValidationError("ຊັບໄຕເຕີ້ລ໌ຕ້ອງເປັນໄຟລ໌ .srt")
        return f


@staff_member_required
def dashboard(request):
    form = ClipForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        clip = form.save(commit=False)
        clip.status = Clip.Status.READY
        clip.save()
        messages.success(request, f"ເພີ່ມ \"{clip}\" ເຂົ້າຄິວແລ້ວ")
        return redirect("autopost:dashboard")
    accounts = {a.platform: a for a in SocialAccount.objects.all()}
    return render(request, "autopost/dashboard.html", {
        "form": form,
        "platforms": [(p, label, accounts.get(p)) for p, label in
                      [("youtube", "YouTube"), ("facebook", "Facebook Page"), ("tiktok", "TikTok")]],
        "queue": Clip.objects.exclude(status__in=[Clip.Status.POSTED, Clip.Status.SKIPPED])[:30],
        "recent": PlatformPost.objects.select_related("clip")[:20],
        "operators": ChatOperator.objects.all(),
        "pair_code_set": bool(conf.get("PAIR_CODE")),
    })


@staff_member_required
@require_POST
def post_now(request, pk):
    clip = get_object_or_404(Clip, pk=pk)
    if start_posting(clip):
        messages.success(request, f"⏳ ກຳລັງໂພສ \"{clip}\"")
    else:
        messages.error(request, "ຍັງບໍ່ໄດ້ເຊື່ອມຕໍ່ບັນຊີໃດເລີຍ")
    return redirect("autopost:dashboard")


@staff_member_required
@require_POST
def toggle_account(request, platform):
    acc = get_object_or_404(SocialAccount, platform=platform)
    acc.enabled = not acc.enabled
    acc.save(update_fields=["enabled"])
    return redirect("autopost:dashboard")
