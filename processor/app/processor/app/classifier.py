# Basit TF-IDF + LogisticRegression yükleyici (model.joblib ve vect.joblib aynı klasörde olacak)
import joblib
import os

MODEL_PATH = os.getenv("MODEL_PATH", "./model.joblib")
VECT_PATH = os.getenv("VECT_PATH", "./vect.joblib")

class MailClassifier:
    def __init__(self):
        if not os.path.exists(MODEL_PATH) or not os.path.exists(VECT_PATH):
            raise RuntimeError("Model veya vect bulunamadı. model_train.py ile oluştur.")
        self.model = joblib.load(MODEL_PATH)
        self.vect = joblib.load(VECT_PATH)

    def predict(self, subject, body):
        text = (subject or "") + "\n" + (body or "")
        X = self.vect.transform([text])
        pred = self.model.predict(X)[0]
        proba = max(self.model.predict_proba(X)[0])
        return {"category": pred, "confidence": float(proba)}
