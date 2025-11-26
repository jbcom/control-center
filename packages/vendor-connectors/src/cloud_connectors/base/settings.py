"""Settings for cloud_connectors package."""
import logging
import os

# Default log level
DEFAULT_LOG_LEVEL = logging.INFO

# Verbosity setting from environment
VERBOSITY = int(os.getenv("VERBOSITY", "0"))
VERBOSE = VERBOSITY > 0

# Doppler settings
DOPPLER_PROJECT = os.getenv("DOPPLER_PROJECT", "")
DOPPLER_CONFIG = os.getenv("DOPPLER_CONFIG", "")

# Max description length for truncation
MAX_DESCRIPTION_LENGTH = 100

# Log file settings
LOG_FILE_NAME = os.getenv("LOG_FILE_NAME", "cloud_connectors.log")

# File lock timeout in seconds
MAX_FILE_LOCK_WAIT = 10
