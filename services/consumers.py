from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import StopConsumer
import asyncio

class VideoStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.source_id = self.scope['url_route']['kwargs']['source_id']
        self.is_streaming = False
        await self.accept()
        self.is_streaming = True

    async def disconnect(self, close_code):
        self.is_streaming = False
        try:
            # Clean up any resources
            if hasattr(self, 'stream_task'):
                self.stream_task.cancel()
                try:
                    await self.stream_task
                except asyncio.CancelledError:
                    pass
        finally:
            raise StopConsumer()

    async def receive(self, text_data=None, bytes_data=None):
        # Handle incoming messages if needed
        pass
