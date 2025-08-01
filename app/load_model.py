import torch
from app.model import SimpleCNN  # your model definition
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_cnn_model():
    try:
        model_path = "models/best_model.pth"
        logger.info(f"Attempting to load model from: {model_path}")
        
        # Check if model file exists
        if not os.path.exists(model_path):
            logger.error(f"Model file not found at: {model_path}")
            logger.info(f"Current working directory: {os.getcwd()}")
            logger.info(f"Directory contents: {os.listdir(os.path.dirname(model_path) if os.path.dirname(model_path) else '.')}")
            raise FileNotFoundError(f"Model file not found at: {model_path}")
        
        model = SimpleCNN()
        model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
        logger.info("Model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise
