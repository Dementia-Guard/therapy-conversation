from flask import Flask
from user_services.routes import user_services_bp
from user_services.database import init_db
from user_services.models import User
from flask_cors import CORS
from quiz_services.routes import quiz_services_bp
from chatbot_services.routes import chatbot_services_bp 
from extract_services.routes import extract_services_bp
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config.from_object('config.Config')
CORS(app)

if not firebase_admin._apps:
    # Initialize Firebase
    firebase_cred_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    if firebase_cred_json:
        try:
            # Parse the JSON string from .env
            cred_dict = json.loads(firebase_cred_json)
            cred = credentials.Certificate(cred_dict)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to parse FIREBASE_SERVICE_ACCOUNT_KEY: {e}")
    else:
        cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)

# Initialize Firestore and ensure user_id=1 exists
def initialize_default_user():
    db = firestore.client()  # Get Firestore client directly here for initialization
    user_ref = db.collection(User.COLLECTION).document('1')  # Use '1' as the document ID
    if not user_ref.get().exists:
        default_user = User.to_dict({
            'full_name': 'Vidusha',
            'birth_date': '2000-08-24T00:00:00Z',  # ISO format
            'hometown': 'Malabe',
            'email': 'vidusha@example.com',
            'password': 'vidusha123'
        })
        user_ref.set(default_user)
        print("Created default user with user_id=1")
    else:
        print("User with user_id=1 already exists")

# Initialize Firestore
init_db(app)
initialize_default_user()

# Register blueprints
app.register_blueprint(user_services_bp, url_prefix='/user_services')
app.register_blueprint(quiz_services_bp, url_prefix='/quiz_services')
app.register_blueprint(chatbot_services_bp , url_prefix='/chatbot_services')
app.register_blueprint(extract_services_bp , url_prefix='/extract_services')


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
