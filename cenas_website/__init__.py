import os
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

ALLOWED_CODE = os.environ.get("ALLOWED_CODE")

db = SQLAlchemy()
migrate = Migrate()  # initialize outside for flexibility

def create_app():
    app = Flask(__name__)

    # --- Secret Key ---
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

    # --- Database ---
    uri = os.environ.get("DATABASE_URL", "sqlite:///database.sqlite3")
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

     # --- Media storage (persistent) ---
    render_disk = "/data"  # default Render mount path
    if os.path.isdir(render_disk):
        base_media = os.path.join(render_disk, "media")
    else:
        # local dev fallback
        base_media = os.path.join(app.root_path, "..", "media")

    app.config["MEDIA_ROOT"] = base_media
    app.config["PRODUCT_MEDIA"] = os.path.join(base_media, "products")
    app.config["TRAINING_MEDIA"] = os.path.join(base_media, "training")

    os.makedirs(app.config["PRODUCT_MEDIA"], exist_ok=True)
    os.makedirs(app.config["TRAINING_MEDIA"], exist_ok=True)


    # Optional: helps with stale connections on Render
    app.config.setdefault("SQLALCHEMY_ENGINE_OPTIONS", {"pool_pre_ping": True})

    db.init_app(app)
    migrate.init_app(app, db)

    # --- Import models before login_manager ---
    from .models import Customer, Cart, Product, Order, OrderItem, TrainingVideo

    # --- Login Manager ---
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(id):
        return Customer.query.get(int(id))

    # --- Blueprints ---
    from .views import views
    from .auth import auth
    from .admin import admin
    from .cart import cart
    from .career import career
    from .training import training
    from .catering import catering

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")
    app.register_blueprint(admin, url_prefix="/")
    app.register_blueprint(cart, url_prefix="/")
    app.register_blueprint(career, url_prefix="/")
    app.register_blueprint(training, url_prefix="/")
    app.register_blueprint(catering, url_prefix="/")

    from .cart import _store_from_email
    app.jinja_env.filters['store_name'] = _store_from_email

    # # --- Create tables ONLY for SQLite (dev). Postgres uses Alembic migrations. ---
    # if uri.startswith("sqlite"):
    #     with app.app_context():
    #         db.create_all()
    #         print("✅ Database Created (SQLite)")

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static', 'images'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    return app



