import requests
import json
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

class WebhookError():
    def __init__(self):
        self.GOOGLE_CHAT_WEBHOOK_URL = os.getenv('WEBHOOK_URL')
        
    async def send_google_chat_alert(self,message_text):
        """Sends a text message alert to a Google Chat webhook."""
        headers = {'Content-Type': 'application/json; charset=UTF-8'}
        payload = {'text': message_text}
        try:
            response = requests.post(url=self.GOOGLE_CHAT_WEBHOOK_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status()  # Raise an exception for bad status codes
            print("Alert sent successfully to Google Chat.")
        except requests.exceptions.RequestException as e:
            print(f"Error sending alert to Google Chat: {e}")

if __name__ == "__main__":
    alert_message = "Urgent: Server is getting 429 Error for client requests."
    # obj = WebhookError()
    # obj.send_google_chat_alert(alert_message)
    asyncio.run(WebhookError().send_google_chat_alert(alert_message))
