# test_upload.py - Optional testing script
import os
import requests
import json

def test_ecg_prediction(file_path, server_url="http://localhost:5000"):
    """
    Test the ECG prediction API with a continuous ECG CSV file
    
    Note: The API expects continuous ECG data (MIT-BIH format) and handles
    all preprocessing internally to convert it to model-ready segments.
    """
    try:
        print(f"Testing ECG Classification API with: {file_path}")
        print("=" * 60)
        
        # Test health endpoint
        health_response = requests.get(f"{server_url}/health")
        health_data = health_response.json()
        print("🏥 Health Check:")
        print(f"   Status: {health_data['status']}")
        print(f"   Model Loaded: {health_data['model_loaded']}")
        print(f"   Scaler Loaded: {health_data['scaler_loaded']}")
        print()
        
        # Test class information
        classes_response = requests.get(f"{server_url}/classes")
        if classes_response.status_code == 200:
            classes_data = classes_response.json()
            print(f"📊 Available Classes ({classes_data['total_classes']}):")
            for i, class_name in enumerate(classes_data['classes'], 1):
                print(f"   {i}. {class_name}")
            print()
        
        # Test prediction endpoint with continuous ECG data
        print("🔄 Processing Continuous ECG Signal...")
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{server_url}/predict", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ PREDICTION RESULTS:")
            print(f"   📋 Final Diagnosis: {result['predicted_diagnosis']}")
            print(f"   🎯 Confidence: {result['overall_confidence']:.4f}")
            print(f"   💓 Total Heartbeats: {result['total_heartbeats']}")
            print(f"   📈 Continuous Samples: {result['continuous_samples']}")
            print(f"   🗳️  Majority Votes: {result['majority_vote_count']}")
            print()
            
            print("📊 HEARTBEAT-WISE DISTRIBUTION:")
            for diagnosis, stats in result['segment_distribution'].items():
                print(f"   {diagnosis}:")
                print(f"      • Heartbeats: {stats['segment_count']}")
                print(f"      • Percentage: {stats['percentage']}%")
                print(f"      • Avg Confidence: {stats['avg_confidence']:.4f}")
            print()
            
            print("🔍 PREPROCESSING PIPELINE:")
            print(f"   • Continuous ECG → {result['total_heartbeats']} heartbeat segments")
            print(f"   • Each segment: 250 samples (R-peak centered)")
            print(f"   • Normalization: Applied using training scaler")
            print(f"   • Model input: ({result['total_heartbeats']}, 250, 1) tensor")
            print(f"   • Final prediction: Majority voting across segments")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    # Test with MIT-BIH database file
    # These files contain continuous ECG data that will be preprocessed automatically
    test_files = [
        "uploads/100.csv",  # Normal sinus rhythm
        "uploads/104.csv",  
        "uploads/109.csv",
        "uploads/233.csv",
        "uploads/118.csv"
            # Ectopic beats
          # Various arrhythmias
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            test_ecg_prediction(test_file)
            print("\n" + "="*80 + "\n")
        else:
            print(f"Test file not found: {test_file}")
            print("Please place MIT-BIH CSV files in the uploads/ directory")
