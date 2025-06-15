import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv
from ml_model import get_crop_recommendations_from_ml

# Import the Gemini library
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app) # Enable CORS for frontend to communicate with backend

# --- Configuration (Load API keys from environment variables) ---
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
model = None # Initialize model to None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Initialize the Generative Model (using 'gemini-pro' for text-only interactions)
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')# <--- Update this line# <--- Make sure this matches your list_gemini_models.py output!

        print("DEBUG: Gemini model 'gemini-pro' configured successfully.")
    except Exception as e:
        print(f"WARNING: Error configuring Gemini API: {e}. Chatbot will not function.")
else:
    print("WARNING: GEMINI_API_KEY not found in backend/.env. Chatbot will not function.")

# --- API Endpoints ---

@app.route('/api/weather', methods=['GET'])
def get_weather():
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        print(f"DEBUG: Latitude ({lat}) or Longitude ({lon}) missing for weather request.")
        return jsonify({"error": "Latitude and Longitude are required."}), 400

    if not OPENWEATHER_API_KEY:
        print("DEBUG: OpenWeatherMap API key not configured.")
        return jsonify({"error": "OpenWeatherMap API key not configured in backend/.env"}), 500

    try:
        # Use OpenWeatherMap 2.5 Current Weather API (free tier)
        current_weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"

        print(f"DEBUG: Fetching current weather from: {current_weather_url}")
        current_weather_response = requests.get(current_weather_url)
        print(f"DEBUG: Fetching forecast from: {forecast_url}")
        forecast_response = requests.get(forecast_url)

        current_weather_data = current_weather_response.json()
        forecast_data = forecast_response.json()

        print(f"DEBUG: Current Weather API Response Status: {current_weather_response.status_code}")
        print(f"DEBUG: Forecast API Response Status: {forecast_response.status_code}")

        if current_weather_response.status_code != 200:
            print(f"DEBUG: OpenWeather current weather error: {current_weather_data.get('message', 'Unknown error')}")
            return jsonify({"error": current_weather_data.get('message', 'Failed to fetch current weather')}), current_weather_response.status_code
        if forecast_response.status_code != 200:
            print(f"DEBUG: OpenWeather forecast error: {forecast_data.get('message', 'Unknown error')}")
            return jsonify({"error": forecast_data.get('message', 'Failed to fetch forecast')}), forecast_response.status_code

        return jsonify({
            "current_weather": current_weather_data,
            "forecast": forecast_data
        })

    except requests.exceptions.RequestException as e:
        print(f"DEBUG: Network or API error while fetching weather: {str(e)}")
        return jsonify({"error": f"Network or API error while fetching weather: {str(e)}"}), 500
    except Exception as e:
        print(f"DEBUG: An unexpected error occurred while fetching weather: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred while fetching weather: {str(e)}"}), 500

@app.route('/api/recommend_crops', methods=['POST'])
def recommend_crops():
    data = request.get_json()
    if not data:
        print("DEBUG: No JSON data received for crop recommendation.")
        return jsonify({"error": "Invalid JSON data received."}), 400

    location_data = data.get('location', {})
    current_weather = data.get('current_weather', {})
    forecast_data = data.get('forecast_data', {})
    soil_type = data.get('soilType')
    preferences = data.get('cropPreferences')

    if not location_data or not current_weather or not soil_type:
        print("DEBUG: Missing required fields for crop recommendation.")
        return jsonify({"error": "Location, current weather, and soil type are required for recommendations."}), 400

    try:
        recommendations = get_crop_recommendations_from_ml(location_data, current_weather, forecast_data, soil_type, preferences)
        return jsonify({"recommendations": recommendations})
    except Exception as e:
        print(f"DEBUG: Error in ML model: {e}")
        return jsonify({"error": f"Error generating crop recommendations: {str(e)}"}), 500

@app.route('/api/chatbot_query', methods=['POST'])
def chatbot_query():
    try:
        user_query = request.json.get('query', '')
        user_info = request.json.get('userInfo', {})

        if not user_query:
            print("DEBUG: Chatbot query is empty.")
            return jsonify({"response": "Please enter a question for the chatbot."}), 400

        if not model:  # Check if Gemini model was initialized successfully
            print("DEBUG: Gemini API not configured or failed to initialize. Cannot process chatbot query.")
            return jsonify({"response": "Sorry, my AI brain is not connected right now. Please check the backend configuration."}), 503

        prompt_parts = [
            "You are an expert agricultural AI assistant named AgriBot.",
            "Your goal is to provide helpful, concise, and accurate farming advice.",
            "Focus on topics like weather implications for farming, crop recommendations, soil types, and general agricultural practices.",
            "If the user asks about the weather, and you have information, mention it naturally.",
            "If the user asks about crop recommendations, and you have information, suggest they use the dedicated feature for detailed recommendations.",
            "Current User Context:",
            f"Location: {user_info.get('location', 'not available')}",
            f"Soil Type: {user_info.get('soilType', 'not available')}",
            f"Current Weather: {user_info.get('currentWeather', 'not available')}",
            "",
            f"User Query: {user_query}",
            "AgriBot's Response:"
        ]

        full_prompt = "\n".join(prompt_parts)
        print(f"DEBUG: Sending to Gemini: {full_prompt}")

        response = model.generate_content(full_prompt)
        response_text = getattr(response, 'text', None)
        if not response_text:
            print("ERROR: Gemini API returned no text.")
            response_text = "Sorry, I couldn't get a response from the AI model."

        print(f"DEBUG: Received from Gemini: {response_text}")

        return jsonify({"response": response_text})

    except Exception as e:
        print(f"ERROR: Error calling Gemini API: {e}")
        response_text = f"Sorry, I'm having trouble connecting to my AI brain. Error: {str(e)}"
        return jsonify({"response": response_text}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)