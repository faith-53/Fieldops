import os

os.environ.setdefault("USE_SQLITE", "true")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret")
