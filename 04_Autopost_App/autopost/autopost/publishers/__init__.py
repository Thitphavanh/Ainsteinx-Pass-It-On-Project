from .base import PublishError, PublishResult  # noqa: F401


def get_publisher(platform):
    if platform == "youtube":
        from .youtube import YouTubePublisher
        return YouTubePublisher()
    if platform == "facebook":
        from .facebook import FacebookPublisher
        return FacebookPublisher()
    if platform == "tiktok":
        from .tiktok import TikTokPublisher
        return TikTokPublisher()
    raise ValueError(platform)
