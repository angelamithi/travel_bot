import requests
from functools import lru_cache
from urllib.parse import urlencode
from auth import get_access_token
import logging
import json
# Setup basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@lru_cache(maxsize=512)
def fetch_iata_code(place_name):
    access_token = get_access_token()
    if not access_token:
        logging.error("Failed to retrieve access token")
        return None

    base_url = "https://test.api.amadeus.com/v1/reference-data/locations"
    headers = {"Authorization": f"Bearer {access_token}"}
    subtypes = ['CITY', 'AIRPORT']
    for subtype in subtypes:
        params = {"subType": subtype, "keyword": place_name}
        url = f"{base_url}?{urlencode(params)}"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json().get('data', [])
                if data:
                    iata_code = data[0].get('iataCode')
                    if iata_code:
                        logging.info(f"Successfully retrieved IATA code: {iata_code} for {place_name} as a {subtype}")
                        return iata_code
            else:
                logging.error(f"API request failed for subtype {subtype} with status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error during API request: {e}")
    logging.warning(f"No IATA code found for {place_name} in both CITY and AIRPORT categories")
    return None

airline_names = {}

def load_airline_names(filepath='airlines.json'):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            global airline_names
            airline_names = json.load(file)
            logging.info("Airline names loaded successfully.")
    except Exception as e:
        logging.error(f"Failed to load airline names from {filepath}: {e}")

load_airline_names()

def get_airline_name(carrier_code):
    return airline_names.get(carrier_code, 'Unknown Airline')

def search_flights(origin_name, destination_name, departure_date, return_date=None, adults=1):
    origin_iata = fetch_iata_code(origin_name)
    destination_iata = fetch_iata_code(destination_name)
    if not origin_iata or not destination_iata:
        logging.error("Could not find valid IATA codes for provided locations")
        return None

    access_token = get_access_token()
    if not access_token:
        logging.error("Failed to retrieve access token")
        return None

    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"originLocationCode": origin_iata, "destinationLocationCode": destination_iata,
              "departureDate": departure_date, "adults": adults}
    if return_date:
        params['returnDate'] = return_date

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            flights = response.json()['data']
            simplified_flights = []
            for flight in flights:
                for itinerary in flight['itineraries']:
                    for segment in itinerary['segments']:
                        airline_name = get_airline_name(segment['carrierCode'])
                        simplified_flights.append({
                            "airline_name": airline_name,
                            "flight_number": segment['carrierCode'] + segment['number'],
                            "departure": segment['departure']['at'],
                            "arrival": segment.get('arrival', {}).get('at', 'N/A'),
                            "price": flight['price']['total']
                        })
            return simplified_flights
        else:
            logging.error(f"No flights found or API request failed with status code {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during API call: {e}")
    return None