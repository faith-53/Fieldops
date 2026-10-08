from .base import BASE_DIR, env

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": env("POSTGRES_DB", "fieldops"),
        "USER": env("POSTGRES_USER", "fieldops"),
        "PASSWORD": env("POSTGRES_PASSWORD", "fieldops"),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
    }
}

if env("USE_SQLITE", "false").lower() == "true":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
