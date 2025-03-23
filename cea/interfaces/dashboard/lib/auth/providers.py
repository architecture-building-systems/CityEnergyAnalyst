import json
from typing import Optional
from urllib.parse import unquote

import jwt
import requests
from fastapi import Request

from cea.interfaces.dashboard.settings import StackAuthSettings

_settings = StackAuthSettings()

class StackAuth:
    project_id = _settings.project_id
    publishable_client_key = _settings.publishable_client_key

    cookie_name = _settings.cookie_name
    jwks_url = f"https://api.stack-auth.com/api/v1/projects/{project_id}/.well-known/jwks.json"

    def __init__(self, access_token: str):
        self.access_token = access_token

    @staticmethod
    def parse_token(token_string: str):
        return json.loads(unquote(token_string))[1]

    @staticmethod
    def get_token(request: Request) -> Optional[str]:
        # Get access token from cookie
        token_string = request.cookies.get(StackAuth.cookie_name)

        if token_string is None:
            # raise Exception("Access token not found in cookie. Load token first before sending requests.")
            return None

        token = StackAuth.parse_token(token_string)
        return token

    def _stack_auth_request(self, method, endpoint, **kwargs):
        if not self.access_token:
            raise Exception("Access token not found. Load token first before sending requests.")

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
            raise Exception(f"Stack Auth API request failed with {res.status_code}: {res.text}")
        return res.json()

    def get_user_id(self):
        # TODO: Verify signature
        data = jwt.decode(self.access_token.encode(), options={"verify_signature": False})
        return data['sub']

    def get_current_user(self):
        res = self._stack_auth_request("GET", "/api/v1/users/me")
        return res

    def logout(self):
        res = self._stack_auth_request("DELETE", "/api/v1/auth/sessions/current")
        return res