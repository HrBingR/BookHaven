from asgiref.wsgi import WsgiToAsgi

# Import the existing Flask WSGI app
from main import app as flask_app

# Expose an ASGI-compatible app for uvicorn
asgi_app = WsgiToAsgi(flask_app)
