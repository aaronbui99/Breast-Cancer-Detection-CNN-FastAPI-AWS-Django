# Use AWS Lambda Python 3.10 base image
FROM public.ecr.aws/lambda/python:3.10

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install dependencies with optimizations
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torch==2.0.0+cpu torchvision==0.15.0+cpu && \
    pip install --no-cache-dir \
    fastapi uvicorn Pillow python-multipart numpy mangum boto3

# Copy application code
COPY app/ ./app/
COPY models/ ./models/

# Set the handler
CMD ["app.main.handler"]