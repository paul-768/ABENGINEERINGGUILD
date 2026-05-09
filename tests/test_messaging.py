# test_messaging.py
import sys
print("Testing messaging system dependencies...")

try:
    import flask_socketio
    print("✓ Flask-SocketIO installed")
except ImportError:
    print("✗ Flask-SocketIO not installed")

try:
    import eventlet
    print("✓ eventlet installed")
except ImportError:
    print("✗ eventlet not installed")

try:
    from PIL import Image
    print("✓ Pillow installed")
except ImportError:
    print("✗ Pillow not installed")

try:
    import cv2
    print("✓ OpenCV installed")
except ImportError:
    print("✗ OpenCV not installed")

try:
    import mutagen
    print("✓ mutagen installed")
except ImportError:
    print("✗ mutagen not installed")

print("\nTo test the messaging system:")
print("1. Run: python run.py")
print("2. Open http://localhost:5000/messages/inbox")
print("3. Start a conversation")
print("4. Test calls, emojis, and file uploads")