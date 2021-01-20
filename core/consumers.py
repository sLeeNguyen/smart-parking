import json

import channels
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer

from core.exceptions import DataException


PARKING_STATE_GROUP = 'parking_state'


class ParkingStateConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_name = PARKING_STATE_GROUP

    async def connect(self):
        # join group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print("accept new connection, new channel was created: " + self.channel_name)

    async def disconnect(self, code):
        # remove from group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print("remove channel from group: " + self.channel_name)

    async def send_data(self, event):
        data = event['data']
        if type(data) != dict:
            raise DataException("The data must be dict.")
        print("send data: ", data)
        await self.send(text_data=json.dumps(data))


def send_parking_state_data(data):
    channel_layer = channels.layers.get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        PARKING_STATE_GROUP,
        {"type": "send_data", "data": data}
    )
