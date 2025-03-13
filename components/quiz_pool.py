from database.db import get_db
import random
import json

def get_quiz_questions(user_id):
    db = get_db()

    """Generate a detailed pool of quiz questions for the user based on user data."""
    user_doc = db.collection('users').document(user_id).get()
    user_data = user_doc.to_dict() if user_doc.exists else None

    pref_doc = db.collection('user_preferences').document(user_id).get()
    preferences = pref_doc.to_dict() if pref_doc.exists else None

    life_events = [doc.to_dict() for doc in db.collection('life_events').where('user_id', '==', user_id).stream()]

    images_context = [doc.to_dict() for doc in db.collection('images_with_context').where('user_id', '==', user_id).stream()]

    # Initialize quiz pool structure
    quiz_pool = {
        "about_me": [],
        "life_events": [],
        "image_context": []
    }

    # About Me Questions
    if user_data:
        full_name = user_data.get('full_name')
        birth_date = user_data.get('birth_date')
        hometown = user_data.get('hometown')
        quiz_pool["about_me"].append({
            "question": "What is your full name?",
            "answer": full_name,
            "sub_questions": [
                "Who gave you your name?",
                "Does your name have a special meaning or origin?",
                "Have you ever met someone with the same name?",
                "Do you like your full name? Why or why not?",
                "How did your family choose your name?",
                "Are there any nicknames associated with your full name?",
                "Does your full_name have any historical or cultural significance?",
                "How do you feel when you hear your full name spoken aloud?",
                "Have you ever changed your name, or would you consider changing it?",
                "Do you have any fun facts about your name?"
            ]
        })
        quiz_pool["about_me"].append({
            "question": "When is your birthday (MM-DD-YYYY)?",
            "answer": birth_date,
            "sub_questions": [
                "Do you remember a memorable birthday party?",
                "How do you usually celebrate your birthday?",
                "What's the best birthday gift you've ever received?",
                "Who do you like to celebrate your birthday with?",
                "What is the most special birthday memory you have?",
                "Have you ever had a surprise birthday party?",
                "What is your favorite part of your birthday celebration?",
                "How do you feel about getting older?",
                "What's a memorable birthday wish you've made?",
                "Do you have a favorite birthday tradition?"
            ]
        })
        quiz_pool["about_me"].append({
            "question": "Where is your hometown?",
            "answer": hometown,
            "sub_questions": [
                "What is the best memory you have from your hometown?",
                "Who do you miss the most from your hometown?",
                "How has your hometown changed over time?",
                "What makes your hometown special to you?",
                "Do you plan to visit your hometown again?",
                "What is the first thing you do when you go back to your hometown?",
                "What are the most famous places in your hometown?",
                "Do you still keep in touch with people from your hometown?",
                "How would you describe your hometown to someone who’s never been there?",
                "Would you want to live in your hometown again?"
            ]
        })

    if preferences:
        hobby = preferences.get('hobby', [])
        favorite_color = preferences.get('favorite_color')
        favorite_food = preferences.get('favorite_food')
        favorite_song = preferences.get('favorite_song')
        favorite_movie = preferences.get('favorite_movie')
        quiz_pool["about_me"].append({
            "question": "What is your favorite color?",
            "answer": favorite_color,
            "sub_questions": [
                "How many clothes do you have in your favorite color?",
                "Do you associate any memories with this color?",
                "Can you describe a special moment when this color stood out to you?",
                "Do you like to decorate your space in this color?",
                "Does this color influence your mood?",
                "Have you ever painted a room or object in this color?",
                "What other colors do you like to pair with your favorite color?",
                "Does your favorite color change with the seasons or your mood?",
                "What was the first item you bought in your favorite color?",
                "Does your favorite color represent something to you personally?"
            ]
        })
        quiz_pool["about_me"].append({
            "question": "What food do you love the most?",
            "answer": favorite_food,
            "sub_questions": [
                "When did you first try this food?",
                "Can you cook this food yourself?",
                "Who introduced you to this food?",
                "What is the most memorable experience you’ve had while eating this food?",
                "Is this food a part of any family or cultural tradition?",
                "What restaurant or place serves the best version of this food?",
                "How often do you eat this food?",
                "Is there a specific memory tied to eating this food?",
                "What is your favorite drink or side dish to pair with this food?",
                "How do you feel when you eat this food?"
            ]
        })

    # Life Events Questions
    for event in life_events:
        event_title = event.get('event_title')
        event_date = event.get('event_date')
        description = event.get('description')
        quiz_pool["life_events"].append({
            "question": f"What happened during {event_title}?",
            "answer": description,
            "sub_questions": [
                f"When did {event_title} occur (MM-DD-YYYY)?",
                "How did this event affect your life?",
                "Who was the most important person during {event_title}?",
                f"Can you describe the emotions you felt during {event_title}?",
                f"Was there a specific moment that stands out from {event_title}?",
                f"What did you learn from {event_title}?",
                f"How has {event_title} impacted you today?",
                f"Do you remember any funny or unexpected moments from {event_title}?",
                f"Who helped you through {event_title}?",
                f"Is there a specific song or memory tied to {event_title}?"
            ]
        })

    # Image Context Questions
    for image in images_context:
        context_who = image.get('context_who')
        context_where = image.get('context_where')
        context_when = image.get('context_when')
        event_title = image.get('event_title')
        quiz_pool["image_context"].append({
            "question": f"Who are the people in the image from {event_title}?",
            "answer": json.dumps(context_who),  # Store as JSON string
            "sub_questions": [
                "What event is captured in this image?",
                "How do you feel about the people in this photo?",
                "Who was the most emotional person during the event?",
                "How did you interact with the people in this photo?",
                "Who is the person you remember the most from this photo?",
                "Do you still stay in touch with anyone from this event?",
                f"What story does this photo tell about {event_title}?",
                "Who took this picture and why was it significant?",
                "Is there a memory associated with this specific photo?",
                "What moment in the event is captured in this photo?"
            ]
        })

    # Select 2 random questions for each category with their sub-questions
    quiz_result = {
        "about_me": random.sample(quiz_pool["about_me"], min(2, len(quiz_pool["about_me"]))),
        "life_events": random.sample(quiz_pool["life_events"], min(2, len(quiz_pool["life_events"]))),
        "image_context": random.sample(quiz_pool["image_context"], min(2, len(quiz_pool["image_context"])))
    }
    return quiz_result
