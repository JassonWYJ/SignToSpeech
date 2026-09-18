# SignToSpeech

Local sign-language demo using a 1025-sensor board and an RBF-SVM model.

## Run the local demo

Install the backend dependencies:

```bash
python -m pip install -r backend/requirements.txt
```

Start the backend from the repository root:

```bash
python backend/main.py
```

In another terminal, start the frontend:

```bash
cd frontend
npm install
npm run serve
```

Open <http://localhost:8080>. The right side is blank before recognition.
Press `Space` or `s` to start recognition. The backend always reads `COM3`,
collects exactly 1025 numeric values at 115200 baud, and passes them directly to
`backend/rbf_svm_1m_raw.joblib`. The frontend then shows the predicted label and
plays the matching MP4 from `frontend/src/assets/videos` plus its MP3 sound.

Optional environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `SIGN_SERIAL_BAUD` | `115200` | Serial baud rate |
| `SIGN_CAPTURE_TIMEOUT` | `10` | Capture timeout in seconds |
| `SIGN_SKIP_VALUES` | `0` | Numeric header values to discard before the 1025 sensors |
| `SIGN_CAPTURE_COMMAND` | empty | Text written to the board before reading |

## Training-set heatmap

Generate the confusion matrix produced by predicting the model's own training
data:

```bash
python backend/plot_training_confusion.py
```

The image is saved as `backend/training_confusion_heatmap.png`. It measures
training-set fit only and must not be reported as field accuracy.
