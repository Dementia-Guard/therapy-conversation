import torch
import cv2
import base64
import numpy as np
from flask import request, jsonify, Blueprint

extract_services_bp = Blueprint('extract_services', __name__)

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5n')

@extract_services_bp.route('/extract', methods=['POST'])
def extract_objects():
    try:
        # Get JSON data from request
        data = request.get_json()
        if 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
        
        # Decode base64 image
        image_data = base64.b64decode(data['image'])
        np_arr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        # Perform object detection
        result = model(img)
        data_frame = result.pandas().xyxy[0]
        
        # Extract object names
        objects = data_frame['name'].tolist()
        
        # Create response format
        response = {
            "event_title": "What event is this image related to?",
            "context_who": f"Who are the individuals or objects present in the image, such as {', '.join(set(objects))}?",
            "context_where": "Where was this image taken?",
            "context_when": "When was this image taken?",
            "description": "Describe what is happening in the image?",
            "objects": list(set(objects))
        }


        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
