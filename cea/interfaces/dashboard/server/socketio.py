from typing import Dict

import socketio

from socketio.exceptions import ConnectionRefusedError

from cea.interfaces.dashboard.dependencies import settings
from cea.interfaces.dashboard.lib.auth.providers import StackAuth
from cea.interfaces.dashboard.lib.database.models import LOCAL_USER_ID

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=[])
socket_app = socketio.ASGIApp(sio)


def cookie_string_to_dict(cookie_string: str) -> Dict[str, str]:
    token_string = cookie_string.split('; ')
    token_string = [x for x in token_string if x.startswith(StackAuth.cookie_prefix)]
    return {k:v for k,v in [x.split('=') for x in token_string]}

@sio.event
async def connect(sid, environ, auth):
    if settings.local:
        await sio.enter_room(sid, f"user-{LOCAL_USER_ID}")
        return True

    cookie_string = environ.get('HTTP_COOKIE')
    if cookie_string is None:
        print('authentication failed')
        raise ConnectionRefusedError('authentication failed')

    cookie_dict = cookie_string_to_dict(cookie_string)
    if len(cookie_dict.keys()) == 0:
        print('unable to find token')
        raise ConnectionRefusedError('authentication failed')

    auth_client = StackAuth.from_request_cookies(cookie_dict)
    user_id = auth_client.get_user_id()

    await sio.enter_room(sid, f"user-{user_id}")

    return True