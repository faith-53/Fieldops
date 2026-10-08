import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("fieldops")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "deadline-reminders": {
        "task": "notifications.tasks.send_deadline_reminders",
        "schedule": crontab(minute="*/15"),
    },
    "overdue-alerts": {
        "task": "notifications.tasks.send_overdue_alerts",
        "schedule": crontab(hour="7", minute="0"),
    },
}
