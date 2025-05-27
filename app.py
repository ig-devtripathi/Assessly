from flask import Flask, request, jsonify, render_template
import os
from dotenv import load_dotenv
import google.generativeai as genai
import re

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Load Gemini API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Simulated user data storage (reset for each session)
user_data = {}

# Enhanced FAQ responses
faq_responses = {
    "what are your working hours": "Our working hours are Monday to Friday, 9 AM to 8 PM IST.",
    "where is your office located": "Our office is located at Bagdola, Sector 8 Dwarka, Palam, New Delhi.",
    "how does test creation work": "With Assessly, HR professionals can create custom tests using our AI-powered platform. You can define question types, set difficulty levels, and generate tests tailored to your needs.",
    "what is hr": "HR stands for Human Resources. It refers to the department in an organization responsible for managing employee-related processes like hiring, training, payroll, and ensuring a positive workplace environment.",
    "is ai working": "Yes, I'm working perfectly! I'm Assessly, your AI assistant, here to help with your queries. What would you like to know?",
    "how to contact support": "You can reach our support team via email at info@uptoskills.com or call us at +91-7417269505 during working hours.",
    "what is assessly": "Assessly is an AI-powered HR assessment platform that helps organizations streamline their hiring process by creating custom tests, evaluating candidates, and providing insightful analytics.",
    "how to create an account": "To create an account, visit our website at uptoskills.com, click on 'Sign Up,' and fill in your details. You'll receive a confirmation email to activate your account.",
    "what types of tests are available": "We offer a variety of tests including aptitude tests, technical skills assessments, personality tests, and role-specific evaluations tailored for HR needs.",
    "how to schedule a test": "To schedule a test, log in to your Assessly account, go to the 'Tests' section, select the test you want to schedule, and choose a date and time. You can then invite candidates via email."
}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/chat', methods=['POST'])
def chat():
    global user_data
    data = request.get_json()
    user_message = data.get('message', '').strip()
    user_message_lower = user_message.lower()

    if not user_message:
        return jsonify({"response": "Please enter a message.", "type": "error"})

    # FAQs
    for question, answer in faq_responses.items():
        if question in user_message_lower:
            user_data = {}
            return jsonify({"response": answer, "type": "bot"})

    # HR contact flow
    if "talk to someone" in user_message_lower:
        user_data = {'name': None, 'email': None, 'phone': None}
        return jsonify({"response": "Sure, please provide your name.", "type": "bot"})

    if user_data and user_data.get('name') is None:
        user_data['name'] = user_message
        return jsonify({"response": "Thanks, now please provide your email.", "type": "bot"})

    if user_data and user_data.get('email') is None:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", user_message):
            return jsonify({"response": "Please provide a valid email address.", "type": "error"})
        user_data['email'] = user_message
        return jsonify({"response": "Great, now please provide your phone number.", "type": "bot"})

    if user_data and user_data.get('phone') is None:
        if not re.match(r"\+?\d{10,15}", user_message):
            return jsonify({"response": "Please provide a valid phone number.", "type": "error"})
        user_data['phone'] = user_message
        response = f"Thank you, {user_data['name']}! We've noted your details:\nEmail: {user_data['email']}\nPhone: {user_data['phone']}\nOur team will reach out to you soon!"
        user_data = {}
        return jsonify({"response": response, "type": "bot"})

    # Friendly answers to general HR-related introductions
    general_queries = ["what can you do", "who are you", "what are you", "how can you help"]
    if any(q in user_message_lower for q in general_queries):
        return jsonify({
            "response": "I'm Assessly 👩‍💼 — your AI-powered HR assistant! I can help with interview tips, test creation, candidate assessments, HR terms, and more. Just ask me anything in the HR space!",
            "type": "bot"
        })

    # Soft filter for unrelated topics
    off_topic = ['joke', 'weather', 'cricket', 'movie', 'game', 'bitcoin']
    if any(word in user_message_lower for word in off_topic):
        return jsonify({
            "response": "I'm built to assist with hiring, HR, assessments, and workplace topics 😊. Ask me anything related to your career or recruitment!",
            "type": "bot"
        })

    # Gemini fallback for other HR-like queries (e.g., strengths, interview help)
    try:
        prompt = (
            "You are Assessly — a friendly, conversational, and intelligent AI assistant trained to help with everything HR-related. "
            "You can help users understand how to create or take assessments, prepare for interviews, explain HR processes, share company info, and more. "
            "You’re warm and helpful, capable of answering questions like 'What are your strengths?', 'Tell me about yourself', or 'What can you do?'. "
            "If someone asks off-topic questions (like about weather, jokes, or cricket), gently guide them back to HR or career topics in a kind way.\n\n"
            f"User: {user_message}\n\nKeep your tone friendly and conversational. Keep the response under 150 words."
        )

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=150
            )
        )
        if response and response.text:
            cleaned_response = re.sub(r'[*#]+', '', response.text)
            cleaned_response = re.sub(r'(\n\s*)+', '\n', cleaned_response)
            cleaned_response = re.sub(r'(\d+\.\s|[IVX]+\.\s)', '', cleaned_response)
            cleaned_response = cleaned_response.strip()
            return jsonify({"response": cleaned_response, "type": "bot"})
        else:
            return jsonify({"response": "Sorry, I couldn't generate a response. Please try again or ask something else.", "type": "error"})

    except Exception as e:
        return jsonify({"response": f"Sorry, an error occurred: {str(e)}. Please try again later or ask a common question like 'What are your working hours?'", "type": "error"})

if __name__ == '__main__':
    app.run(debug=True)
