from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS

jwt = JWTManager()
bcrypt = Bcrypt()
cors = CORS()
