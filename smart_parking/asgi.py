"""
ASGI config for smart_parking project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

import core.routing
from mqtt.mqtt_client import MQTTClient
from elasticsearch_client import es as elasticsearch


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_parking.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            core.routing.websocket_urlpatterns
        )
    )
})

# create connection to mqtt broker
client = MQTTClient.get_instance()
client.default_connect()
client.loop_start()

# create connection to elasticsearch
elasticsearch.init()
