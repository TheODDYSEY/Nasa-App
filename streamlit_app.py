import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw, MeasureControl
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
import os
import tempfile
from datetime import datetime

# Set Streamlit page configuration for a clean UI
st.set_page_config(
    page_title="Kenya Farmer Weather & Crop Health Dashboard",
    layout="wide",  # Set layout to wide for larger map view
    initial_sidebar_state="expanded",
    page_icon="🌾"
)

# NASA POWER API function
def get_nasa_power_data(lat, lon, start_date, end_date):
    base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        'latitude': lat,
        'longitude': lon,
        'start': start_date,
        'end': end_date,
        'parameters': 'T2M,PRECTOTCORR,WS2M,RH2M',
        'community': 'AG',
        'format': 'JSON',
    }
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch weather data from NASA API.")
        return None

# Simulated NDVI data retrieval function
def get_ndvi_data(lat, lon):
    ndvi_value = (lat + lon) % 1  # Simulated NDVI value between 0 and 1
    return round(ndvi_value, 2)

# Function to create the interactive map
def create_map(map_type="precipitation", user_location=None, layer_type="OpenWeather"):
    lat, lon = user_location if user_location else [-1.2921, 36.8219]  # Default to Nairobi, Kenya
    m = folium.Map(location=[lat, lon], zoom_start=10 if user_location else 7)  # Zoom in if user location is provided

    API_KEY = "b34c9deda17fc49608cb2619e56cdaca"
    if layer_type == "OpenWeather":
        if map_type == "precipitation":
            folium.TileLayer(
                tiles=f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}",
                attr="OpenWeatherMap",
                name="Precipitation",
            ).add_to(m)
        elif map_type == "temperature":
            folium.TileLayer(
                tiles=f"https://tile.openweathermap.org/map/temp_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}",
                attr="OpenWeatherMap",
                name="Temperature",
            ).add_to(m)
        elif map_type == "ndvi":
            folium.TileLayer(
                tiles="https://your-ndvi-api-url/{{z}}/{{x}}/{{y}}.png",  # Use a real NDVI tile source
                attr="Simulated NDVI",
                name="NDVI",
            ).add_to(m)
    elif layer_type == "Google Satellite":
        folium.TileLayer(
            tiles="http://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            attr="Google Satellite",
            name="Google Satellite",
        ).add_to(m)

    draw = Draw(export=True)
    draw.add_to(m)
    m.add_child(MeasureControl())

    return m



# Function to generate a PDF
# Function to generate a PDF
def generate_pdf(weather_data, ndvi_value, lat, lon):
    buffer = BytesIO()
    report_date = datetime.today().strftime('%Y-%m-%d')
    
    if weather_data and 'properties' in weather_data:
        params = weather_data['properties'].get('parameter', {})
        
        # Extracting data for the report
        temp_data = params.get('T2M', {})
        precipitation_data = params.get('PRECTOTCORR', {})
        wind_data = params.get('WS2M', {})
        humidity_data = params.get('RH2M', {})

        dates = list(temp_data.keys())
        temps = list(temp_data.values())
        precipitation = list(precipitation_data.values())
        wind_speeds = list(wind_data.values())
        humidity = list(humidity_data.values())

        df = pd.DataFrame({
            'Date': dates,
            'Temperature (°C)': temps,
            'Precipitation (mm)': precipitation,
            'Wind Speed (m/s)': wind_speeds,
            'Humidity (%)': humidity
        })

        # Plotting weather data
        fig, ax = plt.subplots(2, 1, figsize=(10, 12))
        
        ax[0].plot(df['Date'], df['Temperature (°C)'], label="Temperature", color='tab:red')
        ax[0].plot(df['Date'], df['Precipitation (mm)'], label="Precipitation", color='tab:blue')
        ax[0].set_title("Temperature and Precipitation Over Time")
        ax[0].set_xlabel("Date")
        ax[0].set_ylabel("Temperature (°C) / Precipitation (mm)")
        ax[0].legend()

        ax[1].plot(df['Date'], df['Wind Speed (m/s)'], label="Wind Speed", color='tab:green')
        ax[1].plot(df['Date'], df['Humidity (%)'], label="Humidity", color='tab:purple')
        ax[1].set_title("Wind Speed and Humidity Over Time")
        ax[1].set_xlabel("Date")
        ax[1].set_ylabel("Wind Speed (m/s) / Humidity (%)")
        ax[1].legend()

        plt.tight_layout()
        plt.savefig(buffer, format='pdf')
        buffer.seek(0)
        
        # Report content
        avg_temp = round(sum(temps) / len(temps), 2)
        total_precipitation = round(sum(precipitation), 2)
        avg_wind_speed = round(sum(wind_speeds) / len(wind_speeds), 2)
        avg_humidity = round(sum(humidity) / len(humidity), 2)

        report_content = f"""
        Kenya Farmer Weather Report
        Report Date: {report_date}
        Location: Latitude: {lat}, Longitude: {lon}
        
        Weather Overview:
        This report provides critical data to help maize farmers make informed decisions about crop management and field operations. The following weather parameters are crucial for maize growth: temperature, precipitation, wind speed, and humidity.

        Key Parameters:
        - Temperature: Average of {avg_temp}°C (Optimal range: 18°C - 32°C for maize growth).
        - Precipitation: Total of {total_precipitation} mm (Optimal: 450-600 mm/month).
        - Wind Speed: Average of {avg_wind_speed} m/s (Optimal: < 3 m/s for crop stability).
        - Humidity: Average of {avg_humidity}% (Optimal range: 60% - 80%).

        NDVI Value: {ndvi_value}

        Recommendations:
        - Temperature: The average temperature is {avg_temp}°C, which is { "within" if 18 <= avg_temp <= 32 else "outside" } the optimal range for maize. Adjust irrigation and fertilization accordingly.
        - Precipitation: The total precipitation was {total_precipitation} mm. { "This is sufficient" if total_precipitation >= 450 and total_precipitation <= 600 else "Irrigation may be required" } for optimal crop health.
        - Wind Speed: With an average wind speed of {avg_wind_speed} m/s, { "it is safe for crop stability." if avg_wind_speed <= 3 else "extra precautions may be needed." }
        - Humidity: The humidity level is {avg_humidity}%, which { "fits" if 60 <= avg_humidity <= 80 else "does not fit" } the optimal range for maize crops.
        """
        
        return buffer, report_content
    else:
        st.error("Insufficient weather data to generate the PDF.")
        return None, None


# Main app UI layout
st.title("🌾 Kenya Farmer Weather & NDVI Dashboard")
st.write("Plan your farming with real-time weather and crop health data.")

st.sidebar.header("Settings")
map_type = st.sidebar.selectbox("Select Map Type", ["NDVI", "Precipitation", "Temperature"])
layer_type = st.sidebar.radio("Select Map Layer", ["OpenWeather", "Google Satellite"])
enable_location = st.sidebar.checkbox("Enable Location")

# counties = ["Nairobi", "Mombasa", "Kisumu"]  # Placeholder counties
# constituencies = {"Nairobi": ["Westlands", "Lang'ata"], "Mombasa": ["Likoni", "Nyali"], "Kisumu": ["Kisumu Central", "Kisumu West"]}
# selected_county = st.sidebar.selectbox("Filter by County", counties)
# selected_constituency = st.sidebar.selectbox("Filter by Constituency", constituencies.get(selected_county, []))

user_location = [-1.2921, 36.8219] if not enable_location else None

start_date = st.sidebar.date_input("Start Date", value=datetime.today())
end_date = st.sidebar.date_input("End Date", value=datetime.today())
crop_type = "Maize"  # Fixed to Maize only

st.write("### Interactive Weather & NDVI Map")
map_data = st_folium(create_map(map_type.lower(), user_location, layer_type), width=1000, height=900)

if map_data and 'all_drawings' in map_data and map_data['all_drawings']:
    shape = map_data['all_drawings'][0]['geometry']
    lat, lon = shape['coordinates'][0][0]

    # Update user location if "Enable Location" is checked
    if enable_location:
        user_location = [lat, lon]

    weather_data = get_nasa_power_data(lat, lon, start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d'))
    if weather_data and 'properties' in weather_data:
        params = weather_data['properties'].get('parameter', {})
        temp = params.get('T2M', {}).get(start_date.strftime('%Y%m%d'), 'No data')
        precipitation = params.get('PRECTOTCORR', {}).get(start_date.strftime('%Y%m%d'), 'No data')
        wind_speed = params.get('WS2M', {}).get(start_date.strftime('%Y%m%d'), 'No data')
        humidity = params.get('RH2M', {}).get(start_date.strftime('%Y%m%d'), 'No data')

        st.write(f"### Weather Data for Latitude: {lat}, Longitude: {lon}")
        st.write(f"**Temperature**: {temp} °C")
        st.write(f"**Precipitation**: {precipitation} mm")
        st.write(f"**Wind Speed**: {wind_speed} m/s")
        st.write(f"**Humidity**: {humidity} %")

    if map_type == "NDVI":
        ndvi_value = get_ndvi_data(lat, lon)
        st.subheader(f"🌿 NDVI for Selected Area (lat: {lat}, lon: {lon}):")
        st.markdown(f"**🌱 NDVI Value:** {ndvi_value}")

        # Provide insights based on NDVI value
        if ndvi_value > 0.6:
            st.success("🌳 **Healthy Vegetation Detected!** Optimal conditions for maize growth.")
        elif 0.3 < ndvi_value <= 0.6:
            st.warning("🌿 **Moderate Vegetation Health:** Consider irrigation or monitoring closely for maize.")
        else:
            st.error("⚠️ **Low NDVI Detected:** Poor vegetation health; maize may struggle to grow.")

    if st.button("Generate PDF"):
        pdf, report_content = generate_pdf(weather_data, ndvi_value, lat, lon)
        
        if pdf is not None:
            st.success("PDF generated successfully!")
            
            # Allow user to download the PDF
            st.download_button("Download PDF", data=pdf, file_name="weather_report.pdf", mime="application/pdf")
            
            # Optionally display report content
            st.write(report_content)
        else:
            st.error("Failed to generate PDF.")