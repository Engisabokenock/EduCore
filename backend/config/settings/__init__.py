import os

env = os.environ.get("DJANGO_SETTINGS_MODULE", "config.settings.production")
if "production" in env:
    from .production import *  # noqa
elif "testing" in env:
    from .testing import *  # noqa
elif "development" in env:
    from .development import *  # noqa
else:
    from .production import *  # noqa
