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
        return None
    
    predictions = response.json().get('predictions', [])
    if predictions:
        return predictions[0]['description']
    return None

def get_short_city_name(full_city_name):
    # Split the full city name and return only the first part
    return full_city_name.split(',')[0]

@functions_framework.http
def validate_single_city_name(request):
    request_json = request.get_json(silent=True)
    print("Received request:", request_json)  # Logging request

    if request_json:
        # Extract parameters based on Dialogflow CX request structure
        intent_info = request_json.get('intentInfo', {})
        parameters = intent_info.get('parameters', {})
        
        city_info = parameters.get('geo-city2', {})
        
        city = city_info.get('resolvedValue')
        
        if city:
            corrected_city = get_correct_city_name(city)
            print("Corrected city:", corrected_city)  # Logging corrected city
            
            if corrected_city:
                short_city = get_short_city_name(corrected_city)
                response = {
                    "fulfillmentResponse": {
                        "messages": [
                            {
                                "text": {
                                    "text": [
                                        f"Your arrival city is confirmed as {corrected_city}."
                                    ]
                                }
                            }
                        ]
                    },
                    "sessionInfo": {
                        "parameters": {
                            "geo-city2": short_city
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
                                        "The city you entered is not valid. Please provide a valid city."
                                    ]
                                }
                            }
                        ]
                    },
                    "sessionInfo": {
                        "parameters": {
                            "geo-city2": None  # Clear the invalid city parameter
                        }
                    }
                }
        else:
            response = {
                "fulfillmentResponse": {
                    "messages": [
                        {
                            "text": {
                                "text": [
                                    "Please provide a city."
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
