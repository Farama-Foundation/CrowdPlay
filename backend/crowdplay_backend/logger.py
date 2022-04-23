import logging
import logging.config

DEFAULT_LOGGER_CONF = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(processName)s - %(message)s",
        },
        "simple": {
            "format": "%(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "null": {
            "level": "DEBUG",
            "class": "logging.NullHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}


def setLoggerConfig(log_level="INFO"):
    logging.config.dictConfig(
        {
            **DEFAULT_LOGGER_CONF,
            **{
                "root": {
                    **DEFAULT_LOGGER_CONF["root"],
                    "level": log_level,
                }
            },
        }
    )


def getLogger(name):
    return logging.getLogger(name)
