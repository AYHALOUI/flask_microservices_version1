from  flask import  Flask
import logging
import os
from blueprints.contact_blueprint import contact_bp

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)

    #Configure logging
    logging.basicConfig(level=logging.INFO)

    #Register blueprint
    app.register_blueprint(contact_bp)   
    return app;

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port="5000", debug=True)