from flask import Blueprint, request, jsonify
from .models import User, UserPreference, LifeEvent, ImageWithContext
from flask import current_app
import json
from datetime import datetime

user_services_bp = Blueprint('user_services', __name__)

# Helper to get Firestore DB
def get_db():
    return current_app.config['FIRESTORE_DB']

@user_services_bp.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()
    
    # Convert birth_date string to a datetime.date object
    if 'birth_date' in data:
        data['birth_date'] = datetime.strptime(data['birth_date'], "%Y-%m-%d").isoformat()

    user_data = User.to_dict(data)
    db = get_db()
    user_ref = db.collection(User.COLLECTION).document()
    user_ref.set(user_data)
    
    return jsonify({"message": "User created successfully"}), 201

@user_services_bp.route('/create_preference', methods=['POST'])
def create_preference():
    data = request.json
    pref_data = UserPreference.to_dict(data)
    db = get_db()
    pref_ref = db.collection(UserPreference.COLLECTION).document()
    pref_ref.set(pref_data)
    return jsonify({'message': 'User preference created'})

@user_services_bp.route('/create_life_event', methods=['POST'])
def create_life_event():
    data = request.json
    if 'event_date' in data:
        data['event_date'] = datetime.strptime(data['event_date'], '%Y-%m-%d').isoformat()
    event_data = LifeEvent.to_dict(data)
    db = get_db()
    event_ref = db.collection(LifeEvent.COLLECTION).document()
    event_ref.set(event_data)
    return jsonify({'message': 'Life event created', 'event_id': event_ref.id})  # Use event.id instead of event.event_id

@user_services_bp.route('/create_image', methods=['POST'])
def create_image():
    data = request.json
    if 'context_when' in data:
        data['context_when'] = datetime.strptime(data['context_when'], '%Y-%m-%d').isoformat()
    image_data = ImageWithContext.to_dict(data)
    db = get_db()
    image_ref = db.collection(ImageWithContext.COLLECTION).document()
    image_ref.set(image_data)
    return jsonify({'message': 'Image with context created', 'image_id': image_ref.id})  # Use image.id instead of image.image_id

@user_services_bp.route('/get_user/<user_id>', methods=['GET'])
def get_user(user_id):
    db = get_db()
    user_ref = db.collection(User.COLLECTION).document(user_id).get()
    if not user_ref.exists:
        return jsonify({'message': 'User not found'}), 404
    user = user_ref.to_dict()
    return jsonify({
        'user_id': user_ref.id,
        'full_name': user['full_name'],
        'birth_date': user['birth_date'],  # Already ISO string
        'hometown': user.get('hometown')
    })

@user_services_bp.route('/get_preferences/<int:user_id>', methods=['GET'])
def get_preferences(user_id):
    db = get_db()
    prefs = db.collection(UserPreference.COLLECTION).where('user_id', '==', user_id).stream()
    preferences = [pref.to_dict() for pref in prefs]
    return jsonify(preferences)

@user_services_bp.route('/get_life_events/<int:user_id>', methods=['GET'])
def get_life_events(user_id):
    db = get_db()
    events = db.collection(LifeEvent.COLLECTION).where('user_id', '==', user_id).stream()
    event_list = [{
        'event_id': event.id,
        'user_id': event.to_dict()['user_id'],
        'event_title': event.to_dict()['event_title'],
        'event_date': event.to_dict().get('event_date'),
        'description': event.to_dict().get('description'),
        'emotions': event.to_dict().get('emotions', [])
    } for event in events]
    if not event_list:
        return jsonify({'message': 'No life events found for this user'}), 404
    return jsonify(event_list)


@user_services_bp.route('/get_images/<int:user_id>', methods=['GET'])
def get_images(user_id):
    db = get_db()
    images = db.collection(ImageWithContext.COLLECTION).where('user_id', '==', user_id).stream()
    image_list = [{
        'image_id': image.id,
        'user_id': image.to_dict()['user_id'],
        'image_base64': image.to_dict()['image_base64'],
        'context_who': image.to_dict().get('context_who', []),
        'context_where': image.to_dict().get('context_where'),
        'context_when': image.to_dict().get('context_when'),
        'event_title': image.to_dict().get('event_title'),
        'description': image.to_dict().get('description')
    } for image in images]
    if not image_list:
        return jsonify({'message': 'No images found for this user'}), 404
    return jsonify(image_list)

@user_services_bp.route('/request_login', methods=['POST'])
def request_login():
    data = request.get_json()
    db = get_db()
    users = db.collection(User.COLLECTION).where('email', '==', data['email']).where('password', '==', data['password']).stream()
    user = next(iter(users), None)
    if user:
        return jsonify({"message": "Login successful", "user_id": user.id})
    return jsonify({"error": "Invalid credentials"}), 401