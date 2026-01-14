import requests
import time
import sys

def test_local_health():
    url = "http://127.0.0.1:8000/ping"
    print(f"Checking {url}...")
    for i in range(10):
        try:
            resp = requests.get(url, timeout=5)
            print(f"Attempt {i+1}: Status Code: {resp.status_code}")
            if resp.status_code == 200:
                print("[SUCCESS] Server is responsive locally.")
                return True
        except Exception as e:
            print(f"Attempt {i+1}: Failed to connect: {e}")
        time.sleep(2)
    print("[FAILURE] Server did not respond after 10 attempts.")
    return False

if __name__ == "__main__":
    if test_local_health():
        sys.exit(0)
    else:
        sys.exit(1)
