"""
JWT token utilities for download authentication.
Provides token generation and verification for pre-signed download URLs.
"""
import jwt
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from cea.interfaces.dashboard.lib.logs import getCEAServerLogger

logger = getCEAServerLogger("cea-auth-tokens")

# Secret key for JWT signing (should be configurable in production)
# In production, this should be loaded from environment variables or secrets manager
_JWT_SECRET = None


def get_jwt_secret() -> str:
    """
    Get or generate JWT secret key.
    In production, this should be loaded from environment variables.
    For development/local mode, generates a random secret per server instance.
    """
    global _JWT_SECRET
    if _JWT_SECRET is None:
        import os
        _JWT_SECRET = os.getenv('CEA_JWT_SECRET')
        if not _JWT_SECRET:
            # Generate random secret for local development
            # WARNING: This means tokens won't survive server restarts
            _JWT_SECRET = secrets.token_urlsafe(32)
            logger.warning(
                "Using randomly generated JWT secret. "
                "Set CEA_JWT_SECRET environment variable for production."
            )
    return _JWT_SECRET


def create_download_token(download_id: str, user_id: str, expires_in_seconds: int = 300) -> str:
    """
    Create a short-lived JWT token for downloading a file.

    Args:
        download_id: Download ID
        user_id: User ID who created the download
        expires_in_seconds: Token expiration time (default: 5 minutes)

    Returns:
        JWT token string
    """
    now = datetime.now(timezone.utc)
    expiration = now + timedelta(seconds=expires_in_seconds)

    payload = {
        'download_id': download_id,
        'user_id': user_id,
        'iat': now,  # Issued at
        'exp': expiration,  # Expiration time
        'type': 'download'  # Token type for validation
    }

    token = jwt.encode(payload, get_jwt_secret(), algorithm='HS256')
    logger.debug(f"Created download token for {download_id}, expires in {expires_in_seconds}s")

    return token


def verify_download_token(token: str, download_id: str) -> Optional[str]:
    """
    Verify a download token and return the user_id if valid.

    Args:
        token: JWT token string
        download_id: Expected download ID

    Returns:
        User ID if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=['HS256'],
            options={
                'verify_exp': True,  # Verify expiration
                'require_exp': True,  # Require expiration claim
            }
        )

        # Validate token type
        if payload.get('type') != 'download':
            logger.warning(f"Invalid token type: {payload.get('type')}")
            return None

        # Validate download_id matches
        if payload.get('download_id') != download_id:
            logger.warning(
                f"Token download_id mismatch: "
                f"expected {download_id}, got {payload.get('download_id')}"
            )
            return None

        user_id = payload.get('user_id')
        if not user_id:
            logger.warning("Token missing user_id claim")
            return None

        return user_id

    except jwt.ExpiredSignatureError:
        logger.debug(f"Token expired for download {download_id}")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token for download {download_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None


def create_worker_token(job_id: str, user_id: str, expires_in_seconds: int = 60 * 60 * 24) -> str:
    """
    Create a job-scoped JWT token so a ``cea-worker`` subprocess can authenticate its
    callbacks (``/jobs/started``, ``/jobs/success``, ``/jobs/error``, ``/streams/write``)
    without the browser session cookies it has no access to.

    Args:
        job_id: Job ID the token is scoped to
        user_id: User ID who created the job (the worker acts on their behalf)
        expires_in_seconds: Token expiration time (default: 24 hours, to outlast long-running simulations)

    Returns:
        JWT token string
    """
    now = datetime.now(timezone.utc)
    expiration = now + timedelta(seconds=expires_in_seconds)

    payload = {
        'job_id': job_id,
        'user_id': user_id,
        'iat': now,
        'exp': expiration,
        'type': 'worker'
    }

    token = jwt.encode(payload, get_jwt_secret(), algorithm='HS256')
    logger.debug(f"Created worker token for job {job_id}, expires in {expires_in_seconds}s")

    return token


def verify_worker_token(token: str, job_id: str) -> Optional[str]:
    """
    Verify a worker token and return the user_id if valid.

    Args:
        token: JWT token string
        job_id: Expected job ID

    Returns:
        User ID if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=['HS256'],
            options={
                'verify_exp': True,
                'require_exp': True,
            }
        )

        if payload.get('type') != 'worker':
            logger.warning(f"Invalid token type: {payload.get('type')}")
            return None

        if payload.get('job_id') != job_id:
            logger.warning(
                f"Token job_id mismatch: expected {job_id}, got {payload.get('job_id')}"
            )
            return None

        user_id = payload.get('user_id')
        if not user_id:
            logger.warning("Token missing user_id claim")
            return None

        return user_id

    except jwt.ExpiredSignatureError:
        logger.debug(f"Worker token expired for job {job_id}")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid worker token for job {job_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying worker token: {e}")
        return None
