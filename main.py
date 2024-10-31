import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json
import plotly.graph_objects as go
import plotly.express as px

def load_api_key():
    """
    Loads the API key from a config JSON file.
    """
    try:
        with open("config.json") as f:
            config = json.load(f)
            return config["api_key"]
    except FileNotFoundError:
        st.error("API key configuration file not found.")
        return None

def load_weather_data(city, api_key):
    """
    Loads weather data for current, 48-hour, and 10-day forecasts.
    """
    try:
        # Current and 48-hour forecast
        url_48hr = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={city}&days=2&aqi=no&alerts=no"
        response_48hr = requests.get(url_48hr)
        data_48hr = response_48hr.json()
        
        # Current weather data
        current_data = {
            "temperature": data_48hr["current"]["temp_c"],
            "feels_like": data_48hr["current"]["feelslike_c"],
            "humidity": data_48hr["current"]["humidity"],
            "condition": data_48hr["current"]["condition"]["text"],
            "wind_speed": data_48hr["current"]["wind_kph"],
            "icon": f"http:{data_48hr['current']['condition']['icon']}",
            "sunrise": data_48hr["forecast"]["forecastday"][0]["astro"]["sunrise"],
            "sunset": data_48hr["forecast"]["forecastday"][0]["astro"]["sunset"]
        }

        # Hourly forecast for 48 hours with icons
        forecast_48hr = pd.DataFrame([{
            "time": hour["time"],
            "temperature": hour["temp_c"],
            "feels_like": hour["feelslike_c"],
            "humidity": hour["humidity"],
            "condition": hour["condition"]["text"],
            "wind_speed": hour["wind_kph"],
            "icon": f"http:{hour['condition']['icon']}"
        } for day in data_48hr["forecast"]["forecastday"] for hour in day["hour"]])
        
        # Daily forecast for 10 days with icons
        url_10day = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={city}&days=10&aqi=no&alerts=no"
        response_10day = requests.get(url_10day)
        data_10day = response_10day.json()
        
        forecast_10day = pd.DataFrame([{
            "date": day["date"],
            "avg_temperature": day["day"]["avgtemp_c"],
            "condition": day["day"]["condition"]["text"],
            "wind_speed": day["day"]["maxwind_kph"],
            "sunrise": day["astro"]["sunrise"],
            "sunset": day["astro"]["sunset"],
            "icon": f"http:{day['day']['condition']['icon']}"
        } for day in data_10day["forecast"]["forecastday"]])
        
        return current_data, forecast_48hr, forecast_10day

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, pd.DataFrame(), pd.DataFrame()

def main():
    st.title("Weather Data Viewer")
    
    api_key = load_api_key()
    if not api_key:
        st.stop()  # Stop the app if API key is missing
    
    st.sidebar.header("City Selection and Options")
    city = st.sidebar.text_input("Enter City", value="London")
    show_48hr = st.sidebar.checkbox("Show 48-Hour Forecast", value=False)
    show_10day = st.sidebar.checkbox("Show 10-Day Forecast", value=False)
    
    current_data, forecast_48hr, forecast_10day = load_weather_data(city, api_key)

    if current_data:
        # Display current weather with visuals
        st.subheader(f"Current Weather in {city}")
        st.image(current_data['icon'], width=100)  # Display weather icon
        st.write(f"**Temperature:** {current_data['temperature']}°C")
        st.write(f"**Feels Like:** {current_data['feels_like']}°C")
        st.write(f"**Condition:** {current_data['condition']}")
        st.write(f"**Wind Speed:** {current_data['wind_speed']} km/h")
        st.write(f"**Humidity:** {current_data['humidity']}%")
        st.write(f"**Sunrise:** {current_data['sunrise']}")
        st.write(f"**Sunset:** {current_data['sunset']}")
        
        # Plotly visuals for current weather
        st.subheader("Current Weather Visuals")
        
        # Arrange charts in a row
        col1, col2 = st.columns(2)
        
        with col1:
            # Temperature Gauge
            temp_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=current_data['temperature'],
                title={'text': "Temperature (°C)"},
                gauge={
                    'axis': {'range': [-30, 50]},
                    'bar': {'color': "blue"},
                }
            ))
            st.plotly_chart(temp_gauge)
        
        with col2:
            # Humidity Pie Chart
            humidity_pie = px.pie(
                names=['Humidity', 'Remaining'],
                values=[current_data['humidity'], 100 - current_data['humidity']],
                title='Humidity Level (%)',
                hole=0.4
            )
            st.plotly_chart(humidity_pie)
        
        # Feels Like Line Chart (Variation Over Time - Sample Data)
        st.subheader("Feels Like Temperature Throughout the Day")
        feels_like_line = px.line(
            x=['Morning', 'Afternoon', 'Evening', 'Night'],
            y=[current_data['feels_like'] - 2, current_data['feels_like'], current_data['feels_like'] - 1, current_data['feels_like'] - 3],
            labels={'x': 'Time of Day', 'y': 'Feels Like Temperature (°C)'},
            title='Feels Like Temperature Throughout the Day'
        )
        st.plotly_chart(feels_like_line)

    # Display 48-hour forecast if selected
    if show_48hr and not forecast_48hr.empty:
        st.subheader("48-Hour Forecast")
        forecast_48hr_display = forecast_48hr.copy()
        forecast_48hr_display["icon"] = forecast_48hr_display["icon"].apply(lambda x: f'<img src="{x}" width="32">')
        forecast_48hr_display = forecast_48hr_display[["time", "temperature", "feels_like", "humidity", "condition", "wind_speed", "icon"]]
        st.write(forecast_48hr_display.to_html(escape=False, index=False), unsafe_allow_html=True)

    # Display 10-day forecast if selected
    if show_10day and not forecast_10day.empty:
        st.subheader("10-Day Forecast")
        forecast_10day_display = forecast_10day.copy()
        forecast_10day_display["icon"] = forecast_10day_display["icon"].apply(lambda x: f'<img src="{x}" width="32">')
        forecast_10day_display = forecast_10day_display[["date", "avg_temperature", "condition", "wind_speed", "sunrise", "sunset", "icon"]]
        st.write(forecast_10day_display.to_html(escape=False, index=False), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
