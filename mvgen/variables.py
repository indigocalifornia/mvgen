import os

WSL = os.getenv('WSL')
CUDA = not int(os.getenv('CUDA_DISABLED', 0))
