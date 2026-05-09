# test_messages.py
import os
import sys

print("Testing messaging system...")
print("=" * 50)

# Check if default images exist
default_profile = 'app/static/img/default_profile.png'
default_cover = 'app/static/img/default_cover.jpg'

if os.path.exists(default_profile):
    print(f"✓ Default profile image: {default_profile}")
else:
    print(f"✗ Missing: {default_profile}")

if os.path.exists(default_cover):
    print(f"✓ Default cover image: {default_cover}")
else:
    print(f"✗ Missing: {default_cover}")

# Check required directories
dirs = [
    'app/static/uploads/profile_pictures',
    'app/static/uploads/message_attachments',
    'app/static/js',
    'app/static/css'
]

for dir_path in dirs:
    if os.path.exists(dir_path):
        print(f"✓ Directory exists: {dir_path}")
    else:
        print(f"✗ Missing directory: {dir_path}")

print("\nTo test the messaging system:")
print("1. Make sure you have at least 2 user accounts")
print("2. Login with one account")
print("3. Go to /messages/inbox")
print("4. Start a conversation with another user")
print("5. Test these features:")
print("   - Send message (press Enter or click send button)")
print("   - Make a voice call (phone icon)")
print("   - Make a video call (video icon)")
print("   - Open emoji picker (smiley icon)")
print("   - Open more options (three dots)")
print("\nIf calls don't work, check browser console for errors.")
print("If messages don't send, check the network tab in browser dev tools.")