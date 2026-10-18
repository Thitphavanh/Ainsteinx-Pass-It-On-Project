import time

from django.core.management.base import BaseCommand

from autopost.jobs import claim_next, reset_stuck, run_one


class Command(BaseCommand):
    help = "Upload queued clips to YouTube / Facebook / TikTok (keep this running, e.g. with systemd)."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="process what is due, then exit (for cron)")
        parser.add_argument("--sleep", type=float, default=3.0)

    def handle(self, *args, once=False, sleep=3.0, **kw):
        n = reset_stuck()
        if n:
            self.stdout.write(f"re-queued {n} stuck posts")
        while True:
            post = claim_next()
            if post:
                post = run_one(post)
                self.stdout.write(f"{post.clip} → {post.platform}: {post.status} {post.url or post.error[:120]}")
                continue
            if once:
                return
            time.sleep(sleep)
