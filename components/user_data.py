from database.db import get_db
import json

def save_user_data(user_id, user_data):
    db = get_db()

    """Save user data to the database."""
    try:
        # Save basic user information
        about_me = user_data['about_me']
        db.collection('users').document(user_id).set({
            'user_id': user_id,
            'full_name': about_me['full_name'],
            'birth_date': about_me['birth_date'],
            'hometown': about_me['hometown']
        })

        # Save user preferences
        db.collection('user_preferences').document(user_id).set({
            'user_id': user_id,
            'hobby': about_me['hobbies'],
            'favorite_color': about_me['favorite_things']['color'],
            'favorite_food': about_me['favorite_things']['food'],
            'favorite_song': about_me['favorite_things']['song'],
            'favorite_movie': about_me['favorite_things']['movie']
        })

        # Save life events
        for event in user_data['life_events']:
            event_doc = db.collection('life_events').add({
                'user_id': user_id,
                'event_title': event['event_title'],
                'event_date': event['date'],
                'description': event['description'],
                'emotions': event['emotions']
            })[1]
            event_id = event_doc.id
            for person in event['related_people']:
                db.collection('life_event_people').add({
                    'event_id': event_id,
                    'person_name': person
                })

        # Save images with context
        for image in user_data['images_with_context']:
            db.collection('images_with_context').add({
                'user_id': user_id,
                'image_base64': image['image_base64'],
                'context_who': image['context']['who'],
                'context_where': image['context']['where'],
                'context_when': image['context']['when'],
                'event_title': image['context']['event_title'],
                'description': image['context']['description']
            })

        return {"message": "User data saved successfully"}

    except Exception as e:
        return {"error": str(e)}