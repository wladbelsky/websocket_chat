import asyncio
from asyncio import CancelledError
from datetime import datetime, UTC
from typing import Dict

from broadcaster import Broadcast
from fastapi import WebSocket
from pydantic import BaseModel
from starlette.websockets import WebSocketDisconnect, WebSocketState

from app.schemas.websocket_messages import ChatMessageOut, ReadStatusOut


class ConnectionManager:
    def __init__(self, broadcast: Broadcast):
        self.listing_tasks: Dict[WebSocket, asyncio.Task] = {}
        self.broadcast = broadcast
        self.chat_locks: Dict[int, asyncio.Lock] = {}

    async def connect(self, websocket: WebSocket, chat_id: int):
        await websocket.accept()
        self.listing_tasks[websocket] = asyncio.create_task(self.listen_for_messages(websocket, chat_id))

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.listing_tasks:
            task = self.listing_tasks[websocket]
            if not task.done():
                task.cancel()
            del self.listing_tasks[websocket]
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()

    async def broadcast_to_chat(self, chat_id: int, message: BaseModel):
        """Broadcast a message to all clients in a chat"""
        channel_name = f"chat:{chat_id}"
        message_json = message.model_dump_json()
        await self.broadcast.publish(channel=channel_name, message=message_json)

    async def broadcast_message(self, chat_id: int, message: ChatMessageOut):
        """Broadcast a chat message to all clients in the chat"""
        await self.broadcast_to_chat(chat_id, message)

    async def broadcast_read_status(self, message_id: int, chat_id: int, reader_id: int):
        """Broadcast that a user has read a message"""
        read_notification = ReadStatusOut(
            message_id=message_id,
            reader_id=reader_id,
            timestamp=datetime.now(UTC)
        )
        await self.broadcast_to_chat(chat_id, read_notification)

    async def listen_for_messages(self, websocket: WebSocket, chat_id: int):
        """Listen for messages on the chat channel and forward them to the WebSocket"""
        channel_name = f"chat:{chat_id}"
        try:
            async with self.broadcast.subscribe(channel=channel_name) as subscriber:
                async for event in subscriber:
                    try:
                        # The message is already JSON-serialized when published
                        await websocket.send_text(event.message)
                    except WebSocketDisconnect:
                        await self.disconnect(websocket)
                        break
        except CancelledError:
            pass  # Ignore cancellation errors

    async def get_chat_lock(self, chat_id: int) -> asyncio.Lock:
        """Get or create a lock for a specific chat"""
        if chat_id not in self.chat_locks:
            self.chat_locks[chat_id] = asyncio.Lock()
        return self.chat_locks[chat_id]
