import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.signal import find_peaks


def create_comparison_plot(df1, df2, x_column, y_column, title, selected_lap, col, username1, username2):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df1[x_column], y=df1[y_column], mode='lines', name=f'{username1}', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df2[x_column], y=df2[y_column], mode='lines', name=f'{username2}', line=dict(color='red')))
    fig.update_layout(title=title, xaxis_title='Lap Progress', yaxis_title=title, height=300)
    col.plotly_chart(fig, use_container_width=True)


def create_combined_annotated_race_line_plot(df1, df2, selected_lap, username1, username2):
    df1_reduced = df1.iloc[::10, :]  # Take every xrd point instead of every 5th
    df2_reduced = df2.iloc[::10, :]

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
    add_speed_annotations(fig, df1, 'red', 5, 5, username1, add_start=True)  # User 1: offset 5px to the left and up
    add_speed_annotations(fig, df2, 'blue', -5, -5, username1, add_start=False)  # User 2: offset 5px to the right and down

    fig.update_layout(
        title=f'Combined Annotated Race Lines: Lap {selected_lap}',
        # xaxis_title='X Position',
        # yaxis_title='Z Position',
        showlegend=True,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        yaxis=dict(scaleanchor="x", scaleratio=1, autorange="reversed"),
        margin=dict(l=0, r=0, t=30, b=0),
    )

    return fig


def add_speed_annotations(fig, df, color, x_offset, y_offset, username, add_start=False):
    speed = df['speed'].values
    
    # Simple peak and valley detection
    peaks, _ = find_peaks(speed, distance=480, prominence=1)
    valleys, _ = find_peaks(-speed, distance=480, prominence=1)

    max_annotations = 40
    peaks = peaks[:max_annotations]
    valleys = valleys[:max_annotations]

    for i in peaks:
        fig.add_annotation(
            x=df['position_x'].iloc[i] + x_offset,
            y=df['position_z'].iloc[i] + y_offset,
            text=f"{username}: ▴{speed[i]:.0f}",
            showarrow=False,
            font=dict(color=color, size=10),
            bgcolor="white",
            opacity=0.8
        )

    for i in valleys:
        fig.add_annotation(
            x=df['position_x'].iloc[i] + x_offset,
            y=df['position_z'].iloc[i] + y_offset,
            text=f"{username}: {speed[i]:.0f}▾",
            showarrow=False,
            font=dict(color=color, size=10),
            bgcolor="white",
            opacity=0.8
        )

    if add_start and len(df) > 0:
        fig.add_annotation(x=df['position_x'].iloc[0], y=df['position_z'].iloc[0], text="START", showarrow=False)


# new plot

def create_detail_race_line(df1, df2, selected_lap, username1, username2):
    df1_reduced = df1.iloc[::10, :]  # Take every 10th point
    df2_reduced = df2.iloc[::10, :]
    fig = go.Figure()

    def assign_color(throttle, brake):
        if throttle > 0 and throttle > brake:
            return 'blue'
        elif brake > 0 and brake > throttle:
            return 'red'
        else:
            return 'green'

    def add_user_trace(df, username, line_width, opacity=1):
        for i in range(len(df) - 1):
            color = assign_color(df['throttle'].iloc[i], df['brake'].iloc[i])
            fig.add_trace(go.Scatter(
                x=[df['position_x'].iloc[i], df['position_x'].iloc[i + 1]],
                y=[df['position_z'].iloc[i], df['position_z'].iloc[i + 1]],
                mode='lines',
                line=dict(color=color, width=line_width),
                opacity=opacity,
                name=username if i == 0 else '',
                showlegend=(i == 0),
                hoverinfo='text',
                text=f"Throttle: {df['throttle'].iloc[i]:.2f}, Brake: {df['brake'].iloc[i]:.2f}"
            ))

    # Add trace for user 1 (normal line)
    add_user_trace(df1_reduced, username1, line_width=3)

    # Add trace for user 2 (wider, semi-transparent line)
    add_user_trace(df2_reduced, username2, line_width=8, opacity=0.4)

    # Add speed annotations
    add_speed_annotations(fig, df1, 'gray', 5, 5, username1, add_start=True)  # User 1: offset 5px to the right and up
    add_speed_annotations(fig, df2, 'gray', -5, -5, username2, add_start=False)  # User 2: offset 5px to the left and down

    fig.update_layout(
        title=f'Detailed Race Lines: Lap {selected_lap}',
        xaxis_title='X Position',
        yaxis_title='Z Position',
        showlegend=True,
        yaxis=dict(scaleanchor="x", scaleratio=1, autorange="reversed"),
        margin=dict(l=0, r=0, t=30, b=0),
    )

    return fig


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
    print_lap_times_table(df_static_1, df_static_2)

    selected_lap = st.selectbox("比較するラップを選択してください:", 
                                df_dynamic_1['lap'].unique(), key="lap_select")

    selected_lap_data_1 = df_dynamic_1[df_dynamic_1['lap'] == selected_lap]
    selected_lap_data_2 = df_dynamic_2[df_dynamic_2['lap'] == selected_lap]

    username1 = df_static_1['username'].iloc[0]
    username2 = df_static_2['username'].iloc[0]


    # Race Lineの可視化
    # race_line_plot = create_combined_annotated_race_line_plot(
    # selected_lap_data_1, selected_lap_data_2, selected_lap, username1, username2
    # )
    # st.plotly_chart(race_line_plot, use_container_width=True)


    # Race Lineの可視化
    detail_race_line_plot = create_detail_race_line(
    selected_lap_data_1, selected_lap_data_2, selected_lap, username1, username2
    )
    st.plotly_chart(detail_race_line_plot, use_container_width=True)



    # 他の可視化（2列のレイアウト）
    for i in range(0, len(selected_plots), 2):
        col1, col2 = st.columns(2)
        
        create_comparison_plot(selected_lap_data_1, selected_lap_data_2, 'lap_index', 
                               selected_plots[i][0], selected_plots[i][1], selected_lap, 
                               col1, username1, username2)
        
        if i + 1 < len(selected_plots):
            create_comparison_plot(selected_lap_data_1, selected_lap_data_2, 'lap_index', 
                                   selected_plots[i+1][0], selected_plots[i+1][1], selected_lap, 
                                   col2, username1, username2)

