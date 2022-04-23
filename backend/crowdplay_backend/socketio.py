from engineio.payload import Payload
from flask_socketio import SocketIO

Payload.max_decode_packets = 500
socketio = SocketIO()
