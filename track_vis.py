import os
import json
import plotly.graph_objects as go


def get_course_list(directory):
    """List available JSON files (course tracks) in the specified directory."""
    return [f for f in os.listdir(directory) if f.endswith('.json')]


def get_course_track(json_file_path, reduction_factor=10):
    # Load the course track data from the JSON file
    with open(json_file_path, "r") as file:
        data = json.load(file)

    # Extract and reduce the number of points by selecting every nth point
    left_x = data["left_edge"]["position_x"][::reduction_factor]
    right_x = data["right_edge"]["position_x"][::reduction_factor]
    left_y = data["left_edge"]["position_z"][::reduction_factor]
    right_y = data["right_edge"]["position_z"][::reduction_factor]

    # Create a Plotly figure for the course track
    fig = go.Figure()

    # Add left edge of the track
    fig.add_trace(go.Scatter(
        x=left_x,
        y=left_y,
        mode="lines",
        name="Left Edge",
        line=dict(color="blue")
    ))

    # Add right edge of the track
    fig.add_trace(go.Scatter(
        x=right_x,
        y=right_y,
        mode="lines",
        name="Right Edge",
        line=dict(color="red")
    ))

    # Fill the area between the left and right edges to represent the road
    fig.add_trace(go.Scatter(
        x=left_x + right_x[::-1],  # Combine left_x and right_x for the fill
        y=left_y + right_y[::-1],  # Combine left_y and right_y for the fill
        fill="toself",  # Fill between the two edges
        fillcolor="lightgray",  # Road color (adjust this as needed)
        line=dict(color="lightgray"),  # Optional: set outline color to match
        name="Road",
        hoverinfo="skip"  # Hide hover info for the fill
    ))

    # Update layout to give a title and axis labels
    fig.update_layout(
        title="Course Track with Road Fill",
        xaxis_title="Position X",
        yaxis_title="Position Z",
        showlegend=True
    )

    return fig