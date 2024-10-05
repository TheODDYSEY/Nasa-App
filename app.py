import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw

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
    
    # Check if the response is valid
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch weather data from NASA API.")
        return None

# Simulated NDVI data retrieval function
def get_ndvi_data(lat, lon):
    # Simulate NDVI data for the region based on latitude and longitude
    ndvi_value = (lat + lon) % 1  # Simulated NDVI value between 0 and 1
    return round(ndvi_value, 2)

# Function to create the interactive map
def create_map(map_type="precipitation"):
    m = folium.Map(location=[-1.2921, 36.8219], zoom_start=7)  # Nairobi, Kenya

    # Choose the map layer
    API_KEY = "b34c9deda17fc49608cb2619e56cdaca"

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
        # Display a simulated NDVI layer
        folium.TileLayer(
            tiles="https://your-ndvi-api-url/{{z}}/{{x}}/{{y}}.png",  # Use a real NDVI tile source
            attr="Simulated NDVI",
            name="NDVI",
        ).add_to(m)
    
    # Add drawing tools to the map
    draw = Draw(export=True)
    draw.add_to(m)
    
    return m

# Main app UI layout
st.title("🌾 Kenya Farmer Weather & NDVI Dashboard")
st.write("Plan your farming with real-time weather and crop health data.")

# Sidebar: Select map type and additional inputs
st.sidebar.header("Settings")
map_type = st.sidebar.selectbox("Select Map Type", ["Precipitation", "Temperature", "NDVI"])

# Change the color of the app based on the selected map type
if map_type == "NDVI":
    st.markdown(
        """
        <style>
        .reportview-container {
            background-color: #e8f5e9;  /* Light green background */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

start_date = st.sidebar.date_input("Start Date")
end_date = st.sidebar.date_input("End Date")
crop_type = "Maize"  # Fixed to Maize only

# Generate the interactive map with a larger size
st.write("### Interactive Weather & NDVI Map")
st.write("Use the map to draw a shape and get weather and NDVI data.")
map_data = st_folium(create_map(map_type.lower()), width=900, height=600)

# Handle shape drawing and fetch NASA data
if map_data and 'all_drawings' in map_data and map_data['all_drawings']:
    shape = map_data['all_drawings'][0]['geometry']
    lat, lon = shape['coordinates'][0][0]  # Get lat, lon from the first point

    # Fetch weather data from NASA API
    weather_data = get_nasa_power_data(lat, lon, start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d'))
    
    # Check if weather data is retrieved
    if weather_data and 'properties' in weather_data:
        params = weather_data['properties'].get('parameter', {})

        # Safely get the weather parameters
        temp = params.get('T2M', {}).get(start_date.strftime('%Y%m%d'), 'No data')
        precipitation = params.get('PRECTOTCORR', {}).get(start_date.strftime('%Y%m%d'), 'No data')
        wind_speed = params.get('WS2M', {}).get(start_date.strftime('%Y%m%d'), 'No data')
        humidity = params.get('RH2M', {}).get(start_date.strftime('%Y%m%d'), 'No data')

        # Display the weather data with improved formatting
        st.subheader("🌤️ Weather Data for Selected Area")
        
        # Format temperature output
        temp_display = f"{temp:.2f} °C" if isinstance(temp, (int, float)) and temp != -999.0 else "Data not available"
        precipitation_display = f"{precipitation:.2f} mm" if isinstance(precipitation, (int, float)) and precipitation != -999.0 else "Data not available"
        wind_speed_display = f"{wind_speed:.2f} m/s" if isinstance(wind_speed, (int, float)) and wind_speed != -999.0 else "Data not available"
        humidity_display = f"{humidity:.2f} %" if isinstance(humidity, (int, float)) and humidity != -999.0 else "Data not available"

        # Display formatted data with icons
        st.markdown(f"**🌡️ Temperature:** {temp_display}")
        st.markdown(f"**💧 Precipitation:** {precipitation_display}")
        st.markdown(f"**💨 Wind Speed:** {wind_speed_display}")
        st.markdown(f"**🌫️ Humidity:** {humidity_display}")

        # Suggest farming actions based on conditions
        st.subheader("🌱 Farming Insights")
        
        # Check precipitation value
        if precipitation == 'No data' or precipitation == -999.0:
            st.warning("🚱 Rainfall data is unavailable. Consider irrigation as a precaution.")
        elif isinstance(precipitation, (int, float)) and precipitation < 5:  # Adjust this threshold as necessary
            st.warning("🚱 Low Rainfall Detected: Irrigation is required.")
        else:
            st.success("🌧️ Sufficient rainfall detected.")

    # Fetch simulated NDVI data
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

# Additional resources and tips
st.sidebar.subheader("Farming Tips")
st.sidebar.write(""" 
- NDVI helps monitor crop health and predict yields.
- Ensure proper soil moisture for better yields.
- High humidity levels promote fungal growth—use fungicides if needed.
""")

st.sidebar.markdown("### [Need Help? Contact Us](#)")

st.write("For more farming tips, please contact our agronomists or visit our resource center.")
