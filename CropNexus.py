import streamlit as st #for user interface
import requests #for fetching weather data
import os
import pyttsx3  # Offline TTS
from gtts import gTTS  # Online TTS
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import base64  # Required for download button

load_dotenv()

# Weather API URL
WEATHER_API_URL = "http://api.weatherapi.com/v1/forecast.json"

# Supported Languages for Translation & TTS
LANGUAGES = {
    "English": "en",
    "Yoruba": "fr",
    "Igbo": "es",
    "Hausa": "de",
}
#Fetching the weather data for a given location using WeatherAPI
def get_weather_data(location, api_key):
    
    if not api_key:
        st.error("Weather API Key is required to fetch weather data.")
        return None
    
    params = {"key": api_key, "q": location, "days": 30, "aqi": "no", "alerts": "no"}
    try:
        response = requests.get(WEATHER_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        forecast = data.get("forecast", {}).get("forecastday", [])
        if not forecast:
            return None
        avg_temp = round(sum(day['day']['avgtemp_c'] for day in forecast) / len(forecast), 2)
        total_rainfall = round(sum(day['day']['totalprecip_mm'] for day in forecast), 2)
        avg_humidity = round(sum(day['day']['avghumidity'] for day in forecast) / len(forecast), 2)
        return {'avg_temp': avg_temp, 'total_rainfall': total_rainfall, 'avg_humidity': avg_humidity}
    except requests.exceptions.RequestException as e:
        st.error(f"Weather API Error: {e}")
        return None

#Generate a crop planting recommendation based on the defined inputs and the selected language
def generate_recommendation(crop, planting_period, location, soil_type, language, weather_api_key, groq_api_key):
    
    weather_summary = get_weather_data(location, weather_api_key)
    if not weather_summary:
        return "Error fetching weather data. Please check your API key and location."
    
    if not groq_api_key:
        return "Groq API Key is required to generate recommendations."
    
    if not crop_info:
        return "Crop data not found in the dataset."

#Defining the prompt for our model
    prompt = f"""
    You are an AI assistant helping farmers make decision and optimize their crop planting strategy.
    Provide the recommendation in {language}.
    Crop: {crop}
    Location: {location}
    Soil Type: {soil_type if soil_type else "Not specified"}
    Planting Period: {planting_period}
    Weather Conditions:
    - Avg Temp: {weather_summary['avg_temp']}°C
    - Total Rainfall: {weather_summary['total_rainfall']} mm
    - Avg Humidity: {weather_summary['avg_humidity']}%
    Analyze the given conditions and determine whether the provided planting period is optimal in {language}.  
    - If the planting period is optimal, confirm that it is the best time to plant{language}.  
    - If the planting period is not optimal, suggest the best planting period and explain why it is preferable{language}.  

    Additionally:   
    - Provide a concise summary of expected crop performance based on seasonal weather trends and historical data{language}
    - Generate the number of days until crop maturity and overall crop viability if planted during the specified period
    - Recommend the best crop to plant based on the optimal planting period{language}. 
    - Suggest the best approach for successful farming during that period{language}.  
    - Provide possible adjustments to improve farming conditions if necessary{language}. 
    """

    chat_model = ChatGroq(model="llama3-70b-8192", api_key=groq_api_key)
    response = chat_model.invoke(prompt)
    return response.content
#Converts text to speech in English
def text_to_speech(text, lang="en", method="gtts"):
    """Converts text to speech in the selected language."""
    audio_file = "recommendation.mp3"
    
    if method == "gtts":  # Online TTS
        tts = gTTS(text=text, lang=lang)
        tts.save(audio_file)
    #elif method == "pyttsx3":  # Offline TTS
        #engine = pyttsx3.init()
        #engine.save_to_file(text, audio_file)
        #engine.runAndWait()
    
    return audio_file

#Create a download link for an audio file
def get_audio_download_link(file_path):
    
    with open(file_path, "rb") as file:
        audio_bytes = file.read()
    
    b64 = base64.b64encode(audio_bytes).decode()
    href = f'<a href="data:audio/mp3;base64,{b64}" download="recommendation.mp3">📥 Download MP3</a>'
    return href


st.sidebar.title("API Keys (visit www.weatherapi.com and www.groq.com to generate your api key) ")
weather_api_key = st.sidebar.text_input("🌦️ Weather API Key:", type="password")
groq_api_key = st.sidebar.text_input("🤖 Groq API Key:", type="password")

# Language Selection in Sidebar
st.sidebar.title("🌍 Settings")
language = st.sidebar.selectbox("Select Language:", list(LANGUAGES.keys()))

# Developing the Main Interface
st.title("🌱 CropNexus: AI-Powered Multilingual Crop Recommendation System")

with st.form("crop_form"):
    crop = st.selectbox("Enter Crop Name:", options = ['Sorghum', 'Millet', 'Rice', 'Maize', 'Wheat', 'Yam', 'Cocoa', 'Cassava',
    'Groundnut', 'Tomato'])
    region = st.selectbox("Enter your Region :",options= ['North-West', 'South-South', 'North-Central', 'South-East', 'South-West',
    'North-East'])
    location = st.text_input("Enter the Intended Location(State):")
    planting_period = st.selectbox("Select the intended Planting Period:", options = ['Jan-Feb','March-May', 'June-Aug','July-Sept','Oct-Dec' ])
    soil_type = st.selectbox("Enter Soil Type (optional):", options = ['Silt', 'Sandy', 'Loamy', 'Clay', 'Peaty'])
    submit_button = st.form_submit_button("Get Recommendation")

if submit_button:
    if not weather_api_key:
        st.sidebar.error(" Please enter your Weather API Key before generating recommendations.")
    elif not groq_api_key:
        st.sidebar.error("Please enter your Groq API Key before generating recommendations.")
    elif crop and planting_period and location:
        recommendation = generate_recommendation(
            crop, planting_period, location, soil_type, language, weather_api_key, groq_api_key
        )
        
        st.subheader(f"Recommendation ({language}):")
        st.write(recommendation)
        
        # Convert text to speech in selected language
        audio_path = text_to_speech(recommendation, LANGUAGES[language])
        
        # Play audio in Streamlit
        st.audio(audio_path, format="audio/mp3")
        
        # Adding download button in streamlit
        st.markdown(get_audio_download_link(audio_path), unsafe_allow_html=True)

    else:
        st.warning("⚠️ Please fill in all required fields.")
