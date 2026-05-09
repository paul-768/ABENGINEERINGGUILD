from flask import Blueprint

reviewer_bp = Blueprint('reviewer', __name__)

from app.reviewer import routes