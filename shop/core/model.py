# myapp/model.py
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib

# Ruta a tus archivos de modelo
# VECTOR_PATH = './core/model/Vectorizer'
# MODEL_PATH = './core/model/Sentiment'

# Cargar el vectorizador y el modelo
def load_model():
    vectorizer = joblib.load('./core/model/Vectorizer')
    model = joblib.load('./core/model/Sentiment')
    return vectorizer, model

vectorizer, model = load_model()

def classify_comment(comment):
    # Convertir el comentario en el formato que espera el modelo
    X = vectorizer.transform([comment])
    # Predecir el sentimiento
    prediction = model.predict(X)
    return 'positive' if prediction[0] == 1 else 'negative'
