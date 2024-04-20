import os
import time
from flask import Flask, request, jsonify
import openai
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)

# Set up the OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Create an OpenAI client instance
client = openai.Client(api_key=openai.api_key)

# Assume the create_assistant function is defined correctly in the functions.py file
from functions import create_assistant

# Create or load assistant using the 'client' instance
assistant_id = create_assistant(client)  # Pass 'client' if it's needed in the function

# Start conversation thread
@app.route('/start', methods=['GET'])
def start_conversation():
    print("Starting a new conversation...")
    thread = client.Thread.create()
    print(f"New thread created with ID: {thread.id}")
    return jsonify({"thread_id": thread.id})

# Generate response
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    thread_id = data.get('thread_id')
    user_input = data.get('message', '')

    if not thread_id:
        return jsonify({"error": "Missing thread_id"}), 400

    print(f"Received message: {user_input} for thread ID: {thread_id}")

    # Add the user's message to the thread and run the Assistant
    message = client.Message.create(thread_id=thread_id, role="user", content=user_input)
    run = client.Run.create(thread_id=thread_id, assistant_id=assistant_id)

    # Check if the Run requires action (function call)
    while True:
        run_status = client.Run.retrieve(thread_id=thread_id, run_id=run.id)
        if run_status.status == 'completed':
            break
        elif run_status.status == 'requires_action':
            handle_action(run_status, thread_id, run.id)
        time.sleep(1)  # Avoid tight loop

    # Retrieve and return the latest message from the assistant
    messages = client.Message.list(thread_id=thread_id)
    response = messages.data[-1].content if messages.data else "No response from assistant."
    return jsonify({"response": response})

def handle_action(run_status, thread_id, run_id):
    # Example action handler for flight search
    for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
        if tool_call.function.name == "search_flights":
            arguments = json.loads(tool_call.function.arguments)
            available_flights = search_flights(
                origin_name=arguments["origin"],
                destination_name=arguments["destination"],
                departure_date=arguments["departure_date"],
                return_date=arguments.get("return_date"),  # Handle optional return date
                adults=arguments.get("no_of_travellers", 1)  # Default to 1 if not specified
            )
            client.Run.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=[{
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(available_flights)
                }]
            )
            print("Submitted flight search results back to the Assistant...")
        else:
            raise ValueError(f"Unknown Function: {tool_call.function.name}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
