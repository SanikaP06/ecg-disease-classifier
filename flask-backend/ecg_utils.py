# ecg_utils.py - Enhanced utility functions for ECG preprocessing
import numpy as np
import pandas as pd
from scipy import signal
from sklearn.preprocessing import StandardScaler
import logging
import gc

logger = logging.getLogger(__name__)

def preprocess_ecg(ecg_signal, sampling_rate=360):
    """
    Preprocess ECG signal with filtering and noise reduction
    
    Args:
        ecg_signal: Raw ECG signal array
        sampling_rate: Sampling rate in Hz (default 360 for MIT-BIH)
    
    Returns:
        Filtered ECG signal
    """
    try:
        # Convert to numpy array and handle memory efficiently
        ecg_signal = np.asarray(ecg_signal, dtype=np.float32)
        
        # Remove DC offset
        ecg_signal = ecg_signal - np.mean(ecg_signal)
        
        # Apply bandpass filter (0.5-40 Hz)
        nyquist = sampling_rate / 2
        low_freq = 0.5 / nyquist
        high_freq = 40.0 / nyquist
        
        # Ensure frequencies are within valid range
        low_freq = max(low_freq, 0.001)
        high_freq = min(high_freq, 0.999)
        
        b, a = signal.butter(4, [low_freq, high_freq], btype='band')
        filtered_signal = signal.filtfilt(b, a, ecg_signal)
        
        return filtered_signal
        
    except Exception as e:
        logger.error(f"Error in ECG preprocessing: {str(e)}")
        raise

def detect_r_peaks_scipy(ecg_signal, sampling_rate=360):
    """
    Robust R-peak detection using scipy with multiple fallback strategies
    
    Args:
        ecg_signal: Preprocessed ECG signal
        sampling_rate: Sampling rate in Hz
    
    Returns:
        Array of R-peak indices
    """
    try:
        from scipy.signal import find_peaks
        
        # Normalize signal for peak detection
        normalized_signal = (ecg_signal - np.mean(ecg_signal)) / (np.std(ecg_signal) + 1e-8)
        
        # Strategy 1: Standard R-peak detection
        min_distance = int(0.6 * sampling_rate)  # 600ms minimum distance between peaks
        height_threshold = np.percentile(normalized_signal, 75)  # Adaptive threshold
        
        r_peaks, properties = find_peaks(
            normalized_signal,
            height=height_threshold,
            distance=min_distance,
            prominence=0.3,
            width=1
        )
        
        # Strategy 2: If too few peaks found, try more lenient parameters
        if len(r_peaks) < 3:
            logger.warning("Few R-peaks detected, trying more lenient parameters")
            r_peaks, properties = find_peaks(
                normalized_signal,
                height=np.percentile(normalized_signal, 60),
                distance=int(0.4 * sampling_rate),  # 400ms minimum
                prominence=0.1
            )
        
        # Strategy 3: If still too few, try without height constraint
        if len(r_peaks) < 3:
            logger.warning("Still few R-peaks, trying without height constraint")
            r_peaks, properties = find_peaks(
                normalized_signal,
                distance=int(0.4 * sampling_rate),
                prominence=0.1
            )
        
        return r_peaks
        
    except Exception as e:
        logger.error(f"Error in scipy R-peak detection: {str(e)}")
        raise

def detect_r_peaks_wfdb(ecg_signal, sampling_rate=360):
    """
    R-peak detection using WFDB library with fallback handling
    
    Args:
        ecg_signal: Preprocessed ECG signal
        sampling_rate: Sampling rate in Hz
    
    Returns:
        Array of R-peak indices
    """
    try:
        import wfdb
        
        # Try different WFDB API versions
        try:
            # Try newer API first
            r_peaks = wfdb.processing.gqrs_detect(ecg_signal, fs=sampling_rate)
        except AttributeError:
            # Try older API
            try:
                import wfdb.processing as wfdb_proc
                r_peaks = wfdb_proc.gqrs_detect(ecg_signal, fs=sampling_rate)
            except:
                raise ImportError("WFDB gqrs_detect not available")
        
        return np.array(r_peaks)
        
    except Exception as e:
        logger.warning(f"WFDB R-peak detection failed: {str(e)}")
        raise

def detect_r_peaks(ecg_signal, sampling_rate=360):
    """
    Detect R-peaks with multiple fallback strategies
    
    Args:
        ecg_signal: Preprocessed ECG signal
        sampling_rate: Sampling rate in Hz
    
    Returns:
        Array of R-peak indices
    """
    try:
        # Strategy 1: Try WFDB first (most accurate)
        try:
            r_peaks = detect_r_peaks_wfdb(ecg_signal, sampling_rate)
            logger.info(f"Used WFDB for R-peak detection: {len(r_peaks)} peaks")
        except:
            # Strategy 2: Fall back to scipy
            r_peaks = detect_r_peaks_scipy(ecg_signal, sampling_rate)
            logger.info(f"Used scipy for R-peak detection: {len(r_peaks)} peaks")
        
        # Filter out peaks too close to signal boundaries
        min_distance = int(0.2 * sampling_rate)  # 200ms minimum distance from edges
        valid_peaks = []
        
        for peak in r_peaks:
            if min_distance <= peak < len(ecg_signal) - min_distance:
                valid_peaks.append(peak)
        
        valid_peaks = np.array(valid_peaks)
        
        if len(valid_peaks) == 0:
            raise ValueError("No valid R-peaks found after boundary filtering")
        
        logger.info(f"Final valid R-peaks: {len(valid_peaks)}")
        return valid_peaks
        
    except Exception as e:
        logger.error(f"Error in R-peak detection: {str(e)}")
        raise

def extract_heartbeat_segments(ecg_signal, r_peaks, segment_length=250):
    """
    Extract fixed-length heartbeat segments centered around R-peaks
    
    Args:
        ecg_signal: Preprocessed ECG signal
        r_peaks: Array of R-peak indices
        segment_length: Length of each segment (default 250 samples)
    
    Returns:
        List of heartbeat segments
    """
    segments = []
    half_length = segment_length // 2
    
    try:
        for r_peak in r_peaks:
            start_idx = r_peak - half_length
            end_idx = r_peak + half_length
            
            # Check if segment is within signal boundaries
            if start_idx >= 0 and end_idx < len(ecg_signal):
                segment = ecg_signal[start_idx:end_idx]
                
                # Ensure segment is exactly the required length
                if len(segment) == segment_length:
                    segments.append(segment)
                else:
                    logger.warning(f"Segment length mismatch: expected {segment_length}, got {len(segment)}")
        
        logger.info(f"Extracted {len(segments)} valid segments from {len(r_peaks)} R-peaks")
        return segments
        
    except Exception as e:
        logger.error(f"Error extracting heartbeat segments: {str(e)}")
        raise

def validate_segments(segments, expected_length=250):
    """
    Validate extracted segments for quality and consistency
    
    Args:
        segments: List of heartbeat segments
        expected_length: Expected length of each segment
    
    Returns:
        List of validated segments
    """
    valid_segments = []
    
    for i, segment in enumerate(segments):
        try:
            # Check length
            if len(segment) != expected_length:
                continue
                
            # Check for NaN or infinite values
            if np.any(np.isnan(segment)) or np.any(np.isinf(segment)):
                continue
                
            # Check for flat signals (all zeros or constant values)
            if np.std(segment) < 1e-6:
                continue
                
            # Check for reasonable amplitude range
            if np.max(np.abs(segment)) > 100:  # Unusually high amplitude
                continue
                
            valid_segments.append(segment)
            
        except Exception as e:
            logger.warning(f"Error validating segment {i}: {str(e)}")
            continue
    
    logger.info(f"Validated {len(valid_segments)} segments out of {len(segments)}")
    return valid_segments

def segment_ecg_beats(continuous_ecg, scaler, segment_length=250, sampling_rate=360):
    """
    CRITICAL PREPROCESSING PIPELINE: Convert continuous ECG to model-ready heartbeat segments
    
    The CNN+LSTM model CANNOT process continuous ECG signals directly. It requires:
    - Fixed-length segments (250 samples each)
    - Segments centered around R-peaks 
    - Normalized using the same scaler from training
    
    This function bridges the gap between raw user input and model expectations.
    
    Args:
        continuous_ecg: Continuous ECG signal from uploaded CSV
        scaler: Pre-trained StandardScaler (same one used during model training)
        segment_length: Fixed segment length (250 samples to match training)
        sampling_rate: ECG sampling rate in Hz (360 Hz for MIT-BIH)
    
    Returns:
        List of normalized 250-sample heartbeat segments ready for CNN+LSTM model
    """
    try:
        logger.info(f"Starting preprocessing pipeline for {len(continuous_ecg)} continuous samples")
        
        # Step 1: Filter and clean the continuous signal
        filtered_signal = preprocess_ecg(continuous_ecg, sampling_rate)
        logger.info("Applied bandpass filter and noise reduction")
        
        # Step 2: Detect R-peaks in the continuous signal
        r_peaks = detect_r_peaks(filtered_signal, sampling_rate)
        
        if len(r_peaks) == 0:
            raise ValueError("No R-peaks detected in continuous ECG signal. "
                           "Check signal quality or try different parameters.")
        
        logger.info(f"Detected {len(r_peaks)} R-peaks in continuous signal")
        
        # Step 3: Extract fixed-length segments around each R-peak
        raw_segments = extract_heartbeat_segments(filtered_signal, r_peaks, segment_length)
        
        if len(raw_segments) == 0:
            raise ValueError("No valid heartbeat segments extracted. "
                           "R-peaks may be too close to signal boundaries.")
        
        logger.info(f"Extracted {len(raw_segments)} raw heartbeat segments")
        
        # Step 4: Validate segments for quality
        validated_segments = validate_segments(raw_segments, segment_length)
        
        if len(validated_segments) == 0:
            raise ValueError("No valid heartbeat segments after quality validation.")
        
        if len(validated_segments) < len(raw_segments) * 0.5:
            logger.warning(f"Many segments filtered out: {len(validated_segments)}/{len(raw_segments)} remain")
        
        # Step 5: CRITICAL - Normalize using the SAME scaler from training
        # This ensures compatibility with the trained model
        segments_array = np.array(validated_segments, dtype=np.float32)
        
        # Handle potential memory issues with large arrays
        if segments_array.nbytes > 500 * 1024 * 1024:  # More than 500MB
            logger.warning(f"Large segment array detected: {segments_array.nbytes / (1024*1024):.1f} MB")
        
        normalized_segments = scaler.transform(segments_array)
        
        logger.info(f"Applied normalization using training scaler. "
                   f"Segment stats: mean={np.mean(normalized_segments):.4f}, "
                   f"std={np.std(normalized_segments):.4f}")
        
        # Verify segment dimensions match model expectations
        if normalized_segments.shape[1] != segment_length:
            raise ValueError(f"Segment length mismatch. Expected {segment_length}, "
                           f"got {normalized_segments.shape[1]}")
        
        # Force garbage collection to free memory
        del segments_array, validated_segments, raw_segments, filtered_signal
        gc.collect()
        
        return normalized_segments.tolist()
        
    except Exception as e:
        logger.error(f"Error in continuous ECG to segments pipeline: {str(e)}")
        raise