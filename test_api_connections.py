import os
import requests
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
bearer_token = os.getenv("BEARER_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Test Twitter API
url = "https://api.twitter.com/2/users/by/username/elonmusk"
headers = {"Authorization": f"Bearer {bearer_token}"}
response = requests.get(url, headers=headers)
print("Twitter API Response:", response.status_code, response.text)

# Test OpenAI API
try:
    response = openai.Completion.create(
        engine="davinci",
        prompt="Say hello!",
        max_tokens=5
    )
    print("OpenAI Response:", response.choices[0].text.strip())
except Exception as e:
    print("OpenAI API Error:", e)
