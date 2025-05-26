from flask import Flask, request, jsonify, session, send_from_directory, render_template
import csv
import os
import re
import requests
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import time

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.urandom(24)

logging.basicConfig(filename='errors.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

user_states = {}
user_conversations = defaultdict(list)
STATE_TIMEOUT = 600  # 10 minutes in seconds

faq_responses = {
    "how can i contact you": "You can reach us right here in this chat, or say 'I want to talk to someone' to share your details for a follow-up!",
    "what are your working hours": "We're available Monday to Friday, 9 AM to 5 PM IST. Drop a message anytime, and I'll respond promptly!",
    "where is your office located": "Our office is at 123 Tech Park, Bengaluru, Karnataka, India. Want to visit? Let me know!",
    "how does test creation work": "HRs can craft custom tests (MCQs, coding, aptitude) by selecting job roles, skills, and difficulty levels. Our AI-powered analytics provide detailed evaluation insights.",
    "what is proctoring": "Proctoring ensures test integrity with live camera monitoring, facial recognition, and behavior tracking, flagging any suspicious activity.",
    "how do i access the test portal": "Candidates get a unique HR-provided link to access the test portal, featuring autosave, resume, and support for various question types.",
    "who are you": "I'm Assessly, your AI-powered HR Assessment Assistant, here to help with creating tests, understanding proctoring, navigating the candidate portal, and more!"
}

intents = {
    "test_creation": [r"test\s*creation", r"create\s*test", r"make\s*test", r"generate\s*test"],
    "proctoring": [r"proctoring", r"monitoring", r"camera", r"facial\s*recognition"],
    "test_portal": [r"test\s*portal", r"candidate\s*portal", r"access\s*test", r"take\s*test"],
    "human_support": [r"human", r"agent", r"real\s*person", r"support\s*team", r"talk\s*to\s*someone"],
    "system_info": [r"what\s*(is|are)\s*(ur|your|the)\s*(system|bot|platform)(\s*(for|do(es)?))?", r"platform\s*details", r"about\s*(system|platform)"]
}

# General keywords for queries like "what can you do"
general_keywords = [
    "what can you do", "tell me about yourself", "who are you", "what are you", "introduce yourself",
    "what do you do", "how can you help", "what is your purpose", "what can you help with"
]

def clean_response(text):
    """Remove Markdown and format for plain text."""
    text = re.sub(r'\*{1,2}([^\*]+)\*{1,2}', r'\1', text)  # Remove **bold** and *italic*
    text = re.sub(r'^- ', '', text, flags=re.MULTILINE)    # Remove bullet points
    text = re.sub(r'^\* ', '', text, flags=re.MULTILINE)   # Remove * bullets
    text = re.sub(r'\n{2,}', '\n', text)                   # Normalize newlines
    text = text.replace('\n', ' ')                         # Convert newlines to spaces
    text = re.sub(r'\s+', ' ', text).strip()               # Clean extra spaces
    return text

def clear_stale_states():
    """Remove user states older than STATE_TIMEOUT."""
    current_time = time.time()
    for user_id in list(user_states.keys()):
        if current_time - user_states[user_id].get('last_updated', 0) > STATE_TIMEOUT:
            logging.info(f"Clearing stale state for user {user_id}")
            del user_states[user_id]

def save_contact_details(name, email, message):
    try:
        file_exists = os.path.isfile('contacts.csv')
        with open('contacts.csv', 'a', newline='') as csvfile:
            fieldnames = ['Name', 'Email', 'Message', 'Timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                'Name': name,
                'Email': email,
                'Message': message,
                'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
    except Exception as e:
        logging.error(f"Error saving contact details: {str(e)}")
        raise

def query_gemini_api(user_message, user_id, intent=None):
    if not GEMINI_API_KEY or not GEMINI_API_KEY.startswith('AIzaSy'):
        logging.error("Invalid or missing Gemini API key")
        return clean_response("Sorry, I'm having trouble connecting. Try FAQs like 'What is proctoring?' or say 'I want to talk to someone'.")
    
    for attempt in range(2):  # Try once, retry once
        try:
            history = user_conversations[user_id][-5:]
            system_prompt = (
                "You are Assessly, a friendly and conversational AI assistant for an AI Assessment Platform for HR, assisting HR professionals and candidates. "
                "The platform enables HR to create custom tests (MCQs, coding, aptitude), offers a candidate test portal with autosave and resume features, "
                "and includes proctoring with camera monitoring, facial recognition, and behavior tracking. "
                "Provide concise, accurate, and professional answers in plain text, avoiding Markdown, bullet points, or special formatting. "
                "Keep responses under 150 words. While your primary focus is HR-related queries, you can also answer common conversational questions (like telling a joke or general knowledge) in a friendly way. "
                "After answering unrelated queries, gently guide the user back to HR topics by suggesting they ask about test creation, proctoring, or the test portal. "
                "Example: If asked 'Tell me a joke', respond with a joke and then say, 'Speaking of fun, want to know how to make hiring fun with our test creation tools?' "
                "Use conversation history for context: " + "; ".join([f"User: {msg['user']}, Bot: {msg['bot']}" for msg in history]) + "."
            )
            response = requests.post(
                'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent',
                headers={'Content-Type': 'application/json'},
                params={'key': GEMINI_API_KEY},
                json={
                    'contents': [{
                        'parts': [
                            {'text': system_prompt},
                            {'text': user_message}
                        ]
                    }],
                    'generationConfig': {
                        'maxOutputTokens': 150,
                        'temperature': 0.7
                    }
                },
                timeout=15
            )
            response.raise_for_status()
            result = response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            cleaned_result = clean_response(result)
            logging.info(f"Raw response: {result} | Cleaned: {cleaned_result}")
            user_conversations[user_id].append({'user': user_message, 'bot': cleaned_result})
            return cleaned_result
        except requests.exceptions.HTTPError as e:
            logging.error(f"Gemini API HTTP error (attempt {attempt + 1}): {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 401:
                return clean_response("Invalid API key. Please contact support or try FAQ questions.")
            elif e.response.status_code == 429:
                if attempt == 0:
                    time.sleep(2)  # Wait before retry
                    continue
                return clean_response("I'm getting too many requests. Please try again in a moment or ask an FAQ question.")
            elif e.response.status_code >= 500:
                return clean_response("AI service is temporarily down. Try an FAQ like 'What is proctoring?' or say 'I want to talk to someone'.")
            return clean_response("Sorry, I'm having trouble connecting. Try an FAQ or say 'I want to talk to someone'.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Gemini API network error (attempt {attempt + 1}): {str(e)}")
            if attempt == 0:
                time.sleep(2)
                continue
            return clean_response("Network issue connecting to my AI module. Please try FAQ questions.")
        except Exception as e:
            logging.error(f"Unexpected Gemini API error (attempt {attempt + 1}): {str(e)}")
            return clean_response("Something went wrong with my AI module. Try an FAQ or say 'I want to talk to someone'.")

@app.route('/')
def index():
    session['user_id'] = session.get('user_id', os.urandom(16).hex())
    if session['user_id'] in user_states:
        logging.info(f"Clearing state for new session: {session['user_id']}")
        del user_states[session['user_id']]  # Reset state for new session
    return app.send_static_file('index.html')

@app.route('/contact')
def contact():
    session['user_id'] = session.get('user_id', os.urandom(16).hex())
    if session['user_id'] in user_states:
        logging.info(f"Clearing state for new session: {session['user_id']}")
        del user_states[session['user_id']]  # Reset state for new session
    return render_template('contact.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    user_id = session.get('user_id', request.remote_addr)

    if not user_message:
        return jsonify({'response': 'Please enter a message.'})

    logging.info(f"User {user_id}: {user_message}")

    # Clear stale states
    clear_stale_states()

    # Initialize or update user state
    if user_id not in user_states:
        user_states[user_id] = {'step': None, 'last_updated': time.time()}
    else:
        user_states[user_id]['last_updated'] = time.time()

    # Handle contact form steps
    if user_states[user_id].get('step'):
        state = user_states[user_id]
        if state['step'] == 'name':
            if len(user_message) < 2:
                return jsonify({'response': 'Please provide a valid full name.'})
            state['name'] = user_message
            state['step'] = 'email'
            user_states[user_id] = state
            response = 'Thanks! Please provide your email address.'
            user_conversations[user_id].append({'user': user_message, 'bot': response})
            return jsonify({'response': response})
        elif state['step'] == 'email':
            if not re.match(r"[^@]+@[^@]+\.[^@]+", user_message):
                return jsonify({'response': 'Please enter a valid email address.'})
            state['email'] = user_message
            state['step'] = 'message'
            user_states[user_id] = state
            response = 'Great! What’s your message or reason for contact?'
            user_conversations[user_id].append({'user': user_message, 'bot': response})
            return jsonify({'response': response})
        elif state['step'] == 'message':
            if len(user_message) < 5:
                return jsonify({'response': 'Please provide a detailed message.'})
            try:
                save_contact_details(state['name'], state['email'], user_message)
                del user_states[user_id]
                response = 'Thank you! We’ve saved your details and will get back to you soon.'
                user_conversations[user_id].append({'user': user_message, 'bot': response})
                return jsonify({'response': response})
            except Exception as e:
                logging.error(f"Contact save error: {str(e)}")
                return jsonify({'response': 'Error saving your details. Please try again.'})

    # Handle human support request
    if any(phrase in user_message.lower() for phrase in ["talk to someone", "contact someone", "human", "agent", "real person", "support team"]):
        user_states[user_id] = {'step': 'name', 'last_updated': time.time()}
        response = 'I’ll connect you with our support team! Please provide your full name.'
        user_conversations[user_id].append({'user': user_message, 'bot': response})
        return jsonify({'response': response})

    # Handle FAQ responses
    for question, answer in faq_responses.items():
        if question in user_message.lower():
            cleaned_answer = clean_response(answer)
            user_conversations[user_id].append({'user': user_message, 'bot': cleaned_answer})
            return jsonify({'response': cleaned_answer})

    # Check for general queries like "what can you do"
    user_message_lower = user_message.lower()
    is_general_query = any(keyword in user_message_lower for keyword in general_keywords)
    if is_general_query:
        response = "Hey, I'm Assessly, your HR assistant! I'm here to help with HR-related tasks like creating tests, scheduling assessments, or answering questions about hiring and recruitment. I can also guide you on how to contact support or create an account. What do you want to talk about?"
        user_conversations[user_id].append({'user': user_message, 'bot': response})
        return jsonify({'response': response})

    # Handle all other queries using Gemini API (no strict HR filtering)
    detected_intent = None
    for intent, patterns in intents.items():
        if any(re.search(pattern, user_message_lower) for pattern in patterns):
            detected_intent = intent
            break

    response = query_gemini_api(user_message, user_id, detected_intent)
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)