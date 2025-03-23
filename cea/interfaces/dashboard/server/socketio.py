import socketio

from socketio.exceptions import ConnectionRefusedError

from cea.interfaces.dashboard.dependencies import settings
from cea.interfaces.dashboard.lib.auth.providers import StackAuth
from cea.interfaces.dashboard.lib.database.models import LOCAL_USER_ID

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=[])
socket_app = socketio.ASGIApp(sio)


@sio.event
async def connect(sid, environ, auth):
    if settings.local:
        await sio.enter_room(sid, f"user-{LOCAL_USER_ID}")
        return True

    token_string = environ.get('HTTP_COOKIE')

    if token_string is None:
        print('authentication failed')
        raise ConnectionRefusedError('authentication failed')

    token_string = token_string.split('; ')
    token_string = [x for x in token_string if x.startswith(StackAuth.cookie_name)]

    if len(token_string) == 0:
        print('unable to find token')
        raise ConnectionRefusedError('authentication failed')

    token_string = StackAuth.parse_token(token_string[0].split('=')[1])
    user_id = StackAuth(token_string).get_user_id()

    await sio.enter_room(sid, f"user-{user_id}")

    return True