from fastapi import APIRouter, Response

from cea.interfaces.dashboard.dependencies import CEAUser, CEAAuthClient

router = APIRouter()

@router.get("/")
async def get_user_info(user: CEAUser):
    return user


@router.delete("/logout")
async def logout(auth_client: CEAAuthClient):
    try:
        message =  auth_client.logout()
    except Exception as e:
        # TODO: Handle error based on error code
        print(e)
    
    response = Response(status_code=204)
    response.headers["Clear-Site-Data"] = "\"cookies\""
    return response

