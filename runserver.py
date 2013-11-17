from betty import app

from betty.database import init_db
init_db()

app.config.from_object('settings')
app.run(debug=True)
