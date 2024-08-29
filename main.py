import streamlit as st
import pandas as pd
import json
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import firebase_admin
from firebase_admin import credentials, storage
import tempfile
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Firebase app (do this only once)
load_dotenv()

@st.cache_resource
def initialize_firebase():
    if not firebase_admin._apps:
        # Create a dictionary with the Firebase configuration
        firebase_config = {
            "type": os.getenv("FIREBASE_TYPE"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN")
        }
        
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred, {'storageBucket': 'mint-poc-p1.appspot.com'})
    return storage.bucket()

# Use the function to initialize Firebase and get the bucket
bucket = initialize_firebase()


# When to deploy the app, you can use the following code snippet:
# def initialize_firebase():
#     # Initialize Firebase app (do this only once)
#     if not firebase_admin._apps:
#         # Use st.secrets to access the Firebase credentials
#         cred = credentials.Certificate(st.secrets["firebase"])
#         firebase_admin.initialize_app(cred, {'storageBucket': 'mint-poc-p1.appspot.com'})

# bucket = storage.bucket()



st.title('GT7 Telemetry Data')

def find_user_races(username):
    blobs = bucket.list_blobs(prefix=f"{username}/")
    file_list = [blob.name for blob in blobs]
    return file_list

@st.cache_data
def load_data(file_name):
    blob = bucket.blob(file_name)
    _, temp_local_filename = tempfile.mkstemp()
    blob.download_to_filename(temp_local_filename)

    with open(temp_local_filename, 'r') as file:
        data = json.load(file)

    # Extract static data
    static_data = data['static_data']
    df_static = pd.DataFrame([static_data])

    # Extract and process dynamic data
    dynamic_data = data['dynamic_data']
    df_dynamic = pd.DataFrame()

    for lap, lap_data in dynamic_data.items():
        lap_df = pd.DataFrame(lap_data)
        lap_df['lap'] = int(lap)
        df_dynamic = pd.concat([df_dynamic, lap_df], ignore_index=True)
    df_dynamic['lap_index'] = df_dynamic.groupby('lap').cumcount()
    return df_static, df_dynamic

def visualize_data(df_static_1, df_dynamic_1, df_static_2, df_dynamic_2):
    print_lap_times_table(df_static_1, df_static_2)

    selected_lap = st.selectbox("Select a lap to compare:", 
                                st.session_state.df_dynamic1['lap'].unique(), key="lap_select")


    # Prepare data for plotting
    selected_lap_data_1 = df_dynamic_1[df_dynamic_1['lap'] == selected_lap]
    selected_lap_data_2 = df_dynamic_2[df_dynamic_2['lap'] == selected_lap]

    # Create the comparison plots
    plot_comparison(selected_lap_data_1, selected_lap_data_2, 'speed', 'Speed', selected_lap)
    plot_comparison(selected_lap_data_1, selected_lap_data_2, 'rpm', 'RPM', selected_lap)
    plot_comparison(selected_lap_data_1, selected_lap_data_2, 'throttle', 'Throttle', selected_lap)

def plot_comparison(selected_lap_data_1, selected_lap_data_2, metric, metric_name, selected_lap):
    # st.write(f"{metric_name} vs Time: Lap {selected_lap} Comparison")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=selected_lap_data_1['lap_index'], y=selected_lap_data_1[metric],
                             mode='lines', name=f'Race 1 Lap {selected_lap} {metric_name}', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=selected_lap_data_2['lap_index'], y=selected_lap_data_2[metric],
                             mode='lines', name=f'Race 2 Lap {selected_lap} {metric_name}', line=dict(color='red')))
    fig.update_layout(title=f'{metric_name} vs Time: Lap {selected_lap} Comparison',
                      xaxis_title='Lap Time',
                      yaxis_title=metric_name,
                      height=300)
    st.plotly_chart(fig)

def print_lap_times_table(df_static_1, df_static_2):
    st.subheader("Lap Times Comparison")
    
    # Function to parse lap times from a single row
    def parse_lap_times(row):
        if isinstance(row['lap_times'], str):
            return json.loads(row['lap_times'])
        elif isinstance(row['lap_times'], dict):
            return row['lap_times']
        else:
            st.error(f"Unexpected type for lap_times: {type(row['lap_times'])}")
            return {}

    # Parse lap times and extract usernames for both races
    lap_times_1 = parse_lap_times(df_static_1.iloc[0])
    lap_times_2 = parse_lap_times(df_static_2.iloc[0])
    username_1 = df_static_1.iloc[0]['username']
    username_2 = df_static_2.iloc[0]['username']

    # Find the maximum number of laps
    max_laps = max(len(lap_times_1), len(lap_times_2))

    # Create a DataFrame for the lap times
    data = []
    for lap in range(1, max_laps + 1):
        row = {
            'Lap': lap,
            username_1: lap_times_1.get(str(lap), 'N/A'),
            username_2: lap_times_2.get(str(lap), 'N/A')
        }
        data.append(row)
    
    df_lap_times = pd.DataFrame(data)
    
    # Ensure the 'Lap' column is displayed as integers
    df_lap_times['Lap'] = df_lap_times['Lap'].astype(int)
    
    # Display the DataFrame as a table without index
    st.dataframe(df_lap_times.set_index('Lap'))

# Main app logic
# st.subheader("Race 1")
# Create two columns for user inputs
col1, col2 = st.columns(2)

with col1:
    st.subheader("Race 1")
    username1 = st.text_input("Enter username for Race 1:")
    submit_username1 = st.button("Submit Username for Race 1")

    if submit_username1 and username1:
        st.session_state.user_races1 = find_user_races(username1)
        if not st.session_state.user_races1:
            st.error(f"No data found for username: {username1}")
        else:
            st.success(f"Found {len(st.session_state.user_races1)} races for {username1}")

    if 'user_races1' in st.session_state:
        selected_race1 = st.selectbox("Choose a race to visualize for Race 1:", st.session_state.user_races1, key="race_select1")

        if selected_race1:
            load_race_button1 = st.button("Load Selected Race 1")

            if load_race_button1:
                data_load_state1 = st.text('Loading data for Race 1...')
                st.session_state.df_static1, st.session_state.df_dynamic1 = load_data(selected_race1)
                data_load_state1.text('Loading data for Race 1...done!')

with col2:
    st.subheader("Race 2")
    username2 = st.text_input("Enter username for Race 2:")
    submit_username2 = st.button("Submit Username for Race 2")

    if submit_username2 and username2:
        st.session_state.user_races2 = find_user_races(username2)
        if not st.session_state.user_races2:
            st.error(f"No data found for username: {username2}")
        else:
            st.success(f"Found {len(st.session_state.user_races2)} races for {username2}")

    if 'user_races2' in st.session_state:
        selected_race2 = st.selectbox("Choose a race to visualize for Race 2:", st.session_state.user_races2, key="race_select2")

        if selected_race2:
            load_race_button2 = st.button("Load Selected Race 2")

            if load_race_button2:
                data_load_state2 = st.text('Loading data for Race 2...')
                st.session_state.df_static2, st.session_state.df_dynamic2 = load_data(selected_race2)
                data_load_state2.text('Loading data for Race 2...done!')

# Visualization section (outside of columns)
if 'df_static1' in st.session_state and 'df_dynamic1' in st.session_state and \
   'df_static2' in st.session_state and 'df_dynamic2' in st.session_state:
    st.header("Race Comparison")
    

    visualize_data(st.session_state.df_static1, st.session_state.df_dynamic1, 
                   st.session_state.df_static2, st.session_state.df_dynamic2)                    