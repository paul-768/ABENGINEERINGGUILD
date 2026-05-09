# app/config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(basedir, 'data')
os.makedirs(data_dir, exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(data_dir, "quizzes.db")}'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'pdf', 'doc', 'docx', 'txt', 'mp3', 'wav', 'mp4'}
    WTF_CSRF_CHECK_DEFAULT = False
