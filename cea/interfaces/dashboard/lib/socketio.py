from typing import Dict

import socketio

from socketio.exceptions import ConnectionRefusedError

from cea.interfaces.dashboard.dependencies import settings
from cea.interfaces.dashboard.lib.auth import CEAAuthError
from cea.interfaces.dashboard.lib.auth.providers import StackAuth
from cea.interfaces.dashboard.lib.cache.settings import CacheSettings
from cea.interfaces.dashboard.lib.database.models import LOCAL_USER_ID
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger
from cea.interfaces.dashboard.settings import get_settings

logger = getCEAServerLogger("cea-server-socketio")


def _get_cors_origin():
    cors_origin = get_settings().cors_origin
    # Disable cors_origin if wildcard given
    if cors_origin == '*':
        return []

    return cors_origin


def _get_client_manager():
    cache_settings = CacheSettings()
    if cache_settings.host and cache_settings.port:
        try:
            mgr = socketio.AsyncRedisManager(f'redis://{cache_settings.host}:{cache_settings.port}',
                                             write_only=False,  # Ensure reading is enabled
                                             channel='socketio',  # Use a consistent channel name
                                             )
            logger.info(f'Using Redis as message broker [{cache_settings.host}:{cache_settings.port}]')
            return mgr
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")

    return None

client_manager = _get_client_manager()
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=_get_cors_origin(),
                           client_manager=client_manager)
socket_app = socketio.ASGIApp(sio)


def cookie_string_to_dict(cookie_string: str) -> Dict[str, str]:
    token_string = cookie_string.split('; ')
    token_string = [x for x in token_string if x.startswith(StackAuth.cookie_prefix)]
    return {k: v for k, v in [x.split('=') for x in token_string]}


@sio.event
async def connect(sid, environ, auth):
    if settings.local:
        await sio.enter_room(sid, f"user-{LOCAL_USER_ID}")
        return True

    cookie_string = environ.get('HTTP_COOKIE')
    if cookie_string is None:
        logger.error('authentication failed')
        raise ConnectionRefusedError('authentication failed. no cookie found')

    cookie_dict = cookie_string_to_dict(cookie_string)
    if len(cookie_dict.keys()) == 0:
        logger.error('unable to find token')
        raise ConnectionRefusedError('authentication failed. no token found')

    auth_client = StackAuth.from_request_cookies(cookie_dict)

    try:
        user_id = auth_client.get_user_id()
    except CEAAuthError:
        logger.error('unable to determine user id')
        raise ConnectionRefusedError('authentication failed. invalid token')

    await sio.enter_room(sid, f"user-{user_id}")

    return True
