from flask import Flask
app = Flask(__name__)
app.config.from_object('settings')

from raven.contrib.flask import Sentry
sentry = Sentry(app)

import betty.views