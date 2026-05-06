# run_once_add_category.py
from sqlalchemy import text

# Try the variant that matches your app:
try:
    # If you have a global `app` in cenas_website/__init__.py
    from cenas_website import app, db
    ctx = app.app_context()
except ImportError:
    # If you use an app factory `create_app()`
    from cenas_website import create_app, db
    app = create_app()
    ctx = app.app_context()

with ctx:
    # Add the column with a default so existing rows are valid
    db.session.execute(
        text("ALTER TABLE product ADD COLUMN category VARCHAR(100) NOT NULL DEFAULT 'Office'")
    )
    db.session.commit()
    print("✅ Added product.category")
