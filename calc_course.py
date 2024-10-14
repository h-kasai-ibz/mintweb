import json

# Path to your JSON file
json_file_path = "track_json/course01.json"

# Open and load the JSON file
with open(json_file_path, "r") as file:
    data = json.load(file)

# Now `data` contains the loaded JSON data as a Python dictionary
print(data)


# Extract the position data
left_x = data["left_edge"]["position_x"]
right_x = data["right_edge"]["position_x"]
left_y = data["left_edge"]["position_z"]
right_y = data["right_edge"]["position_z"]

# Find the extreme positions
min_left_x = min(left_x)
max_right_x = max(right_x)

x_width = max_right_x - min_left_x
print(f"Width of the track: {x_width} m")