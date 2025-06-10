from fastapi import APIRouter, HTTPException, Response, status

from cea.interfaces.dashboard.dependencies import CEAUser, CEAAuthClient
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger

logger = getCEAServerLogger("cea-server-user")

router = APIRouter()


@router.get("")
async def get_user_info(user: CEAUser):
    return user


@router.post("/session/refresh")
async def refresh_session(auth_client: CEAAuthClient, response: Response):
    if auth_client is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
        )

    try:
        new_access_token = auth_client.refresh_access_token()

        # Prevent caching of refresh response
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"

        return {"access_token": new_access_token}
    except Exception as e:
        # TODO: Handle error based on error code
        logger.error(f"Error during refresh session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh"
        )


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
            "Clear-Site-Data": "\"cookies\"",
            "Cache-Control": "no-store",
            "Pragma": "no-cache"
        }
    )
