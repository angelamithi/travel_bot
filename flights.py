from auth import get_access_token
from geolocation import get_origin_coordinates, get_destination_coordinates
import requests

def get_nearest_airport(place_name):
    latitude, longitude = get_origin_coordinates(place_name)
    if latitude is None or longitude is None:
        print("Failed to get coordinates")
        return None

    access_token = get_access_token()
    if not access_token:
        print("Failed to retrieve access token")
        return None

    url = "https://test.api.amadeus.com/v1/reference-data/locations/airports"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"latitude": latitude, "longitude": longitude}
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            airports = response.json()['data']
            if airports:
                return airports[0]['iataCode']  # Return the IATA code of the nearest airport
            return None
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching nearest airport: {e}")
        return None

def search_flights(origin, destination, departure_date, return_date=None, adults=1):
    # Get the nearest airport IATA code for both origin and destination
    origin_airport_iata = get_nearest_airport(origin)
    if not origin_airport_iata:
        print("Could not find a nearest airport for the origin.")
        return None

    destination_airport_iata = get_nearest_airport(destination)
    if not destination_airport_iata:
        print("Could not find a nearest airport for the destination.")
        return None

    access_token = get_access_token()
    if not access_token:
        print("Failed to retrieve access token")
        return None

    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "originLocationCode": origin_airport_iata,
        "destinationLocationCode": destination_airport_iata,
        "departureDate": departure_date,
        "adults": adults  # Number of adults traveling
    }

    # Add return date to the parameters if it exists
    if return_date:
        params['returnDate'] = return_date

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            flights = response.json()['data']
            return flights
        else:
            return None
    except requests.exceptions.RequestException as e:
        print("Error occurred during API request:", e)
        return None
