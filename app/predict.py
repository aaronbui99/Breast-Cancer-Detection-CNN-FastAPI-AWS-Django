from fastapi import APIRouter, UploadFile, File
from PIL import Image
import torch
import torchvision.transforms as transforms
from app.load_model import load_cnn_model
import io

predict_route = APIRouter()
model = load_cnn_model()

@predict_route.post("/")
async def predict(file: UploadFile = File(...)):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")

    transform = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
    ])
    input_tensor = transform(image).unsqueeze(0)

    model.eval()
    with torch.no_grad():
        output = model(input_tensor)
        prob = torch.sigmoid(output).item()
        predicted_class = 1 if prob > 0.5 else 0

    return {"prediction": predicted_class, "probability": prob}