from geopy.geocoders import GoogleV3
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize the geocoder with your API key
google_maps_api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
geolocator = GoogleV3(api_key=google_maps_api_key)

def get_origin_coordinates(origin):
    location = geolocator.geocode(origin)
    if location:
        return location.latitude, location.longitude
    else:
        return None, None

def get_destination_coordinates(destination):
    location = geolocator.geocode(destination)
    if location:
        return location.latitude, location.longitude
    else:
        return None, None
