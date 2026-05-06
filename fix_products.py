# fix_products.py
from cenas_website import create_app, db
from cenas_website.models import Product
import os

app = create_app()
with app.app_context():
    for p in Product.query.all():
        p.product_picture = os.path.basename(p.product_picture)
    db.session.commit()
    print("Updated all product paths to filenames only.")
