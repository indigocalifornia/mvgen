import os

WSL = os.getenv('WSL')
CUDA = not int(os.getenv('CUDA_DISABLED', 0))
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
