from fastapi import FastAPI, UploadFile, File
from PIL import Image
import io
from app.load_model import load_cnn_model
from app.predict import predict_route

app = FastAPI()
app.include_router(predict_route, prefix="/predict")
model = load_cnn_model()

@app.get("/")
def read_root():
    return {"message": "Model is loaded and ready!"}
