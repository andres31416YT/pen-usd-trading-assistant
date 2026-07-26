# ---- Etapa de build: descarga el modelo ----
FROM python:3.11-slim AS builder

WORKDIR /app
RUN pip install --no-cache-dir huggingface_hub

RUN python3 -c "\
from huggingface_hub import hf_hub_download; \
import shutil, os; \
os.makedirs('/app/model', exist_ok=True); \
path = hf_hub_download(repo_id='andres31416/pen-usd-trading-model', filename='checkpoints/best_model.pt'); \
shutil.copy(path, '/app/model/best_model.pt')"

# ---- Etapa final ----
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /app/model/best_model.pt /tmp/model/best_model.pt

RUN mkdir -p /app/model

ENV MODEL_CHECKPOINT_PATH=/app/model/best_model.pt

CMD ["sh", "-c", "if [ ! -f /app/model/best_model.pt ]; then cp /tmp/model/best_model.pt /app/model/best_model.pt; fi; sleep infinity"]