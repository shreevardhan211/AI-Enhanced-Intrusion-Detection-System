#!/usr/bin/env python3
"""
AI-Enhanced Intrusion Detection System - Flask Backend
Serves REST API for the IDS dashboard
"""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os
import sys
import pickle
import threading
import json
from datetime import datetime
import numpy as np
from collections import deque
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='../dashboard/templates', 
            static_folder='../dashboard/static')
CORS(app)

# Global state
class IDSState:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.feature_names = None
        self.logs = deque(maxlen=1000)  # Keep last 1000 logs
        self.stats = {
            'total_packets': 0,
            'normal_packets': 0,
            'attack_packets': 0,
            'dos_count': 0,
            'probe_count': 0,
            'r2l_count': 0,
            'u2r_count': 0,
        }
        self.alerts = deque(maxlen=50)
        self.running = True

ids_state = IDSState()


class MLPredictor:
    """Handle ML model predictions"""
    
    @staticmethod
    def load_model(model_path='ml/model.pkl'):
        """Load pre-trained model"""
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
                ids_state.model = model_data['model']
                ids_state.scaler = model_data['scaler']
                ids_state.label_encoder = model_data['label_encoder']
                ids_state.feature_names = model_data['feature_names']
            logger.info("[✓] Model loaded successfully")
            return True
        except FileNotFoundError:
            logger.error(f"[✗] Model file not found at {model_path}")
            return False
        except Exception as e:
            logger.error(f"[✗] Error loading model: {e}")
            return False
    
    @staticmethod
    def predict(features_dict):
        """Make prediction from feature dictionary"""
        try:
            if ids_state.model is None:
                return {'error': 'Model not loaded'}, 400
            
            # Create feature array in correct order
            feature_array = np.array([
                features_dict.get(feat, 0) for feat in ids_state.feature_names
            ]).reshape(1, -1)
            
            # Normalize using the same scaler
            feature_scaled = ids_state.scaler.transform(feature_array)
            
            # Get prediction
            prediction = ids_state.model.predict(feature_scaled)[0]
            probabilities = ids_state.model.predict_proba(feature_scaled)[0]
            
            # Decode attack type
            attack_type = ids_state.label_encoder.inverse_transform([prediction])[0]
            
            # Get confidence
            confidence = float(max(probabilities)) * 100
            
            return {
                'attack_type': attack_type,
                'confidence': confidence,
                'probabilities': {
                    label: float(prob) * 100
                    for label, prob in zip(ids_state.label_encoder.classes_, probabilities)
                }
            }, 200
        
        except Exception as e:
            logger.error(f"[✗] Prediction error: {e}")
            return {'error': str(e)}, 500


class TrafficSimulator:
    """Simulate network traffic for testing"""
    
    @staticmethod
    def generate_traffic():
        """Generate random traffic sample"""
        attack_type = np.random.choice(
            ['Normal', 'DoS', 'Probe', 'R2L', 'U2R'],
            p=[0.70, 0.15, 0.08, 0.04, 0.03]
        )
        
        features = {
            'src_port': int(np.random.randint(1024, 65535)),
            'dst_port': int(np.random.choice([80, 443, 22, 25, 21, 23])),
            'protocol': int(np.random.choice([6, 17])),
            'packet_length': float(np.random.normal(512, 256)),
            'packet_count': float(np.random.poisson(5) if attack_type == 'Normal' else np.random.poisson(50)),
            'duration': float(np.random.exponential(10)),
            'window_size': int(np.random.randint(512, 65535)),
            'ack_count': float(np.random.poisson(3)),
            'syn_count': float(np.random.poisson(1) if attack_type == 'Normal' else np.random.poisson(50)),
            'rst_count': float(np.random.poisson(0.1)),
            'psh_count': float(np.random.poisson(2)),
            'urg_count': float(np.random.poisson(0.01)),
            'fin_count': float(np.random.poisson(0.5)),
            'flow_rate': float(np.random.normal(100, 30) if attack_type == 'Normal' else np.random.normal(1000, 200)),
            'bytes_in': float(np.random.normal(1024, 512)),
            'bytes_out': float(np.random.normal(512, 256)),
        }
        
        return features


def traffic_processing_thread():
    """Background thread for continuous traffic simulation and processing"""
    import time
    
    while ids_state.running:
        try:
            # Generate traffic
            traffic = TrafficSimulator.generate_traffic()
            
            # Make prediction
            result, status = MLPredictor.predict(traffic)
            
            if status == 200:
                attack_type = result['attack_type']
                confidence = result['confidence']
                
                # Update statistics
                ids_state.stats['total_packets'] += 1
                
                if attack_type == 'Normal':
                    ids_state.stats['normal_packets'] += 1
                else:
                    ids_state.stats['attack_packets'] += 1
                    
                    # Update attack counters
                    if attack_type == 'DoS':
                        ids_state.stats['dos_count'] += 1
                    elif attack_type == 'Probe':
                        ids_state.stats['probe_count'] += 1
                    elif attack_type == 'R2L':
                        ids_state.stats['r2l_count'] += 1
                    elif attack_type == 'U2R':
                        ids_state.stats['u2r_count'] += 1
                    
                    # Create alert
                    alert = {
                        'timestamp': datetime.now().isoformat(),
                        'type': attack_type,
                        'severity': 'CRITICAL' if confidence > 90 else 'HIGH' if confidence > 70 else 'MEDIUM',
                        'confidence': round(confidence, 2),
                        'src_port': traffic['src_port'],
                        'dst_port': int(traffic['dst_port']),
                    }
                    ids_state.alerts.appendleft(alert)
                
                # Log entry
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'attack_type': attack_type,
                    'confidence': round(confidence, 2),
                    'src_port': traffic['src_port'],
                    'dst_port': int(traffic['dst_port']),
                    'packet_count': int(traffic['packet_count']),
                    'severity': 'LOW' if attack_type == 'Normal' else 'HIGH'
                }
                ids_state.logs.appendleft(log_entry)
            
            time.sleep(0.5)  # Simulate 1 packet every 500ms
        
        except Exception as e:
            logger.error(f"[✗] Error in traffic thread: {e}")
            time.sleep(1)


# ============================================================================
# REST API ENDPOINTS
# ============================================================================

@app.route('/')
def index():
    """Serve dashboard"""
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    model_loaded = ids_state.model is not None
    return jsonify({
        'status': 'online' if model_loaded else 'offline',
        'model_loaded': model_loaded,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get current IDS statistics"""
    total = ids_state.stats['total_packets']
    
    return jsonify({
        'total_packets': total,
        'normal_packets': ids_state.stats['normal_packets'],
        'attack_packets': ids_state.stats['attack_packets'],
        'normal_percentage': round((ids_state.stats['normal_packets'] / total * 100) if total > 0 else 0, 2),
        'attack_percentage': round((ids_state.stats['attack_packets'] / total * 100) if total > 0 else 0, 2),
        'attack_breakdown': {
            'DoS': ids_state.stats['dos_count'],
            'Probe': ids_state.stats['probe_count'],
            'R2L': ids_state.stats['r2l_count'],
            'U2R': ids_state.stats['u2r_count'],
        },
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get recent traffic logs"""
    limit = request.args.get('limit', 100, type=int)
    return jsonify({
        'logs': list(ids_state.logs)[:limit],
        'total': len(ids_state.logs),
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get security alerts"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify({
        'alerts': list(ids_state.alerts)[:limit],
        'total': len(ids_state.alerts),
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/predict', methods=['POST'])
def predict():
    """Make prediction on provided features"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    # Required features
    required_features = ids_state.feature_names
    
    # Validate all features are present
    missing_features = [f for f in required_features if f not in data]
    if missing_features:
        return jsonify({
            'error': f'Missing features: {missing_features}'
        }), 400
    
    # Make prediction
    result, status = MLPredictor.predict(data)
    
    # Log the prediction
    if status == 200:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'attack_type': result['attack_type'],
            'confidence': result['confidence'],
            'src_port': data.get('src_port', 0),
            'dst_port': data.get('dst_port', 0),
            'packet_count': data.get('packet_count', 0),
            'severity': 'LOW' if result['attack_type'] == 'Normal' else 'HIGH'
        }
        ids_state.logs.appendleft(log_entry)
    
    return jsonify(result), status


@app.route('/api/model-info', methods=['GET'])
def model_info():
    """Get model information"""
    if ids_state.model is None:
        return jsonify({'error': 'Model not loaded'}), 400
    
    return jsonify({
        'model_type': 'RandomForestClassifier',
        'n_estimators': ids_state.model.n_estimators,
        'classes': ids_state.label_encoder.classes_.tolist(),
        'n_features': len(ids_state.feature_names),
        'features': ids_state.feature_names,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/reset-stats', methods=['POST'])
def reset_stats():
    """Reset all statistics"""
    ids_state.stats = {
        'total_packets': 0,
        'normal_packets': 0,
        'attack_packets': 0,
        'dos_count': 0,
        'probe_count': 0,
        'r2l_count': 0,
        'u2r_count': 0,
    }
    ids_state.logs.clear()
    ids_state.alerts.clear()
    
    return jsonify({
        'status': 'success',
        'message': 'Statistics reset',
        'timestamp': datetime.now().isoformat()
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


def main():
    """Initialize and run the application"""
    print("="*60)
    print("AI-ENHANCED INTRUSION DETECTION SYSTEM")
    print("Backend Server")
    print("="*60 + "\n")
    
    # Load model
    if not MLPredictor.load_model():
        print("[✗] Failed to load model. Run 'python ml/train_model.py' first.")
        sys.exit(1)
    
    # Start background traffic processing thread
    traffic_thread = threading.Thread(target=traffic_processing_thread, daemon=True)
    traffic_thread.start()
    logger.info("[✓] Traffic processing thread started")
    
    # Run Flask app
    print("\n[✓] Starting Flask server...")
    print("[✓] Dashboard available at: http://localhost:5000")
    print("[✓] API available at: http://localhost:5000/api/*\n")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n[✓] Shutting down...")
        ids_state.running = False


if __name__ == '__main__':
    main()
