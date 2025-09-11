from locust import HttpUser, task, between
import random
import json

# Load the JSON file once at module level for efficiency
with open("data.json", "r") as f:
    request_bodies = json.load(f)

class WebsiteUser(HttpUser):
    # wait_time = between(1, 2)
    host = "http://127.0.0.1:9000"
    
    @task
    def send_random_post(self):
        body = random.choice(request_bodies)
        self.client.post(
            "/sendRequest/",
            json=body
        )
