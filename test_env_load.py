import os
import pathlib

env_path = pathlib.Path(".env")
print(f"Loading from: {env_path.resolve()}")
print(f"File exists: {env_path.exists()}")

if env_path.exists():
    print("Reading file with utf-8-sig...")
    with open(env_path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            print(f"Raw line: {repr(line)}")
            line = line.strip()
            if line and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                print(f"  Setting: {key} = {value[:20]}...")
                os.environ[key] = value

print(f"\nAfter setting:")
api_key = os.getenv("API_KEY")
print(f"API_KEY from os.getenv: {api_key[:20] if api_key else None}...")
