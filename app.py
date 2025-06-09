# app.py
from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
import os
from dotenv import load_dotenv
import time
import uuid

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')

def get_openrouter_response(user_message):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": os.getenv("YOUR_SITE_URL", ""),
            "X-Title": os.getenv("YOUR_SITE_NAME", ""),
        },
        model="deepseek/deepseek-r1-0528:free",
        messages=[{"role": "user", "content": user_message}]
    )
    return completion.choices[0].message.content

@app.route('/')
def home():
    # Initialize or get session ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    try:
        bot_response = get_openrouter_response(user_message)
        return jsonify({'response': bot_response})
    except Exception as e:
        return jsonify({'response': f"Error: {str(e)}"}), 500

@app.route('/new_chat', methods=['POST'])
def new_chat():
    # Generate new session ID
    session['session_id'] = str(uuid.uuid4())
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
