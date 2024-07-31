from matplotlib.animation import FuncAnimation, PillowWriter
import json
import numpy as np

def get_body_parts(data):
    """
    This function preturns 'body_parts' dictionary, that links the name of the body part, with its index.
    """
    try:
        body_parts = {node['name']: node['index'] for node in data['used_nodes']}
    except KeyError:
        # Some exercises (f.e. 'D1_flexion) do not contain the 'used_nodes' key, so let's assume the following:
        body_parts = {
            'NOSE': 0,
            'LEFT_EYE': 1,
            'RIGHT_EYE': 2,
            'LEFT_EAR': 3,
            'RIGHT_EAR': 4,
            'LEFT_SHOULDER': 5,
            'RIGHT_SHOULDER': 6,
            'LEFT_ELBOW': 7,
            'RIGHT_ELBOW': 8,
            'LEFT_WRIST': 9,
            'RIGHT_WRIST': 10,
            'LEFT_HIP': 11,
            'RIGHT_HIP': 12,
            'LEFT_KNEE': 13,
            'RIGHT_KNEE': 14,
            'LEFT_FOOT': 15,
            'RIGHT_FOOT': 16
        }
    return body_parts

# def get_list_of_positions(data):
#     """
#     This function preprocesses the 'golden_rep_poses' key into a list of frames.
#     Each frame is a list of lists [x, y] representing the position of each node.
#     """
#     list_of_positions = []
#     try:
#         for timestamp in data['golden_rep_poses']:
#             positions = timestamp['pose']
#             list_of_tuples_for_each_timestamp = [
#                 [positions[i], positions[i+1]] for i in range(0, 34, 2)
#             ]
#             list_of_positions.append(list_of_tuples_for_each_timestamp)
#     except KeyError:
#         try:
#             pose_data = data["golden_video_metadata"]["pose"]

#             for pose in pose_data:
#                 pose = pose[1:] # first element is a time
#                 list_of_tuples_for_each_pose = [
#                     [pose[i], pose[i+1]] for i in range(0, 34, 2)
#                 ]
#                 list_of_positions.append(list_of_tuples_for_each_pose)
#         except:
#             try:
#                 pose_data = data["user_poses"]

#                 for index in pose_data:
#                     pose = index['pose']
#                     list_of_tuples_for_each_pose = [
#                         [pose[i], pose[i+1]] for i in range(0, 34, 2)
#                     ]
#                     list_of_positions.append(list_of_tuples_for_each_pose)
#             except:
#                 try:
#                     pose_data = data['record']['results']
                    
#                     for index in pose_data:
#                         pose = index['input_pose']['pose']
#                         list_of_tuples_for_each_pose = [
#                             [pose[i], pose[i+1]] for i in range(0, 34, 2)
#                         ]
#                         list_of_positions.append(list_of_tuples_for_each_pose)
#                 except:
#                     pose_data = data['results']
                        
#                     for index in pose_data:
#                         pose = index['input_pose']['pose']
#                         list_of_tuples_for_each_pose = [
#                             [pose[i], pose[i+1]] for i in range(0, 34, 2)
#                         ]
#                         list_of_positions.append(list_of_tuples_for_each_pose)
       
#     return list_of_positions

def get_list_of_positions(data):
    """
    This function preprocesses position data into a list of frames.
    Each frame is a list of lists [x, y] representing the position of each node.
    """
    list_of_positions = []
    
    # Define a list of key paths to check in order of precedence
    key_paths = [
        ['golden_rep_poses'],
        ['golden_video_metadata', 'pose'],
        ['user_poses'],
        ['record', 'results'],
        ['results']
    ]
    
    # Iterate over each key path
    for path in key_paths:
        try:
            # Navigate through the nested keys
            pose_data = data
            for key in path:
                pose_data = pose_data[key]
            
            # Process the pose data based on the current key path
            for item in pose_data:
                if path == ['results']:  # Special handling for the 'results' key path
                    list_of_tuples_for_each_pose = []
                    for j in item['input_pose']['pose']:
                        list_of_tuples_for_each_pose.append(
                            [round(j['position']['x'], 3), round(j['position']['y'], 3)]
                        )
                    list_of_positions.append(list_of_tuples_for_each_pose)
                else:  # General handling for other key paths
                    pose = item['pose'] if 'pose' in item else item[1:]
                    list_of_tuples_for_each_pose = [
                        [pose[i], pose[i+1]] for i in range(0, 34, 2)
                    ]
                    list_of_positions.append(list_of_tuples_for_each_pose)
            
            return list_of_positions  # Return the result if processing is successful

        except KeyError:
            continue  # Try the next key path if the current one fails
    
    return list_of_positions  # Return an empty list if no valid key path is found

def differecne_measurment(list_of_positions, reference_node, body_parts):
    """Comes in handy whenever actor flies over the screen"""
    reference_index = body_parts[reference_node]
    for frame in list_of_positions:
        ref_x = frame[reference_index][0]
        ref_y = frame[reference_index][1]
        for node in frame:
            node[0] -= (ref_x - 0.5)
            node[1] -= (ref_y - 0.5)
    return list_of_positions

def transform_list_of_positions(list_of_positions, scale_to_pixels=True):
    """the function can be extended, for now I need only to reflect the node by liney=0.5, as the image is
    upside-down

    When we will need to add a scale it's a good place to do so.

    """
    for frame in list_of_positions:
        for node in frame:
            node[1] = -node[1]+1
            if scale_to_pixels:
                node[0] = int(node[0]*720)
                node[1] = int(node[1]*1280)
            # print(node)

    return list_of_positions

def smooth_positions(list_of_positions, window_size=5):
    """Applies a moving average filter to smooth the positions of each node over time."""
    smoothed_positions = []
    for i in range(len(list_of_positions)):
        if i < window_size:
            smoothed_positions.append(list_of_positions[i])
        else:
            smoothed_frame = []
            for j in range(len(list_of_positions[i])):
                smoothed_x = np.mean([list_of_positions[k][j][0] for k in range(i-window_size, i+1)])
                smoothed_y = np.mean([list_of_positions[k][j][1] for k in range(i-window_size, i+1)])
                smoothed_frame.append([smoothed_x, smoothed_y])
            smoothed_positions.append(smoothed_frame)
    return smoothed_positions

def center_skeleton(list_of_positions):
    """Centers the skeleton in the frame by shifting all coordinates."""
    for frame in list_of_positions:
        # Calculate the center of the skeleton
        x_coords = [node[0] for node in frame]
        y_coords = [node[1] for node in frame]
        center_x = np.mean(x_coords)
        center_y = np.mean(y_coords)

        # Shift all nodes to center the skeleton
        for node in frame:
            node[0] -= center_x - 0.5  # Centering on the x-axis (0.5 is the center)
            node[1] -= center_y - 0.5  # Centering on the y-axis (0.5 is the center)
    return list_of_positions

def add_fake_point_between_A_and_B(A, B, list_of_positions, body_parts, name):
    """
    Adds a fake point between points A and B and appends it to each frame in list_of_positions.
    """
    for frame in list_of_positions:
        fake_point_x = (frame[body_parts[A]][0] + frame[body_parts[B]][0]) / 2
        fake_point_y = (frame[body_parts[A]][1] + frame[body_parts[B]][1]) / 2
        frame.append([fake_point_x, fake_point_y])
    body_parts[name] = len(body_parts)

def get_trace(node, list_of_positions, body_parts):
    trace = []
    node_index = body_parts[node]
    for frame in list_of_positions:
        trace.append(frame[node_index])

    return trace

def get_velocity(trace):
    x_vel = []
    y_vel = []
    for frame in trace:
        x_vel.append(frame[0])
        y_vel.append(frame[1])

    return np.gradient(np.array(x_vel)), np.gradient(np.array(y_vel))


import math
def get_angle(A, B, C, list_of_positions, body_parts):
    angles = []
    for frame in list_of_positions:
        a = frame[body_parts[A]]
        b = frame[body_parts[B]]
        c = frame[body_parts[C]]

        BA = [a[0] - b[0], a[1] - b[1]]
        BC = [c[0] - b[0], c[1] - b[1]]
        
        # Dot product of BA and BC
        dot_product = BA[0] * BC[0] + BA[1] * BC[1]
        
        # Magnitudes of BA and BC
        magnitude_BA = math.sqrt(BA[0]**2 + BA[1]**2)
        magnitude_BC = math.sqrt(BC[0]**2 + BC[1]**2)
        
        # Cosine of the angle
        cos_angle = dot_product / (magnitude_BA * magnitude_BC)
        
        # Angle in radians
        angle_radians = math.acos(cos_angle)
        
        # Convert to degrees
        angle_degrees = math.degrees(angle_radians)
        angles.append(angle_degrees)

    return angles

HUMAN_BLUEPRINT = [
    ('LEFT_SHOULDER', 'LEFT_ELBOW'), ('LEFT_ELBOW', 'LEFT_WRIST'),
    ('RIGHT_SHOULDER', 'RIGHT_ELBOW'), ('RIGHT_ELBOW', 'RIGHT_WRIST'),
    ('RIGHT_SHOULDER', 'LEFT_SHOULDER'), ('RIGHT_HIP', 'LEFT_HIP'),
    ('LEFT_HIP', 'LEFT_KNEE'), ('LEFT_KNEE', 'LEFT_FOOT'),
    ('RIGHT_HIP', 'RIGHT_KNEE'), ('RIGHT_KNEE', 'RIGHT_FOOT')
]