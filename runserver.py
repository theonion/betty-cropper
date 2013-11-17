from betty import app

from betty.database import init_db
init_db()

app.run(debug=True)