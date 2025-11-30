# Toy trainer: gerçek veriyle değiştir. Bu script model.joblib ve vect.joblib oluşturur.
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib

texts = [
    "Meeting at 10am tomorrow",
    "Invoice for your purchase",
    "Limited time offer! Buy now",
    "Reset your password using this link",
    "John invited you to connect on LinkedIn",
    "Your package has shipped"
]
labels = ["business","business","promotion","security","social","personal"]

vect = TfidfVectorizer(max_features=2000)
X = vect.fit_transform(texts)
model = LogisticRegression(max_iter=200)
model.fit(X, labels)

joblib.dump(model, "model.joblib")
joblib.dump(vect, "vect.joblib")
print("Model and vectorizer saved (model.joblib, vect.joblib).")
