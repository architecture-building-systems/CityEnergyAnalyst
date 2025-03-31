import json
from typing import Optional
from urllib.parse import unquote

import jwt
import requests
from fastapi import Request

from cea.interfaces.dashboard.lib.auth import CEAAuthError
from cea.interfaces.dashboard.settings import StackAuthSettings


class StackAuth:
    _settings = StackAuthSettings()

    project_id = _settings.project_id
    publishable_client_key = _settings.publishable_client_key

    cookie_name = _settings.cookie_name
    jwks_url = f"https://api.stack-auth.com/api/v1/projects/{project_id}/.well-known/jwks.json"

    def __init__(self, access_token: str):
        if self.project_id is None:
            raise ValueError("Project ID not set.")
        if self.publishable_client_key is None:
            raise ValueError("Publishable client key not set.")

        self.access_token = access_token

    @staticmethod
    def parse_cookie(cookie_string: str):
        return json.loads(unquote(cookie_string))[1]

    @classmethod
    def get_token(cls, request: Request) -> Optional[str]:
        # Get access token from cookie
        token_string = request.cookies.get(cls.cookie_name)

        if token_string is None:
            # raise Exception("Access token not found in cookie. Load token first before sending requests.")
            return None

        token = cls.parse_cookie(token_string)
        return token

    def verify_token(self):
        """Verify the JWT token signature using cached JWKS"""
        if not self.access_token:
            raise CEAAuthError("Access token not found")

        try:
            jwks_client = jwt.PyJWKClient(self.jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(self.access_token)

            payload = jwt.decode(
                self.access_token,
                signing_key,
                algorithms=["ES256"],
                audience=self.project_id,
            )

            return payload

        except jwt.PyJWTError as e:
            raise CEAAuthError(f"Token verification failed: {str(e)}")

    def get_user_id(self):
        # Use verified token instead of skipping verification
        verified_token = self.verify_token()
        return verified_token['sub']

    def _stack_auth_request(self, method, endpoint, **kwargs):
        if not self.access_token:
            raise CEAAuthError("Access token not found. Load token first before sending requests.")

        # TODO: Use async requests
        res = requests.request(
            method,
            f'https://api.stack-auth.com{endpoint}',
            headers={
                'x-stack-access-type': 'client',  # or 'client' if you're only accessing the client API
                'x-stack-project-id': self.project_id,
                'x-stack-publishable-client-key': self.publishable_client_key,
                # 'x-stack-secret-server-key': self.secret_server_key,  # not necessary if access type is 'client'
                'x-stack-access-token': self.access_token,
                **kwargs.pop('headers', {}),
            },
            **kwargs,
        )
        if res.status_code >= 400:
            raise CEAAuthError(f"Stack Auth API request failed with {res.status_code}: {res.text}")
        return res.json()

    def get_current_user(self):
        res = self._stack_auth_request("GET", "/api/v1/users/me")
        return res

    def logout(self):
        res = self._stack_auth_request("DELETE", "/api/v1/auth/sessions/current")
        return res
