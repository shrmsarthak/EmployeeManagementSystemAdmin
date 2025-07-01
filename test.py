import requests
import json

def test_google_geolocation_api(api_key):
    """
    Test the Google Maps Geolocation API key.
    """
    url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={api_key}"

    # Empty body: Google will geolocate via IP
    body = {}

    try:
        response = requests.post(url, json=body, timeout=10)
        data = response.json()

        if response.status_code == 200:
            print("✅ API Key is working.")
            print("Location:", data.get("location"))
            print("Accuracy (meters):", data.get("accuracy"))
            return True
        else:
            print("❌ API Error:")
            print(json.dumps(data, indent=2))
            return False

    except requests.exceptions.RequestException as e:
        print("❌ Request failed:", e)
        return False

if __name__ == "__main__":
    # Paste your real API key here:
    YOUR_API_KEY = "AIzaSyBjTYnRgK9kGRtBCGvHsXaho3EZVkqTiWo"

    if not YOUR_API_KEY:
        print("⚠️ Please set your API key in the script.")
    else:
        test_google_geolocation_api(YOUR_API_KEY)
