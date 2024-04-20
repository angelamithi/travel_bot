import openai
import time
import json
import os
import streamlit as st
from geolocation import get_destination_coordinates, get_origin_coordinates
from auth import get_access_token
from flights import search_flights
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai.api_key)
model = "gpt-3.5-turbo-16k"

class AssistantManager:
    thread_id = None
    assistant_id = None

    def __init__(self, model: str = model):
        self.client = openai.OpenAI()
        self.model = model
        self.assistant = None
        self.thread = None
        self.run = None
        self.summary = None

        # Retrieve existing assistant and thread if IDs are stored in session state
        if st.session_state.assistant_id:
            self.assistant = self.client.beta.assistants.retrieve(
                assistant_id=st.session_state.assistant_id
            )
        if st.session_state.thread_id:
            self.thread = self.client.beta.threads.retrieve(
                thread_id=st.session_state.thread_id
            )

    def create_assistant(self, name, instructions, tools):
        if not self.assistant:
            assistant_obj = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                tools=tools,
                model=self.model
            )
            AssistantManager.assistant_id = assistant_obj.id
            self.assistant = assistant_obj  # This is now our new assistant
            print(f"Assistant ID:::: {self.assistant.id}")

    def create_thread(self):
        if not self.thread:
            thread_obj = self.client.beta.threads.create()
            self.thread = thread_obj  # This sets the local thread instance
            st.session_state.thread_id = thread_obj.id  # Save the thread ID in session state
            print(f"Thread ID:::: {self.thread.id}")

    def add_message_to_thread(self, role, content):
        if self.thread:
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role=role,
                content=content
            )

    def run_assistant(self, instructions):
        if self.assistant and self.thread:
            self.run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                instructions=instructions
            )

    def process_message(self):
        if self.thread:
            messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
            summary = []
            last_message = messages.data[0]
            role = last_message.role
            response = last_message.content[0].text.value
            summary.append(response)
            self.summary = "\n".join(summary)
            print(f"SUMMARY-----> {role.capitalize()}: ==> {response}")

    def wait_for_completion(self):
        if self.thread and self.run:
            while True:
                time.sleep(5)
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=self.run.id
                )
                print(f"RUN STATUS::{run_status.model_dump_json(indent=4)}")
                if run_status.status == "completed":
                    self.process_message()
                    break
                elif run_status.status == "requires_action":
                    print("FUNCTION CALLING NOW....")
                    self.call_required_functions(required_actions=run_status.required_action.submit_tool_outputs.model_dump())

    def call_required_functions(self, required_actions):
        if not self.run:
            return
        tool_outputs = []
        for action in required_actions["tool_calls"]:
            func_name = action["function"]["name"]
            arguments = json.loads(action["function"]["arguments"])
            if func_name == "search_flights":
                # Call the search_flights function with captured inputs
                available_flights = search_flights(
                    origin_name=arguments["origin"],
                    destination_name=arguments["destination"],
                    departure_date=arguments["departure_date"],
                    return_date=arguments.get("return_date"),  # Handle optional return date
                    adults=arguments.get("no_of_travellers", 1)  # Default to 1 if not specified
                )
                tool_outputs.append({
                    "tool_call_id": action["id"],
                    "output": json.dumps(available_flights),
                })
            else:
                raise ValueError(f"Unknown Function: {func_name}")
        print("Submitting outputs back to the Assistant...")
        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread.id,
            run_id=self.run.id,
            tool_outputs=tool_outputs,
        )

    def get_summary(self):
        return self.summary

    def run_steps(self):
        if not self.thread:
            print("No thread available")
            return []
    
        run_steps = self.client.beta.threads.runs.steps.list(
            thread_id=self.thread.id,
            run_id=self.run.id
        )
        print(f"Run-Steps::: {run_steps}")
        return run_steps.data

def main():
    st.title("Tara the Travel Mate")

    if 'assistant_id' not in st.session_state or 'thread_id' not in st.session_state:
        st.session_state.assistant_id = None
        st.session_state.thread_id = None

    with st.form(key="user_input_form"):
        origin = st.text_input("Origin")
        destination = st.text_input("Destination")
        departure_date = st.date_input("Departure Date")
        return_date = st.date_input("Return Date (Optional)", value=None)
        no_of_travellers = st.number_input("Number of Travelers", min_value=1, value=1)

        submit_button = st.form_submit_button(label="Start Planning with Tara")

        if submit_button:
            manager = AssistantManager()
            if not st.session_state.assistant_id:
                manager.create_assistant(
                    name="Tara the Travel Mate",
                    instructions="You are Tara, you are an experienced and an enthusiastic travel companion. You can assist users to search for available flights and book the flights on their behalf. You are always excited about exploring new destinations and experiences. You encourage travelers to step out of their comfort zones. You are friendly and approachable: You have a warm and welcoming tone, making users feel like they're chatting with a well-traveled friend. You have extensive travel experience, thus offering insightful advice and recommendations based on real-world experiences. You understand the ups and downs of travel and is there to offer support, whether it's finding the best local spots or helping out in emergencies. You are also passionate about sustainable travel and promotes eco-friendly options. You use casual language that's easy to understand, making users feel at ease. Your messages convey excitement about travel and a positive outlook on exploring new places. You show understanding and empathy towards users' concerns and preferences, offering personalized advice. You motivate users to try new experiences and reassures them when they're uncertain",
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
                st.session_state.assistant_id = manager.assistant.id
            
            if not st.session_state.thread_id:
                manager.create_thread()
                st.session_state.thread_id = manager.thread.id

            manager.add_message_to_thread(
                role="user",
                content=f"Looking to book a flight from {origin} to {destination} on {departure_date}, returning on {return_date}. Travelers: {no_of_travellers}"
            )
            manager.run_assistant(instructions="Book a flight")
            manager.wait_for_completion()
            recommendations = manager.get_summary()
            st.write(recommendations)
            st.text("Run Steps:")
            st.code(manager.run_steps(), line_numbers=True)

if __name__ == "__main__":
    main()