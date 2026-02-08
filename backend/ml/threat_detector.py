"""
Advanced ML-based threat detection using transformer models
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib
from transformers import (
    AutoTokenizer, 
    AutoModel,
    RobertaTokenizer, 
    RobertaForSequenceClassification,
    pipeline
)
from sentence_transformers import SentenceTransformer
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import joblib
import asyncio
from pathlib import Path
import json

@dataclass
class ThreatPrediction:
    """Represents a threat prediction"""
    threat_type: str
    confidence: float
    severity: str
    explanation: str
    features: Dict[str, float]
    model_used: str

class CodeBertAnalyzer:
    """CodeBERT-based code understanding and threat detection"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load CodeBERT for code understanding
        self.tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
        self.model = AutoModel.from_pretrained("microsoft/codebert-base").to(self.device)
        
        # Load sentence transformer for semantic similarity
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Known malicious patterns embeddings (would be loaded from training)
        self.malicious_embeddings = self._load_malicious_patterns()
        
        # Fine-tuned classifier head
        self.classifier = self._build_classifier()
        
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
            
    def _build_classifier(self) -> nn.Module:
        """Build classification head for threat detection"""
        return nn.Sequential(
            nn.Linear(768, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 10)  # 10 threat categories
        ).to(self.device)
        
    def _load_malicious_patterns(self) -> Dict[str, np.ndarray]:
        """Load embeddings of known malicious patterns"""
        # In production, these would be loaded from a trained database
        patterns = {
            "backdoor": "Code that creates hidden access points",
            "injection": "Code vulnerable to injection attacks",
            "crypto_weakness": "Weak cryptographic implementations",
            "data_leak": "Code that may leak sensitive data",
            "timing_attack": "Code vulnerable to timing attacks",
            "privilege_escalation": "Code attempting privilege escalation",
            "obfuscation": "Heavily obfuscated code",
            "ransomware": "Ransomware-like behavior patterns",
            "botnet": "Botnet command and control patterns",
            "rootkit": "Rootkit installation patterns"
        }
        
        embeddings = {}
        for threat_type, description in patterns.items():
            embeddings[threat_type] = self.sentence_model.encode(description)
            
        return embeddings
        
    async def analyze_code(self, code: str) -> List[ThreatPrediction]:
        """Analyze code using transformer models"""
        predictions = []
        
        # Get code embedding
        code_embedding = await self._get_code_embedding(code)
        
        # Check similarity with known malicious patterns
        similarities = self._compute_similarities(code_embedding)
        
        # Run through classifier
        threat_scores = await self._classify_threats(code_embedding)
        
        # Generate predictions
        threat_categories = [
            "backdoor", "injection", "crypto_weakness", "data_leak",
            "timing_attack", "privilege_escalation", "obfuscation",
            "ransomware", "botnet", "rootkit"
        ]
        
        for idx, (category, score) in enumerate(zip(threat_categories, threat_scores)):
            if score > 0.3:  # Threshold for reporting
                predictions.append(ThreatPrediction(
                    threat_type=category,
                    confidence=float(score),
                    severity=self._get_severity(category, score),
                    explanation=self._generate_explanation(category, score, similarities),
                    features={"embedding_similarity": similarities.get(category, 0.0)},
                    model_used="CodeBERT"
                ))
                
        return predictions
        
    async def _get_code_embedding(self, code: str) -> np.ndarray:
        """Get CodeBERT embedding for code"""
        # Tokenize code
        inputs = self.tokenizer(
            code,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True
        ).to(self.device)
        
        # Get embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use pooled output or mean of last hidden states
            embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
            
        return embeddings[0]
        
    def _compute_similarities(self, code_embedding: np.ndarray) -> Dict[str, float]:
        """Compute similarity with known malicious patterns"""
        similarities = {}
        
        for threat_type, pattern_embedding in self.malicious_embeddings.items():
            # Cosine similarity
            similarity = np.dot(code_embedding, pattern_embedding) / (
                np.linalg.norm(code_embedding) * np.linalg.norm(pattern_embedding)
            )
            similarities[threat_type] = float(similarity)
            
        return similarities
        
    async def _classify_threats(self, embedding: np.ndarray) -> np.ndarray:
        """Classify threats using neural network"""
        embedding_tensor = torch.FloatTensor(embedding).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            # Pad or truncate to expected size (768)
            if embedding_tensor.shape[1] < 768:
                padding = torch.zeros(1, 768 - embedding_tensor.shape[1]).to(self.device)
                embedding_tensor = torch.cat([embedding_tensor, padding], dim=1)
            elif embedding_tensor.shape[1] > 768:
                embedding_tensor = embedding_tensor[:, :768]
                
            logits = self.classifier(embedding_tensor)
            scores = torch.softmax(logits, dim=1).cpu().numpy()[0]
            
        return scores
        
    def _get_severity(self, threat_type: str, confidence: float) -> str:
        """Determine severity based on threat type and confidence"""
        critical_threats = {"backdoor", "ransomware", "rootkit", "privilege_escalation"}
        high_threats = {"injection", "data_leak", "botnet"}
        
        if threat_type in critical_threats and confidence > 0.7:
            return "CRITICAL"
        elif threat_type in critical_threats or (threat_type in high_threats and confidence > 0.7):
            return "HIGH"
        elif confidence > 0.5:
            return "MEDIUM"
        else:
            return "LOW"
            
    def _generate_explanation(self, threat_type: str, confidence: float, similarities: Dict[str, float]) -> str:
        """Generate human-readable explanation"""
        explanations = {
            "backdoor": "Code exhibits patterns consistent with backdoor implementation",
            "injection": "Code contains potential injection vulnerabilities",
            "crypto_weakness": "Weak or insecure cryptographic practices detected",
            "data_leak": "Code may inadvertently expose sensitive data",
            "timing_attack": "Implementation vulnerable to timing-based attacks",
            "privilege_escalation": "Code attempts to escalate privileges",
            "obfuscation": "Code appears to be intentionally obfuscated",
            "ransomware": "Ransomware-like encryption and extortion patterns detected",
            "botnet": "Command and control communication patterns identified",
            "rootkit": "System-level hiding and persistence mechanisms detected"
        }
        
        base_explanation = explanations.get(threat_type, "Suspicious pattern detected")
        similarity_score = similarities.get(threat_type, 0)
        
        return f"{base_explanation}. Confidence: {confidence:.2%}, Pattern similarity: {similarity_score:.2f}"
        
    def save_model(self, path: str):
        """Save trained model"""
        torch.save({
            'classifier_state_dict': self.classifier.state_dict(),
            'malicious_embeddings': self.malicious_embeddings
        }, path)
        
    def load_model(self, path: str):
        """Load trained model"""
        checkpoint = torch.load(path, map_location=self.device)
        self.classifier.load_state_dict(checkpoint['classifier_state_dict'])
        self.malicious_embeddings = checkpoint['malicious_embeddings']


class AnomalyDetector:
    """Anomaly detection for unknown threats"""
    
    def __init__(self):
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.dbscan = DBSCAN(eps=0.5, min_samples=5)
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def extract_features(self, code: str) -> np.ndarray:
        """Extract statistical features from code"""
        features = []
        
        # Basic metrics
        features.append(len(code))
        features.append(code.count('\n'))
        features.append(code.count(' '))
        features.append(code.count('\t'))
        
        # Complexity metrics
        features.append(code.count('if '))
        features.append(code.count('for '))
        features.append(code.count('while '))
        features.append(code.count('def '))
        features.append(code.count('class '))
        features.append(code.count('import '))
        features.append(code.count('try:'))
        features.append(code.count('except'))
        
        # Suspicious patterns
        features.append(code.count('eval'))
        features.append(code.count('exec'))
        features.append(code.count('__import__'))
        features.append(code.count('compile'))
        features.append(code.count('globals'))
        features.append(code.count('locals'))
        features.append(code.count('setattr'))
        features.append(code.count('getattr'))
        
        # String operations
        features.append(code.count('base64'))
        features.append(code.count('decode'))
        features.append(code.count('encode'))
        features.append(code.count('encrypt'))
        features.append(code.count('decrypt'))
        
        # Network operations
        features.append(code.count('socket'))
        features.append(code.count('request'))
        features.append(code.count('urllib'))
        features.append(code.count('http'))
        
        # File operations
        features.append(code.count('open('))
        features.append(code.count('write'))
        features.append(code.count('read'))
        features.append(code.count('os.'))
        features.append(code.count('subprocess'))
        
        # Calculate entropy
        entropy = self._calculate_entropy(code)
        features.append(entropy)
        
        # Character distribution
        for char in '()[]{}":;,.<>=/\\|':
            features.append(code.count(char))
            
        return np.array(features)
        
    def _calculate_entropy(self, data: str) -> float:
        """Calculate Shannon entropy"""
        if not data:
            return 0
            
        entropy = 0
        for x in range(256):
            p_x = float(data.count(chr(x))) / len(data)
            if p_x > 0:
                import math
                entropy += - p_x * math.log(p_x, 2)
                
        return entropy
        
    async def detect_anomalies(self, code: str) -> List[ThreatPrediction]:
        """Detect anomalies in code"""
        features = self.extract_features(code).reshape(1, -1)
        
        if not self.is_trained:
            # In production, would load pre-trained model
            return []
            
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Isolation Forest prediction
        anomaly_score = self.isolation_forest.decision_function(features_scaled)[0]
        is_anomaly = self.isolation_forest.predict(features_scaled)[0] == -1
        
        predictions = []
        
        if is_anomaly:
            confidence = abs(anomaly_score)
            predictions.append(ThreatPrediction(
                threat_type="unknown_anomaly",
                confidence=min(confidence, 1.0),
                severity="HIGH" if confidence > 0.7 else "MEDIUM",
                explanation=f"Code exhibits unusual patterns not seen in normal code. Anomaly score: {anomaly_score:.3f}",
                features={"anomaly_score": float(anomaly_score)},
                model_used="IsolationForest"
            ))
            
        return predictions
        
    def train(self, code_samples: List[str], labels: Optional[List[int]] = None):
        """Train anomaly detector on code samples"""
        features = np.array([self.extract_features(code) for code in code_samples])
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Train Isolation Forest
        self.isolation_forest.fit(features_scaled)
        
        # Train DBSCAN for clustering
        self.dbscan.fit(features_scaled)
        
        self.is_trained = True
        
    def save_model(self, path: str):
        """Save trained models"""
        joblib.dump({
            'isolation_forest': self.isolation_forest,
            'dbscan': self.dbscan,
            'scaler': self.scaler,
            'is_trained': self.is_trained
        }, path)
        
    def load_model(self, path: str):
        """Load trained models"""
        models = joblib.load(path)
        self.isolation_forest = models['isolation_forest']
        self.dbscan = models['dbscan']
        self.scaler = models['scaler']
        self.is_trained = models['is_trained']


class EnsembleThreatDetector:
    """Ensemble of multiple ML models for robust threat detection"""
    
    def __init__(self, models_dir: Optional[str] = None):
        self.codebert_analyzer = CodeBertAnalyzer(models_dir)
        self.anomaly_detector = AnomalyDetector()
        
        if models_dir:
            anomaly_path = Path(models_dir) / "anomaly_model.joblib"
            if anomaly_path.exists():
                self.anomaly_detector.load_model(str(anomaly_path))
                
    async def analyze(self, code: str) -> Dict[str, Any]:
        """Run ensemble analysis"""
        # Run all models in parallel
        codebert_task = self.codebert_analyzer.analyze_code(code)
        anomaly_task = self.anomaly_detector.detect_anomalies(code)
        
        codebert_predictions, anomaly_predictions = await asyncio.gather(
            codebert_task, anomaly_task
        )
        
        # Combine predictions
        all_predictions = codebert_predictions + anomaly_predictions
        
        # Calculate aggregate threat score
        if all_predictions:
            max_confidence = max(p.confidence for p in all_predictions)
            avg_confidence = sum(p.confidence for p in all_predictions) / len(all_predictions)
        else:
            max_confidence = 0
            avg_confidence = 0
            
        # Group by threat type
        threats_by_type = {}
        for pred in all_predictions:
            if pred.threat_type not in threats_by_type:
                threats_by_type[pred.threat_type] = []
            threats_by_type[pred.threat_type].append(pred)
            
        return {
            "predictions": [self._serialize_prediction(p) for p in all_predictions],
            "threat_score": float(max_confidence),
            "average_confidence": float(avg_confidence),
            "threats_by_type": {
                threat_type: [self._serialize_prediction(p) for p in preds]
                for threat_type, preds in threats_by_type.items()
            },
            "models_used": ["CodeBERT", "IsolationForest"],
            "high_risk": max_confidence > 0.7,
            "recommendations": self._generate_recommendations(all_predictions)
        }
        
    def _serialize_prediction(self, pred: ThreatPrediction) -> Dict[str, Any]:
        """Serialize prediction to dict"""
        return {
            "threat_type": pred.threat_type,
            "confidence": pred.confidence,
            "severity": pred.severity,
            "explanation": pred.explanation,
            "features": pred.features,
            "model_used": pred.model_used
        }
        
    def _generate_recommendations(self, predictions: List[ThreatPrediction]) -> List[str]:
        """Generate security recommendations based on predictions"""
        recommendations = []
        
        threat_types = {p.threat_type for p in predictions if p.confidence > 0.5}
        
        if "backdoor" in threat_types:
            recommendations.append("Perform thorough code review for hidden access points")
            recommendations.append("Check for unauthorized network connections")
            
        if "injection" in threat_types:
            recommendations.append("Implement input validation and sanitization")
            recommendations.append("Use parameterized queries for database operations")
            
        if "crypto_weakness" in threat_types:
            recommendations.append("Update to modern cryptographic algorithms")
            recommendations.append("Use established cryptographic libraries")
            
        if "data_leak" in threat_types:
            recommendations.append("Review data handling and storage practices")
            recommendations.append("Implement proper access controls")
            
        if "obfuscation" in threat_types:
            recommendations.append("Deobfuscate code for security review")
            recommendations.append("Investigate purpose of obfuscation")
            
        if not recommendations:
            recommendations.append("Continue regular security monitoring")
            
        return recommendations