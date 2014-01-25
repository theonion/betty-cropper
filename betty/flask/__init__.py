from __future__ import absolute_import

import os
from flask import Flask

__version__ = "0.1"
app = Flask(__name__, template_folder="../templates")
app.config.from_object(os.environ.get('SETTINGS_MODULE', 'settings'))

if 'SENTRY_DSN' in app.config:
    from raven.contrib.flask import Sentry
    sentry = Sentry(app)

from betty.flask.database import init_db
init_db()

import betty.flask.views