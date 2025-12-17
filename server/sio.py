import socketio

# Create a standard Async Socket.IO server
# cors_allowed_origins='*' allows your Vue app to connect from any port
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')