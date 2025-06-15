# This file would contain your actual Machine Learning model logic.
# For the hackathon, this is a placeholder using rule-based logic.

def get_crop_recommendations_from_ml(location_data, current_weather_data, forecast_data, soil_type, crop_preferences):
    """
    Placeholder for your crop recommendation ML model.
    In a real scenario, this function would:
    1. Load a pre-trained ML model (e.g., a scikit-learn model, TensorFlow/PyTorch model).
    2. Preprocess the input data (location, current weather, forecast, soil type)
       to match the format expected by your model.
    3. Make a prediction using the loaded model.
    4. Translate the model's output into human-readable crop recommendations
       and associated advice.

    For now, it returns mock recommendations based on temperature.
    """
    print("--- ML Model Input ---")
    print(f"Location: {location_data}")
    print(f"Current Weather: {current_weather_data}")
    print(f"Soil Type: {soil_type}")
    print(f"Crop Preferences: {crop_preferences}")
    print("----------------------")

    # Extract relevant weather info (mock logic)
    # For OWM 2.5 'weather' API, temperature is under 'main' key.
    temp_celsius = current_weather_data.get('main', {}).get('temp')
    weather_description = current_weather_data.get('weather', [{}])[0].get('description', '').lower()
    humidity = current_weather_data.get('main', {}).get('humidity')


    recommendations = []

    if temp_celsius is not None:
        # Check for potential forecast rain in the next 12 hours (4 * 3-hour forecasts)
        has_forecast_rain = False
        if forecast_data and 'list' in forecast_data:
            for item in forecast_data['list'][:4]: # Check next 12 hours (4 * 3-hour intervals)
                if 'rain' in item.get('weather', [{}])[0].get('description', '').lower():
                    has_forecast_rain = True
                    break

        if temp_celsius > 30 and ("rain" in weather_description or has_forecast_rain):
            recommendations.append({"crop": "Paddy (Rice)", "details": "Ideal for high temperatures and abundant rainfall. Ensure good drainage if excessive rain."})
            recommendations.append({"crop": "Sugarcane", "details": "Thrives in warm, humid conditions with good water supply."})
        elif temp_celsius >= 20 and temp_celsius <= 30:
            if "clear" in weather_description or "clouds" in weather_description:
                recommendations.append({"crop": "Maize (Corn)", "details": "Adapts well to moderate temperatures and needs well-drained soil."})
                recommendations.append({"crop": "Soybean", "details": "Requires warm temperatures and moderate rainfall. Good for soil nitrogen."})
            elif "rain" in weather_description or has_forecast_rain:
                 recommendations.append({"crop": "Groundnut (Peanut)", "details": "Benefits from moderate rain and warm soil, thrives in sandy loamy soil."})
        elif temp_celsius < 20:
            recommendations.append({"crop": "Wheat", "details": "Best suited for cool and moist conditions during early growth."})
            recommendations.append({"crop": "Mustard", "details": "Grows well in cool, dry weather conditions."})

    # Add soil-based recommendations (simple rule-based for now, ML would be more complex)
    if soil_type: # Ensure soil_type is not empty
        if "sandy" in soil_type.lower():
            recommendations.append({"crop": "Millet", "details": "Very hardy, suitable for sandy soils and drought-prone areas."})
        elif "clay" in soil_type.lower():
            recommendations.append({"crop": "Cotton", "details": "Prefers clayey soils for good water retention, needs warm climate."})
        elif "loamy" in soil_type.lower():
            recommendations.append({"crop": "Vegetables (various)", "details": "Loamy soil is versatile and good for most vegetables due to balanced texture."})
        elif "silt" in soil_type.lower():
            recommendations.append({"crop": "Potato", "details": "Silt loam is ideal for root crops like potatoes due to good drainage and fertility."})
        elif "alluvial" in soil_type.lower():
            recommendations.append({"crop": "Paddy (Rice)", "details": "Highly fertile and retains moisture, excellent for rice cultivation."})

    # Filter based on preferences (basic example)
    final_recommendations = []
    if crop_preferences:
        pref_keywords = [p.strip().lower() for p in crop_preferences.split(',')]
        for rec in recommendations:
            if any(kw in rec['crop'].lower() or kw in rec['details'].lower() for kw in pref_keywords):
                final_recommendations.append(rec)
        if not final_recommendations and recommendations: # If no match, return some generic if preferences don't filter
            final_recommendations = recommendations[:2] # Return top 2 if preferences don't filter to something
    else:
        final_recommendations = recommendations

    if not final_recommendations:
        final_recommendations.append({"crop": "No specific recommendation", "details": "Current conditions or provided information might not yield a clear crop. Consider general hardy crops or consult a local expert."})

    return final_recommendations[:3] # Limit to top 3 recommendations for display