from dotenv import load_dotenv
import os

# Clear any existing environment variables
os.environ.clear()

# Load environment variables with override
load_dotenv(override=True)

# Print all Twitter-related environment variables
print("X (Twitter) Environment Variables:")
print("-" * 30)
for key, value in os.environ.items():
    if key.startswith('X_'):
        print(f"{key}: {value}")
