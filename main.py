import streamlit as st
import pandas as pd
import json
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

st.title('gt7 telemetry data')
DATA_URL = 'data/gt7_telemetry_20240823_2044_52.json'

@st.cache_data
def load_data(DATA_URL):
    # Read the JSON file
    with open(DATA_URL, 'r') as file:
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

data_load_state = st.text('Loading data...')
df_static, df_dynamic = load_data(DATA_URL)
data_load_state.text('Loading data...done!')

# Display the dynamic data
# st.write("df_dynamic head(10):")
# st.write(df_dynamic.head(500))
# Sidebar for navigation
page = st.sidebar.selectbox("Choose a page", ["Overview", "Lap Analysis", "Performance Metrics"])

if page == "Overview":
    st.header("Overview")
    
    # Display static data
    st.subheader("Race Information")
    for column in df_static.columns:
        st.write(f"{column.replace('_', ' ').title()}: {df_static[column][0]}")
    
    # Basic statistics
    st.subheader("Basic Statistics")
    st.write(df_dynamic.describe())
    
    # Data sample
    st.subheader("Data Sample")
    st.dataframe(df_dynamic.head(2000))

# elif page == "Lap Analysis":
    st.header("Lap Analysis")
    
    # Lap time comparison 
    st.subheader("Lap Time Comparison")
    lap_times = df_dynamic.groupby('lap')['current_lap_time'].max()
    fig = px.bar(lap_times, x=lap_times.index, y='current_lap_time', 
                 labels={'current_lap_time': 'Lap Time', 'lap': 'Lap Number'},
                 title='Lap Times Comparison')
    fig.update_layout(height=300)
    st.plotly_chart(fig)
    
    # Lap selection for detailed analysis
    selected_lap = st.selectbox("Select a lap to compare with average", df_dynamic['lap'].unique())
    
    # Prepare data for plotting
    avg_speed = df_dynamic.groupby('lap_index')['speed'].mean().reset_index()
    # avg_speed_f = 
    avg_rpm = df_dynamic.groupby('lap_index')['rpm'].mean().reset_index()
    avg_throttle = df_dynamic.groupby('lap_index')['throttle'].mean().reset_index()
    selected_lap_data = df_dynamic[df_dynamic['lap'] == selected_lap]
    
    # Create the comparison plot
    st.subheader(f"Speed vs Time: Average vs Lap {selected_lap}")
    fig = go.Figure()
    
    # Add average speed trace
    fig.add_trace(go.Scatter(x=avg_speed['lap_index'], y=avg_speed['speed'],
                             mode='lines', name='Average Speed', line=dict(color='blue')))
    
    # Add selected lap speed trace
    fig.add_trace(go.Scatter(x=selected_lap_data['lap_index'], y=selected_lap_data['speed'],
                             mode='lines', name=f'Lap {selected_lap} Speed', line=dict(color='red')))
    
    fig.update_layout(title=f'Speed vs Time: Average vs Lap {selected_lap}',
                      xaxis_title='Lap Time',
                      yaxis_title='Speed',
                      height=300)
    
    st.plotly_chart(fig)

    # Create the RPM comparison plot
    st.subheader(f"RPM vs Time: Average vs Lap {selected_lap}")
    fig_rpm = go.Figure()
    
    fig_rpm.add_trace(go.Scatter(x=avg_rpm['lap_index'], y=avg_rpm['rpm'],
                                 mode='lines', name='Average RPM', line=dict(color='blue')))
    fig_rpm.add_trace(go.Scatter(x=selected_lap_data['lap_index'], y=selected_lap_data['rpm'],
                                 mode='lines', name=f'Lap {selected_lap} RPM', line=dict(color='red')))
    
    fig_rpm.update_layout(title=f'RPM vs Time: Average vs Lap {selected_lap}',
                          xaxis_title='Lap Time',
                          yaxis_title='RPM',
                          height=300)
    
    st.plotly_chart(fig_rpm)

    # Create the throttle comparison plot
    st.subheader(f"Throttle vs Time: Average vs Lap {selected_lap}")
    fig_throttle = go.Figure()
    fig_throttle.add_trace(go.Scatter(x=avg_throttle['lap_index'], y=avg_throttle['throttle'],
                                      mode='lines', name='Average Throttle', line=dict(color='blue')))
    fig_throttle.add_trace(go.Scatter(x=selected_lap_data['lap_index'], y=selected_lap_data['throttle'],
                                      mode='lines', name=f'Lap {selected_lap} Throttle', line=dict(color='red')))
    fig_throttle.update_layout(title=f'Throttle vs Time: Average vs Lap {selected_lap}',
                               xaxis_title='Lap Time', yaxis_title='Throttle', height=250)
    st.plotly_chart(fig_throttle)
    
    # Additional analysis or statistics about the selected lap
    st.subheader(f"Lap {selected_lap} Statistics")
    st.write(selected_lap_data[['speed', 'rpm', 'throttle', 'brake']].describe())

    # Comparison with average
    st.subheader(f"Lap {selected_lap} vs Average")
    avg_stats = df_dynamic[['speed', 'rpm', 'throttle', 'brake']].mean()
    lap_stats = selected_lap_data[['speed', 'rpm', 'throttle', 'brake']].mean()
    comparison = pd.DataFrame({'Lap': lap_stats, 'Average': avg_stats})
    comparison['Difference'] = comparison['Lap'] - comparison['Average']
    st.write(comparison)

elif page == "Performance Metrics":
    st.header("Performance Metrics")
    
    # Speed vs RPM scatter plot
    st.subheader("Speed vs RPM")
    fig = px.scatter(df_dynamic, x='speed', y='rpm', color='lap', 
                     title='Speed vs RPM across all laps')
    st.plotly_chart(fig)
    
    # Throttle and Brake usage
    st.subheader("Throttle and Brake Usage")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_dynamic['lap_index'], y=df_dynamic['throttle'], 
                             mode='lines', name='Throttle'))
    fig.add_trace(go.Scatter(x=df_dynamic['lap_index'], y=df_dynamic['brake'], 
                             mode='lines', name='Brake'))
    fig.update_layout(title='Throttle and Brake Usage Over Time', xaxis_title='Lap Time', yaxis_title='Usage')
    st.plotly_chart(fig)