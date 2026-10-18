from django.urls import path

from . import oauth, views

app_name = "autopost"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("clip/<int:pk>/post/", views.post_now, name="post_now"),
    path("account/<str:platform>/toggle/", views.toggle_account, name="toggle_account"),
    path("connect/<str:platform>/", oauth.connect, name="connect"),
    path("oauth/<str:platform>/callback/", oauth.oauth_callback, name="oauth_callback"),
    path("webhook/line/", views.line_webhook, name="line_webhook"),
    path("webhook/whatsapp/", views.whatsapp_webhook, name="whatsapp_webhook"),
]
