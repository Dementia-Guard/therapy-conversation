import random
from flask import Blueprint, jsonify, current_app
from user_services.models import UserPreference, LifeEvent, ImageWithContext
import json
from datetime import datetime, timedelta

quiz_services_bp = Blueprint('quiz_services', __name__)

# Helper to get Firestore DB
def get_db():
    return current_app.config['FIRESTORE_DB']

# Quiz for user preferences (Multiple questions)
def get_preferences_quiz(user_id):
    db = get_db()
    prefs = db.collection(UserPreference.COLLECTION).where('user_id', '==', user_id).stream()
    preferences = [pref.to_dict() for pref in prefs]
    if not preferences:
        return None
    # Randomly select one preference question
    pref = preferences[0]  # As we know the structure, we just pick the first one
    questions = [
        {"question": "What is your favorite color?", "answer": pref.get('favorite_color')},
        {"question": "What is your favorite food?", "answer": pref.get('favorite_food')},
        {"question": "What is your favorite movie?", "answer": pref.get('favorite_movie')},
        {"question": "What is your favorite song?", "answer": pref.get('favorite_song')},
        {"question": "What is your favorite hobby?", "answer": pref.get('hobby')}
    ]
    return random.choice(questions)


def get_life_events_quiz(user_id):
    db = get_db()
    events = db.collection(LifeEvent.COLLECTION).where('user_id', '==', user_id).stream()
    life_events = [event.to_dict() for event in events]
    if not life_events:
        return jsonify({'message': 'No life events found for this user'}), 404
    
    # Randomly select a life event
    random_event = random.choice(life_events)

    # Format event date properly
    event_date = random_event.get('event_date')
    event_date_str = event_date if event_date else "Unknown date"
    if event_date:
        event_date_str = datetime.fromisoformat(event_date).strftime('%Y-%m-%d')
    event_title = random_event.get('event_title', "Untitled Event")
    event_desc = random_event.get('description', "No description available")
    event_emotions = random_event.get('emotions', ["No emotions recorded"])

    # Quiz questions with event context
    questions = [
        {"question": f"Regarding the event on {event_date_str}, what is the title?", "answer": event_title},
        {"question": f"You had an event titled '{event_title}' on {event_date_str}. Can you describe what happened?", "answer": event_desc},
        {"question": f"How did you feel during the event on {event_date_str}?", "answer": event_emotions},
        {"question": f"What was the most memorable part of '{event_title}'?", "answer": event_desc},
        {"question": f"Can you recall the exact date of the event '{event_title}'?", "answer": event_date_str},
        {"question": f"Think back to '{event_title}'. What were two emotions you felt?", "answer": event_emotions[:2] if len(event_emotions) >= 2 else event_emotions},
        {"question": f"If you could summarize '{event_title}' in one word, what would it be?", "answer": event_title.split()[0] if event_title else "No answer"},
        {"question": f"What impact did the event on {event_date_str} have on your life?", "answer": event_desc},
        {"question": f"If you were to describe '{event_title}' to a friend, what would you say?", "answer": event_desc},
    ]
    
    # Return a random question from the quiz pool
    return jsonify(random.choice(questions))


def get_images_quiz(user_id):
    db = get_db()
    images = db.collection(ImageWithContext.COLLECTION).where('user_id', '==', user_id).stream()
    image_list = [image.to_dict() for image in images]
    if not image_list:
        return None
    
    # Randomly select an image
    image = random.choice(image_list)

    # Extract details safely
    event_title = image.get('event_title', "Unknown Event")
    context_when = image.get('context_when')
    context_when_str = context_when if context_when else "Date Not Available"
    if context_when:
        context_when_str = datetime.fromisoformat(context_when).strftime('%Y-%m-%d')
    context_where = image.get('context_where', "Location Not Available")
    context_who = image.get('context_who', ["Unknown People"])
    description = image.get('description', "No description available")
    
    # Quiz questions
    questions = [
        {"question": f"This image is linked to an event. Can you recall which one?", "answer": event_title},
        {"question": f"Think back to this image. What was the occasion?", "answer": event_title},
        {"question": f"When was this photo taken?", "answer": context_when_str},
        {"question": f"Where was this picture captured?", "answer": context_where},
        {"question": f"Can you name one person in the image?", "answer": context_who[0] if context_who else "Unknown"},
        {"question": f"List all the people you remember in this photo.", "answer": ", ".join(context_who)},
        {"question": f"What emotions does this image bring back?", "answer": "Happy, Excited" if "party" in description.lower() else "Sentimental, Nostalgic"},
        {"question": f"If you had to give this image a title, what would it be?", "answer": event_title},
        {"question": f"Describe what was happening in this image.", "answer": description},
        {"question": f"What do you remember most about this day?", "answer": description}
    ]

    # Select a random question
    quiz = random.choice(questions)
    quiz["image_base64"] = image.get('image_base64')  # Include image in response
    return quiz