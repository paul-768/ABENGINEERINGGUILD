# app/messages/__init__.py
from flask import Blueprint

messages_bp = Blueprint('messages', __name__)

from app.messages import routes