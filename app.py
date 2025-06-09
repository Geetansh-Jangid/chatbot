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

# MODIFICATION 1: Function now accepts the entire message history
def get_openrouter_response(messages):
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
        # Pass the entire conversation history to the model
        messages=messages 
    )
    return completion.choices[0].message.content

@app.route('/')
def home():
    # Initialize session and chat history if they don't exist
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session['chat_history'] = []
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    
    # MODIFICATION 2: Manage conversation history in the session
    # Retrieve history, or start a new list if it's not there
    chat_history = session.get('chat_history', [])
    
    # Add the new user message to the history
    chat_history.append({"role": "user", "content": user_message})
    
    try:
        # Get the bot's response using the full history
        bot_response = get_openrouter_response(chat_history)
        
        # Add the bot's response to the history. The API uses 'assistant' role.
        chat_history.append({"role": "assistant", "content": bot_response})
        
        # Save the updated history back to the session
        session['chat_history'] = chat_history
        
        return jsonify({'response': bot_response})
    except Exception as e:
        # If an error occurs, remove the last user message to allow a retry
        if chat_history:
            chat_history.pop()
        session['chat_history'] = chat_history
        return jsonify({'response': f"Error: {str(e)}"}), 500

@app.route('/new_chat', methods=['POST'])
def new_chat():
    # MODIFICATION 3: Clear the chat history for a new conversation
    session['chat_history'] = []
    # Optionally, you can also generate a new session ID, though clearing history is the key part
    session['session_id'] = str(uuid.uuid4()) 
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
