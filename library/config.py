"""Settings, read from environment variables (or a local .env file)."""
import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional
    pass

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _env_database_url():
    return os.environ.get('DATABASE_URL') or os.environ.get('SQL_DATABASE_URL')


def _database_url():
    url = _env_database_url()
    if url:
        # Heroku still hands out postgres://, which SQLAlchemy 1.4+ rejects.
        if url.startswith('postgres://'):
            url = 'postgresql://' + url[len('postgres://'):]
        return url
    path = os.path.join(BASE_DIR, 'library.db').replace('\\', '/')
    return f'sqlite:///{path}'


def _secret_key():
    key = os.environ.get('SECRET_KEY')
    if key:
        return key
    if _env_database_url():
        # A hosted database means a real deployment: never fall back to a known key.
        raise RuntimeError('Set the SECRET_KEY environment variable before deploying.')
    return 'dev-only-secret-change-me'


def _int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


class Config:
    SECRET_KEY = _secret_key()
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}

    # A desk page can stay open all day, so CSRF tokens last as long as the session.
    WTF_CSRF_TIME_LIMIT = None

    # Library rules
    BORROW_FEE = _int('BORROW_FEE', 30)        # charged to the member each time a book is issued
    DEBT_LIMIT = _int('DEBT_LIMIT', 500)       # members owing this much (or more) can't borrow
    DEFAULT_STOCK = _int('DEFAULT_STOCK', 20)  # copies created for each imported book
    PER_PAGE = _int('PER_PAGE', 25)
    CURRENCY = os.environ.get('CURRENCY', '')  # for example "Rs. " or "$"

    FRAPPE_API_URL = os.environ.get('FRAPPE_API_URL', 'https://frappe.io/api/method/frappe-library')
