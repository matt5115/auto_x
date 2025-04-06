import requests

# Hardcode the bearer token
bearer_token = "AAAAAAAAAAAAAAAAAAAAAE1Q0QEAAAAAV1STdkcJlI0u6u7zwcYe%2Br2QMFU%3DKfVG8nV6AoSr1x9bD8NQiMFCtb8ayMl6u5sARTbuY3QkwQEwHe"

# Print the bearer token to verify it's loaded correctly
print("Loaded Bearer Token:", bearer_token)

# Define the URL for the test request
url = "https://api.twitter.com/2/users/by/username/elonmusk"
headers = {"Authorization": f"Bearer {bearer_token}"}

# Make the request
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raises an error for bad status codes
    print("Response:", response.json())
except Exception as e:
    print(f"Error: {e}")
