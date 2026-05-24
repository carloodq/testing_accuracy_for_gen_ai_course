from pyngrok import ngrok

# Start tunnel to port 8000
public_url = ngrok.connect(8000)
print(f"ngrok tunnel available at: {public_url}")

# Keep tunnel open
import time
while True:
    time.sleep(1)
