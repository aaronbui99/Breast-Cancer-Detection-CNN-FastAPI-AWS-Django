import torch
from app.model import SimpleCNN  # your model definition
import os

def load_cnn_model():
    model = SimpleCNN()
    model.load_state_dict(torch.load("models/best_model.pth", map_location=torch.device('cpu')))
    return model
