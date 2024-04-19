import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_access_token():
    # Retrieve client ID and secret from environment variables
    client_id = os.getenv("AMADEUS_API_KEY")
    client_secret = os.getenv("AMADEUS_SECRET_KEY")

    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        return None

# Example usage
access_token = get_access_token()
if access_token:
    print("Access Token:", access_token)
else:
    print("Failed to get access token")
