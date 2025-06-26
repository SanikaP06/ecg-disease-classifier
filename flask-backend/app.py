# app.py - Fixed Flask API for ECG Classification
from flask import Flask
from flask_cors import CORS # Import CORS

# This part was duplicated in your uploaded file, ensure Flask app is initialized once.
# app = Flask(__name__)
# CORS(app) 
# ... rest of your app.py code

import os
import json
import pickle
import numpy as np
import pandas as pd
# from flask import Flask, request, jsonify # Flask is already imported
from flask import request, jsonify # request and jsonify are needed
from werkzeug.utils import secure_filename
import tensorflow as tf
from collections import Counter
from ecg_utils import preprocess_ecg, segment_ecg_beats # Assuming ecg_utils.py is in the same directory
import logging
import tempfile
import time
import gc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__) # Initialize Flask app here
CORS(app) # Apply CORS to the app instance

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size for large ECG files

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variables for loaded models and scalers
model = None
scaler = None
class_mapping = None

def load_models():
    """Load the pre-trained model, scaler, and class mapping"""
    global model, scaler, class_mapping
    
    try:
        # Load the trained CNN+LSTM model
        model = tf.keras.models.load_model('cnn_lstm_ecg_classifier_v1.keras')
        logger.info("Model loaded successfully")
        
        # Load the StandardScaler used during training
        with open('ecg_scaler.pkl', 'rb') as f:
            scaler = pickle.load(f)
        logger.info("Scaler loaded successfully")
        
        # Load class mapping (index -> diagnosis label)
        with open('class_mapping.pkl', 'rb') as f:
            class_mapping = pickle.load(f)
        logger.info("Class mapping loaded successfully")
        
    except Exception as e:
        logger.error(f"Error loading models: {str(e)}")
        raise

# Load models when the app starts
load_models()

def allowed_file(filename):
    """Check if the uploaded file has a valid extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'

def safe_file_cleanup(filepath, max_retries=5, delay=0.1):
    """Safely delete a file with retries to handle Windows file locking"""
    for attempt in range(max_retries):
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Successfully deleted temporary file: {filepath}")
            return True
        except (OSError, PermissionError) as e:
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1} to delete {filepath} failed: {str(e)}. Retrying...")
                time.sleep(delay)
                gc.collect()  # Force garbage collection
            else:
                logger.error(f"Failed to delete {filepath} after {max_retries} attempts: {str(e)}")
                return False
    return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'scaler_loaded': scaler is not None,
        'class_mapping_loaded': class_mapping is not None
    })

@app.route('/predict', methods=['POST'])
def predict_ecg():
    """
    Main ECG Classification Endpoint
    """
    filepath = None
    try:
        # Validate file upload
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload a CSV file'}), 400
        
        filename = secure_filename(file.filename)
        temp_fd, filepath = tempfile.mkstemp(suffix='.csv', prefix=f'ecg_{filename}_')
        
        try:
            with os.fdopen(temp_fd, 'wb') as temp_file:
                file.save(temp_file)
        except Exception as e:
            try:
                os.close(temp_fd)
            except:
                pass
            raise e
        
        logger.info(f"Processing uploaded file: {filename} (temp: {filepath})")
        result = process_ecg_file(filepath)
        
        # Check if processing itself returned an error (e.g. from process_ecg_file directly)
        if isinstance(result, tuple) and isinstance(result[0], dict) and 'error' in result[0]:
             # This means process_ecg_file already formatted an error response
             return jsonify(result[0]), result[1]

        logger.info(f"Successfully processed {filename}. "
                   f"Diagnosis: {result['predicted_diagnosis']}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in ECG prediction pipeline: {str(e)}")
        return jsonify({
            'error': f'ECG processing failed: {str(e)}',
            'preprocessing_success': False
        }), 500
        
    finally:
        if filepath:
            safe_file_cleanup(filepath)

def process_ecg_file(filepath):
    """
    Process continuous ECG file and return prediction results
    """
    df = None
    try:
        df = pd.read_csv(filepath)
        
        # UPDATED: Added 'ecg' (lowercase) to the list
        possible_columns = ['MLII', 'MLI', 'V1', 'V2', 'Lead II', 'lead_II', 'ECG', 'ecg', '0', '1']
        ecg_column = None
        
        for col_name_or_index in possible_columns:
            try:
                # Try as column name first
                if col_name_or_index in df.columns:
                    ecg_column = col_name_or_index
                    break
                # Try as integer index if it's a string representing an integer (like '0', '1')
                elif isinstance(col_name_or_index, str) and col_name_or_index.isdigit():
                    col_idx = int(col_name_or_index)
                    if col_idx < len(df.columns):
                         # Use the actual column name at this index for clarity in logs
                        ecg_column = df.columns[col_idx]
                        break
            except ValueError: # If col_name_or_index cannot be converted to int
                continue
            except KeyError: # If df[col_name_or_index] fails
                continue

        if ecg_column is None:
            available_columns = list(df.columns)
            # This error will be caught by the calling function (predict_ecg)
            raise ValueError(f"No valid ECG column found. Available columns: {available_columns}. "
                           f"Expected one of: {possible_columns}")
        
        logger.info(f"Using column '{ecg_column}' as ECG signal")
        continuous_ecg = df[ecg_column].values.astype(np.float32)
        
        del df; df = None; gc.collect()
        
        continuous_ecg = continuous_ecg[~np.isnan(continuous_ecg)]
        continuous_ecg = continuous_ecg[np.isfinite(continuous_ecg)]
        
        if len(continuous_ecg) == 0:
            raise ValueError("ECG signal contains no valid data after cleaning")
        
        if len(continuous_ecg) > 1000000:
            logger.warning(f"Large ECG file detected ({len(continuous_ecg)} samples). "
                          f"Consider using shorter recordings for faster processing.")
        
        logger.info(f"Loaded continuous ECG signal with {len(continuous_ecg)} samples")
        heartbeat_segments = segment_ecg_beats(continuous_ecg, scaler, segment_length=250)
        
        if len(heartbeat_segments) == 0:
            raise ValueError("No valid heartbeat segments extracted. "
                           "Check if ECG signal contains detectable R-peaks.")
        
        logger.info(f"Successfully extracted {len(heartbeat_segments)} heartbeat segments "
                   f"of 250 samples each")
        
        X_segments = np.array(heartbeat_segments)
        X_segments = X_segments.reshape(X_segments.shape[0], X_segments.shape[1], 1)
        logger.info(f"Prepared data shape for model: {X_segments.shape}")
        
        batch_size = 100
        all_predictions = []
        all_confidences = []
        
        for i in range(0, len(X_segments), batch_size):
            batch = X_segments[i:i+batch_size]
            batch_predictions = model.predict(batch, verbose=0)
            all_predictions.extend(np.argmax(batch_predictions, axis=1))
            all_confidences.extend(np.max(batch_predictions, axis=1))
        
        segment_classes = np.array(all_predictions)
        segment_confidences = np.array(all_confidences)
        logger.info(f"Generated predictions for {len(segment_classes)} heartbeat segments")
        
        class_votes = Counter(segment_classes)
        final_class_idx = max(class_votes, key=class_votes.get)
        final_diagnosis = class_mapping[final_class_idx]
        
        majority_segments = class_votes[final_class_idx]
        majority_confidence_values = [conf for i, conf in enumerate(segment_confidences) if segment_classes[i] == final_class_idx]
        majority_confidence = np.mean(majority_confidence_values) if majority_confidence_values else 0.0

        segment_distribution = {}
        total_segments = len(segment_classes)
        
        for class_idx_loop, vote_count in class_votes.items():
            diagnosis_name = class_mapping[class_idx_loop]
            current_segment_confidences = [conf for i, conf in enumerate(segment_confidences) if segment_classes[i] == class_idx_loop]
            avg_confidence = np.mean(current_segment_confidences) if current_segment_confidences else 0.0
            
            segment_distribution[diagnosis_name] = {
                'segment_count': vote_count,
                'percentage': round((vote_count / total_segments) * 100, 2) if total_segments > 0 else 0,
                'avg_confidence': round(float(avg_confidence), 4)
            }
        
        return {
            'predicted_diagnosis': final_diagnosis,
            'overall_confidence': round(float(majority_confidence), 4),
            'total_heartbeats': total_segments,
            'continuous_samples': len(continuous_ecg),
            'segment_distribution': segment_distribution,
            'preprocessing_success': True,
            'majority_vote_count': majority_segments
        }
        
    except ValueError as ve: # Catch ValueError specifically to return a more specific error
        logger.error(f"ValueError in ECG preprocessing: {str(ve)}")
        # Return a dictionary that can be caught by predict_ecg and turned into a 400 or 500 response
        # This structure allows predict_ecg to decide the HTTP status code.
        # For "No valid ECG column found", a 400 Bad Request might be more appropriate.
        # However, the original code structure has the main try-except in predict_ecg return 500.
        # To maintain that, we re-raise or let predict_ecg handle it.
        # For now, we'll re-raise so predict_ecg's main exception handler catches it.
        raise ve 
    except Exception as e:
        logger.error(f"Generic error in ECG preprocessing pipeline: {str(e)}")
        raise # Re-raise to be caught by predict_ecg's main exception handler
    finally:
        if df is not None:
            del df
        gc.collect()

@app.route('/classes', methods=['GET'])
def get_classes():
    """Return available diagnosis classes"""
    if class_mapping is None:
        return jsonify({'error': 'Class mapping not loaded'}), 500
    
    return jsonify({
        'classes': list(class_mapping.values()),
        'total_classes': len(class_mapping)
    })

@app.route('/predict_batch', methods=['POST'])
def predict_ecg_batch():
    """
    Batch processing endpoint for multiple ECG files
    """
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400
        
        results = []
        for file_item in files: # Renamed 'file' to 'file_item' to avoid conflict
            if file_item.filename != '' and allowed_file(file_item.filename):
                filepath_batch = None # Ensure filepath_batch is defined for the finally block
                try:
                    filename_batch = secure_filename(file_item.filename)
                    temp_fd_batch, filepath_batch = tempfile.mkstemp(suffix='.csv', prefix=f'ecg_batch_{filename_batch}_')
                    
                    try:
                        with os.fdopen(temp_fd_batch, 'wb') as temp_file_batch:
                            file_item.save(temp_file_batch)
                        
                        result_batch = process_ecg_file(filepath_batch)
                        # Check if processing itself returned an error
                        if isinstance(result_batch, tuple) and isinstance(result_batch[0], dict) and 'error' in result_batch[0]:
                            results.append({
                                'filename': filename_batch,
                                'error': result_batch[0]['error'],
                                'preprocessing_success': False
                            })
                        else:
                            result_batch['filename'] = filename_batch
                            results.append(result_batch)
                        
                    finally: # Changed from except to finally for cleanup
                        # This was os.close(temp_fd_batch) which is wrong, should be safe_file_cleanup
                        if filepath_batch: # Ensure filepath_batch was assigned
                           safe_file_cleanup(filepath_batch)
                        
                except Exception as e_batch:
                    results.append({
                        'filename': file_item.filename, # Use file_item.filename
                        'error': str(e_batch),
                        'preprocessing_success': False
                    })
            elif file_item.filename != '': # If file is not empty but not allowed
                 results.append({
                        'filename': file_item.filename,
                        'error': 'Invalid file type. Only CSV allowed.',
                        'preprocessing_success': False
                    })


        return jsonify({
            'batch_results': results,
            'total_files': len(files), # Use len(files) for total attempts
            'successful_predictions': len([r for r in results if r.get('preprocessing_success', False)])
        })
        
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        return jsonify({'error': f'Batch processing failed: {str(e)}'}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 100MB'}), 413

@app.errorhandler(500)
def internal_error(e):
    # Log the actual exception for server-side debugging
    logger.error(f"Internal server error: {e}", exc_info=True)
    return jsonify({'error': 'Internal server error. Please try again.'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)