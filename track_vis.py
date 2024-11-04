import os
import json
import plotly.graph_objects as go


def get_course_list(directory):
    """List available JSON files (course tracks) in the specified directory."""
    return [f for f in os.listdir(directory) if f.endswith('.json')]


def get_course_track(json_file_path, reduction_factor=1):
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

    # Just create the road fill without edge lines
    fig.add_trace(go.Scatter(
        x=left_x + right_x[::-1],  # Combine left_x and right_x for the fill
        y=left_y + right_y[::-1],  # Combine left_y and right_y for the fill
        fill="toself",             # Fill between the two edges
        fillcolor="gray",          # Road color
        opacity=0.3,               # Make it slightly transparent
        line=dict(width=0),        # Remove the edge line completely
        name="Road",
        hoverinfo="skip"           # Hide hover info for the fill
    ))

    # Update layout
    fig.update_layout(
        xaxis_title="Position X",
        yaxis_title="Position Z",
        showlegend=False           # Hide legend since we only have the road
    )

    return fig