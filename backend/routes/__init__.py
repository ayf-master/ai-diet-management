from flask import Blueprint

api = Blueprint('api', __name__, url_prefix='/api')

from . import auth
from . import food
from . import recipe
from . import meal
from . import weight
from . import ai
from . import disease
