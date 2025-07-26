import os
from flask import Flask

def create_app():
    
    app = Flask(__name__, static_folder=os.path.join(os.getcwd(), "static"))
    
    from .routes import bp
    app.register_blueprint(bp)

    print("Static folder:", app.static_folder)

    return app
