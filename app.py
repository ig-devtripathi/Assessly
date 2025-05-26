from flask import Flask, request, jsonify, session, send_from_directory, render_template
import csv
import os
import re
import requests
from dotenv import load_dotenv
import logging
from datetime import datetime
from collections import defaultdict
import time

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.urandom(24)

# Logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('errors.log'),
        logging.StreamHandler()
    ]
)

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

user_states = {}
user_conversations = defaultdict(list)
STATE_TIMEOUT = 600  # 10 minutes

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

def clean_response(text):
    text = re.sub(r'\*{1,2}([^\*]+)\*{1,2}', r'\1', text)
    text = re.sub(r'^[-*] ', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{2,}', '\n', text)
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clear_stale_states():
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
        return "Sorry, AI connection issue. Try FAQs or say 'talk to someone'."

    for attempt in range(2):
        try:
            history = user_conversations[user_id][-5:]
            system_prompt = (
                "You are Assessly, a friendly and conversational AI assistant for an AI Assessment Platform for HR, assisting HR professionals and candidates. "
                "The platform enables HR to create custom tests (MCQs, coding, aptitude), offers a candidate test portal with autosave and resume features, "
                "and includes proctoring with camera monitoring, facial recognition, and behavior tracking. "
                "Provide concise, accurate, and professional answers in plain text, avoiding Markdown or formatting. "
                "If the query is unrelated, gently guide the user back to HR topics. "
                "History: " + "; ".join([f"User: {msg['user']}, Bot: {msg['bot']}" for msg in history])
            )

            response = requests.post(
                'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent',
                headers={'Content-Type': 'application/json'},
                params={'key': GEMINI_API_KEY},
                json={
                    'contents': [{'parts': [{'text': system_prompt}, {'text': user_message}]}],
                    'generationConfig': {
                        'maxOutputTokens': 150,
                        'temperature': 0.7
                    }
                },
                timeout=15
            )
            response.raise_for_status()
            result = response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            cleaned = clean_response(result)
            user_conversations[user_id].append({'user': user_message, 'bot': cleaned})
            return cleaned
        except Exception as e:
            logging.error(f"AI Error (attempt {attempt+1}): {str(e)}")
            time.sleep(2 if attempt == 0 else 0)
            continue
    return "AI error. Try again or ask an FAQ."

@app.route('/')
def index():
    session['user_id'] = session.get('user_id', os.urandom(16).hex())
    user_states.pop(session['user_id'], None)
    return app.send_static_file('index.html')

@app.route('/contact')
def contact():
    session['user_id'] = session.get('user_id', os.urandom(16).hex())
    user_states.pop(session['user_id'], None)
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
    clear_stale_states()

    state = user_states.get(user_id, {'step': None, 'last_updated': time.time()})
    state['last_updated'] = time.time()
    user_states[user_id] = state

    # Contact steps
    if state['step']:
        if state['step'] == 'name':
            if len(user_message) < 2:
                return jsonify({'response': 'Please provide a valid full name.'})
            state['name'] = user_message
            state['step'] = 'email'
            return jsonify({'response': 'Thanks! Please provide your email address.'})
        elif state['step'] == 'email':
            if not re.match(r"[^@]+@[^@]+\.[^@]+", user_message):
                return jsonify({'response': 'Please enter a valid email address.'})
            state['email'] = user_message
            state['step'] = 'message'
            return jsonify({'response': 'Great! What’s your message or reason for contact?'})
        elif state['step'] == 'message':
            if len(user_message) < 5:
                return jsonify({'response': 'Please provide a detailed message.'})
            try:
                save_contact_details(state['name'], state['email'], user_message)
                del user_states[user_id]
                return jsonify({'response': 'Thank you! We’ve saved your details and will get back to you soon.'})
            except:
                return jsonify({'response': 'Error saving your details. Please try again.'})

    # Human support
    if any(phrase in user_message.lower() for phrase in ["talk to someone", "contact", "real person", "agent", "support team"]):
        user_states[user_id] = {'step': 'name', 'last_updated': time.time()}
        return jsonify({'response': 'I’ll connect you with our support team! Please provide your full name.'})

    # FAQ
    for q in faq_responses:
        if q in user_message.lower():
            return jsonify({'response': faq_responses[q]})

    # Detect intent
    matched_intent = None
    for intent, patterns in intents.items():
        for pattern in patterns:
            if re.search(pattern, user_message, re.IGNORECASE):
                matched_intent = intent
                break
        if matched_intent:
            break

    ai_reply = query_gemini_api(user_message, user_id, matched_intent)
    return jsonify({'response': ai_reply})

if __name__ == '__main__':
    app.run(debug=True)
