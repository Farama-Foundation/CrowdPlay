import os

from dotenv import load_dotenv

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "HUAeUqhKraOwfidFSdvkOvZ3c3kLJTrz"

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URI") or "sqlite:///" + os.path.join(
        basedir, "crowdplaydb.sqlite"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    APP_HOST = os.environ.get("APP_HOST") or "0.0.0.0"
    APP_PORT = os.environ.get("APP_PORT") or "5000"

    # Non-environ configuration (Fixed config items)
    RUN_DEBUG = True
    LOG_LEVEL = "DEBUG"
    WS_NS = "/env"
    # TIME_PLAYING = 60 * 10  # 10 minutes
    TIME_PLAYING = 5  # 30 seconds
    NO_HIT = "NO_HIT"


class ConfigLocalDocker(Config):
    pass


class ConfigProd(Config):
    RUN_DEBUG = False
    LOG_LEVEL = "INFO"
