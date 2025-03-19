from firebase_admin import firestore

db = None

def init_db(app):
    global db
    db = firestore.client()  # Initialize Firestore client
    app.config['FIRESTORE_DB'] = db
