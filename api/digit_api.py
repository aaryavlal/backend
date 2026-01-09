from flask import Blueprint, request, jsonify, current_app
from flask_cors import CORS
import tensorflow as tf
from tensorflow import keras
import numpy as np
from PIL import Image
import io
import base64
from scipy import ndimage
from scipy.ndimage import rotate, shift
import cv2
import os

digit_api = Blueprint('digit_api', __name__)

# Load ultimate model
MODEL_DIR = os.path.join(os.path.dirname(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, 'best_model.keras')

model = None
ensemble_models = []

try:
    if os.path.exists(MODEL_PATH):
        print(f"Loading model from {MODEL_PATH}...")
        model = keras.models.load_model(MODEL_PATH)
        print("Model loaded successfully!")
    else:
        print(f"WARNING: Model not found at {MODEL_PATH}")
        print("The digit recognition API will not work until the model is available.")
except Exception as e:
    print(f"ERROR loading model: {e}")
    print("The digit recognition API will not work.")

# Try to load ensemble if available
if model is not None:
    for i in range(5):
        ensemble_path = os.path.join(MODEL_DIR, f'ensemble_model_{i}.keras')
        if os.path.exists(ensemble_path):
            try:
                ensemble_models.append(keras.models.load_model(ensemble_path))
            except Exception as e:
                print(f"Warning: Could not load ensemble model {i}: {e}")

    if ensemble_models:
        print(f"✓ Loaded {len(ensemble_models)} ensemble models")

def find_connected_components(img_array, threshold=250):
    """Find separate digits using projection-based segmentation"""
    # Binarize
    binary = (img_array < threshold).astype(np.uint8) * 255

    # Try horizontal projection to find digit boundaries
    horizontal_projection = np.sum(binary, axis=0)

    # Find valleys in projection (gaps between digits)
    # Use a very sensitive threshold to catch even small gaps
    max_projection = np.max(horizontal_projection)
    threshold_proj = max_projection * 0.05  # Very low threshold to catch tiny gaps

    # Find segments where projection is below threshold (gaps)
    is_gap = horizontal_projection < threshold_proj

    # Find transitions from digit to gap and gap to digit
    transitions = np.diff(is_gap.astype(int))
    digit_starts = np.where(transitions == -1)[0] + 1
    digit_ends = np.where(transitions == 1)[0] + 1

    # Handle edge cases
    if len(horizontal_projection) > 0 and horizontal_projection[0] > threshold_proj:
        digit_starts = np.concatenate([[0], digit_starts])
    if len(horizontal_projection) > 0 and horizontal_projection[-1] > threshold_proj:
        digit_ends = np.concatenate([digit_ends, [len(horizontal_projection)]])

    # Create components from projection segments
    components = []

    if len(digit_starts) > 0 and len(digit_ends) > 0:
        # Match starts with ends
        for start, end in zip(digit_starts, digit_ends[:len(digit_starts)]):
            if end - start < 10:  # Too narrow
                continue

            # Find vertical bounds within this horizontal segment
            segment = binary[:, start:end]
            vertical_projection = np.sum(segment, axis=1)

            rows_with_content = np.where(vertical_projection > 0)[0]
            if len(rows_with_content) == 0:
                continue

            rmin = rows_with_content[0]
            rmax = rows_with_content[-1]

            if rmax - rmin < 10:  # Too short
                continue

            # Add padding
            width = end - start
            height = rmax - rmin
            padding = max(int(0.15 * max(width, height)), 10)

            rmin = max(0, rmin - padding)
            rmax = min(img_array.shape[0], rmax + padding)
            cmin = max(0, start - padding)
            cmax = min(img_array.shape[1], end + padding)

            components.append({
                'bbox': (rmin, rmax, cmin, cmax),
                'center_x': (cmin + cmax) / 2
            })

    # Fallback to connected components if projection fails
    if len(components) == 0:
        labeled, num_features = ndimage.label(binary)

        for i in range(1, num_features + 1):
            rows, cols = np.where(labeled == i)

            if len(rows) < 15:
                continue

            rmin, rmax = rows.min(), rows.max()
            cmin, cmax = cols.min(), cols.max()

            width = cmax - cmin
            height = rmax - rmin

            if width < 10 or height < 10:
                continue

            padding = max(int(0.15 * max(width, height)), 10)
            rmin = max(0, rmin - padding)
            rmax = min(img_array.shape[0], rmax + padding)
            cmin = max(0, cmin - padding)
            cmax = min(img_array.shape[1], cmax + padding)

            components.append({
                'bbox': (rmin, rmax, cmin, cmax),
                'center_x': (cmin + cmax) / 2
            })

    components.sort(key=lambda x: x['center_x'])
    return components

def advanced_preprocess_digit(img_array, bbox):
    """Enhanced preprocessing with rotation correction and thinning"""
    rmin, rmax, cmin, cmax = bbox
    cropped = img_array[rmin:rmax, cmin:cmax]

    # Binary threshold (simple, not adaptive - works better for thick strokes)
    _, cropped = cv2.threshold(cropped, 127, 255, cv2.THRESH_BINARY)

    cropped = 255 - cropped

    # Detect and correct rotation using moments (conservative approach)
    coords = cv2.findNonZero(cropped)
    if coords is None:
        return np.zeros((28, 28))

    # Calculate the angle of rotation using image moments
    moments = cv2.moments(coords)
    if moments['mu02'] != 0 and moments['mu20'] != 0:
        # Calculate the orientation angle
        angle = 0.5 * np.arctan2(2 * moments['mu11'], moments['mu20'] - moments['mu02'])
        angle_degrees = np.degrees(angle)

        # Normalize angle to [-45, 45] range to avoid over-rotation
        # This prevents rotating upright digits
        while angle_degrees > 45:
            angle_degrees -= 90
        while angle_degrees < -45:
            angle_degrees += 90

        # Only correct if angle is significant (> 10 degrees) and reasonable
        # Increased threshold to avoid rotating nearly-upright digits
        if abs(angle_degrees) > 10 and abs(angle_degrees) < 45:
            # Get rotation matrix
            center = (cropped.shape[1] // 2, cropped.shape[0] // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, angle_degrees, 1.0)

            # Apply rotation
            cropped = cv2.warpAffine(cropped, rotation_matrix, (cropped.shape[1], cropped.shape[0]),
                                    flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

    # Morphological thinning to handle thick strokes
    kernel = np.ones((2, 2), np.uint8)
    cropped = cv2.erode(cropped, kernel, iterations=1)

    # Find content after rotation
    coords = cv2.findNonZero(cropped)
    if coords is None:
        return np.zeros((28, 28))

    x, y, w, h = cv2.boundingRect(coords)
    cropped = cropped[y:y+h, x:x+w]

    height, width = cropped.shape

    # MNIST digits are roughly square, so we make ours similar
    if height > width:
        new_height = 20
        new_width = max(1, int(20 * width / height))
    else:
        new_width = 20
        new_height = max(1, int(20 * height / width))

    resized = cv2.resize(cropped, (new_width, new_height), interpolation=cv2.INTER_AREA)

    # Center in 28x28 with proper MNIST-style centering
    final = np.zeros((28, 28), dtype=np.uint8)
    y_offset = (28 - new_height) // 2
    x_offset = (28 - new_width) // 2
    final[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = resized

    # Apply slight blur to match MNIST smoothness
    final = cv2.GaussianBlur(final, (3, 3), 0.8)

    # Normalize to 0-1 range
    final = final.astype(np.float32) / 255.0
    final_max = final.max()
    final_min = final.min()
    if final_max > final_min:
        final = (final - final_min) / (final_max - final_min)

    return final

def predict_with_tta(image, num_augmentations=8):
    """Test-Time Augmentation for robust predictions"""
    predictions = []
    
    # Original
    predictions.append(model.predict(image.reshape(1, 28, 28, 1), verbose=0)[0])
    
    # Augmented versions
    for _ in range(num_augmentations - 1):
        aug_image = image.copy()
        
        # Small rotation
        angle = np.random.uniform(-5, 5)
        aug_image = rotate(aug_image, angle, reshape=False, mode='constant', cval=0)
        
        # Small shift
        shift_x = np.random.randint(-2, 3)
        shift_y = np.random.randint(-2, 3)
        aug_image = shift(aug_image, [shift_y, shift_x], mode='constant', cval=0)
        
        predictions.append(model.predict(aug_image.reshape(1, 28, 28, 1), verbose=0)[0])
    
    # Ensemble if available
    if ensemble_models:
        for ens_model in ensemble_models:
            predictions.append(ens_model.predict(image.reshape(1, 28, 28, 1), verbose=0)[0])
    
    # Average
    avg_prediction = np.mean(predictions, axis=0)
    
    return avg_prediction

@digit_api.route('/api/digit/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok' if model is not None else 'error',
        'model_loaded': model is not None,
        'ensemble_models': len(ensemble_models),
        'tta_enabled': True,
        'model_path': MODEL_PATH
    })

def extract_layer_activations(image):
    """Extract intermediate layer activations for visualization"""
    # Prepare input
    input_data = image.reshape(1, 28, 28, 1)

    # Use a functional approach to extract activations
    layer_outputs = []
    layer_names = []

    # Get activations by running inference and accessing intermediate outputs
    from tensorflow.keras import Model

    # Build a list of layer outputs we want to visualize
    outputs_to_extract = []
    for layer in model.layers:
        if 'conv' in layer.name or 'dense' in layer.name or 'max_pooling' in layer.name:
            outputs_to_extract.append(layer.output)
            layer_names.append(layer.name)

    if outputs_to_extract:
        # Create a model that outputs all intermediate activations
        try:
            activation_model = Model(inputs=model.input, outputs=outputs_to_extract)
            activations = activation_model.predict(input_data, verbose=0)

            # If only one output, wrap it in a list
            if not isinstance(activations, list):
                activations = [activations]

            for activation in activations:
                layer_outputs.append(activation[0])  # Remove batch dimension

        except Exception as e:
            print(f"Error extracting activations: {e}")
            # Fallback: try layer by layer
            for layer in model.layers:
                if 'conv' in layer.name or 'dense' in layer.name or 'max_pooling' in layer.name:
                    try:
                        temp_model = Model(inputs=model.input, outputs=layer.output)
                        activation = temp_model.predict(input_data, verbose=0)[0]
                        layer_outputs.append(activation)
                    except:
                        continue

    # Convert activations to base64 images
    visualizations = []
    for layer_name, activation in zip(layer_names, layer_outputs):
        if len(activation.shape) == 3:  # Conv layers (height, width, channels)
            # Take first 8 feature maps
            num_features = min(8, activation.shape[-1])
            feature_maps = []

            for i in range(num_features):
                feature_map = activation[:, :, i]
                # Normalize
                fmap_max = feature_map.max()
                fmap_min = feature_map.min()
                if fmap_max > fmap_min:
                    feature_map = (feature_map - fmap_min) / (fmap_max - fmap_min)
                else:
                    feature_map = np.zeros_like(feature_map)
                feature_map = (feature_map * 255).astype(np.uint8)

                # Convert to base64
                img = Image.fromarray(feature_map)
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                feature_maps.append(f'data:image/png;base64,{img_base64}')

            visualizations.append({
                'layer_name': layer_name,
                'type': 'conv',
                'shape': list(activation.shape),
                'feature_maps': feature_maps
            })
        elif len(activation.shape) == 1:  # Dense layers
            visualizations.append({
                'layer_name': layer_name,
                'type': 'dense',
                'shape': list(activation.shape),
                'values': activation.tolist()
            })

    return visualizations

@digit_api.route('/api/digit/predict', methods=['POST'])
def predict():
    try:
        # Check if model is loaded
        if model is None:
            return jsonify({
                'error': 'Model not loaded',
                'message': 'The digit recognition model is not available. Please check server logs.'
            }), 503

        data = request.get_json()

        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400

        image_data = data['image']
        if not image_data or len(image_data.strip()) == 0:
            return jsonify({'error': 'Empty image data'}), 400

        if ',' in image_data:
            image_data = image_data.split(',')[1]

        img_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(img_bytes)).convert('L')
        img_array = np.array(img)

        components = find_connected_components(img_array)

        if not components:
            return jsonify({
                'success': True,
                'digits': [],
                'number': '',
                'message': 'No digits found'
            })

        # Process all digits
        processed_digits = []
        for component in components:
            bbox = component['bbox']
            processed = advanced_preprocess_digit(img_array, bbox)
            processed_digits.append(processed)

        # Batch predict with TTA
        results = []
        recognized_digits = []

        for idx, (component, processed) in enumerate(zip(components, processed_digits)):
            bbox = component['bbox']

            # Predict with TTA
            predictions = predict_with_tta(processed, num_augmentations=8)

            top_3_idx = np.argsort(predictions)[-3:][::-1]
            predicted_digit = int(top_3_idx[0])
            confidence = float(predictions[predicted_digit])

            recognized_digits.append(str(predicted_digit))

            # Convert processed to base64
            processed_display = ((1 - processed) * 255).astype(np.uint8)
            processed_img = Image.fromarray(processed_display)
            buffered = io.BytesIO()
            processed_img.save(buffered, format="PNG")
            processed_base64 = base64.b64encode(buffered.getvalue()).decode()

            results.append({
                'digit': predicted_digit,
                'confidence': confidence,
                'top3': [
                    {
                        'digit': int(top_3_idx[i]),
                        'confidence': float(predictions[top_3_idx[i]])
                    }
                    for i in range(3)
                ],
                'bbox': {
                    'x': int(bbox[2]),
                    'y': int(bbox[0]),
                    'width': int(bbox[3] - bbox[2]),
                    'height': int(bbox[1] - bbox[0])
                },
                'processed_image': f'data:image/png;base64,{processed_base64}'
            })

        full_number = ''.join(recognized_digits)

        return jsonify({
            'success': True,
            'digits': results,
            'number': full_number,
            'count': len(results)
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@digit_api.route('/api/digit/visualize', methods=['POST'])
def visualize():
    """Get CNN layer activations for educational visualization"""
    try:
        # Check if model is loaded
        if model is None:
            return jsonify({
                'error': 'Model not loaded',
                'message': 'The digit recognition model is not available. Please check server logs.'
            }), 503

        data = request.get_json()

        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400

        image_data = data['image']
        if not image_data or len(image_data.strip()) == 0:
            return jsonify({'error': 'Empty image data'}), 400

        if ',' in image_data:
            image_data = image_data.split(',')[1]

        img_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(img_bytes)).convert('L')
        img_array = np.array(img)

        # Get all digits
        components = find_connected_components(img_array)
        if not components:
            return jsonify({'error': 'Please draw a digit first'}), 400

        if len(components) > 1:
            return jsonify({'error': 'Please draw only ONE digit for visualization (detected multiple)'}), 400

        # Process the single digit
        bbox = components[0]['bbox']
        processed = advanced_preprocess_digit(img_array, bbox)

        # Get predictions
        predictions = model.predict(processed.reshape(1, 28, 28, 1), verbose=0)[0]
        predicted_digit = int(np.argmax(predictions))

        # Get layer activations
        layer_activations = extract_layer_activations(processed)

        # Input image
        input_display = ((1 - processed) * 255).astype(np.uint8)
        input_img = Image.fromarray(input_display)
        buffered = io.BytesIO()
        input_img.save(buffered, format="PNG")
        input_base64 = base64.b64encode(buffered.getvalue()).decode()

        return jsonify({
            'success': True,
            'input_image': f'data:image/png;base64,{input_base64}',
            'predicted_digit': predicted_digit,
            'confidence': float(predictions[predicted_digit]),
            'all_probabilities': predictions.tolist(),
            'layers': layer_activations
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500