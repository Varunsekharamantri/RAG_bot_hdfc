import os
import pathlib
from dotenv import load_dotenv

# Test path resolution
project_root = pathlib.Path(__file__).parent.parent.parent
env_path = project_root / ".env"
print(f"Looking for .env at: {env_path}")
print(f"File exists: {env_path.exists()}")

if env_path.exists():
    with open(env_path, 'r') as f:
        content = f.read()
    print(f"File content:\n{content}")

# Try loading
print("\nAttempting to load .env...")
result = load_dotenv(dotenv_path=env_path)
print(f"Load result: {result}")

# Check if API_KEY is set
api_key = os.getenv("API_KEY")
print(f"\nAPI_KEY from os.getenv: {api_key}")

# Check all environment vars
print(f"\nAll vars with 'API' or 'KEY': ")
for key, value in os.environ.items():
    if "API" in key or "KEY" in key:
        masked_value = value[:10] + "..." if len(value) > 10 else value
        print(f"  {key}: {masked_value}")
