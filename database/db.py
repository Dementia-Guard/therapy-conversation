import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json") 
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
