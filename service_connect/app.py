from flask import Flask
import logging
from blueprints.connect_blueprint import connect_bp

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Register blueprint
    app.register_blueprint(connect_bp)
    
    # DEBUG: Print all registered routes
    print("🔍 REGISTERED ROUTES:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint} [{', '.join(rule.methods)}]")
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)