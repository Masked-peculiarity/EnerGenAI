from flask import Flask
from extensions import jwt, bcrypt, cors

def create_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "energy-secret-key"

    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app)

    from auth.routes import auth_bp
    from chat.routes import chat_bp
    from dashboard.routes import dashboard_bp
    from predict.routes import prediction_bp
    from queries.routes import query_bp


    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(prediction_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(query_bp)

    return app

app = create_app()

@app.route("/health")
def health():
    return {"status": "ok"}
    
@app.route("/")
def home():
    return "OK"

if __name__ == "__main__":
    app.run()







