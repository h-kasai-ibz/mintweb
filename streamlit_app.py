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

## UI 
# authenticator.login()
# if st.session_state["authentication_status"]:

## ログイン成功
# with st.sidebar:
st.markdown(f'### Welcome *{st.session_state["name"]}*')
# authenticator.logout('Logout', 'main')
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
    # blob = bucket.blob(file_name)
    # _, temp_local_filename = tempfile.mkstemp()
    # blob.download_to_filename(temp_local_filename)

    with open(file_name, 'r') as file:
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

# # Main app logic
# def handle_race_input(col, race_number):
#   with col:
#       st.markdown(
#           f"""
#           <style>
#               div[data-testid="column"] > div:has(div.stButton) {{
#                   background-color: white;
#                   padding: 32px 64px;
#                   border-radius: 8px;
#                   margin-top: 32px;
#                   margin-bottom: 16px;
#                   border: 1px solid #dcdcdc;
#               }}
#           </style>
#           """,
#           unsafe_allow_html=True
#       )

#       st.subheader(f"Race {race_number}")
      
#       # Custom CSS for text input
#       input_style = """
#       <style>
#       div[data-baseweb="input"] {
#           max-width: 400px !important;
#       }
#       div[data-baseweb="select"] {
#           max-width: 400px !important;
#       }
#       div[data-baseweb="stNotificationContentSuccess"] {
#           width: 400px !important;
#           # background-color: white !important;
#       }
#       div[data-baseweb="input"]:hover, div[data-baseweb="input"]:focus-within {
#           border-color: #80bdff !important;
#           box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25) !important;
#       }
#       div[data-testid="stForm"] {
#                   border: none;
#                   max-width: 400px;
#                   min-height: 240px;
#                   padding: 0;
#               }
#       div[data-testid="stVerticalBlockBorderWrapper"] {
#                   margin: 0;
#               }
#       </style>
#       """
#       st.markdown(input_style, unsafe_allow_html=True)

#       with st.form(key=f'race_form_{race_number}'):
#           username = st.text_input(f"Enter username for Race {race_number}:", key=f'username_{race_number}')
#           submit_username = st.form_submit_button(f"Submit Username for Race {race_number}")

#           if submit_username and username:
#               user_races = find_user_races(username)
#               if not user_races:
#                   st.error(f"No data found for username: {username}")
#               else:
#                   st.success(f"Found {len(user_races)} races for {username}")
#                   st.session_state[f'user_races{race_number}'] = user_races

#           if f'user_races{race_number}' in st.session_state:
#               selected_race = st.selectbox(f"Choose a race to visualize for Race {race_number}:", 
#                                            st.session_state[f'user_races{race_number}'], 
#                                            key=f"race_select{race_number}")

#               if selected_race:
#                   load_race_button = st.form_submit_button(f"Load Selected Race {race_number}")

#                   if load_race_button:
#                       data_load_state = st.text(f'Loading data for Race {race_number}...')
#                       df_static, df_dynamic = load_data(selected_race)
#                       st.session_state[f'df_static{race_number}'] = df_static
#                       st.session_state[f'df_dynamic{race_number}'] = df_dynamic
#                       data_load_state.text(f'Loading data for Race {race_number}...done!')

#   return username, selected_race if 'selected_race' in locals() else None

# Usage in main app logic
# col1, col2 = st.columns(2)

# username1, selected_race1 = handle_race_input(col1, 1)
# username2, selected_race2 = handle_race_input(col2, 2)

course_track_directory = 'course_track'

# Main app logic
def handle_race_input(col, race_number, json_file_path):
    with col:
        st.subheader(f"Race {race_number}")

        # Custom CSS for input styling
        input_style = '''
        <style>
        div[data-baseweb="input"], div[data-baseweb="select"] {
            max-width: 400px !important;
        }
        </style>
        '''
        st.markdown(input_style, unsafe_allow_html=True)

        if st.button(f"Load Race {race_number} Data"):
            data_load_state = st.text(f'Loading data for Race {race_number}...')
            df_static, df_dynamic = load_data(json_file_path)
            st.session_state[f'df_static{race_number}'] = df_static
            st.session_state[f'df_dynamic{race_number}'] = df_dynamic
            data_load_state.text(f'Loading data for Race {race_number}...done!')
    
    return df_static['username'].iloc[0] if 'df_static' in locals() else f"User {race_number}", json_file_path

# Usage in main app logic
col1, col2 = st.columns(2)

# Example paths to JSON files (replace with actual files)
json_file_1 = "data/suzuka_01.json"
json_file_2 = "data/suzuka_02.json"

# Handle input for both races
username1, selected_race1 = handle_race_input(col1, 1, json_file_1)
username2, selected_race2 = handle_race_input(col2, 2, json_file_2)

# Single course track selection (appears only once for both races)
course_track_options = get_course_list(course_track_directory)

if course_track_options:
    selected_course_track = st.selectbox("Select Course Track for Both Races:", course_track_options, key="course_track")
    course_track_data = get_course_track(os.path.join(course_track_directory, selected_course_track))
else:
    st.error("No course tracks available")
    course_track_data = None

if all(key in st.session_state for key in ['df_static1', 'df_dynamic1', 'df_static2', 'df_dynamic2']) and course_track_data:
    st.subheader("Race Comparison")

    # 全ての指標のリスト
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
        # ('ride_height', '車高 (mm)'),
        # ('position_x', '位置X (m)'),
        # ('position_y', '位置Y (m)'),
        # ('position_z', '位置Z (m)'),
        ('velocity_x', '速度X (m/s)'),
        ('velocity_y', '速度Y (m/s)'),
        ('velocity_z', '速度Z (m/s)'),
        ('rotation_pitch', '回転（ピッチ）'),
        ('rotation_yaw', '回転（ヨー）'),
        ('rotation_roll', '回転（ロール）'),
        # ('rotation_w', '回転W クォータニオンのW成分'),
        ('angular_velocity_x', '角速度X (rad/s)'),
        ('angular_velocity_y', '角速度Y (rad/s)'),
        ('angular_velocity_z', '角速度Z (rad/s)'),
        # ('road_plane_x', '路面平面X'),
        # ('road_plane_y', '路面平面Y'),
        # ('road_plane_z', '路面平面Z'),
        # ('road_plane_m', '路面平面M')
    ]

    # Race Line の可視化を含めて全てのデータを可視化
    visualize_data(st.session_state.df_static1, st.session_state.df_dynamic1, 
                   st.session_state.df_static2, st.session_state.df_dynamic2,
                   all_metrics, course_track_data)
else:
    st.warning("両方のレースのデータをロードして、比較を行ってください。")


# elif st.session_state["authentication_status"] is False:
#     ## ログイン成功ログイン失敗
#     st.error('Username/password is incorrect')

# elif st.session_state["authentication_status"] is None:
#     ## デフォルト
#     css_layout_centered = """
#     <style>
#         .block-container {
#             max-width: 800px;
#         }
#     </style>
#     """
#     st.markdown(css_layout_centered, unsafe_allow_html=True)
#     st.warning('Please enter your username and password')

#     # Initialize 'show_signup' in session_state if it doesn't exist
#     if 'show_signup' not in st.session_state:
#         st.session_state['show_signup'] = False

#     # "Sign Up" button
#     signup_page = st.button("Sign Up")

#     if signup_page:
#         # Set 'show_signup' to True when the button is clicked
#         st.session_state['show_signup'] = True

#     if st.session_state['show_signup']:
#         # Display the sign-up form
#         with st.form("signup_form"):
#             st.subheader("Sign Up")
#             new_username = st.text_input("Username")
#             new_name = st.text_input("Full Name")
#             new_email = st.text_input("Email")
#             new_password = st.text_input("Password", type="password")
#             confirm_password = st.text_input("Confirm Password", type="password")
#             signup_button = st.form_submit_button("Submit")

#             if signup_button:
#                 if new_password == confirm_password:
#                     if new_username not in config['credentials']['usernames']:
#                         # Hash the password
#                         hashed_password = stauth.Hasher([new_password]).generate()[0]

#                         # Add new user to config
#                         config['credentials']['usernames'][new_username] = {
#                             'email': new_email,
#                             'name': new_name,
#                             'password': hashed_password
#                         }

#                         # Save updated config
#                         save_config(config)

#                         st.success("You have successfully signed up! Please log in.")
#                         # Reset 'show_signup' to hide the form
#                         st.session_state['show_signup'] = False
#                     else:
#                         st.error("Username already exists. Please choose a different username.")
#                 else:
#                     st.error("Passwords do not match.")
#     else:
#         # You can place your login form here or other content
#         pass