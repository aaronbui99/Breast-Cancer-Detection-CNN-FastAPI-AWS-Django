from fastapi import FastAPI, UploadFile, File
from PIL import Image
import io
from app.predict import predict_route

app = FastAPI()
app.include_router(predict_route, prefix="/predict")

