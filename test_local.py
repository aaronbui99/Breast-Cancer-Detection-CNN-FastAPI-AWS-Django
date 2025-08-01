import uvicorn
import os

# Set environment variables for local testing
os.environ["S3_BUCKET_NAME"] = "test-bucket-local"

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)