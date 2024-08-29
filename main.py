import os
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

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Firebase app (do this only once)
@st.cache_resource
# def initialize_firebase():
#     if not firebase_admin._apps:
#         cred = credentials.Certificate("cred/serviceAccountKey.json")
#         firebase_admin.initialize_app(cred, {'storageBucket': 'mint-poc-p1.appspot.com'})
#     return storage.bucket()

# # Use the function to initialize Firebase and get the bucket
# bucket = initialize_firebase()


# When to deploy the app, you can use the following code snippet:
def initialize_firebase():
    if not firebase_admin._apps:
        # Load the Firebase configuration from Streamlit secrets
        firebase_config = st.secrets["firebase"]
        
        # Create a temporary file to store the Firebase configuration
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            json.dump(firebase_config, temp_file)
            temp_file_path = temp_file.name

        # Initialize Firebase with the temporary file
        cred = credentials.Certificate(temp_file_path)
        firebase_admin.initialize_app(cred, {'storageBucket': 'mint-poc-p1.appspot.com'})
        
        # Remove the temporary file
        os.unlink(temp_file_path)

    return storage.bucket()

# Use the function to initialize Firebase and get the bucket
bucket = initialize_firebase()


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

def visualize_data(df_static_1, df_dynamic_1, df_static_2, df_dynamic_2, selected_lap):
    st.header("Overview")
    # Display static data for both races
    st.subheader("Race 1 Information")
    st.write(df_static_1.head())

    st.subheader("Race 2 Information")
    st.write(df_static_2.head())

    # Lap time comparison for both races
    lap_times_1 = df_dynamic_1.groupby('lap')['current_lap_time'].max()
    lap_times_2 = df_dynamic_2.groupby('lap')['current_lap_time'].max()

    fig = go.Figure()
    fig.add_trace(go.Bar(x=lap_times_1.index, y=lap_times_1, name='Race 1'))
    fig.add_trace(go.Bar(x=lap_times_2.index, y=lap_times_2, name='Race 2'))
    fig.update_layout(title='Lap Times Comparison', xaxis_title='Lap Number', yaxis_title='Lap Time', height=300)
    st.plotly_chart(fig)

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

# Main app logic
st.subheader("Race 1")
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
    selected_lap = st.selectbox("Select a lap to compare:", 
                                st.session_state.df_dynamic1['lap'].unique(), key="lap_select")

    visualize_data(st.session_state.df_static1, st.session_state.df_dynamic1, 
                   st.session_state.df_static2, st.session_state.df_dynamic2, selected_lap)                    