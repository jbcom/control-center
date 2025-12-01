# Doppler configuration
import os

DOPPLER_PROJECT = os.environ.get("DOPPLER_PROJECT", "terraform")
DOPPLER_CONFIG = os.environ.get("DOPPLER_CONFIG", "prod")

__all__ = ["DOPPLER_PROJECT", "DOPPLER_CONFIG"]
