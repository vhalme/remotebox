import os
from flask import Flask

def create_app():
    
    app = Flask(__name__, template_folder=os.path.join(os.getcwd(), "templates"))
    
    from .routes import bp
    app.register_blueprint(bp)
    
    print("Template folder:", app.template_folder)

    return app
