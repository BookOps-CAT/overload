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
            'format': '{"app":"%(name)s", "asciTime":"%(asctime)s", "filename":"%(filename)s", "lineNo":"%(lineno)d", "levelName":"%(levelname)s", "message":"%(message)s"}'
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
        'overload-dev': {
            'handlers': ['loggly'],
            'level': 'DEBUG',
            'propagate': True
        },
        'overload_console': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
}