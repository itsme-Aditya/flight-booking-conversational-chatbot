import functions_framework
import requests
from flask import jsonify

# Your Google Places API Key
GOOGLE_PLACES_API_KEY = 'Your Google Places API Key'

def get_correct_city_name(city_name):
    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {
        'input': city_name,
        'types': '(cities)',
        'key': GOOGLE_PLACES_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for bad status codes
    except requests.RequestException as e:
        print(f"Error fetching data from Google Places API: {e}")
        return city_name
    
    predictions = response.json().get('predictions', [])
    if predictions:
        return predictions[0]['description']
    return city_name

def get_short_city_name(full_city_name):
    # Split the full city name and return only the first part
    return full_city_name.split(',')[0]

@functions_framework.http
def validate_city_names(request):
    request_json = request.get_json(silent=True)
    print("Received request:", request_json)  # Logging request

    if request_json:
        # Extract parameters based on Dialogflow CX request structure
        intent_info = request_json.get('intentInfo', {})
        parameters = intent_info.get('parameters', {})
        
        departure_city_info = parameters.get('geo-city1', {})
        arrival_city_info = parameters.get('geo-city2', {})
        
        departure_city = departure_city_info.get('resolvedValue')
        arrival_city = arrival_city_info.get('resolvedValue')
        
        if departure_city and arrival_city:
            corrected_departure_city = get_correct_city_name(departure_city)
            corrected_arrival_city = get_correct_city_name(arrival_city)
            print("Corrected cities:", corrected_departure_city, corrected_arrival_city)  # Logging corrected cities
            
            short_departure_city = get_short_city_name(corrected_departure_city)
            short_arrival_city = get_short_city_name(corrected_arrival_city)
            
            response = {
                "fulfillmentResponse": {
                    "messages": [
                        {
                            "text": {
                                "text": [
                                    f"Your departure airport is confirmed as {corrected_departure_city} and your arrival airport as {corrected_arrival_city}."
                                ]
                            }
                        }
                    ]
                },
                "sessionInfo": {
                    "parameters": {
                        "geo-city1": short_departure_city,
                        "geo-city2": short_arrival_city
                    }
                },
                "targetPage": "projects/flight-booking-426706/locations/global/agents/2e8d6964-eeea-4dd8-8c8d-2c60c6b61dfc/flows/93286822-a14b-4771-988b-8f488fcbb6b8/pages/7ff7a983-4988-4a5c-be1f-05c8c2344dc5"
            }
        else:
            response = {
                "fulfillmentResponse": {
                    "messages": [
                        {
                            "text": {
                                "text": [
                                    "Please provide both departure and arrival cities."
                                ]
                            }
                        }
                    ]
                }
            }
    else:
        response = {
            "fulfillmentResponse": {
                "messages": [
                    {
                        "text": {
                            "text": [
                                "Error processing the request."
                            ]
                        }
                    }
                ]
            }
        }
    
    print("Response:", response)  # Logging response
    return jsonify(response)
