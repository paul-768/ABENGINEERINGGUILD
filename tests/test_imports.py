try:
    from flask_wtf import FlaskForm
    print("✓ flask_wtf: OK")
except ImportError as e:
    print(f"✗ flask_wtf: {e}")

try:
    import flask_socketio
    print("✓ flask_socketio: OK")
except ImportError as e:
    print(f"✗ flask_socketio: {e}")

try:
    import eventlet
    print("✓ eventlet: OK")
except ImportError as e:
    print(f"✗ eventlet: {e}")

print("All required packages installed!")