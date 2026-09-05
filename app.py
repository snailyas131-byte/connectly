import os
from datetime import datetime, timezone
from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from models import db, User


def create_app(config_class=Config):
    """Application factory for Connectly Contact Book."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload and instance directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.contacts import contacts_bp
    from routes.data_io import data_io_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(contacts_bp)
    app.register_blueprint(data_io_bp)
    app.register_blueprint(api_bp)

    # Context processors
    @app.context_processor
    def inject_globals():
        return {
            'current_year': datetime.now(timezone.utc).year,
            'app_name': 'Connectly'
        }

    # Error handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return render_template('errors/413.html'), 413

    # Create tables automatically within app context
    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=5000)
