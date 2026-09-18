from __future__ import annotations

import os
import re
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from time import monotonic
from typing import Annotated

import joblib
import numpy as np
import serial
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


BACKEND_DIR = Path(__file__).resolve().parent
MODEL_PATH = BACKEND_DIR / "rbf_svm_1m_raw.joblib"
N_SENSOR_VALUES = 1025
SERIAL_PORT = "COM3"
BAUD_RATE = int(os.getenv("SIGN_SERIAL_BAUD", "115200"))
CAPTURE_TIMEOUT_SECONDS = float(os.getenv("SIGN_CAPTURE_TIMEOUT", "10"))
SERIAL_READ_TIMEOUT_SECONDS = 0.25
SKIP_VALUES = int(os.getenv("SIGN_SKIP_VALUES", "0"))
CAPTURE_COMMAND = os.getenv("SIGN_CAPTURE_COMMAND", "")
NUMBER_PATTERN = re.compile(
    r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
)
capture_lock = threading.Lock()


class PredictRequest(BaseModel):
    signals: Annotated[list[float], Field(min_length=N_SENSOR_VALUES, max_length=N_SENSOR_VALUES)]


class PredictionResponse(BaseModel):
    prediction: str
    samples: int
    port: str | None = None


class CaptureTimeoutError(Exception):
    def __init__(self, received: int):
        self.received = received
        super().__init__(f"Only received {received} sensor values")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

    model = joblib.load(MODEL_PATH)
    if getattr(model, "n_features_in_", None) != N_SENSOR_VALUES:
        raise ValueError(
            f"Model expects {getattr(model, 'n_features_in_', None)} features, "
            f"not {N_SENSOR_VALUES}"
        )
    app.state.model = model
    print(f"Loaded {MODEL_PATH.name}; classes={model.classes_.tolist()}")
    yield
    app.state.model = None


app = FastAPI(title="SignToSpeech Local API", lifespan=lifespan)

allowed_origins = os.getenv(
    "SIGN_CORS_ORIGINS",
    "http://localhost:8080,http://127.0.0.1:8080",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def read_sensor_values(port: str) -> np.ndarray:
    required_values = N_SENSOR_VALUES + SKIP_VALUES
    values: list[float] = []
    deadline = monotonic() + CAPTURE_TIMEOUT_SECONDS

    try:
        with serial.Serial(
            port=port,
            baudrate=BAUD_RATE,
            timeout=SERIAL_READ_TIMEOUT_SECONDS,
            write_timeout=1,
        ) as connection:
            connection.reset_input_buffer()
            if CAPTURE_COMMAND:
                connection.write(CAPTURE_COMMAND.encode("utf-8"))
                connection.flush()

            while len(values) < required_values and monotonic() < deadline:
                line = connection.readline()
                if not line:
                    continue
                text = line.decode("utf-8", errors="ignore")
                values.extend(float(value) for value in NUMBER_PATTERN.findall(text))
    except serial.SerialException as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to read serial port {port}: {exc}",
        ) from exc

    if len(values) < required_values:
        raise CaptureTimeoutError(len(values))

    selected = values[SKIP_VALUES : SKIP_VALUES + N_SENSOR_VALUES]
    sensor_values = np.asarray(selected, dtype=np.float32)
    if not np.isfinite(sensor_values).all():
        raise HTTPException(status_code=422, detail="Sensor data contains invalid values")
    return sensor_values


def predict_sign(model, values: np.ndarray) -> str:
    signals = np.asarray(values, dtype=np.float32)
    if signals.shape != (N_SENSOR_VALUES,):
        raise HTTPException(
            status_code=422,
            detail=f"Expected {N_SENSOR_VALUES} sensor values, got {signals.size}",
        )
    if not np.isfinite(signals).all():
        raise HTTPException(status_code=422, detail="Sensor data contains invalid values")
    return str(model.predict(signals.reshape(1, -1))[0])


@app.get("/health")
def health(request: Request) -> dict[str, object]:
    model = request.app.state.model
    return {
        "status": "ok",
        "model": MODEL_PATH.name,
        "features": int(model.n_features_in_),
        "classes": model.classes_.tolist(),
    }


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictRequest, request: Request) -> PredictionResponse:
    values = np.asarray(payload.signals, dtype=np.float32)
    label = predict_sign(request.app.state.model, values)
    return PredictionResponse(prediction=label, samples=len(values))


@app.post("/capture-predict", response_model=PredictionResponse)
def capture_and_predict(request: Request) -> PredictionResponse:
    if not capture_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="A capture is already in progress")

    try:
        values = read_sensor_values(SERIAL_PORT)
        label = predict_sign(request.app.state.model, values)
        return PredictionResponse(
            prediction=label,
            samples=len(values),
            port=SERIAL_PORT,
        )
    except CaptureTimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail=(
                f"Capture timed out after {CAPTURE_TIMEOUT_SECONDS:g}s: "
                f"received {exc.received}/{N_SENSOR_VALUES + SKIP_VALUES} values"
            ),
        ) from exc
    finally:
        capture_lock.release()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
