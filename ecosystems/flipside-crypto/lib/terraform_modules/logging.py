# Logging wrapper for backwards compatibility with terraform_modules
# Maps old interface (to_console, to_file) to new lifecyclelogging interface
from lifecyclelogging import Logging as _BaseLogging


class Logging(_BaseLogging):
    """Wrapper for lifecyclelogging.Logging with backwards-compatible interface."""
    
    def __init__(
        self,
        to_console: bool = False,
        to_file: bool = True,
        **kwargs
    ):
        # Map old arg names to new ones
        super().__init__(
            enable_console=to_console,
            enable_file=to_file,
            **kwargs
        )


__all__ = ["Logging"]
