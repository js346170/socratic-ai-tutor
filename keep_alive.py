# keep_alive.py
import requests
import time
import threading

def ping_app():
    """Ping the app every 10 minutes to keep it awake"""
    while True:
        try:
            # Replace with your actual Streamlit Cloud URL
            requests.get("https://your-app-name.streamlit.app/", timeout=10)
            print("Ping successful - app kept awake")
        except Exception as e:
            print(f"Ping failed: {e}")
        time.sleep(600)  # Ping every 10 minutes

# Start the keep-alive in a background thread
def start_keep_alive():
    thread = threading.Thread(target=ping_app, daemon=True)
    thread.start()