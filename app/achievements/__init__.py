# app/achievements/__init__.py
from flask import Blueprint

achievements_bp = Blueprint('achievements', __name__, url_prefix='/achievements')

from app.achievements import routes