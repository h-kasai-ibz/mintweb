import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from scipy.signal import find_peaks


def create_comparison_plot(df1, df2, x_column, y_column, title, selected_lap, col, username1, username2):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df1[x_column], y=df1[y_column], mode='lines', name=f'{username1}', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df2[x_column], y=df2[y_column], mode='lines', name=f'{username2}', line=dict(color='red')))
    fig.update_layout(title=title, xaxis_title='Lap Progress', yaxis_title=title, height=300)
    col.plotly_chart(fig, use_container_width=True)

def create_comparison_race_line_plot(df1, df2, selected_lap, username1, username2):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df1['position_x'],
        y=df1['position_z'],
        mode='lines', 
        name=f'{username1}',
        line=dict(color='red', width=2)
    ))

    fig.add_trace(go.Scatter(
        x=df2['position_x'],
        y=df2['position_z'],
        mode='lines', 
        name=f'{username2}',
        line=dict(color='blue', width=2)
    ))

    fig.update_layout(
        title=f'Race Line Comparison',
        # xaxis_title='X Position',
        # yaxis_title='Z Position',
        showlegend=True,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        yaxis=dict(scaleanchor="x", scaleratio=1, autorange="reversed"),
        margin=dict(l=0, r=0, t=30, b=0),
    )

    return fig

def create_individual_race_line_plot(df, selected_lap, username, color):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['position_x'],
        y=df['position_z'],
        mode='lines', 
        name=username,
        line=dict(color=color, width=2)
    ))

    # add_speed_annotations(fig, df, color)
    add_speed_annotations(fig, df, color, y_offset=0, x_offset=0)

    fig.update_layout(
        title=f'{username} Race Line',
        # xaxis_title='X Position',
        # yaxis_title='Z Position',
        showlegend=False,
        yaxis=dict(scaleanchor="x", scaleratio=1, autorange="reversed"),
        margin=dict(l=0, r=0, t=30, b=0),
    )

    return fig

def create_combined_annotated_race_line_plot(df1, df2, selected_lap, username1, username2):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df1['position_x'],
        y=df1['position_z'],
        mode='lines', 
        name=f'{username1}',
        line=dict(color='red', width=2)
    ))

    fig.add_trace(go.Scatter(
        x=df2['position_x'],
        y=df2['position_z'],
        mode='lines', 
        name=f'{username2}',
        line=dict(color='blue', width=2)
    ))

    add_speed_annotations(fig, df1, 'red', 24, -24)  # User 1: offset 10px to the left
    add_speed_annotations(fig, df2, 'blue', -24, 24)  # User 2: offset 10px to the right

    fig.update_layout(
        title=f'Combined Annotated Race Lines: Lap {selected_lap}',
        xaxis_title='X Position',
        yaxis_title='Z Position',
        showlegend=True,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        yaxis=dict(scaleanchor="x", scaleratio=1, autorange="reversed"),
        margin=dict(l=0, r=0, t=30, b=0),
    )

    return fig

def add_speed_annotations(fig, df, base_color, y_offset=0, x_offset=0):
    speed = df['speed'].values
    
    peaks, _ = find_peaks(speed, distance=10, prominence=1)
    valleys, _ = find_peaks(-speed, distance=10, prominence=1)

    # high_color = 'darkred' if base_color == 'red' else 'darkblue'
    high_color = 'darkred' if base_color == 'red' else 'darkblue'
    low_color = 'darkred' if base_color == 'red' else 'darkblue'

    # Limit the number of annotations
    max_annotations = 30
    peaks = peaks[:max_annotations]
    valleys = valleys[:max_annotations]

    for i in peaks:
        fig.add_annotation(
            x=df['position_x'].iloc[i],
            y=df['position_z'].iloc[i] + y_offset,
            # text=f"{username1}: ▴{speed[i]:.0f}",
            text=f"▴{speed[i]:.0f}",
            showarrow=False,
            font=dict(color=high_color, size=12),
            bgcolor="white",
            opacity=0.8,
            xshift=x_offset  # Add horizontal offset
        )

    for i in valleys:
        fig.add_annotation(
            x=df['position_x'].iloc[i],
            y=df['position_z'].iloc[i] + y_offset,
            text=f"{speed[i]:.0f}▾",
            # text=f"{username1}: {speed[i]:.0f}▾",
            showarrow=False,
            font=dict(color=low_color, size=12),
            bgcolor="white",
            opacity=0.8,
            xshift=x_offset  # Add horizontal offset
        )
    if len(df) > 0:
        fig.add_annotation(
            x=df['position_x'].iloc[0],
            y=df['position_z'].iloc[0],
            text="START",
            showarrow=False,
            font=dict(size=12, color="black"),
            bgcolor="white",
            opacity=0.8
        )

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

def visualize_data(df_static_1, df_dynamic_1, df_static_2, df_dynamic_2, selected_plots):
    print_lap_times_table(df_static_1, df_static_2)

    selected_lap = st.selectbox("比較するラップを選択してください:", 
                                df_dynamic_1['lap'].unique(), key="lap_select")

    selected_lap_data_1 = df_dynamic_1[df_dynamic_1['lap'] == selected_lap]
    selected_lap_data_2 = df_dynamic_2[df_dynamic_2['lap'] == selected_lap]

    username1 = df_static_1['username'].iloc[0]
    username2 = df_static_2['username'].iloc[0]

    # Create race line plots
    comparison_plot = create_comparison_race_line_plot(
        selected_lap_data_1, selected_lap_data_2, selected_lap, username1, username2
    )
    individual_plot_1 = create_individual_race_line_plot(
        selected_lap_data_1, selected_lap, username1, 'red'
    )
    individual_plot_2 = create_individual_race_line_plot(
        selected_lap_data_2, selected_lap, username2, 'blue'
    )
    combined_annotated_plot = create_combined_annotated_race_line_plot(
        selected_lap_data_1, selected_lap_data_2, selected_lap, username1, username2
    )

    # Display race line plots in four columns
    st.subheader("Race Line Visualizations")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.plotly_chart(comparison_plot, use_container_width=True)
    with col2:
        st.plotly_chart(individual_plot_1, use_container_width=True)
    with col3:
        st.plotly_chart(individual_plot_2, use_container_width=True)
    with col4:
        st.plotly_chart(combined_annotated_plot, use_container_width=True)

    # Other comparison plots (remain the same)
    st.subheader("Other Comparisons")
    for i in range(0, len(selected_plots), 2):
        col1, col2 = st.columns(2)
        
        create_comparison_plot(selected_lap_data_1, selected_lap_data_2, 'lap_index', 
                               selected_plots[i][0], selected_plots[i][1], selected_lap, 
                               col1, username1, username2)
        
        if i + 1 < len(selected_plots):
            create_comparison_plot(selected_lap_data_1, selected_lap_data_2, 'lap_index', 
                                   selected_plots[i+1][0], selected_plots[i+1][1], selected_lap, 
                                   col2, username1, username2)

