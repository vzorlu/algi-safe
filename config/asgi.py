import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from config import settings
from stream.routing import websocket_urlpatterns

# Set Django settings module and setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# Get ASGI application
django_asgi_app = get_asgi_application()

# Create application
application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)

settings.WEBSOCKET_TIMEOUT = 600  # 10 dakika
