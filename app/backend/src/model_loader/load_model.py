import math
import torch
import torch.nn as nn
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env", override=True)

MODEL_CHECKPOINT_PATH = os.getenv("MODEL_CHECKPOINT_PATH")
MODEL_CONFIG_PATH = os.getenv("MODEL_CONFIG_PATH")


class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 1000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float32).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2, dtype=torch.float32) * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x):
        return x + self.pe[:, : x.size(1), :]


class PatchEmbedding(nn.Module):
    def __init__(self, patch_len: int, patch_stride: int, d_model: int):
        super().__init__()
        self.patch_len = patch_len
        self.patch_stride = patch_stride
        self.projection = nn.Linear(patch_len, d_model)

    def forward(self, x):
        x = x.squeeze(-1)
        patches = x.unfold(dimension=1, size=self.patch_len, step=self.patch_stride)
        embedded = self.projection(patches)
        return embedded


class PatchTSTForecaster(nn.Module):
    def __init__(self, lookback_window: int, forecast_horizon: int,
                 patch_len: int, patch_stride: int,
                 d_model: int, n_heads: int, n_layers: int,
                 d_ff: int, dropout: float):
        super().__init__()
        self.patch_embedding = PatchEmbedding(patch_len, patch_stride, d_model)
        n_patches = (lookback_window - patch_len) // patch_stride + 1
        self.positional_encoding = PositionalEncoding(d_model, max_len=n_patches + 1)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dim_feedforward=d_ff,
            dropout=dropout, batch_first=True, activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.norm = nn.LayerNorm(d_model)
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(n_patches * d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, forecast_horizon),
        )

    def forward(self, x):
        embedded = self.patch_embedding(x)
        embedded = self.positional_encoding(embedded)
        encoded = self.encoder(embedded)
        encoded = self.norm(encoded)
        forecast = self.head(encoded)
        return forecast


def _get_yahoo_latest_price(symbol: str) -> float:
    from market_data.yahoo import get_latest_price
    return get_latest_price(symbol)


def _load_checkpoint(checkpoint_path: str):
    return torch.load(checkpoint_path, map_location="cpu", weights_only=False)


def _reconstruct_model(checkpoint: dict) -> PatchTSTForecaster:
    cfg = checkpoint["config"]
    model = PatchTSTForecaster(
        lookback_window=cfg["lookback_window"],
        forecast_horizon=cfg["forecast_horizon"],
        patch_len=cfg["patch_len"],
        patch_stride=cfg["patch_stride"],
        d_model=cfg["d_model"],
        n_heads=cfg["n_heads"],
        n_layers=cfg["n_layers"],
        d_ff=cfg["d_ff"],
        dropout=cfg["dropout"],
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model


def _generar_senal(precio_actual: float, precio_predicho: float,
                   buy_threshold_pct: float = 0.5, sell_threshold_pct: float = -0.5):
    cambio_pct = ((precio_predicho - precio_actual) / precio_actual) * 100
    if cambio_pct <= sell_threshold_pct:
        accion = "buy"
    elif cambio_pct >= buy_threshold_pct:
        accion = "sell"
    else:
        accion = "neutral"
    magnitud = abs(cambio_pct)
    if magnitud >= 2 * abs(buy_threshold_pct):
        confianza = "alta"
    elif magnitud >= abs(buy_threshold_pct):
        confianza = "media"
    else:
        confianza = "baja"
    return accion, max(min(abs(cambio_pct) / 10, 1.0), 0.0), confianza


def _obtener_precios_historicos(pair: str, lookback_days: int, min_points: int) -> list:
    symbol_map = {"PEN/USD": "PEN=X"}
    symbol = symbol_map.get(pair, pair)
    from market_data.yahoo import get_price_history
    timeframe_candidates = ["5D", "1M", "3M", "1Y", "5Y", "Max"]
    data = []
    for timeframe in timeframe_candidates:
        try:
            data = get_price_history(symbol, timeframe)
            if len(data) >= min_points:
                break
        except Exception:
            continue
    return [float(item["price"]) for item in data]


class ModelLoader:
    def __init__(self):
        self.model = None
        self.config = None
        self.checkpoint = None
        self.model_version = None

    def load(self):
        config_path = Path(MODEL_CONFIG_PATH)
        if config_path.exists():
            with open(config_path, "r") as f:
                self.config = json.load(f)

        checkpoint_path = Path(MODEL_CHECKPOINT_PATH)
        if checkpoint_path.exists():
            self.checkpoint = _load_checkpoint(str(checkpoint_path))
            self.model = _reconstruct_model(self.checkpoint)
            self.model_version = self.config.get("version", "unknown") if self.config else "unknown"
        else:
            self.model = None
            self.model_version = None

        return self.model is not None

    def predict(self, pair, lookback_days=30, spread_multiplier=1.0):
        if self.model is None:
            return {
                "direction": "neutral",
                "confidence": 0.0,
                "price_target": None,
                "model_version": self.model_version,
                "spread_multiplier": spread_multiplier,
            }

        try:
            precios = _obtener_precios_historicos(pair, lookback_days, self.checkpoint["config"]["lookback_window"])
            if len(precios) < self.checkpoint["config"]["lookback_window"]:
                return {
                    "direction": "neutral",
                    "confidence": 0.0,
                    "price_target": None,
                    "model_version": self.model_version,
                    "spread_multiplier": spread_multiplier,
                }

            mean = float(self.checkpoint["norm_mean"])
            std = float(self.checkpoint["norm_std"])
            lookback = self.checkpoint["config"]["lookback_window"]
            ventana = precios[-lookback:]
            ventana_norm = [(p - mean) / (std + 1e-8) for p in ventana]
            x = torch.tensor(ventana_norm, dtype=torch.float32).view(1, lookback, 1)

            with torch.no_grad():
                pred_norm = self.model(x).squeeze(0).numpy()

            pred_real = pred_norm * (std + 1e-8) + mean
            precio_actual = precios[-1]
            precio_predicho = float(pred_real[0])

            precio_actual_ajustado = precio_actual * spread_multiplier
            precio_predicho_ajustado = precio_predicho * spread_multiplier

            direction, confidence, conf_str = _generar_senal(
                precio_actual_ajustado, precio_predicho_ajustado, buy_threshold_pct=0.5, sell_threshold_pct=-0.5
            )

            return {
                "direction": direction,
                "confidence": round(confidence, 4),
                "price_target": round(precio_predicho_ajustado, 4),
                "model_version": self.model_version,
                "spread_multiplier": spread_multiplier,
            }
        except Exception:
            return {
                "direction": "neutral",
                "confidence": 0.0,
                "price_target": None,
                "model_version": self.model_version,
                "spread_multiplier": spread_multiplier,
            }

    def generate_signal(self, pair, spread_multiplier=1.0):
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
            current_price = _get_yahoo_latest_price("PEN=X")
            prediction = self.predict(pair, lookback_days=30, spread_multiplier=spread_multiplier)
            return {
                "pair": pair,
                "direction": prediction["direction"],
                "confidence": prediction["confidence"],
                "current_price": current_price * spread_multiplier if current_price else None,
                "target_price": prediction.get("price_target"),
                "indicator": "forecast",
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