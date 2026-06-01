import os

# Automatically import the right settings based on DJANGO_SETTINGS_MODULE env var.
# If not set, fall back to development.
env = os.environ.get("DJANGO_SETTINGS_MODULE", "config.settings.development")
if "production" in env:
    from .production import *  # noqa
elif "testing" in env:
    from .testing import *  # noqa
else:
    from .development import *  # noqa
