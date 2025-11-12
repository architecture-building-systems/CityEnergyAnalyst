from cea import CEAException
from cea.interfaces.dashboard.lib.auth.tokens import (
    create_download_token,
    verify_download_token,
    get_jwt_secret
)

__all__ = [
    'CEAAuthError',
    'create_download_token',
    'verify_download_token',
    'get_jwt_secret'
]


class CEAAuthError(CEAException):
    """Raised when there is an error with the authentication"""
    pass
