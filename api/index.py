# This file serves as the entrypoint for Vercel's Python Serverless Functions.
import sys
import os

# Ensure the root directory is on the python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import the FastAPI app instance from Phase_5
from Phase_5.api import app
