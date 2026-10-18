from django.core.management.base import BaseCommand

from autopost.bot import post_buttons
from autopost.chat import get_adapter
from autopost.models import ChatOperator, Clip


class Command(BaseCommand):
    help = "Send the next ready clip to every operator with Post / Tomorrow / Skip buttons (run from cron once a day)."

    def handle(self, *args, **kw):
        clip = Clip.next_ready()
        if clip is None:
            self.stdout.write("queue is empty")
            return
        for op in ChatOperator.objects.filter(is_active=True, receives_daily_prompt=True):
            try:
                get_adapter(op.channel).send_daily_prompt(op, clip, post_buttons(clip))
                self.stdout.write(f"asked {op} about {clip}")
            except Exception as e:  # noqa: BLE001
                self.stderr.write(f"could not message {op}: {e}")
