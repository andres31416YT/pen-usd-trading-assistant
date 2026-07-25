import torch
import json
import os
from pathlib import Path

MODEL_CHECKPOINT_PATH = os.getenv(
    "MODEL_CHECKPOINT_PATH", "/app/model/best_model.pt"
)
MODEL_CONFIG_PATH = os.getenv(
    "MODEL_CONFIG_PATH", "/app/model/model_config.json"
)


class ModelLoader:
    def __init__(self):
        self.model = None
        self.config = None
        self.model_version = None

    def load(self):
        config_path = Path(MODEL_CONFIG_PATH)
        if config_path.exists():
            with open(config_path, "r") as f:
                self.config = json.load(f)

        checkpoint_path = Path(MODEL_CHECKPOINT_PATH)
        if checkpoint_path.exists():
            self.model = torch.load(checkpoint_path, map_location="cpu")
            self.model.eval()
            self.model_version = self.config.get("version", "unknown") if self.config else "unknown"
        else:
            self.model = None
            self.model_version = None

        return self.model is not None

    def predict(self, pair, lookback_days=30):
        if self.model is None:
            return {
                "direction": "neutral",
                "confidence": 0.0,
                "price_target": None,
                "model_version": self.model_version,
            }

        try:
            with torch.no_grad():
                prediction = self.model.predict(pair, lookback_days)

            direction = prediction.get("direction", "neutral")
            confidence = float(prediction.get("confidence", 0.0))
            price_target = float(prediction.get("price_target", 0.0)) if prediction.get("price_target") else None

            return {
                "direction": direction,
                "confidence": round(confidence, 4),
                "price_target": price_target,
                "model_version": self.model_version,
            }
        except Exception:
            return {
                "direction": "neutral",
                "confidence": 0.0,
                "price_target": None,
                "model_version": self.model_version,
            }

    def generate_signal(self, pair):
        if self.model is None:
            return {
                "pair": pair,
                "direction": "neutral",
                "confidence": 0.0,
                "current_price": None,
                "target_price": None,
                "indicator": "model_not_loaded",
            }

        try:
            with torch.no_grad():
                result = self.model.generate_signal(pair)

            return {
                "pair": pair,
                "direction": result.get("direction", "neutral"),
                "confidence": round(float(result.get("confidence", 0.0)), 4),
                "current_price": float(result.get("current_price", 0.0)) if result.get("current_price") else None,
                "target_price": float(result.get("target_price", 0.0)) if result.get("target_price") else None,
                "indicator": result.get("indicator", "unknown"),
            }
        except Exception:
            return {
                "pair": pair,
                "direction": "neutral",
                "confidence": 0.0,
                "current_price": None,
                "target_price": None,
                "indicator": "error",
            }


_model_loader = None


def get_model_loader():
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader()
        _model_loader.load()
    return _model_loader