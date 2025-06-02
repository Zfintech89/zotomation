# app_wrapper.py
import webview
import threading
import os
from app import app  # Make sure app.py exposes the Flask app

def start_flask():
    # Run Flask in a separate thread so it doesn't block the GUI
    app.run(host='127.0.0.1', port=51285, debug=False, use_reloader=False)

if __name__ == '__main__':
    # Start Flask in a background thread
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Create a PyWebView window
    webview.create_window("SlideWay AI", "http://127.0.0.1:51285", width=1200, height=800)
    webview.start()