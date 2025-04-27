from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from dependency_injector.wiring import inject, Provide
import json
from typing import Dict, Any
from pydantic import ValidationError

from app.core.containers import Container
from app.core.websocket_manager import ConnectionManager
from app.core.websocket_auth import get_user_from_token
from app.repositories.chat_repository import ChatRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.schemas.websocket_messages import (
    MessageType, 
    ChatMessageIn, 
    ChatMessageOut, 
    ReadStatusIn
)

router = APIRouter()

@router.websocket("/ws/chat/{chat_id}")
@inject
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: int,
    chat_repository: ChatRepository = Depends(Provide[Container.chat_repository]),
    message_repository: MessageRepository = Depends(Provide[Container.message_repository]),
    user_repository: UserRepository = Depends(Provide[Container.user_repository]),
    connection_manager: ConnectionManager = Depends(Provide[Container.connection_manager]),
):
    # Get user from token
    user = await get_user_from_token(websocket, user_repository)
    if not user:
        return

    user_id = user.id

    # Get chat with participants loaded to verify membership
    chat = await chat_repository.get_by_id(chat_id, load_relationships=True)
    if not chat:
        await websocket.close(code=1008, reason="Chat not found")
        return

    for participant in chat.participants:
        if participant.user_id == user_id:
            break
    else:
        await websocket.close(code=1008, reason="User is not a participant in this chat")
        return

    # Accept the connection and add it to the manager
    await connection_manager.connect(websocket, chat_id)

    try:
        # Send chat history to the user, load sender information
        chat_history = await message_repository.get_history(chat_id, load_relationships=True)
        for message in chat_history:
            message_model = ChatMessageOut(
                id=message.id,
                sender_id=message.sender_id,
                content=message.text,
                timestamp=message.timestamp,
                is_read=message.is_read
            )
            await websocket.send_text(message_model.model_dump_json())

        # Listen for messages from this client
        while True:
            data = await websocket.receive_text()
            try:
                json_data = json.loads(data)
                message_type = json_data.get("type")

                if message_type == MessageType.MESSAGE:
                    message_in = ChatMessageIn.model_validate(json_data)
                    if not message_in.content.strip():
                        continue
                    # Create message with relationships for the broadcast
                    new_message = await message_repository.create(
                        chat_id=chat_id,
                        sender_id=user_id,
                        text=message_in.content,
                        load_relationships=True
                    )
                    message_out = ChatMessageOut(
                        id=new_message.id,
                        sender_id=new_message.sender_id,
                        content=new_message.text,
                        timestamp=new_message.timestamp,
                        is_read=new_message.is_read
                    )

                    await connection_manager.broadcast_message(chat_id, message_out)

                elif message_type == MessageType.READ_STATUS:
                    read_status = ReadStatusIn.model_validate(json_data)
                    # Mark as read with relationships loaded
                    updated_message = await message_repository.mark_as_read(
                        read_status.message_id,
                        load_relationships=True
                    )
                    if updated_message:
                        await connection_manager.broadcast_read_status(
                            message_id=updated_message.id,
                            chat_id=chat_id,
                            reader_id=user_id
                        )

            except json.JSONDecodeError:
                # Invalid JSON, ignore
                continue
            except ValidationError:
                # Invalid message format, ignore
                continue
            except Exception as e:
                print(f"Error processing message: {str(e)}")

    except WebSocketDisconnect:
        # Client disconnected
        await connection_manager.disconnect(websocket)
