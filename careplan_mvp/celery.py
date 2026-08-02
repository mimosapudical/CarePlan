import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "careplan_mvp.settings")

app = Celery("careplan_mvp")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
