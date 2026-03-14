"""
AI Predictive Module
Train model on historical signals to predict crash probability
"""
import os
import json
import pickle
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from ..utils.db import db
from ..utils.logger import logger

class CrashPredictor:
    MODEL_PATH = "/home/ubuntu/crash_radar/models/crash_model.pkl"
    SCALER_PATH = "/home/ubuntu/crash_radar/models/scaler.pkl"
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.is_trained = False
        
    def _prepare_features(self, signals: List[dict]) -> tuple:
        """Prepare features for training/prediction"""
        X = []
        y = []
        
        for i, signal in enumerate(signals):
            if i == 0:
                continue
                
            features = [
                signals[i-1].get("score", 0),
                signals[i-1].get("rsi", 50) or 50,
                signals[i-1].get("oi_pct", 0) or 0,
                signals[i-1].get("fear_index", 50) or 50,
                1 if signals[i-1].get("cycle_phase") in ["Accumulation", "Run-Up"] else 0,
                1 if signals[i-1].get("signal_type") == "RISK OFF" else 0,
            ]
            
            crash_next = 1 if signal.get("signal_type") == "RISK OFF" else 0
            
            X.append(features)
            y.append(crash_next)
        
        return np.array(X), np.array(y)
    
    def _get_training_data(self, min_records: int = 10) -> List[dict]:
        """Get historical signals for training"""
        query = """
            SELECT * FROM signals 
            ORDER BY created_at DESC 
            LIMIT %s
        """
        results = db.execute(query, (min_records * 2,))
        return list(reversed(results))
    
    def train(self) -> Dict:
        """Train the crash prediction model"""
        signals = self._get_training_data(min_records=20)
        
        if len(signals) < 20:
            logger.warning(f"Insufficient data for training: {len(signals)} records (need 20+)")
            return {"status": "insufficient_data", "records": len(signals)}
        
        try:
            X, y = self._prepare_features(signals)
            
            if len(y) < 10:
                return {"status": "insufficient_features", "samples": len(y)}
            
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=42,
                class_weight="balanced"
            )
            self.model.fit(X_scaled, y)
            
            os.makedirs(os.path.dirname(self.MODEL_PATH), exist_ok=True)
            
            with open(self.MODEL_PATH, "wb") as f:
                pickle.dump(self.model, f)
            with open(self.SCALER_PATH, "wb") as f:
                pickle.dump(self.scaler, f)
            
            train_accuracy = self.model.score(X_scaled, y)
            
            self.is_trained = True
            
            logger.info(f"Model trained: {len(y)} samples, accuracy: {train_accuracy:.2%}")
            
            return {
                "status": "success",
                "samples": len(y),
                "accuracy": train_accuracy,
                "crash_rate": float(np.mean(y))
            }
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def predict(self, current_signal: dict) -> Optional[Dict]:
        """Predict crash probability for next period"""
        if not self.is_trained:
            if not self.load():
                logger.warning("No trained model available")
                return None
        
        try:
            features = [
                current_signal.get("score", 0),
                current_signal.get("rsi", 50) or 50,
                current_signal.get("oi_pct", 0) or 0,
                current_signal.get("fear_index", 50) or 50,
                1 if current_signal.get("cycle_phase") in ["Accumulation", "Run-Up"] else 0,
                1 if current_signal.get("signal_type") == "RISK OFF" else 0,
            ]
            
            X = np.array([features])
            X_scaled = self.scaler.transform(X)
            
            proba = self.model.predict_proba(X_scaled)[0]
            prediction = self.model.predict(X_scaled)[0]
            
            result = {
                "crash_probability": float(proba[1]),
                "safe_probability": float(proba[0]),
                "prediction": "CRASH" if prediction == 1 else "SAFE",
                "confidence": float(max(proba)),
                "timestamp": datetime.now().isoformat()
            }
            
            db.insert_one("signals_predicted", {
                "crash_probability": result["crash_probability"],
                "prediction": result["prediction"],
                "confidence": result["confidence"],
                "signal_id": current_signal.get("id"),
                "created_at": datetime.now()
            })
            
            logger.info(f"Prediction: {result['prediction']} ({result['crash_probability']:.1%} crash prob)")
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return None
    
    def load(self) -> bool:
        """Load trained model from disk"""
        try:
            if os.path.exists(self.MODEL_PATH) and os.path.exists(self.SCALER_PATH):
                with open(self.MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                with open(self.SCALER_PATH, "rb") as f:
                    self.scaler = pickle.load(f)
                self.is_trained = True
                logger.info("Model loaded from disk")
                return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
        return False
    
    def backtest(self) -> Dict:
        """Backtest predictions against historical data"""
        signals = self._get_training_data(min_records=50)
        
        if len(signals) < 50:
            return {"status": "insufficient_data", "records": len(signals)}
        
        self.load()
        
        correct = 0
        total = 0
        
        for i in range(20, len(signals)):
            train_set = signals[:i]
            test_signal = signals[i]
            
            X, y = self._prepare_features(train_set)
            
            if len(y) < 10:
                continue
                
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            model = RandomForestClassifier(n_estimators=50, max_depth=3, random_state=42)
            model.fit(X_scaled, y)
            
            features = [
                signals[i-1].get("score", 0),
                signals[i-1].get("rsi", 50) or 50,
                signals[i-1].get("oi_pct", 0) or 0,
                signals[i-1].get("fear_index", 50) or 50,
                1 if signals[i-1].get("cycle_phase") in ["Accumulation", "Run-Up"] else 0,
                1 if signals[i-1].get("signal_type") == "RISK OFF" else 0,
            ]
            
            X_test = scaler.transform([features])
            pred = model.predict(X_test)[0]
            actual = 1 if test_signal.get("signal_type") == "RISK OFF" else 0
            
            if pred == actual:
                correct += 1
            total += 1
        
        accuracy = correct / total if total > 0 else 0
        
        return {
            "status": "success",
            "backtest_accuracy": accuracy,
            "correct": correct,
            "total": total
        }


def train_model():
    """Train the crash prediction model"""
    db.initialize()
    predictor = CrashPredictor()
    result = predictor.train()
    db.close()
    return result


def predict_crash():
    """Make a prediction based on latest signal"""
    db.initialize()
    predictor = CrashPredictor()
    
    latest = db.execute_one("SELECT * FROM signals ORDER BY created_at DESC LIMIT 1")
    
    if not latest:
        logger.warning("No signals found for prediction")
        db.close()
        return None
    
    result = predictor.predict(latest)
    db.close()
    return result


if __name__ == "__main__":
    print("Crash Predictor AI Module")
    print("=" * 40)
    
    result = train_model()
    print(f"Training result: {result}")
    
    if result.get("status") == "success":
        prediction = predict_crash()
        print(f"Prediction: {prediction}")
