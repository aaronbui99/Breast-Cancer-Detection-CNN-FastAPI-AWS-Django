# Deploying the Breast Cancer Detection API to AWS Lambda

This guide explains how to deploy the FastAPI application to AWS Lambda and integrate it with API Gateway and S3.

## Prerequisites

1. AWS CLI installed and configured with appropriate credentials
2. Node.js and NPM installed
3. Serverless Framework installed globally:
   ```
   npm install -g serverless
   ```
4. Install the Serverless Python Requirements plugin:
   ```
   npm install --save-dev serverless-python-requirements
   ```

## Deployment Steps

1. **Configure AWS Credentials**

   You have two options to configure AWS credentials:
   
   **Option 1**: Using the setup script (recommended)
   
   Create a `.env` file in the project root with your AWS credentials:
   ```
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_DEFAULT_REGION=ap-southeast-2
   ```
   
   Then run the setup script:
   ```
   python setup_aws.py
   ```
   
   **Option 2**: Manual configuration
   ```
   aws configure
   ```
   
   When prompted, enter your AWS access key, secret key, and region (ap-southeast-2).

2. **Install Dependencies**

   Install all required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. **Deploy to AWS**

   **Option 1**: Using the deployment script (recommended)
   ```
   python deploy.py
   ```
   
   This script will:
   - Check for required prerequisites
   - Set up AWS credentials from your .env file
   - Install necessary Serverless plugins
   - Deploy the application to AWS
   
   **Option 2**: Manual deployment
   ```
   npm install --save-dev serverless-python-requirements
   serverless deploy
   ```

   This will:
   - Create an S3 bucket for storing images
   - Deploy the FastAPI application as a Lambda function
   - Set up API Gateway to route requests to the Lambda function
   - Configure IAM permissions for S3 access

4. **Testing the Deployment**

   After deployment, Serverless will output the API Gateway endpoint URL. You can test it with:
   ```
   curl -X GET https://your-api-id.execute-api.region.amazonaws.com/health
   ```

   To test the prediction endpoint, use:
   ```
   curl -X POST https://your-api-id.execute-api.region.amazonaws.com/predict \
     -F "file=@/path/to/your/image.jpg"
   ```

## Environment Variables

The following environment variables can be configured:

- `S3_BUCKET_NAME`: The name of the S3 bucket to store images (automatically set by serverless.yml)

## Customizing the Deployment

You can customize the deployment by modifying the `serverless.yml` file:

- Change the AWS region by using the `--region` flag
- Deploy to a different stage with the `--stage` flag
- Adjust memory size and timeout in the provider section
- Modify CORS settings for the S3 bucket

## Troubleshooting

- **Deployment Failures**: Check CloudFormation logs in the AWS Console
- **Lambda Execution Issues**: Check CloudWatch Logs for the Lambda function
- **S3 Access Problems**: Verify IAM permissions in the serverless.yml file

## Cleaning Up

To remove all deployed resources:
```
serverless remove
```