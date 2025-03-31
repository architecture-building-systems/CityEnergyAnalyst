from fastapi import APIRouter, Response, status

from cea.interfaces.dashboard.dependencies import CEAUser, CEAAuthClient
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger

logger = getCEAServerLogger("cea-server-user")

router = APIRouter()

@router.get("")
async def get_user_info(user: CEAUser):
    return user


@router.delete("/logout")
async def logout(auth_client: CEAAuthClient):
    try:
        auth_client.logout()
    except Exception as e:
        # TODO: Handle error based on error code
        logger.error(f"Error during logout: {e}")

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
        headers={
            "Clear-Site-Data": "\"cookies\""
        }
    )

