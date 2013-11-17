from betty import app

from betty.database import init_db
init_db()

if __name__ == '__main__':
    app.run(debug=True)