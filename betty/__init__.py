import os
from flask import Flask

__version__ = "0.1"
app = Flask(__name__)
app.config.from_object(os.environ.get('SETTINGS_MODULE', 'settings'))

if 'SENTRY_DSN' in app.config:
    from raven.contrib.flask import Sentry
    sentry = Sentry(app)

from betty.database import init_db
init_db()

import betty.views