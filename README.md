# Assessly - AI Assessment Platform Chatbot

Assessly is a Flask-based chatbot for an AI Assessment Platform, helping HR create custom tests, manage candidate portals, and enable proctoring. Powered by Google Gemini API, it features a premium glassmorphism UI, session management, and contact collection.

## Features
- **FAQ Responses**: Instant answers for proctoring, test creation, and more.
- **Gemini AI**: Smart, context-aware replies for dynamic queries.
- **Contact Collection**: Saves user details to `contacts.csv`.
- **Premium UI**: Glassmorphism design, dark/light mode, responsive layout.

## Live Demo
[Assessly Live](https://assessly.onrender.com/)

## Setup
1. Clone: `git clone https://github.com/your-username/assessly.git`
2. Install: `pip install -r requirements.txt`
3. Add `.env` with `GEMINI_API_KEY`
4. Run: `python app.py`

## Deployment
Deployed on Render via GitHub. Update `requirements.txt` and push to redeploy.

## Tech Stack
- Flask, Gemini API, Tailwind CSS, Animate.css
- Render for hosting