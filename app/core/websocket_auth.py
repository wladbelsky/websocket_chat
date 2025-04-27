from fastapi import WebSocket, status
from jose import JWTError, jwt

from app.core.config import settings
from app.repositories.user_repository import UserRepository


async def get_user_from_token(
        websocket: WebSocket,
        user_repository: UserRepository
):
    """
    Get the user from the token in the WebSocket connection.
    The token should be provided in the Authorization header with the Bearer scheme.
    """
    auth_header = websocket.headers.get("Authorization")
    if not auth_header:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication header")
        return None

    try:
        # Extract token from "Bearer <token>" format
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication scheme")
            return None

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication token")
            return None

        # Get user with relationships loaded for WebSocket context
        user = await user_repository.get_by_id(int(user_id), load_relationships=True)
        if user is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
            return None

        return user
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authorization header format")
        return None
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication token")
        return None
