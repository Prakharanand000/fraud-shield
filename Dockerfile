FROM python:3.11-slim
WORKDIR /app

# Install all deps (use ml-service pinned versions; they cover quickstart needs too)
COPY ml-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir fastapi uvicorn[standard] starlette

# Train model at build time so it ships baked into the image
COPY ml-service/ ml-service/
RUN python ml-service/train_model.py && \
    mv fraud_model.joblib ml-service/fraud_model.joblib

# Copy rest of the project
COPY quickstart.py quickstart-requirements.txt ./
COPY java-service/src/main/resources/static/ java-service/src/main/resources/static/

EXPOSE 8080
CMD python quickstart.py
