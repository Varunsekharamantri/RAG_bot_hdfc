import os

env_file_path = r"c:\Users\Admin\Desktop\Varun\RAG Chatbot\.env"
print(f"Checking file: {env_file_path}")
print(f"File exists: {os.path.exists(env_file_path)}")

if os.path.exists(env_file_path):
    print(f"File size: {os.path.getsize(env_file_path)} bytes")
    with open(env_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"Raw content (repr): {repr(content)}")
    print(f"Raw content (str):\n{content}")
    
    # Check for API_KEY
    lines = content.split('\n')
    for i, line in enumerate(lines):
        print(f"Line {i}: {repr(line)}")
