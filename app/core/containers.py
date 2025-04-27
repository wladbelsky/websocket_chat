from dependency_injector import containers, providers
from broadcaster import Broadcast

from app.core import db
from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.message_repository import MessageRepository
from app.services.user_service import UserService
from app.core.websocket_manager import ConnectionManager


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=["app.api.user_routes", "app.api.chat_routes", "app.api.websocket_routes", "app.core.auth", "app.core.websocket_manager"]
    )

    config = providers.Configuration()

    # Database engine and session factory
    db_engine = providers.Singleton(db.get_engine)
    session_factory = providers.Singleton(db.get_session_factory, engine=db_engine)
    db_session = providers.Factory(session_factory)

    # Broadcaster for WebSocket pub/sub
    broadcaster = providers.Singleton(Broadcast, url=settings.REDIS_URL)

    # Repositories
    user_repository = providers.Factory(
        UserRepository,
        session_factory=session_factory,
    )
    chat_repository = providers.Factory(
        ChatRepository,
        session_factory=session_factory,
    )
    message_repository = providers.Factory(
        MessageRepository,
        session_factory=session_factory,
    )

    # Services
    user_service = providers.Factory(
        UserService,
        user_repository=user_repository,
    )

    # WebSocket connection manager
    connection_manager = providers.Singleton(
        ConnectionManager,
        broadcast=broadcaster,
    )
