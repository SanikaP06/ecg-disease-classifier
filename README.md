# 🫀 ECG Disease Classification Using Deep Learning (CNN + LSTM)

This project detects cardiac arrhythmias from raw ECG signals using a deep learning model built with TensorFlow’s Keras API. The model is deployed via a Flask API that accepts ECG data in .csv format and returns real-time diagnostic predictions with confidence scores.

 Model: CNN + LSTM  
 Dataset: MIT-BIH Arrhythmia  
 Deployment: Flask (Python API)  
 Input: ECG data in .csv files

---

## 🚀 Features

- ✅ R-peak detection using WFDB
- ✅ 250-sample heartbeat segment extraction
- ✅ CNN + LSTM architecture for time-series classification
- ✅ Real-time prediction via Flask API
- ✅ Segment-wise analysis and final diagnosis output
- ✅ .csv upload support with confidence scores

---

## 🧠 Model Architecture

- Built with TensorFlow (Keras API)
- Conv1D layers for spatial feature extraction
- LSTM layers for temporal learning
- Softmax output for multi-class classification
- Trained on heartbeat windows centered on R-peaks (250 samples)

Output classes include:
- Normal
- RBBB (Right Bundle Branch Block)
- LBBB (Left Bundle Branch Block)
- AFIB (Atrial Fibrillation)
- PVC (Premature Ventricular Contraction)

---
## 🗂 Project Structure
```bash
ecg-disease-classifier/
├── app.py # Flask app with /predict API
├── model_training.py # Script to train CNN+LSTM model
├── ecg_utils.py # Signal preprocessing, R-peak detection, scaling
├── cnn_lstm_ecg_classifier_v1.keras # Trained model
├── ecg_scaler.pkl # StandardScaler used for normalization
├── class_mapping.pkl # Dictionary for class index → name
├── requirements.txt # Python dependencies




