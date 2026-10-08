from .base import *  # noqa: F401,F403
from .base import env

DEBUG = env("DJANGO_DEBUG", "true").lower() == "true"

if env("DJANGO_ENV", "development") == "production":
    from .production import *  # noqa: F401,F403
else:
    from .development import *  # noqa: F401,F403
