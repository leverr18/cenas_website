from sqlalchemy import text
from cenas_website import create_app, db  # or from cenas_website import app, db
app = create_app()
with app.app_context():
    cols = db.session.execute(text("PRAGMA table_info(product)")).fetchall()
    print(cols)  # look for a row whose 2nd element (name) is 'category'

