from flask import Blueprint

scoreboard_bp = Blueprint('scoreboard', __name__)

from app.scoreboard import routes