import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.graph_objects as go
from scipy.signal import find_peaks
from track_vis import get_course_list, get_course_track



course_track_directory = 'course_track'

def create_comparison_plot(df1, df2, x_column, y_column, title, selected_lap, col, username1, username2):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df1[x_column], y=df1[y_column], mode='lines', name=f'{username1}', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df2[x_column], y=df2[y_column], mode='lines', name=f'{username2}', line=dict(color='red')))
    fig.update_layout(title=title, xaxis_title='Lap Progress', yaxis_title=title, height=300)
    col.plotly_chart(fig, use_container_width=True)


def create_simple_race_line_plot(df1, df2, selected_lap, username1, username2):
    df1_reduced = df1.iloc[::20, :]  # Take every xrd point instead of every 5th
    df2_reduced = df2.iloc[::20, :]

    fig = go.Figure()

    def create_user_trace(df, username, color, line_width, opacity=1):
        trace = go.Scatter(
            x=df['position_x'],
            y=df['position_z'],
            mode='lines',
            name=username,
            line=dict(color=color, width=line_width),
            opacity=opacity,
            text=[f"Throttle: {t:.2f}, Brake: {b:.2f}" for t, b in zip(df['throttle'], df['brake'])],
            hoverinfo='text'
        )
        return trace

    # Add trace for user 1 (thinner line)
    fig.add_trace(create_user_trace(df1_reduced, username1, 'blue', 3))

    # Add trace for user 2 (thicker, semi-transparent line)
    fig.add_trace(create_user_trace(df2_reduced, username2, 'red', 9, opacity=0.4))

    # Add speed annotations
    add_speed_annotations(fig, df1, username1, is_reference=False, add_start=True)
    add_speed_annotations(fig, df2, username1, is_reference=True, add_start=False)
    fig.update_layout(
        title=f'Combined Annotated Race Lines: Lap {selected_lap}',
        # xaxis_title='X Position',
        # yaxis_title='Z Position',
        showlegend=True,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        yaxis=dict(scaleanchor="x", scaleratio=1, autorange="reversed"),
        # axis scaling
        margin=dict(l=0, r=0, t=30, b=0),
    )

    return fig

def add_speed_annotations(fig, df, username, is_reference=False, add_start=False):
    speed = df['speed'].values
    
    # Simple peak and valley detection
    peaks, _ = find_peaks(speed, distance=480, prominence=1)
    valleys, _ = find_peaks(-speed, distance=480, prominence=1)

    max_annotations = 20
    peaks = peaks[:max_annotations]
    valleys = valleys[:max_annotations]

    # Determine text format based on whether it is a reference user or not
    def format_annotation_text(username, speed, is_peak, is_reference):
        direction = "▴" if is_peak else "▾"
        if is_reference:
            return f"(Ref): {speed:.0f}{direction}"
            # return f"(Ref){username}: {speed:.0f}{direction}"
        else:
            # return f"{speed:.0f}{direction}"
            return f"{username}: {speed:.0f}{direction}"

    # Assign colors based on whether it is a peak (high speed) or valley (low speed)
    def assign_color(is_peak):
        return 'blue' if is_peak else 'red'  # Blue for peaks (top speed), red for valleys (slowest)

    # Add annotations for peaks (top speed)
    for i in peaks:
        fig.add_annotation(
            x=df['position_x'].iloc[i],
            y=df['position_z'].iloc[i],
            text=format_annotation_text(username, speed[i], is_peak=True, is_reference=is_reference),
            showarrow=False,
            font=dict(color=assign_color(is_peak=True), size=10),
            bgcolor="white",
            opacity=0.8
        )

    # Add annotations for valleys (slow speed)
    for i in valleys:
        fig.add_annotation(
            x=df['position_x'].iloc[i],
            y=df['position_z'].iloc[i],
            text=format_annotation_text(username, speed[i], is_peak=False, is_reference=is_reference),
            showarrow=False,
            font=dict(color=assign_color(is_peak=False), size=10),
            bgcolor="white",
            opacity=0.8
        )

    # Add a "START" annotation if specified
    if add_start and len(df) > 0:
        fig.add_annotation(x=df['position_x'].iloc[0], y=df['position_z'].iloc[0], text="START", showarrow=False)


def add_user_trace(fig, df, username, line_width, opacity=1):
    def assign_color(throttle, brake):
        if throttle > 0 and throttle > brake:
            return 'blue'
        elif brake > 0 and brake > throttle:
            return 'red'
        else:
            return 'green'

    for i in range(len(df) - 1):
        color = assign_color(df['throttle'].iloc[i], df['brake'].iloc[i])
        fig.add_trace(go.Scatter(
            x=[df['position_x'].iloc[i], df['position_x'].iloc[i + 1]],
            y=[df['position_z'].iloc[i], df['position_z'].iloc[i + 1]],
            mode='lines',
            line=dict(color=color, width=line_width),
            opacity=opacity,
            name=username if i == 0 else '',  # Show legend once
            showlegend=(i == 0),
            hoverinfo='text',
            text=f"Throttle: {df['throttle'].iloc[i]:.2f}, Brake: {df['brake'].iloc[i]:.2f}"
        ))

def create_colored_race_line(df1, df2, selected_lap, username1, username2):
    df1_reduced = df1.iloc[::8, :]  # Take every nth point
    df2_reduced = df2.iloc[::8, :]
    fig = go.Figure()

    def assign_color(throttle, brake):
        if throttle > 0 and throttle > brake:
            return 'blue'
        elif brake > 0 and brake > throttle:
            return 'red'
        else:
            return 'green'

    # Add trace
    add_user_trace(fig, df1_reduced, username1, line_width=1)
    add_user_trace(fig, df2_reduced, username2, line_width=1, opacity=0.4)

    # Add speed annotations
    add_speed_annotations(fig, df1, username1, is_reference=False, add_start=True)
    add_speed_annotations(fig, df2, username2, is_reference=True, add_start=False)

    fig.update_layout(
        title=f'Detailed Race Lines: Lap {selected_lap}',
        xaxis_title='X Position',
        yaxis_title='Z Position',
        showlegend=True,
        yaxis=dict(scaleanchor="x", scaleratio=1),
        margin=dict(l=0, r=0, t=30, b=0),
    )

    return fig

def create_colored_race_line_with_coursetrack(lap_data_1, lap_data_2, selected_lap, username1, username2, course_track_data, width=800, height=600):
    # Create a new figure for the combined plot
    race_line_fig = go.Figure()

    # First, add the course track (road) plot behind everything else
    course_track_fig = get_course_track(course_track_data)
    for trace in course_track_fig['data']:
        race_line_fig.add_trace(trace)

    # Now, add the race line plot on top of the course track
    race_line_detail = create_colored_race_line(lap_data_1, lap_data_2, selected_lap, username1, username2)
    for trace in race_line_detail['data']:
        race_line_fig.add_trace(trace)

    # Update layout for the combined plot (if necessary)
    race_line_fig.update_layout(
        title=f"Race Line and Course Track for Lap {selected_lap}",
        # xaxis_title="X Axis",
        # yaxis_title="Y Axis",
        showlegend=False,
        autosize=False,  # Disable autosizing so that the specified width and height are used
        width=width,   # Set the plot width
        height=height, # Set the plot height
        yaxis_scaleanchor="x",  # Maintain aspect ratio by linking x and y axis scaling
        xaxis=dict(
            scaleanchor="y",   # Ensures the plot maintains its aspect ratio
        )
    )

    # Add speed annotations
    add_speed_annotations(race_line_fig, lap_data_1, username1, is_reference=False, add_start=True)
    add_speed_annotations(race_line_fig, lap_data_2, username2, is_reference=True, add_start=False)

    return race_line_fig

# Function to print lap times as a table
def print_lap_times_table(df_static_1, df_static_2):
    st.markdown("Lap Times Comparison")
    
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


def visualize_data(df_static_1, df_dynamic_1, df_static_2, df_dynamic_2, selected_plots):
    # Display lap times table
    print_lap_times_table(df_static_1, df_static_2)

    # Lap selection for race 1
    selected_lap_1 = st.selectbox(f"{df_static_1['username'].iloc[0]} のラップを選択してください:", 
                                  df_dynamic_1['lap'].unique(), key="lap_select_1")
    
    # Lap selection for race 2
    selected_lap_2 = st.selectbox(f"{df_static_2['username'].iloc[0]} のラップを選択してください:", 
                                  df_dynamic_2['lap'].unique(), key="lap_select_2")
    
    # Get the list of available course track JSON files (filenames only)
    course_track_options = get_course_list(course_track_directory)

    # Validate if there are course track options available
    if not course_track_options:
        st.error("No course track files found.")
        return

    # Let the user select the course track from the available options
    selected_course_track_file = st.selectbox("表示するコーストラックを選択してください:",
                                              course_track_options, key="track_select")

    # Validate the selected course track file
    if not selected_course_track_file:
        st.error("Please select a valid course track.")
        return

    # Load the selected course track JSON data
    selected_course_track_data = os.path.join(course_track_directory, selected_course_track_file)

    # Verify if the course track file exists
    if not os.path.exists(selected_course_track_data):
        st.error(f"The selected course track file {selected_course_track_file} does not exist.")
        return

    # course_track_fig = get_course_track(selected_course_track_data)
    
    # Filter data for the selected lap for each race
    selected_lap_data_1 = df_dynamic_1[df_dynamic_1['lap'] == selected_lap_1]
    selected_lap_data_2 = df_dynamic_2[df_dynamic_2['lap'] == selected_lap_2]

    # Get usernames from static data
    username1 = df_static_1['username'].iloc[0]
    username2 = df_static_2['username'].iloc[0]

    # Visualize race line with course track
    detail_race_line_plot_with_coursetrack = create_colored_race_line_with_coursetrack(
        selected_lap_data_1, selected_lap_data_2, selected_lap_1, username1, username2, selected_course_track_data, width=600, height=600
    )
    st.plotly_chart(detail_race_line_plot_with_coursetrack, use_container_width=True)
    st.write(f"表示されているコース: **{selected_course_track_file}**")

    # Visualize other plots in two-column layout
    for i in range(0, len(selected_plots), 2):
        col1, col2 = st.columns(2)
        
        create_comparison_plot(selected_lap_data_1, selected_lap_data_2, 'lap_index', 
                               selected_plots[i][0], selected_plots[i][1], selected_lap_1, 
                               col1, username1, username2)
        
        if i + 1 < len(selected_plots):
            create_comparison_plot(selected_lap_data_1, selected_lap_data_2, 'lap_index', 
                                   selected_plots[i+1][0], selected_plots[i+1][1], selected_lap_1, 
                                   col2, username1, username2)
