from flask import Flask
from flask_cors import CORS # Import CORS
from .config import Config
from .models import db
# from flask_migrate import Migrate # Add if using migrations

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app) # Initialize CORS with default settings (allow all origins)
    # For more specific CORS settings:
    # CORS(app, resources={r"/api/*": {"origins": "http://your-frontend-domain.com"}})

    db.init_app(app)
    # migrate = Migrate(app, db) # Add if using migrations

    # Register blueprints here
    from .routes import main_bp
    app.register_blueprint(main_bp, url_prefix="/api") # Corrected url_prefix

    with app.app_context():
        db.create_all() # Create tables if they don\\'t exist

    return app

