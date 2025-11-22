"""
Structured logging configuration for the application
"""
import logging
import sys
from logging.config import dictConfig


def setup_logging():
    """
    Configure structured logging for the application
    """
    dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)-8s %(name)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '[%(asctime)s] %(levelname)-8s [%(name)s:%(lineno)d] - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'default',
                'stream': sys.stdout
            },
            'error_console': {
                'class': 'logging.StreamHandler',
                'level': 'ERROR',
                'formatter': 'detailed',
                'stream': sys.stderr
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console', 'error_console']
        },
        'loggers': {
            'uvicorn': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'uvicorn.access': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            }
        }
    })


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given module name

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
