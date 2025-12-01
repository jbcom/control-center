# Shim for AWS client - wraps vendor_connectors.AWSConnector
from vendor_connectors import AWSConnector as AWSClient

def load_vendors_from_asm(*args, **kwargs):
    # Placeholder - implement if needed
    pass

__all__ = ["AWSClient", "load_vendors_from_asm"]
