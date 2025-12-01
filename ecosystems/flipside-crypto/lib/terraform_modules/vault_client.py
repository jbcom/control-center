# Shim for Vault client - wraps vendor_connectors.VaultConnector
from vendor_connectors import VaultConnector as VaultClient

__all__ = ["VaultClient"]
