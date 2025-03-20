import json
from urllib.parse import unquote

import requests
from fastapi import Request

from cea.interfaces.dashboard.settings import StackAuthSettings


class StackAuth:
    def __init__(self, project_id, publishable_client_key, access_token = None):
        self.project_id = project_id
        self.publishable_client_key = publishable_client_key

        self.access_token = access_token

    @staticmethod
    def from_settings():
        settings = StackAuthSettings()

        return StackAuth(settings.project_id, settings.publishable_client_key)

    @staticmethod
    def check_token(request: Request):
        # Get access token from cookie
        cookie_name = StackAuthSettings().cookie_name
        token_string = request.cookies.get(cookie_name)

        return token_string

    def add_token_from_cookie(self, request: Request):
        token_string = self.check_token(request)
        if token_string is None:
            raise Exception("Access token not found in cookie. Load token first before sending requests.")
        token = json.loads(unquote(token_string))[1]

        self.access_token = token

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

    def get_current_user(self):
        res = self._stack_auth_request("GET", "/api/v1/users/me")
        return res

    def logout(self):
        res = self._stack_auth_request("DELETE", "/api/v1/auth/sessions/current")
        return res