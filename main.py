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
st.set_page_config(layout="wide")
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

def create_comparison_plot(df1, df2, x_column, y_column, title, selected_lap, col, username1, username2):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df1[x_column], y=df1[y_column], mode='lines', name=f'{username1}', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df2[x_column], y=df2[y_column], mode='lines', name=f'{username2}', line=dict(color='red')))
    fig.update_layout(title=title, xaxis_title='Lap Progress', yaxis_title=title, height=300)
    col.plotly_chart(fig, use_container_width=True)

def visualize_data(df_static_1, df_dynamic_1, df_static_2, df_dynamic_2, metrics):
    print_lap_times_table(df_static_1, df_static_2)

    selected_lap = st.selectbox("比較するラップを選択してください:", 
                                df_dynamic_1['lap'].unique(), key="lap_select")

    # データの準備
    selected_lap_data_1 = df_dynamic_1[df_dynamic_1['lap'] == selected_lap]
    selected_lap_data_2 = df_dynamic_2[df_dynamic_2['lap'] == selected_lap]

    # ユーザー名の取得
    username1 = df_static_1['username'].iloc[0]
    username2 = df_static_2['username'].iloc[0]

    # 2列のレイアウトを作成
    for i in range(0, len(metrics), 2):
        col1, col2 = st.columns(2)
        
        # 左列のプロット
        create_comparison_plot(selected_lap_data_1, selected_lap_data_2, 'lap_index', 
                               metrics[i][0], metrics[i][1], selected_lap, 
                               col1, username1, username2)
        
        # 右列のプロット（存在する場合）
        if i + 1 < len(metrics):
            create_comparison_plot(selected_lap_data_1, selected_lap_data_2, 'lap_index', 
                                   metrics[i+1][0], metrics[i+1][1], selected_lap, 
                                   col2, username1, username2)
            
# Function to print lap times as a table
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
def handle_race_input(col, race_number):
    with col:
        st.markdown(
            f"""
            <style>
                div[data-testid="column"] > div:has(div.stButton) {{
                    background-color: white;
                    padding: 32px;
                    border-radius: 8px;
                    margin-top: 32px;
                    margin-bottom: 16px;
                    border: 1px solid #dcdcdc;
                }}
            </style>
            """,
            unsafe_allow_html=True
        )

        st.subheader(f"Race {race_number}")
        
        # Custom CSS for text input
        input_style = """
        <style>
        div[data-baseweb="input"] input {
            # background-color: white !important;
        }
        div[data-baseweb="input"] {
            max-width: 400px !important;
        }
        div[data-baseweb="select"] {
            width: 400px !important;
            max-width: 100% !important;
            # background-color: white !important;
        }
        div[data-baseweb="stNotificationContentSuccess"] {
            width: 400px !important;
            # background-color: white !important;
        }
        div[data-baseweb="input"]:hover, div[data-baseweb="input"]:focus-within {
            border-color: #80bdff !important;
            box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25) !important;
        }
        </style>
        """
        st.markdown(input_style, unsafe_allow_html=True)

        # st.subheader(f"Race {race_number}")
        username = st.text_input(f"Enter username for Race {race_number}:")
        submit_username = st.button(f"Submit Username for Race {race_number}")

        if submit_username and username:
            user_races = find_user_races(username)
            if not user_races:
                st.error(f"No data found for username: {username}")
            else:
                st.success(f"Found {len(user_races)} races for {username}")
                st.session_state[f'user_races{race_number}'] = user_races

        if f'user_races{race_number}' in st.session_state:
            selected_race = st.selectbox(f"Choose a race to visualize for Race {race_number}:", 
                                         st.session_state[f'user_races{race_number}'], 
                                         key=f"race_select{race_number}")

            if selected_race:
                load_race_button = st.button(f"Load Selected Race {race_number}")

                if load_race_button:
                    data_load_state = st.text(f'Loading data for Race {race_number}...')
                    df_static, df_dynamic = load_data(selected_race)
                    st.session_state[f'df_static{race_number}'] = df_static
                    st.session_state[f'df_dynamic{race_number}'] = df_dynamic
                    data_load_state.text(f'Loading data for Race {race_number}...done!')

    return username, selected_race if 'selected_race' in locals() else None

# Usage in main app logic
col1, col2 = st.columns(2)

username1, selected_race1 = handle_race_input(col1, 1)
username2, selected_race2 = handle_race_input(col2, 2)


if all(key in st.session_state for key in ['df_static1', 'df_dynamic1', 'df_static2', 'df_dynamic2']):
    st.header("レース比較")

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

    # 全ての指標を使用してデータを可視化
    visualize_data(st.session_state.df_static1, st.session_state.df_dynamic1, 
                   st.session_state.df_static2, st.session_state.df_dynamic2,
                   all_metrics)
else:
    st.warning("両方のレースのデータをロードしてから、比較を行ってください。")