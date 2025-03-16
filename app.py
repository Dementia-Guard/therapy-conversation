from flask import Flask, request, jsonify
from database.db import get_db, init_db
from components.quiz_pool import get_quiz_questions
import json
import random
from datetime import datetime
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from sentence_transformers import SentenceTransformer, util
import numpy as np
import os
from memory_profiler import profile

# Load SentenceTransformer model for evaluating answers
@profile
def load_embedding_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

embedding_model = load_embedding_model()

# Load DialoGPT model and tokenizer for chat conversations
@profile
def load_chatbot_model():
    tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
    model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")
    return tokenizer, model

chatbot_tokenizer, chatbot_model = load_chatbot_model()

# Initialize Flask app
app = Flask(__name__)

# Initialize the database
init_db()

# Function to get or create session data from Firestore
def get_session(user_id):
    db = get_db()
    session_ref = db.collection('sessions').document(user_id)
    session = session_ref.get()
    if not session.exists:
        session_data = {
            'dialog_count': 0,
            'answers': [],
            'start_time': datetime.now().isoformat(),
            'is_quiz_started': False
        }
        session_ref.set(session_data)
        return session_data
    return session.to_dict()

def update_session(user_id, session_data):
    db = get_db()
    db.collection('sessions').document(user_id).set(session_data)

# This function tracks and handles the conversation flow
@profile
def handle_conversation(user_id, user_message):
    # Get active session data for the user
    session_data = get_session(user_id)

    # Update dialogue count and check if we should start the quiz
    session_data['dialog_count'] += 1

    # If dialogue count reaches 12-20 for now put it to 4 the testing, start asking quiz questions
    if session_data['dialog_count'] >= 4 and not session_data['is_quiz_started']:
        session_data['is_quiz_started'] = True
        update_session(user_id, session_data)
        return {
            "message": "Thanks for the little chat! Let's move on to the quiz session.",
            "status": "A"
        }
    
    # If quiz hasn't started, continue with casual conversation (small talk)
    if session_data['dialog_count'] < 4:
        # Get chatbot's response
        chatbot_response = get_chatbot_response(user_message)

        # Store the conversation in the database (both user and chatbot messages)
        store_conversation(user_id, user_message, chatbot_response)
        update_session(user_id, session_data)

        return chatbot_response    

# Function to evaluate the main question answer
@profile
def evaluate_main_question(user_answer, correct_answer, threshold=0.8):
    user_embedding = embedding_model.encode(user_answer, convert_to_tensor=True)
    correct_embedding = embedding_model.encode(correct_answer, convert_to_tensor=True)
    similarity = util.cos_sim(user_embedding, correct_embedding).item()
    return similarity >= threshold, similarity  # Return boolean for correctness and similarity score

# Function to evaluate sub-question answers
@profile
def evaluate_sub_question(user_answer, sub_question, threshold=0.5):
    answer_embedding = embedding_model.encode(user_answer, convert_to_tensor=True)
    question_embedding = embedding_model.encode(sub_question, convert_to_tensor=True)
    relevance = util.cos_sim(answer_embedding, question_embedding).item()
    return relevance >= threshold, relevance  # Return boolean for relevance and similarity score

# Function to save answer to the database
def save_answer_to_db(user_id, question, answer, accuracy, question_type):
    db = get_db()
    db.collection('user_answers').add({
        'user_id': user_id,
        'question': question,
        'answer': answer,
        'accuracy': accuracy,
        'question_type': question_type,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Chatbot API!"})

# Route to handle quiz submissions and evaluate answers
@app.route('/post_quiz/<user_id>', methods=['POST'])
@profile
def post_quiz(user_id):
    # Get the user answers from the request
    data = request.get_json()
    result = []
    
    # Process main question answers
    for quiz in data.get('about_me', []):
        main_question = quiz['question']
        correct_answer = quiz['answer']
        user_answer = quiz['user_answer']
        
        # Evaluate the answer
        is_correct, similarity_score = evaluate_main_question(user_answer, correct_answer)
        
        # Save the result to the database
        save_answer_to_db(user_id, main_question, user_answer, similarity_score, 'main')
        
        result.append({
            'question': main_question,
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'accuracy': similarity_score,
            'is_correct': is_correct
        })
        
        # Process sub-question answers
        for sub_question, user_sub_answer in zip(quiz['sub_questions'], quiz['sub_questions_answer']):
            is_relevant, relevance_score = evaluate_sub_question(user_sub_answer, sub_question)
            
            # Save the result to the database
            save_answer_to_db(user_id, sub_question, user_sub_answer, relevance_score, 'sub')
            
            result.append({
                'sub_question': sub_question,
                'user_sub_answer': user_sub_answer,
                'relevance_score': relevance_score,
                'is_relevant': is_relevant
            })

    # Return the result sheet as JSON response
    return jsonify({"status": "success", "result": result})

# Function to store conversations
def store_conversation(user_id, user_message, chatbot_response):
    db = get_db()
    db.collection('user_conversations').add({
        'user_id': user_id,
        'user_message': user_message,
        'chatbot_response': chatbot_response,
        'timestamp': datetime.now().isoformat()
    })

# Function to get chatbot's response using DialoGPT
@profile
def get_chatbot_response(user_message):
    # Encode the user message
    new_user_input_ids = chatbot_tokenizer.encode(user_message + chatbot_tokenizer.eos_token, return_tensors='pt')

    # Generate a response from the chatbot model
    chat_history_ids = new_user_input_ids
    chatbot_output = chatbot_model.generate(
        chat_history_ids,
        max_length=1000,
        pad_token_id=chatbot_tokenizer.eos_token_id,
        temperature=0.7,
        top_k=50,
        top_p=0.95,
        do_sample=True,
        num_return_sequences=1
    )

    # Decode the chatbot response
    chatbot_response = chatbot_tokenizer.decode(chatbot_output[:, new_user_input_ids.shape[-1]:][0], skip_special_tokens=True)

    return chatbot_response

# Route to start the chat session
@app.route("/start_session/<string:user_id>", methods=["GET"])
@profile
def start_session(user_id):
    get_session(user_id)
    return jsonify({"message": "Hello, how are you today? Let's start chatting!"}), 200

# Route to handle the user's messages during the chat session
@app.route("/send_message/<string:user_id>", methods=["POST"])
@profile
def send_message(user_id):
    user_message = request.json.get("message")  # Get the user message from the request
    
    # Handle the conversation flow (start quiz after 12-20 dialogues)
    response = handle_conversation(user_id, user_message)
    
    # Return response to the user
    return jsonify({"response": response}), 200

# Route to get quiz questions for the user
@app.route("/get_quiz/<string:user_id>", methods=["GET"])
@profile
def get_quiz(user_id):
    quiz_data = get_quiz_questions(user_id)

    # Return only 1 main question and 2 random sub-questions for each category
    result = {
        "about_me": [],
        "life_events": [],
        "image_context": []
    }

    # Iterate through each category and select 1 main question + 2 sub-questions
    for category in quiz_data:
        for main_quiz in quiz_data[category]:
            main_question = main_quiz["question"]
            main_answer = main_quiz["answer"]
            sub_questions = random.sample(main_quiz["sub_questions"], 2)  # Pick 2 random sub-questions
            
            # Append the selected main question with its 2 sub-questions
            result[category].append({
                "question": main_question,
                "answer": main_answer,
                "sub_questions": sub_questions
            })

    return jsonify(result), 200

# Route to save user data to the database
@app.route("/save_user/<string:user_id>", methods=["POST"])
@profile
def save_user(user_id):
    """Save user data to the database."""
    try:
        # Get the user_data from the request payload
        data = request.json.get("user_data", {})
        about_me = data.get("about_me", {})
        life_events = data.get("life_events", [])
        images_with_context = data.get("images_with_context", [])

        db = get_db()

        # Save to users collection
        db.collection('users').document(user_id).set({
            'user_id': user_id,
            'full_name': about_me.get("full_name"),
            'birth_date': about_me.get("birth_date"),
            'hometown': about_me.get("hometown")
        })

        # Insert into user_preferences table
        hobbies = about_me.get("hobbies", [])
        favorite_things = about_me.get("favorite_things", {})
        db.collection('user_preferences').document(user_id).set({
            'user_id': user_id,
            'hobby': hobbies,
            'favorite_color': favorite_things.get("color"),
            'favorite_food': favorite_things.get("food"),
            'favorite_song': favorite_things.get("song"),
            'favorite_movie': favorite_things.get("movie")
        })

        # Insert into life_events and related people
        for event in life_events:
            event_doc = db.collection('life_events').add({
                'user_id': user_id,
                'event_title': event.get("event_title"),
                'event_date': event.get("date"),
                'description': event.get("description"),
                'emotions': event.get("emotions", [])
            })[1]  # Get the document reference
            event_id = event_doc.id
            for person in event.get("related_people", []):
                db.collection('life_event_people').add({
                    'event_id': event_id,
                    'person_name': person
                })

        # Insert into images_with_context
        for image in images_with_context:
            context = image.get("context", {})
            db.collection('images_with_context').add({
                'user_id': user_id,
                'image_base64': image.get("image_base64"),
                'context_who': context.get("who", []),
                'context_where': context.get("where"),
                'context_when': context.get("when"),
                'event_title': context.get("event_title"),
                'description': context.get("description")
            })

        return jsonify({"message": "User data saved successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
