from flask import Blueprint

bp = Blueprint("songs", __name__)

from app.songs import routes
