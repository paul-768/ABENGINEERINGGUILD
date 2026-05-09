import os

# Create the upload directories
base_dir = os.path.join('app', 'static', 'uploads')
dirs = ['profile_pictures', 'cover_photos', 'post_images']

for dir_name in dirs:
    dir_path = os.path.join(base_dir, dir_name)
    os.makedirs(dir_path, exist_ok=True)
    print(f"Created: {dir_path}")

print("Upload directories created!")