import streamlit as st
import pandas as pd
import json
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import firebase_admin
from firebase_admin import credentials, storage
import tempfile
import logging
import os
from dotenv import load_dotenv
from visualization import visualize_data
from track_vis import get_course_track, get_course_list

# authentication
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Firebase app (do this only once)
load_dotenv()
st.set_page_config(layout="wide")

# Function to save config
def save_config(config):
    with open('config.yaml', 'w') as file:
        yaml.dump(config, file, default_flow_style=False)

# Load configuration file
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Create an authentication object
authenticator = stauth.Authenticate(
    credentials=config['credentials'],
    cookie_name=config['cookie']['name'],
    cookie_key=config['cookie']['key'],
    cookie_expiry_days=config['cookie']['expiry_days'],
)

def update_query_params(selected_races, selected_laps=None):
    """Update query parameters for both races and laps"""
    try:
        if selected_races:
            races_str = ','.join(selected_races)
            st.query_params['races'] = races_str
            
            # Add lap parameters if provided
            if selected_laps and len(selected_laps) == 2:
                st.query_params['lap1'] = str(selected_laps[0])
                st.query_params['lap2'] = str(selected_laps[1])
        else:
            # Clear parameters if no races selected
            if 'races' in st.query_params:
                del st.query_params['races']
            if 'lap1' in st.query_params:
                del st.query_params['lap1']
            if 'lap2' in st.query_params:
                del st.query_params['lap2']
    except Exception as e:
        st.error(f"Error updating query params: {str(e)}")

def get_selected_races_from_params():
    """Retrieve both races and laps from URL parameters"""
    races_param = st.query_params.get('races', '')
    lap1_param = st.query_params.get('lap1', '')
    lap2_param = st.query_params.get('lap2', '')
    
    races = races_param.split(',') if races_param else []
    laps = None
    if lap1_param and lap2_param:
        try:
            laps = [int(lap1_param), int(lap2_param)]
        except ValueError:
            st.error("Invalid lap parameters in URL")
    
    return races, laps


## UI 
authenticator.login()
if st.session_state["authentication_status"]:
    ## ログイン成功
    # with st.sidebar:
    st.markdown(f'### Welcome *{st.session_state["name"]}*')
    authenticator.logout('Logout', 'main')
    st.divider()

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
    st.title('GT7 Telemetry Data')

    def find_user_races(username):
        blobs = bucket.list_blobs(prefix=f"{username}/")
        file_list = [blob.name for blob in blobs]
        return file_list

    def calculate_average(df):
        tyre_columns = ['tyre_slip_ratio_FL', 'tyre_slip_ratio_FR', 'tyre_slip_ratio_RL', 'tyre_slip_ratio_RR']
        suspension_columns = ['suspension_FL', 'suspension_FR', 'suspension_RL', 'suspension_RR']
        tyre_temp_columns = ['tyre_temp_FL', 'tyre_temp_FR', 'tyre_temp_RL', 'tyre_temp_RR']
        df['tyre_slip_ratio'] = df[tyre_columns].mean(axis=1)
        df['suspension'] = df[suspension_columns].mean(axis=1)
        df['tyre_temp'] = df[tyre_temp_columns].mean(axis=1)
        return df

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
        
        # Calculate average for specific telemtry after populating the DataFrame
        df_dynamic = calculate_average(df_dynamic)
        
        return df_static, df_dynamic

    # Main app logic
    def handle_race_input():
      # Initialize selected_races and laps from query parameters
      if 'selected_races' not in st.session_state:
        races_from_params, laps_from_params = get_selected_races_from_params()
        st.session_state['selected_races'] = races_from_params if races_from_params != [''] else []
        if laps_from_params:
            st.session_state['selected_laps'] = laps_from_params
      
      col1, col2 = st.columns([1, 2])

      with col1:
          st.subheader("Search for JSON Files")
          with st.form(key='race_form'):
              username = st.text_input("Enter username to search races:", key='username')
              submit_username = st.form_submit_button("Search")

              if submit_username and username:
                  st.write(f"Searching for races for user: {username}")
                  user_races = find_user_races(username)
                  if not user_races:
                      st.error(f"No data found for username: {username}")
                  else:
                      st.success(f"Found {len(user_races)} races for {username}")
                      st.session_state['user_races'] = user_races

      with col2:
          if 'user_races' in st.session_state:
              st.subheader("Search Results")
              selected_race = st.selectbox("Choose a race to add:", st.session_state['user_races'])
              add_race = st.button(f"Add {selected_race} to Visualize")

              if add_race:
                  if len(st.session_state['selected_races']) < 2:
                      if selected_race not in st.session_state['selected_races']:
                          st.write("Adding race to selected_races")
                          st.session_state['selected_races'].append(selected_race)
                          update_query_params(st.session_state['selected_races'])
                      else:
                          st.warning(f"{selected_race} is already added.")
                  else:
                      st.warning("You can select up to 2 races.")

          st.subheader("Selected JSON Files")
          if st.session_state['selected_races']:
              for race in st.session_state['selected_races']:
                  col_race, col_remove = st.columns([4, 1])
                  with col_race:
                      st.write(race)
                  with col_remove:
                      remove_button = st.button("Remove", key=f'remove_{race}')
                      if remove_button:
                          st.session_state['selected_races'].remove(race)
                          update_query_params(st.session_state['selected_races'])
                          st.session_state['visualize_ready'] = False
          else:
              st.write("No files selected yet.")

      if len(st.session_state['selected_races']) == 2:
          st.write("Two races selected, enabling visualization")
          st.session_state['visualize_ready'] = True
    
    handle_race_input()

    course_track_directory = 'course_track'
    course_track_options = get_course_list(course_track_directory)

    if course_track_options:
        selected_course_track = st.selectbox("Select Course Track for Both Races:", course_track_options, key="course_track")
        course_track_data = get_course_track(os.path.join(course_track_directory, selected_course_track))
    else:
        st.error("No course tracks available")
        course_track_data = None


    if 'visualize_ready' in st.session_state and st.session_state['visualize_ready']:
      st.success("Visualizing data")

      df_static_list = []
      df_dynamic_list = []
      
      for index, race in enumerate(st.session_state['selected_races']):
          df_static, df_dynamic = load_data(race)
          st.session_state[f'df_static{index+1}'] = df_static
          st.session_state[f'df_dynamic{index+1}'] = df_dynamic
          df_static_list.append(df_static)
          df_dynamic_list.append(df_dynamic)

      all_metrics = [
            ('speed', '現在の速度 (km/h)'),
            ('rpm', 'エンジン回転数 (rpm)'),
            ('throttle', 'アクセル (%)'),
            ('brake', 'ブレーキ (%)'),
            ('current_gear', '現在のギア'),
            ('oil_pressure', 'オイル圧 (bar)'),
            ('current_fuel', '現在の燃料量 (L)'),
            ('boost', 'ブースト圧 (kPa)'),
            ('clutch', 'クラッチ'),
            ('clutch_engaged', 'クラッチ接続'),
            ('rpm_after_clutch', 'クラッチ後のRPM (rpm)'),
            ('oil_temp', 'オイル温度 (°C)'),
            ('water_temp', '水温 (°C)'),
            ('ride_height', '車高 (mm)'),
            ('position_x', '位置X (m)'),
            ('position_y', '位置Y (m)'),
            ('position_z', '位置Z (m)'),
            ('velocity_x', '速度X (m/s)'),
            ('velocity_y', '速度Y (m/s)'),
            ('velocity_z', '速度Z (m/s)'),
            ('rotation_pitch', '回転（ピッチ）'),
            ('rotation_yaw', '回転（ヨー）'),
            ('rotation_roll', '回転（ロール）'),
            ('rotation_w', '回転W クォータニオンのW成分'),
            ('angular_velocity_x', '角速度X (rad/s)'),
            ('angular_velocity_y', '角速度Y (rad/s)'),
            ('angular_velocity_z', '角速度Z (rad/s)'),
            ('road_plane_x', '路面平面X'),
            ('road_plane_y', '路面平面Y'),
            ('road_plane_z', '路面平面Z'),
            ('road_plane_m', '路面平面M')
        ]

      # Initialize with laps from URL if available
      if 'selected_laps' in st.session_state:
          st.session_state['initial_laps'] = st.session_state['selected_laps']
      

      visualize_data(df_static_list[0], df_dynamic_list[0], df_static_list[1], df_dynamic_list[1], all_metrics, course_track_data, update_query_params)
      st.session_state['visualize_ready'] = False


elif st.session_state["authentication_status"] is False:
    ## ログイン成功ログイン失敗
    st.error('Username/password is incorrect')

elif st.session_state["authentication_status"] is None:
    ## デフォルト
    css_layout_centered = """
    <style>
        .block-container {
            max-width: 800px;
        }
    </style>
    """
    st.markdown(css_layout_centered, unsafe_allow_html=True)
    st.warning('Please enter your username and password')

    # Initialize 'show_signup' in session_state if it doesn't exist
    if 'show_signup' not in st.session_state:
        st.session_state['show_signup'] = False

    # "Sign Up" button
    signup_page = st.button("Sign Up")

    if signup_page:
        # Set 'show_signup' to True when the button is clicked
        st.session_state['show_signup'] = True

    if st.session_state['show_signup']:
        # Display the sign-up form
        with st.form("signup_form"):
            st.subheader("Sign Up")
            new_username = st.text_input("Username")
            new_name = st.text_input("Full Name")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            signup_button = st.form_submit_button("Submit")

            if signup_button:
                if new_password == confirm_password:
                    if new_username not in config['credentials']['usernames']:
                        # Hash the password
                        hashed_password = stauth.Hasher([new_password]).generate()[0]

                        # Add new user to config
                        config['credentials']['usernames'][new_username] = {
                            'email': new_email,
                            'name': new_name,
                            'password': hashed_password
                        }

                        # Save updated config
                        save_config(config)

                        st.success("You have successfully signed up! Please log in.")
                        # Reset 'show_signup' to hide the form
                        st.session_state['show_signup'] = False
                    else:
                        st.error("Username already exists. Please choose a different username.")
                else:
                    st.error("Passwords do not match.")
    else:
        # You can place your login form here or other content
        pass