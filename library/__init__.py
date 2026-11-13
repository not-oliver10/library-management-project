import click
from flask import Flask, flash, redirect, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFError, CSRFProtect

from library.config import Config

db = SQLAlchemy()
csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    csrf.init_app(app)

    from library import models  # noqa: F401  (registers the tables with SQLAlchemy)
    from library.routes import books, main, members, transactions

    for module in (main, books, members, transactions):
        app.register_blueprint(module.bp)

    _register_template_helpers(app)
    _register_error_handlers(app)
    _register_cli(app)

    with app.app_context():
        db.create_all()

    return app


def _register_template_helpers(app):
    @app.template_filter('money')
    def money(value):
        amount = value or 0
        return f"{app.config.get('CURRENCY', '')}{amount:,}"


def _register_error_handlers(app):
    @app.errorhandler(CSRFError)
    def csrf_failed(error):
        flash('That page was open for too long. Please try again.', 'warning')
        return redirect(url_for('main.desk'))

    @app.errorhandler(404)
    def not_found(error):
        return render_template(
            'error.html', code=404, title='Page not found',
            message='The page you asked for doesn’t exist or has been removed.'), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return render_template(
            'error.html', code=405, title='That action isn’t allowed here',
            message='Go back to the desk and try again from there.'), 405

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return render_template(
            'error.html', code=500, title='Something went wrong',
            message='The problem has been logged. Nothing was changed. Please try again.'), 500


def _register_cli(app):
    @app.cli.command('init-db')
    def init_db():
        """Create any missing database tables."""
        db.create_all()
        click.echo('Database tables are ready.')

    @app.cli.command('seed-demo')
    def seed_demo():
        """Add a few books and members so you can try the app."""
        from library.seed import seed

        if seed():
            click.echo('Added demo books and members.')
        else:
            click.echo('The database already has data, so nothing was added.')
