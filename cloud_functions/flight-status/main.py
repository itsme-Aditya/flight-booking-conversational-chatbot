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
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()['access_token']
    except requests.RequestException as e:
        print(f"Error fetching Amadeus API token: {e}")
        return None

@functions_framework.http
def check_flight_status(request):
    try:
        request_json = request.get_json(silent=True)
        print("Received request:", request_json)

        if not request_json:
            raise ValueError("Request JSON is empty")

        intent_info = request_json.get('intentInfo', {})
        parameters = intent_info.get('parameters', {})

        airline_code = request_json.get('sessionInfo', {}).get('parameters', {}).get('airline-code')
        flight_number = request_json.get('sessionInfo', {}).get('parameters', {}).get('number')
        date_info = request_json.get('sessionInfo', {}).get('parameters', {}).get('date', {})

        if isinstance(date_info, dict):
            year = int(date_info.get('year', 0))
            month = int(date_info.get('month', 0))
            day = int(date_info.get('day', 0))
            scheduled_departure_date = f"{year:04d}-{month:02d}-{day:02d}"
        else:
            scheduled_departure_date = None

        if not airline_code or not flight_number or not scheduled_departure_date:
            raise ValueError("Missing required parameters: airline_code, flight_number, or scheduled_departure_date")

        token = get_amadeus_api_token()
        if not token:
            raise ValueError("Authentication with Amadeus API failed")

        url = 'https://test.api.amadeus.com/v2/schedule/flights'
        headers = {
            'Authorization': f'Bearer {token}'
        }
        params = {
            'carrierCode': airline_code,
            'flightNumber': flight_number,
            'scheduledDepartureDate': scheduled_departure_date
        }
        print("Request URL:", url)
        print("Request Headers:", headers)
        print("Request Params:", params)

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        flight_status = response.json()
        print("Fetched flight status:", flight_status)

        if 'data' in flight_status and len(flight_status['data']) > 0:
            flight_info = flight_status['data'][0]
            print("Flight info:", flight_info)
            departure = flight_info['flightPoints'][0]['iataCode']
            arrival = flight_info['flightPoints'][1]['iataCode']
            departure_time = flight_info['flightPoints'][0]['departure']['timings'][0]['value']
            arrival_time = flight_info['flightPoints'][1]['arrival']['timings'][0]['value']
            response_text = (f"Flight {airline_code}{flight_number} from {departure} to {arrival} is scheduled to depart "
                             f"at {departure_time} and arrive at {arrival_time}.")

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
                }
            }
        else:
            print("No flight status data found")
            response = {
                "fulfillmentResponse": {
                    "messages": [
                        {
                            "text": {
                                "text": [
                                    "No status found for the given flight."
                                ]
                            }
                        }
                    ]
                }
            }

    except ValueError as ve:
        print(f"ValueError: {ve}")
        response = {
            "fulfillmentResponse": {
                "messages": [
                    {
                        "text": {
                            "text": [
                                f"Error: {ve}"
                            ]
                        }
                    }
                ]
            }
        }

    except requests.RequestException as re:
        print(f"RequestException: {re}")
        response = {
            "fulfillmentResponse": {
                "messages": [
                    {
                        "text": {
                            "text": [
                                f"Error fetching flight status: {re}"
                            ]
                        }
                    }
                ]
            }
        }

    except Exception as e:
        print(f"Exception: {e}")
        response = {
            "fulfillmentResponse": {
                "messages": [
                    {
                        "text": {
                            "text": [
                                f"Error: {e}"
                            ]
                        }
                    }
                ]
            }
        }

    print("Response:", response)
    return jsonify(response)
