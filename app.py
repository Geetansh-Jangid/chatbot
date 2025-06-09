# app.py
from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# Make sure to set a strong, secret key in your .env file
app.secret_key = os.getenv('SECRET_KEY', 'a-very-secret-key-that-you-should-change')

def get_openrouter_response(message_history):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    
    # You can add a system prompt to guide the model's behavior
    system_prompt = {"role": "system", "content": "You are DeepSeek AI, a helpful and concise assistant."}

    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": os.getenv("YOUR_SITE_URL", "http://localhost:5000"),
            "X-Title": os.getenv("YOUR_SITE_NAME", "DeepSeek AI Chat"),
        },
        model="deepseek/deepseek-coder", # Changed to a free and capable model
        messages=[system_prompt] + message_history
    )
    return completion.choices[0].message.content

@app.route('/')
def home():
    # Initialize chat history in session if it doesn't exist
    if 'chat_history' not in session:
        session['chat_history'] = []
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'response': 'Error: No message received.'}), 400

    # Ensure chat history exists
    if 'chat_history' not in session:
        session['chat_history'] = []

    # Add user message to history
    session['chat_history'].append({"role": "user", "content": user_message})
    # Make sure session is saved
    session.modified = True

    try:
        # Get response from the model using the entire conversation history
        bot_response = get_openrouter_response(session['chat_history'])
        
        # Add bot response to history
        session['chat_history'].append({"role": "assistant", "content": bot_response})
        
        # Limit history to the last 20 messages (10 pairs) to prevent it from growing too large
        session['chat_history'] = session['chat_history'][-20:]
        session.modified = True
        
        return jsonify({'response': bot_response})
    except Exception as e:
        # If an error occurs, remove the last user message to allow for a retry
        if session['chat_history']:
            session['chat_history'].pop()
            session.modified = True
        app.logger.error(f"Error communicating with OpenAI API: {e}")
        return jsonify({'response': f"An error occurred: {str(e)}"}), 500

@app.route('/new_chat', methods=['POST'])
def new_chat():
    # Clear the chat history for the current session
    session.pop('chat_history', None)
    return jsonify({'status': 'success', 'message': 'New chat started.'})

if __name__ == '__main__':
    app.run(debug=True)
