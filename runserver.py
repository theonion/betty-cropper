from betty import app

from betty.database import init_db
init_db()

if 'SENTRY_DSN' in app.config:
    from raven.contrib.flask import Sentry
    sentry = Sentry(app)

if __name__ == '__main__':
    app.run(debug=True)