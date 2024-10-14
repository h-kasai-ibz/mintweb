import dash
from dash import dcc, html
import plotly.graph_objects as go
import json

# Load and process JSON data (update this with your actual file path)
def load_json_data(json_data):
    ''' Load and return JSON data from the specified path '''
    with open(json_data, 'r') as file:
        race_data = json.load(file)
    return race_data

# Function to process each frame of data into a usable format
def create_val_from_json(frame_data):
    ''' Process the JSON frame data for visualization '''
    return {
        "position": {
            "x": frame_data["position_x"],
            "y": frame_data["position_y"],
            "z": frame_data["position_z"]
        },
        "velocity": {
            "x": frame_data["velocity_x"],
            "y": frame_data["velocity_y"],
            "z": frame_data["velocity_z"]
        },
        "rotation": {
            "pitch": frame_data["rotation_pitch"],
            "yaw": frame_data["rotation_yaw"],
            "roll": frame_data["rotation_roll"],
            "w": frame_data["rotation_w"]
        },
        "angular_velocity": {
            "x": frame_data["angular_velocity_x"],
            "y": frame_data["angular_velocity_y"],
            "z": frame_data["angular_velocity_z"]
        }
    }

# Load JSON data
json_data = load_json_data('/data/20240916_1131.json')

# Prepare data for 3D plotting
x_positions = [frame['position_x'] for frame in json_data]
y_positions = [frame['position_y'] for frame in json_data]
z_positions = [frame['position_z'] for frame in json_data]

# Create 3D scatter plot
trace = go.Scatter3d(
    x=x_positions,
    y=y_positions,
    z=z_positions,
    mode='lines+markers',
    marker=dict(size=4, color='blue', opacity=0.8)
)

layout = go.Layout(
    title='Car Visualization',
    scene=dict(
        xaxis_title='X Axis',
        yaxis_title='Y Axis',
        zaxis_title='Z Axis'
    )
)

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the Dash app
app.layout = html.Div([
    html.H1("Car Visualization from JSON Data"),
    dcc.Graph(
        id='3d-graph',
        figure=go.Figure(data=[trace], layout=layout)
    )
])

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
