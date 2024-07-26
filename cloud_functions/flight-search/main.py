import functions_framework
import requests
from flask import jsonify

# Your Amadeus API credentials
AMADEUS_API_KEY = 'Your API Key'
AMADEUS_API_SECRET = 'Your Secret'

# Get Amadeus API token
def get_amadeus_api_token():
    url = 'https://test.api.amadeus.com/v1/security/oauth2/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'client_credentials',
        'client_id': AMADEUS_API_KEY,
        'client_secret': AMADEUS_API_SECRET
    }
    try:
        response = requests.post(url, headers=headers, data=data, verify=False)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()['access_token']
    except requests.RequestException as e:
        print(f"Error fetching Amadeus API token: {e}")
        return None

# Get IATA code for a city
def get_iata_code(city_name, token):
    url = 'https://test.api.amadeus.com/v1/reference-data/locations'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    params = {
        'keyword': city_name,
        'subType': 'CITY'
    }
    try:
        response = requests.get(url, headers=headers, params=params, verify=False)
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()
        if data['data']:
            return data['data'][0]['iataCode']
        else:
            return None
    except requests.RequestException as e:
        print(f"Error fetching IATA code for {city_name}: {e}")
        return None

# Get flights from Amadeus API
def get_flights_from_amadeus(origin, destination, date, token):
    url = 'https://test.api.amadeus.com/v2/shopping/flight-offers'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    params = {
        'originLocationCode': origin,
        'destinationLocationCode': destination,
        'departureDate': date,
        'adults': 1
    }
    try:
        response = requests.get(url, headers=headers, params=params, verify=False)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json(), None
    except requests.RequestException as e:
        print(f"Error fetching flights: {e}")
        return None, str(e)

@functions_framework.http
def get_flights(request):
    request_json = request.get_json(silent=True)
    print("Received request:", request_json)  # Logging request

    if request_json:
        intent_info = request_json.get('intentInfo', {})
        parameters = intent_info.get('parameters', {})
        
        departure_city = request_json.get('sessionInfo', {}).get('parameters', {}).get('geo-city1')
        arrival_city = request_json.get('sessionInfo', {}).get('parameters', {}).get('geo-city2')
        date_info = request_json.get('sessionInfo', {}).get('parameters', {}).get('date', {})
        
        # Extracting the date in YYYY-MM-DD format
        if isinstance(date_info, dict):
            year = int(date_info.get('year', 0))
            month = int(date_info.get('month', 0))
            day = int(date_info.get('day', 0))
            date = f"{year:04d}-{month:02d}-{day:02d}"
        else:
            date = None
        
        if departure_city and arrival_city and date:
            token = get_amadeus_api_token()
            if not token:
                response = {
                    "fulfillmentResponse": {
                        "messages": [
                            {
                                "text": {
                                    "text": [
                                        "Authentication with Amadeus API failed."
                                    ]
                                }
                            }
                        ]
                    }
                }
                print("Response:", response)  # Logging response
                return jsonify(response)
            
            departure_city_code = get_iata_code(departure_city, token)
            arrival_city_code = get_iata_code(arrival_city, token)
            
            if departure_city_code and arrival_city_code:
                flights, error = get_flights_from_amadeus(departure_city_code, arrival_city_code, date, token)
                if error:
                    response = {
                        "fulfillmentResponse": {
                            "messages": [
                                {
                                    "text": {
                                        "text": [
                                            f"Error fetching flights: {error}"
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                else:
                    print("Fetched flights:", flights)  # Logging flights
                    
                    response_text = "Here are some flight options:\n"
                    flight_options = []
                    for i, flight in enumerate(flights.get('data', [])):
                        if i >= 5:  # Limit to 5 flight options
                            break
                        dep_segment = flight['itineraries'][0]['segments'][0]
                        arr_segment = flight['itineraries'][0]['segments'][-1]
                        dep_time = dep_segment['departure']['at'].replace('T', ' ')
                        airline = dep_segment['carrierCode']
                        price = float(flight['price']['total'])
                        currency = flight['price']['currency']
                        if currency == 'EUR':
                            price_in_inr = price * 90.1
                        else:
                            price_in_inr = price  # If not EUR, keep the original price
                        flight_option = {
                            "id": i,
                            "airline": airline,
                            "departure_code": dep_segment['departure']['iataCode'],
                            "arrival_code": arr_segment['arrival']['iataCode'],
                            "departure_time": dep_time,
                            "price": price,
                            "currency": currency,
                            "price_in_inr": price_in_inr
                        }
                        flight_options.append(flight_option)
                        response_text += f"{i + 1}. {airline} flight from {dep_segment['departure']['iataCode']} to {arr_segment['arrival']['iataCode']} on {dep_time}, Price: {price} {currency} (Approx. {price_in_inr:.2f} INR)\n\n\n"
                    
                    response_text += "\nPlease select a flight by entering the corresponding number."
                    response = {
                        "fulfillmentResponse": {
                            "messages": [
                                {
                                    "text": {
                                        "text": [
                                            response_text
                                        ]
                                    }
                                }
                            ]
                        },
                        "sessionInfo": {
                            "parameters": {
                                "flight_options": flight_options
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
                                        "One or both of the cities you entered are not valid. Please provide valid city names."
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
                                    "Please provide departure city, arrival city, and departure date."
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
