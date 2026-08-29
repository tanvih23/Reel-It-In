import requests
import os
from dotenv import load_dotenv

load_dotenv()

REKA_API_KEY = os.getenv("REKA_API_KEY")

print("Testing Reka connection...")
print()

# 1. Check that the API key exists
if not REKA_API_KEY:
    print("❌ REKA_API_KEY was not found in .env")
    exit()

print("✅ API key found in .env")
print()

# 2. Test Reka Vision server
url = "https://vision-agent.api.reka.ai/health"

try:
    response = requests.get(url, timeout=10)

    print("HTTP status:", response.status_code)
    print("Response:", response.text)

    if response.ok:
        print()
        print("✅ Reka Vision server is reachable!")
    else:
        print()
        print("⚠️ Server reached, but returned an unexpected status.")

except requests.exceptions.ConnectionError as e:
    print()
    print("❌ Could not connect to Reka.")
    print()
    print("This is most likely a DNS/network problem.")
    print(e)

except requests.exceptions.Timeout:
    print()
    print("❌ Reka request timed out.")

except Exception as e:
    print()
    print("❌ Unexpected error:")
    print(e)