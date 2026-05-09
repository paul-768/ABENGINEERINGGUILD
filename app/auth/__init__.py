from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

# Import routes AFTER blueprint is defined
from app.auth import routes