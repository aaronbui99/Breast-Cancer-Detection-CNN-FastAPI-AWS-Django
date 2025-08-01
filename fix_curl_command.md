# Fixed Curl Command

## The Problem
Your original curl command was corrupting the binary image data because you manually set the Content-Type header:

```bash
# WRONG - This corrupts the image data
curl -X POST "https://bfgtfg14yh.execute-api.ap-southeast-2.amazonaws.com/prod/predict/" \
  -H "accept: application/json" \
  -H "x-api-key: jEseEYjAD05yKdX8VadOm3M3GN5IKfxO7PkHUeNo" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@D:\Documents\Git\Breast-Cancer-Detection-CNN-FastAPI-AWS-Django\image_class1.png"
```

## The Solution
Remove the manual Content-Type header. Curl automatically sets the correct Content-Type with boundary when using `-F`:

```bash
# CORRECT - Let curl handle Content-Type automatically
curl -X POST "https://bfgtfg14yh.execute-api.ap-southeast-2.amazonaws.com/prod/predict/" \
  -H "accept: application/json" \
  -H "x-api-key: jEseEYjAD05yKdX8VadOm3M3GN5IKfxO7PkHUeNo" \
  -F "file=@D:\Documents\Git\Breast-Cancer-Detection-CNN-FastAPI-AWS-Django\image_class1.png"
```

## Why This Happens
When you use `-F` (multipart form data), curl needs to set a boundary in the Content-Type header like:
```
Content-Type: multipart/form-data; boundary=------------------------12345abcdef
```

By manually setting `Content-Type: multipart/form-data` without the boundary, you prevent curl from setting the proper boundary, which corrupts the multipart encoding and causes the image data to be mangled during transmission.

## Alternative - Using Python Script
You can also use the provided Python test script which handles this correctly:

```bash
python test_debug_endpoint.py
```