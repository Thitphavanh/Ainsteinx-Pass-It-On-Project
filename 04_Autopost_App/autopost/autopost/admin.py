from django.contrib import admin

from .bot import start_posting
from .models import ChatOperator, Clip, PlatformPost, SocialAccount


class PlatformPostInline(admin.TabularInline):
    model = PlatformPost
    extra = 0
    readonly_fields = ["platform", "status", "attempts", "url", "note", "error", "updated_at"]
    can_delete = False


@admin.register(Clip)
class ClipAdmin(admin.ModelAdmin):
    list_display = ["__str__", "category", "status", "queue_position", "created_at"]
    list_filter = ["status", "category"]
    list_editable = ["queue_position"]
    inlines = [PlatformPostInline]
    actions = ["post_now"]

    @admin.action(description="ໂພສດຽວນີ້ ລົງທຸກແພລັດຟອມ")
    def post_now(self, request, queryset):
        n = sum(1 for c in queryset if start_posting(c))
        self.message_user(request, f"ເຂົ້າຄິວໂພສ {n} ຄລິບ")


@admin.register(PlatformPost)
class PlatformPostAdmin(admin.ModelAdmin):
    list_display = ["clip", "platform", "status", "attempts", "url", "updated_at"]
    list_filter = ["platform", "status"]


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ["platform", "name", "external_id", "enabled", "expires_at", "connected_at"]
    exclude = ["access_token", "refresh_token"]


@admin.register(ChatOperator)
class ChatOperatorAdmin(admin.ModelAdmin):
    list_display = ["channel", "name", "external_id", "is_active", "receives_daily_prompt", "last_inbound_at"]
    list_editable = ["is_active", "receives_daily_prompt"]
