# Breast-Cancer-Detection-CNN-FastAPI-AWS-Django

python3 -m venv myvenv
source myvenv/bin/activate

pip3 install "fastapi[standard]"
pip3 install -r requirements.txt
pip3 install python-multipart
pip3 install numpy

#!/bin/bash
uvicorn app.main:app --reload

curl -X POST "http://127.0.0.1:8000/predict/" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@image_class1.png"



