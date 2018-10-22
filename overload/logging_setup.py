import traceback


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '{"app":"%(name)s", "asciTime":"%(asctime)s", "fileName":"%(filename)s", "lineNo":"%(lineno)d", "levelName":"%(levelname)s", "message":"%(message)s"}'
        },
    },
    'handlers': {
        'loggly': {
            'level': 'INFO',
            'class': 'loggly.handlers.HTTPSHandler',
            'formatter': 'standard',
            'url': 'https://logs-01.loggly.com/inputs/[token]/tag/python',
        },
    },
    'loggers': {
        'overload': {
            'handlers': ['loggly'],
            'level': 'INFO',
            'propagate': True
        }
    }
}


DEV_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'brief': {
            'format': '%(name)s-%(asctime)s-%(filename)s-%(lineno)s-%(levelname)s-%(levelno)s-%(message)s'
        },
        'standard': {
            'format': '{"app":"%(name)s", "asciTime":"%(asctime)s", "fileName":"%(filename)s", "lineNo":"%(lineno)d", "levelName":"%(levelname)s", "message":"%(message)s"}'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'brief'
        },
        'loggly': {
            'level': 'DEBUG',
            'class': 'loggly.handlers.HTTPSHandler',
            'formatter': 'standard',
            'url': 'https://logs-01.loggly.com/inputs/[token]/tag/python',
        },
    },
    'loggers': {
        'overload': {
            'handlers': ['console', 'loggly'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
}


def format_traceback(exc, exc_traceback=None):
    """
    Formats logging tracebacks into a format accepted by Loggly service.
    args:
        exc: type, exceptions
        exc_traceback: type, traceback obtained from sys.exc_info()
    returns:
        traceback, string with removed double quotes, line breaks, and double
                   backslashes

    usage:
        try:
            int('a')
        except ValueError as exc:
            _, _, exc_traceback = sys.exc_info()
            tb = format_traceback(exc, exc_traceback)
            logger.error('Unhandled error. {}'.format(tb))
    """

    if exc_traceback is None:
        exc_traceback = exc.__traceback__
    tb_lines = [
        line.replace(
            '"', "'").replace(
            "\n", "\\n").replace(
            '\\', '/') for line in
        traceback.format_exception(exc.__class__, exc, exc_traceback)
    ]

    return ''.join(tb_lines)
