import json
import os
from openai import OpenAI
from prompts import assistant_instructions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


OPENAI_API_KEY = os.environ['OPENAI_API_KEY']


# Init OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)

# Create or load assistant
def create_assistant(client):
    assistant_file_path = 'assistant.json'

    # If there is an assistant.json file already, then load that assistant
    if os.path.exists(assistant_file_path):
        with open(assistant_file_path, 'r') as file:
            assistant_data = json.load(file)
            assistant_id = assistant_data['assistant_id']
            print("Loaded existing assistant ID.")
    else:
        # If no assistant.json is present, create a new assistant without uploading a knowledge document
        assistant = client.beta.assistants.create(
            # Getting assistant prompt from "prompts.py" file, edit on left panel if you want to change the prompt
                    instructions=assistant_instructions,            
                    model="gpt-3.5-turbo-16k",
                    tools=[
                        {
                            "type": "function",
                            "function": {
                                "name": "search_flights",
                                "description": "Search available flights.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "origin": {"type": "string", "description": "The user's origin."},
                                        "destination": {"type": "string", "description": "The user's destination."},
                                        "departure_date": {"type": "string", "description": "The user's planned departure date."},
                                        "return_date": {"type": "string", "description": "The user's planned return date."},
                                        "no_of_travellers": {"type": "number", "description": "How many people are travelling"}
                                    },
                                    "required": ["origin", "destination", "departure_date", "no_of_travellers"]
                                },
                            },
                        }
                    ],
        )

        # Create a new assistant.json file to load on future runs
        with open(assistant_file_path, 'w') as file:
            json.dump({'assistant_id': assistant.id}, file)
            print("Created a new assistant and saved the ID.")

        assistant_id = assistant.id

    return assistant_id
