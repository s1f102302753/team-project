from channels.generic.websocket import AsyncWebsocketConsumer
import json

class PostConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "posts"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        
        message = data["message"]

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "send_post",
                "message": message,
            }
        )

    async def send_post(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"]
        }))