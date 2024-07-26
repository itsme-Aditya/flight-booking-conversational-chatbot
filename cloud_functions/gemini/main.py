import functions_framework
import requests
import logging

# Set your generative language API URL and key
API_KEY = "Your API Key"
API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={API_KEY}"

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@functions_framework.http
def get_answer(request):
    try:
        request_json = request.get_json(silent=True)
        logging.debug(f"Request JSON: {request_json}")

        if not request_json:
            return {"fulfillmentResponse": {"messages": [{"text": {"text": ["Invalid request"]}}]}}, 400

        # Extract query from Dialogflow CX request
        query = request_json.get('text') or request_json.get('queryResult', {}).get('queryText', '')

        if not query:
            return {"fulfillmentResponse": {"messages": [{"text": {"text": ["Query parameter is missing"]}}]}}, 400

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "prompt": query,
            "max_tokens": 150
        }

        logging.debug(f"Headers: {headers}")
        logging.debug(f"Data: {data}")

        json_data = {"contents": [{"role": "user", "parts": [{"text": query}]}]}

        response = requests.post(API_URL, json=json_data)

        logging.debug(f"Response Status Code: {response.status_code}")
        logging.debug(f"Response Text: {response.text}")

        if response.status_code == 200:
            data = response.json()
            org_data = data['candidates'][0]['content']['parts'][0]['text']

            # Formulate the response in Dialogflow CX format
            dialogflow_response = {
                "fulfillmentResponse": {
                    "messages": [
                        {
                            "text": {
                                "text": [org_data]
                            }
                        }
                    ]
                }
            }
            return dialogflow_response
        else:
            return {"fulfillmentResponse": {"messages": [{"text": {"text": [f"Error: {response.status_code}, {response.text}"]}}]}}, response.status_code
    except Exception as e:
        logging.error(f"Exception occurred: {str(e)}")
        return {"fulfillmentResponse": {"messages": [{"text": {"text": [f"Internal server error: {str(e)}"]}}]}}, 500
