"""Module entry point for python-terraform-bridge.

Allows running as: python -m python_terraform_bridge [options]
"""

from __future__ import annotations

import sys

from python_terraform_bridge.cli import main

if __name__ == "__main__":
    sys.exit(main())
