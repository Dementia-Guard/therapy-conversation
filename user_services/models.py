from datetime import datetime
from firebase_admin import firestore

db = None

class User:
    COLLECTION = 'users'

    @staticmethod
    def to_dict(user_data):
        return {
            'full_name': user_data['full_name'],
            'birth_date': user_data['birth_date'],  # ISO format string or timestamp
            'hometown': user_data.get('hometown'),
            'email': user_data['email'],
            'password': user_data['password']  # Note: Hash this in production!
        }

class UserPreference:
    COLLECTION = 'user_preferences'

    @staticmethod
    def to_dict(pref_data):
        return {
            'user_id': pref_data['user_id'],
            'hobby': pref_data.get('hobby'),
            'favorite_color': pref_data.get('favorite_color'),
            'favorite_food': pref_data.get('favorite_food'),
            'favorite_song': pref_data.get('favorite_song'),
            'favorite_movie': pref_data.get('favorite_movie')
        }

class LifeEvent:
    COLLECTION = 'life_events'

    @staticmethod
    def to_dict(event_data):
        return {
            'user_id': event_data['user_id'],
            'event_title': event_data['event_title'],
            'event_date': event_data.get('event_date'),  # ISO format string or timestamp
            'description': event_data.get('description'),
            'emotions': event_data.get('emotions', [])
        }

class ImageWithContext:
    COLLECTION = 'images_with_context'

    @staticmethod
    def to_dict(image_data):
        return {
            'user_id': image_data['user_id'],
            'image_base64': image_data['image_base64'],
            'context_who': image_data.get('context_who', []),
            'context_where': image_data.get('context_where'),
            'context_when': image_data.get('context_when'),  # ISO format string or timestamp
            'event_title': image_data.get('event_title'),
            'description': image_data.get('description')
        }

class ChatSession:
    COLLECTION = 'chat_sessions'

    @staticmethod
    def to_dict(session_data):
        return {
            'user_id': session_data['user_id'],
            'start_time': session_data.get('start_time', datetime.utcnow().isoformat()),
            'last_active': session_data.get('last_active', datetime.utcnow().isoformat()),
            'end_time': session_data.get('end_time'),
            'quiz_count': session_data.get('quiz_count', 0)
        }

class ChatRecord:
    COLLECTION = 'chat_records'

    @staticmethod
    def to_dict(record_data):
        return {
            'session_id': record_data['session_id'],
            'question': record_data['question'],
            'answer': record_data.get('answer'),
            'is_correct': record_data.get('is_correct', False)
        }

class QuizScore:
    COLLECTION = 'quiz_scores'

    @staticmethod
    def to_dict(score_data):
        score = (score_data['correct_answers'] / score_data['total_questions'] * 100) if score_data['total_questions'] > 0 else 0
        return {
            'session_id': score_data['session_id'],
            'total_questions': score_data.get('total_questions', 0),
            'correct_answers': score_data.get('correct_answers', 0),
            'score': score
        }