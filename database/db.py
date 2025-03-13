import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Initialize Firebase Admin SDK
if not firebase_admin._apps:  # Prevent re-initialization
    # Option 1: Load from FIREBASE_SERVICE_ACCOUNT_KEY (JSON string) - used in Cloud Run/GitHub workflow
    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    if service_account_json:
        try:
            cred_dict = json.loads(service_account_json)
            cred = credentials.Certificate(cred_dict)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid FIREBASE_SERVICE_ACCOUNT_KEY JSON: {e}")
    # Option 3: Fallback to Application Default Credentials - for Cloud Run with service account or gcloud auth
    else:
        cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)

db = firestore.client()

def get_db():
    """Return the Firestore client."""
    return db

def init_db():
    """Initialize Firestore with sample data."""
    
    users_ref = db.collection('users')
    if not users_ref.limit(1).get():
        # Insert sample users
        users_ref.document('1').set({
            'user_id': '1',
            'full_name': 'Michael Johnson',
            'birth_date': '1965-04-10',
            'hometown': 'Springfield, Illinois'
        })
        users_ref.document('2').set({
            'user_id': '2',
            'full_name': 'Sarah Williams',
            'birth_date': '1970-07-15',
            'hometown': 'Austin, Texas'
        })
    print("Firestore initialized with sample data if empty.")
