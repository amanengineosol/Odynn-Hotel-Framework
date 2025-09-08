from locust import HttpUser, TaskSet, task, between
import time


class HotelUserBehavior(TaskSet):
    def on_start(self):
        self.post_data = {
            "request_id": "123e4567-e89b-12d3-a456-426614174021",
            "report_id": "123e4567-e89b-12d3-a456-426614174021",
            "client_id": "1d533815-0d3b-4bd2-b2a4-e9039fa73f52",
            "site_id": 1,
            "site_name": "Marriott",
            "retry_count": 2,
            "parameter": {
                "currency": "USD",
                "hotel_id": "lastd-the-english-hotel-las-vegas-a-tribute-portfolio-hotel",
                "check_in_date": "2026-01-20",
                "check_out_date": "2026-01-24",
                "guest_count": 1,
                "pos": "US"
            }
        }
        response = self.client.post("/api/sendRequest/hotel/", json=self.post_data)
        if response.status_code == 202:
            self.cache_key = response.json().get("key")
            self.start_time = time.time()
            self.poll_count = 0
            self.polling_active = True
        else:
            self.cache_key = None
            self.polling_active = False

    @task
    def poll_for_result(self):
        if not self.polling_active:
            return

        max_polls = 30
        poll_interval = 2  # seconds

        response = self.client.get("/api/sendRequest/hotel/", params={"key": self.cache_key})

        if response.status_code == 200 and response.json().get("response") is not None:
            elapsed = time.time() - self.start_time
            print(f"Response received after {self.poll_count} polls in {elapsed:.2f} seconds")
            self.polling_active = False
            self.interrupt()
        elif self.poll_count >= max_polls:
            print(f"Max polls reached without response for key: {self.cache_key}")
            self.polling_active = False
            self.interrupt()
        else:
            self.poll_count += 1
            self.wait(poll_interval)


class WebsiteUser(HttpUser):
    tasks = [HotelUserBehavior]
    wait_time = between(1, 3)
