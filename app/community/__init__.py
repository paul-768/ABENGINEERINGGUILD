# app/community/__init__.py
from flask import Blueprint

# Create the blueprint
community_bp = Blueprint('community', __name__, url_prefix='/community')

# Import routes after blueprint creation
from app.community import routes