from flask import session as flask_session, Blueprint, jsonify, request, current_app
import random
from user_services.models import User, ChatSession, ChatRecord, QuizScore
from quiz_services.routes import get_preferences_quiz, get_life_events_quiz, get_images_quiz
from transformers import AutoTokenizer, AutoModelForCausalLM
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer, util
from firebase_admin import firestore

chatbot_services_bp = Blueprint('chatbot_services', __name__)

chatbot_tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
chatbot_model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Helper to get Firestore DB
def get_db():
    return current_app.config['FIRESTORE_DB']

# Helper to get next session ID
def get_next_session_id(db):
    counter_ref = db.collection('metadata').document('chat_session_counter')
    counter_doc = counter_ref.get()

    # Use a transaction to ensure atomic increment
    @firestore.transactional
    def update_counter(transaction):
        snapshot = counter_ref.get(transaction=transaction)
        if not snapshot.exists:
            # Initialize counter at 0 if it doesn't exist
            transaction.set(counter_ref, {'last_id': 0})
            return 1

        last_id = snapshot.to_dict().get('last_id', 0)
        new_id = last_id + 1
        transaction.update(counter_ref, {'last_id': new_id})
        return new_id

    transaction = db.transaction()
    return update_counter(transaction)

# Start a chat session
@chatbot_services_bp.route('/start_chat/<int:user_id>', methods=['GET'])
def start_chat(user_id):
    db = get_db()
    session_id = get_next_session_id(db)
    now = datetime.utcnow().isoformat()
    session_data = ChatSession.to_dict({
        'user_id': user_id,
        'start_time': now,
        'last_active': now,
        'quiz_count': 0,
        'end_time': None
    })
    session_ref = db.collection(ChatSession.COLLECTION).document(str(session_id))
    session_ref.set(session_data)

    return jsonify({
        'message': 'Hello! I am your therapy assistant. Would you like to take a quiz? Say "yes" to start or "no" to continue chatting.',
        'session_id': session_id
    })

# Chat with the bot
@chatbot_services_bp.route('/chat/<int:session_id>', methods=['POST'])
def chat_with_user(session_id):
    user_input = request.json.get('message', "").strip().lower()
    db = get_db()
    session_ref = db.collection(ChatSession.COLLECTION).document(str(session_id))
    session_doc = session_ref.get()

    if not session_doc.exists:
        return jsonify({'message': 'Chat session not found!'}), 404

    session = session_doc.to_dict()
    last_active = datetime.fromisoformat(session['last_active'])

    # Auto-close session if inactive for 2 minutes
    if last_active < datetime.utcnow() - timedelta(minutes=2):
        return close_session(session_id)
    
    # Update last_active
    session_ref.update({'last_active': datetime.utcnow().isoformat()})

    # Record user input
    chat_record_data = ChatRecord.to_dict({
        'question': user_input,
        'session_id': session_id,
        'answer': None,
        'is_correct': False
    })
    db.collection(ChatRecord.COLLECTION).document().set(chat_record_data)

    # Fetch user full_name for response
    user_doc = db.collection(User.COLLECTION).document(str(session['user_id'])).get()
    user_name = user_doc.to_dict()['full_name'] if user_doc.exists else "User"

    # Handle user responses
    if user_input in ["hello", "hi", "hey"]:
        return jsonify({'user_message': user_input, 'message': f"Hello! How can I assist you today, {user_name}?"})

    # Keywords to trigger the start of the quiz
    quiz_keywords = ["yes","quiz", "ques", "question", "start quiz", "questn", "do next", "session", "begin quiz", "play quiz"]

    # Check if user input contains any of the keywords
    if any(keyword in user_input.lower() for keyword in quiz_keywords):
        return jsonify({'user_message': user_input, 'message': "Let's start the quiz!", 'quiz': True})

    if user_input == "no":
        return jsonify({'user_message': user_input, 'message': 'Alright! Let me know if you need anything else.'})

    if user_input in ["exit", "stop", "quit"]:
        return close_session(session_id)

    if user_input in ["help", "what can you do", "options"]:
        return jsonify({'user_message': user_input, 'message': 'I can chat with you, start a quiz, and provide helpful responses. Just say "quiz" to start!'})

    return chat_response(user_input)

def chat_response(user_input):
    # Use chatbot_tokenizer to generate a response
    input_ids = chatbot_tokenizer.encode(user_input + chatbot_tokenizer.eos_token, return_tensors='pt')
    chat_history_ids = chatbot_model.generate(input_ids, max_length=1000, pad_token_id=chatbot_tokenizer.eos_token_id)
    
    bot_response = chatbot_tokenizer.decode(chat_history_ids[:, input_ids.shape[-1]:][0], skip_special_tokens=True)
    
    return jsonify({'user_message': user_input, 'message': bot_response})


@chatbot_services_bp.route('/quiz/<int:session_id>', methods=['POST'])
def handle_quiz_answer(session_id):
    db = get_db()
    session_ref = db.collection(ChatSession.COLLECTION).document(str(session_id))
    session_doc = session_ref.get()

    if not session_doc.exists:
        return jsonify({'message': 'Chat session not found!'}), 404

    session = session_doc.to_dict()
    user_answer = request.json.get('answer', "").strip()

    # If the user initiates the quiz
    if user_answer.lower() == "start quiz":
        if session.get('quiz_count', 0) == 0:
            quiz = get_preferences_quiz(session['user_id'])
            flask_session['current_quiz_question'] = quiz['question']
            flask_session['current_quiz_answer'] = quiz.get('answer', None)
            flask_session['current_quiz_base64'] = quiz.get('image_base64', None)
            flask_session['asked_questions'] = [quiz['question']]  # Track asked questions
            session_ref.update({'quiz_count': 1})
            print(f"Started quiz, session quiz count: 1")
            return jsonify({
                'question': quiz['question'],
                'answer': quiz.get('answer', None),
                'hint': generate_hint(quiz.get('answer', None)),
                'image_base64': quiz.get('image_base64', None),
                'quiz_done': False,
                'is_correct': None,
                'similarity_score': None
            })
        else:
            return jsonify({'message': 'Quiz already started!'}), 400

    # If the quiz is already started, validate the user's answer
    correct_answer = flask_session.get('current_quiz_answer', None)
    
    if correct_answer:
        if isinstance(correct_answer, list):  # Handle list case
            correct_answer = ', '.join(correct_answer)
        is_correct, similarity_score = check_answer(user_answer, correct_answer)
        
        if(not is_correct):
            return jsonify({
                'question': flask_session['current_quiz_question'],
                'answer': flask_session['current_quiz_answer'],
                'hint': generate_hint(flask_session['current_quiz_answer']),
                'image_base64': flask_session['current_quiz_base64'],
                'quiz_done': False,
                'is_correct': is_correct,
                'similarity_score': similarity_score
            })
        
        # Save the chat record with the user's answer
        chat_record_data = ChatRecord.to_dict({
            'question': flask_session.get('current_quiz_question', ""),
            'answer': user_answer,
            'session_id': session_id,
            'is_correct': is_correct
        })
        db.collection(ChatRecord.COLLECTION).document().set(chat_record_data)

        # Increment quiz count
        quiz_count = session.get('quiz_count', 0) + 1
        session_ref.update({'quiz_count': quiz_count})

        # If the quiz count reaches 5, close the session
        if quiz_count >= 5:
            return close_session(session_id, quiz_complete=True)

        # Fetch next quiz with uniqueness check
        next_quiz = None
        asked_questions = flask_session.get('asked_questions', [])

        while True:
            if quiz_count == 1:
                next_quiz = get_preferences_quiz(session['user_id'])
            elif quiz_count in [2, 3]:
                next_quiz = get_life_events_quiz(session['user_id'])
            elif quiz_count in [4, 5]:
                next_quiz = get_images_quiz(session['user_id'])

            if not next_quiz or 'question' not in next_quiz:
                return jsonify({'message': 'No more quizzes available.'}), 400  

            if next_quiz['question'] not in asked_questions:
                break
            next_quiz = None  # Retry if question was already asked

        # Store the next question and answer in the session
        flask_session['current_quiz_question'] = next_quiz['question']
        flask_session['current_quiz_answer'] = next_quiz.get('answer', None)
        flask_session['asked_questions'] = asked_questions + [next_quiz['question']]

        print(f"Next quiz question: {next_quiz['question']}")

        return jsonify({
            'question': next_quiz['question'],
            'answer': next_quiz.get('answer', None),
            'hint': generate_hint(next_quiz.get('answer', None)),
            'image_base64': next_quiz.get('image_base64', None),
            'quiz_done': False,
            'is_correct': None,
            'similarity_score': None
        })

    # If there's no answer available in the session
    return jsonify({'message': 'No active quiz found.'}), 400


def check_answer(user_answer, correct_answer):
    if not user_answer or not correct_answer:
        return False, None

    print(f"User Answer: '{user_answer.strip().lower()}'")
    print(f"Correct Answer: '{correct_answer.strip().lower()}'")

    try:
        # Attempt to parse both answers as dates
        user_answer_date = datetime.strptime(user_answer.strip().lower(), "%Y-%m-%d")
        correct_answer_date = datetime.strptime(correct_answer.strip().lower(), "%Y-%m-%d")

        # If both are valid dates, compare them directly
        is_correct = user_answer_date == correct_answer_date
        similarity_score = 1.0 if is_correct else 0.0
    except ValueError:
        # Compute embeddings and cosine similarity
        user_embedding = embedding_model.encode(user_answer.strip().lower(), convert_to_tensor=True)
        correct_embedding = embedding_model.encode(correct_answer.strip().lower(), convert_to_tensor=True)

        similarity_score = util.pytorch_cos_sim(user_embedding, correct_embedding).item()
        print(f"Similarity Score: {similarity_score:.2f}")

        # Consider correct if similarity is 70% or higher
        is_correct = similarity_score >= 0.7

    print(f"Answer Correct: {is_correct}")
    return is_correct, similarity_score




# Generate a hint
def generate_hint(correct_answer):
    if not correct_answer:
        return "Try again!"
    return f"The answer starts with '{correct_answer[0]}'." if correct_answer else "Try again!"

def close_session(session_id, quiz_complete=False):
    db = get_db()
    session_ref = db.collection(ChatSession.COLLECTION).document(str(session_id))
    session_doc = session_ref.get()
    if not session_doc.exists:
        return jsonify({'message': 'Session not found!'}), 404
    
    # Calculate total number of correct answers
    correct_answers = sum(1 for record in db.collection(ChatRecord.COLLECTION)
                         .where('session_id', '==', session_id)
                         .where('is_correct', '==', True)
                         .stream())

    if quiz_complete:
        total_questions = 5
        score_data = QuizScore.to_dict({
            'session_id': session_id,
            'total_questions': total_questions,
            'correct_answers': correct_answers
        })
        db.collection(QuizScore.COLLECTION).document(str(session_id)).set(score_data)
        score = score_data['score']
        session_ref.update({'end_time': datetime.utcnow().isoformat()})
        return jsonify({
            'question': f'Quiz complete! Your score: {score:.2f}%. Thanks for playing!',
            'quiz_done': True
        })

    session_ref.update({'end_time': datetime.utcnow().isoformat()})
    return jsonify({'message': 'Session closed due to inactivity or user exit.'})
