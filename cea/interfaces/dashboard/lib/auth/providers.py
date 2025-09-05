import json
from abc import ABC, abstractmethod
from typing import Dict, Optional
from urllib.parse import unquote

import jwt
import requests

from cea.interfaces.dashboard.lib.auth import CEAAuthError
from cea.interfaces.dashboard.settings import StackAuthSettings


class AuthClient(ABC):
    access_token_name: str
    refresh_token_name: str

    @classmethod
    @abstractmethod
    def from_request_cookies(cls, request_cookies: Dict[str, str]) -> "AuthClient":
        pass

    @abstractmethod
    def get_current_user(self) -> dict:
        pass

    @abstractmethod
    def get_user_id(self) -> str:
        pass

    @abstractmethod
    def refresh_access_token(self) -> str:
        pass

    @abstractmethod
    def logout(self) -> None:
        pass


class StackAuth(AuthClient):
    _settings = StackAuthSettings()

    project_id = _settings.project_id
    publishable_client_key = _settings.publishable_client_key

    cookie_prefix = "stack"
    access_token_name = f"{cookie_prefix}-access"
    refresh_token_name = f"{cookie_prefix}-refresh-{project_id}"
    jwks_url = f"https://api.stack-auth.com/api/v1/projects/{project_id}/.well-known/jwks.json"

    def __init__(self, access_token: str, refresh_token: Optional[str]):
        if self.project_id is None:
            raise ValueError("Project ID not set.")
        if self.publishable_client_key is None:
            raise ValueError("Publishable client key not set.")

        self.access_token = access_token
        self.refresh_token = refresh_token

    @classmethod
    def _read_access_token(cls, request_cookies: Dict[str, str]) -> Optional[str]:
        """
        Get access token from cookie dict with `access_token_name` that has the value [refresh_token?, access_token]
        """
        # Get access token from cookie
        token_string = request_cookies.get(cls.access_token_name)
        return json.loads(unquote(token_string))[1] if token_string is not None else None

    @classmethod
    def _read_refresh_token(cls, request_cookies: Dict[str, str]) -> Optional[str]:
        # Get refresh token from cookie
        token_string = request_cookies.get(cls.refresh_token_name)
        return unquote(token_string) if token_string is not None else None

    def _verify_token(self):
        """
        Verify the JWT token signature using cached JWKS. Attempts refresh if expired.
        Returns the decoded token payload.
        Adds refreshed token to payload if refresh was successful [_token_refreshed and _new_refresh_token].
        """
        if not self.access_token:
            raise CEAAuthError("Access token not found")

        try:
            jwks_client = jwt.PyJWKClient(self.jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(self.access_token)

            return jwt.decode(
                self.access_token,
                signing_key,
                algorithms=["ES256"],
                audience=self.project_id,
            )
        except jwt.ExpiredSignatureError:
            raise CEAAuthError("Token expired")
        except jwt.PyJWTError as e:
            # Handle other JWT errors (invalid signature, invalid audience, etc.)
            raise CEAAuthError(f"Token verification failed: {str(e)}")
        except Exception as e:
            # Catch potential errors during JWKS fetching or key retrieval
            raise CEAAuthError(f"An error occurred during token verification process: {str(e)}")

    def _stack_auth_request(self, method, endpoint, **kwargs):
        if not self.access_token:
            raise CEAAuthError("Access token not found. Load token first before sending requests.")

        # TODO: Use async requests (e.g., httpx) for FastAPI integration
        try:
            res = requests.request(
                method,
                f'https://api.stack-auth.com{endpoint}',
                headers={
                    'x-stack-access-type': 'client',
                    'x-stack-project-id': self.project_id,
                    'x-stack-publishable-client-key': self.publishable_client_key,
                    'x-stack-access-token': self.access_token,  # Use current token
                    **kwargs.pop('headers', {}),
                },
                **kwargs,
            )

            if res.status_code == 401:  # Unauthorized - potentially expired token
                raise CEAAuthError("Unauthorized API request, try re-authenticating.")

            elif res.status_code >= 400:
                raise CEAAuthError(f"Stack Auth API request failed with {res.status_code}: {res.text}")

            return res.json()

        except requests.exceptions.RequestException as e:
            # Handle network or connection errors
            raise CEAAuthError(f"Stack Auth API request network error: {str(e)}")

    @classmethod
    def from_request_cookies(cls, request_cookies: Dict[str, str]) -> "StackAuth":
        access_token = cls._read_access_token(request_cookies)
        refresh_token = cls._read_refresh_token(request_cookies)
        return StackAuth(access_token, refresh_token)

    def get_user_id(self):
        verified_token = self._verify_token()
        return verified_token['sub']

    def get_current_user(self):
        res = self._stack_auth_request("GET", "/api/v1/users/me")
        return res

    def refresh_access_token(self):
        if not self.refresh_token:
            raise CEAAuthError("Refresh token not found. Unable to refresh access token.")

        try:
            res = self._stack_auth_request("POST", "/api/v1/auth/sessions/current/refresh",
                                           headers={"x-stack-refresh-token": self.refresh_token,
                                                    # Set access token to None to force a new access token to be generated
                                                    'x-stack-access-token': None})

            new_access_token = res['access_token']
            if not new_access_token:
                raise CEAAuthError("Refresh response did not contain a new access token.")

            self.access_token = new_access_token
            return new_access_token

        except Exception as e:
            raise CEAAuthError(f"An unexpected error occurred during token refresh: {str(e)}")

    def logout(self):
        res = self._stack_auth_request("DELETE", "/api/v1/auth/sessions/current")
        # Clear local tokens after successful server logout
        self.access_token = None
        self.refresh_token = None

        return res
