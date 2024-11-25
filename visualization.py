import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.graph_objects as go
from scipy.signal import find_peaks
from track_vis import get_course_list, get_course_track
from datetime import datetime

def create_comparison_plot(df1, df2, x_column, y_column, title, selected_lap, col, username1, username2):
    if username1 == username2:
      username2 = "(Ref)" + username2
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df1[x_column], y=df1[y_column], mode='lines', name=f'{username1}', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df2[x_column], y=df2[y_column], mode='lines', name=f'{username2}', line=dict(color='red')))
    fig.update_layout(
        title=title,
        xaxis_title='Time (sec)',
        yaxis_title=title,
        height=300
    )
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
    add_user_trace(fig, df2_reduced, username2, line_width=6, opacity=0.4)

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
    if isinstance(course_track_data, go.Figure):
        for trace in course_track_data.data:
            race_line_fig.add_trace(trace)
    elif isinstance(course_track_data, list):
        for trace in course_track_data:
            race_line_fig.add_trace(trace)
    else:
        st.warning("Course track data is not in the expected format. Skipping course track visualization.")

    # Now, add the race line plot on top of the course track
    race_line_detail = create_colored_race_line(lap_data_1, lap_data_2, selected_lap, username1, username2)
    for trace in race_line_detail['data']:
        race_line_fig.add_trace(trace)

    # Update layout for the combined plot
    race_line_fig.update_layout(
        title=f"Race Line and Course Track for Lap {selected_lap}",
        showlegend=False,
        autosize=False,
        width=width,
        height=height,
        yaxis_scaleanchor="x",
        xaxis=dict(scaleanchor="y")
    )

    # Add speed annotations
    add_speed_annotations(race_line_fig, lap_data_1, username1, is_reference=False, add_start=True)
    add_speed_annotations(race_line_fig, lap_data_2, username2, is_reference=True, add_start=False)

    return race_line_fig

# Function to print lap times as a table
def print_lap_times_table(df_static_1, df_static_2, df_dynamic_1, df_dynamic_2):
    st.markdown("Lap Times Comparison")

    # Helper function to extract the last 'current_lap_time' for each lap
    def extract_lap_times(df_dynamic):
        lap_times = {}
        unique_laps = df_dynamic['lap'].unique()
        for lap in unique_laps:
            # Filter data for the current lap and get the last 'current_lap_time'
            lap_data = df_dynamic[df_dynamic['lap'] == lap]
            last_lap_time = lap_data['current_lap_time'].iloc[-1]
            lap_times[str(lap)] = last_lap_time
        return lap_times

    # Extract lap times and usernames for both races
    lap_times_1 = extract_lap_times(df_dynamic_1)
    lap_times_2 = extract_lap_times(df_dynamic_2)
    username_1 = df_static_1['username'].iloc[0] 
    username_2 = df_static_2['username'].iloc[0]
    if username_1 == username_2:
      username_2 = "(Ref)" + username_2

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


course_track_directory = 'course_track'

def get_lap_times_and_fastest(df_dynamic):
    """
    Extract lap times and identify the fastest lap
    Returns a dictionary of lap times and the fastest lap number
    """
    lap_times = {}
    for lap in df_dynamic['lap'].unique():
        # Get the final frame's current_lap_time for each lap
        lap_time = df_dynamic[df_dynamic['lap'] == lap]['current_lap_time'].iloc[-1]
        lap_times[lap] = lap_time
    
    # Find the fastest lap
    fastest_lap = min(lap_times.items(), key=lambda x: x[1])[0]
    return lap_times, fastest_lap

def create_lap_options(df_dynamic):
    """
    Create formatted options for lap selection dropdown
    Returns list of tuples (lap_number, display_text)
    """
    lap_times, fastest_lap = get_lap_times_and_fastest(df_dynamic)
    
    # Format each lap option, adding (fastest) to the fastest lap
    lap_options = []
    for lap in sorted(lap_times.keys()):
        display_text = f"Lap {lap} - {lap_times[lap]:.3f}s"
        if lap == fastest_lap:
            display_text += " (fastest)"
        lap_options.append((lap, display_text))
    
    return lap_options

def visualize_data(df_static_1, df_dynamic_1, df_static_2, df_dynamic_2, selected_plots, course_track_options, update_query_params):
    # Display lap times table
    username1 = df_static_1['username'].iloc[0]
    username2 = df_static_2['username'].iloc[0]
    if username1 == username2:
        display_username2 = f"(Ref){username2}"
    else:
        display_username2 = username2
    print_lap_times_table(df_static_1, df_static_2, df_dynamic_1, df_dynamic_2)

    # Create lap options with fastest lap indicator
    lap_options_1 = create_lap_options(df_dynamic_1)
    lap_options_2 = create_lap_options(df_dynamic_2)

    # Get initial lap selections from URL parameters if available, otherwise use fastest laps
    initial_lap1 = None
    initial_lap2 = None
    if 'selected_laps' in st.session_state:
        initial_lap1 = next((opt for opt in lap_options_1 if opt[0] == st.session_state['selected_laps'][0]), None)
        initial_lap2 = next((opt for opt in lap_options_2 if opt[0] == st.session_state['selected_laps'][1]), None)
    
    # If no laps in URL, use fastest laps
    if not initial_lap1 or not initial_lap2:
        _, fastest_lap_1 = get_lap_times_and_fastest(df_dynamic_1)
        _, fastest_lap_2 = get_lap_times_and_fastest(df_dynamic_2)
        initial_lap1 = next((opt for opt in lap_options_1 if opt[0] == fastest_lap_1), lap_options_1[0])
        initial_lap2 = next((opt for opt in lap_options_2 if opt[0] == fastest_lap_2), lap_options_2[0])
        st.session_state['selected_laps'] = [fastest_lap_1, fastest_lap_2]

    # Use st.form to group lap selection and avoid re-runs
    with st.form(key="lap_selection_form"):
        # Lap selection for race 1
        selected_lap_1 = st.selectbox(
            f"{username1} のラップを選択してください:",
            options=lap_options_1,
            format_func=lambda x: x[1],
            key="lap_select_1",
            index=lap_options_1.index(initial_lap1)
        )

        # Lap selection for race 2
        selected_lap_2 = st.selectbox(
            f"{display_username2} のラップを選択してください:",
            options=lap_options_2,
            format_func=lambda x: x[1],
            key="lap_select_2",
            index=lap_options_2.index(initial_lap2)
        )

        # Submit button to apply lap selections
        submit_button = st.form_submit_button("Submit")

    # Determine if we should auto-visualize
    should_auto_visualize = (
        'selected_laps' in st.session_state and 
        not st.session_state.get('has_auto_visualized', False)
    )

    # Update URL parameters and visualize when form is submitted or auto-visualize is triggered
    if submit_button or should_auto_visualize:
        # Get the lap numbers to use
        if submit_button:
            selected_lap_num_1 = selected_lap_1[0]
            selected_lap_num_2 = selected_lap_2[0]
        else:  # Auto-visualize case
            selected_lap_num_1 = st.session_state['selected_laps'][0]
            selected_lap_num_2 = st.session_state['selected_laps'][1]
            # Mark that we've done the auto-visualization
            st.session_state['has_auto_visualized'] = True
        
        # Update URL with both races and laps
        update_query_params(
            st.session_state['selected_races'], 
            [selected_lap_num_1, selected_lap_num_2]
        )

        # Filter data for the selected lap for each race
        selected_lap_data_1 = df_dynamic_1[df_dynamic_1['lap'] == selected_lap_num_1]
        selected_lap_data_2 = df_dynamic_2[df_dynamic_2['lap'] == selected_lap_num_2]

        # Visualize race line with course track
        detail_race_line_plot_with_coursetrack = create_colored_race_line_with_coursetrack(
            selected_lap_data_1, selected_lap_data_2, selected_lap_num_1, 
            username1, username2, course_track_options, width=600, height=600
        )
        st.plotly_chart(detail_race_line_plot_with_coursetrack, use_container_width=True)

        # Visualize other plots in two-column layout
        for i in range(0, len(selected_plots), 2):
            col1, col2 = st.columns(2)
            
            create_comparison_plot(
                selected_lap_data_1, selected_lap_data_2, 'current_lap_time',
                selected_plots[i][0], selected_plots[i][1], selected_lap_num_1,
                col1, username1, username2
            )
            
            if i + 1 < len(selected_plots):
                create_comparison_plot(
                    selected_lap_data_1, selected_lap_data_2, 'current_lap_time',
                    selected_plots[i + 1][0], selected_plots[i + 1][1], selected_lap_num_1,
                    col2, username1, username2
                )