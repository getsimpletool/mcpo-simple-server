from locust import HttpUser, task, between
import random
import json


class MCPToolUser(HttpUser):
    # Set the host directly in the class
    host = "http://localhost:8000"

    # Wait time between tasks (simulates user think time)
    # wait_time = between(0.5, 2)

    # Cities for weather forecast
    CITIES = [
        "WaasadsdasDA"  # Invalid city to test error handling
    ]

    # Time converter input formats
    TIME_FORMATS = [
        {"date_time_str": "NOW"},
        {"date_time_str": "NOW", "to_timezone": "America/New_York"}
    ]

    # @task(3)  # Weight: more frequent weather forecast tests
    def test_weather_forecast(self):
        """Test weather forecast tool with random cities"""
        city = random.choice(self.CITIES)
        payload = {
            "arguments": {
                "city": city,
                "days": random.randint(1, 7)
            }
        }

        with self.client.post(
            "/tools/call?name=weather_us_forecast",  # Add name as query parameter
            json=payload,
            catch_response=True
        ) as response:
            try:
                # Check if response contains text content
                if "text" in response.text:
                    response.success()
                else:
                    response.failure(f"Invalid response for city {city} -> {response.text}")
            except Exception as e:
                response.failure(str(e))

    @task(2)  # Weight: time converter tests
    def test_time_converter(self):
        """Test time converter tool with various input formats"""
        time_args = random.choice(self.TIME_FORMATS)
        payload = {
            "arguments": time_args
        }

        with self.client.post(
            "/tools/call?name=time_converter",
            json=payload,
            catch_response=True
        ) as response:
            try:
                # Check if response contains text content
                if "text" in response.text:
                    response.success()
                else:
                    # Include full response for debugging
                    response.failure(f"Invalid response for time args {time_args} -> {response.text}")
            except Exception as e:
                response.failure(f"Error processing time converter response: {str(e)}")

    # @task(1)  # Occasional current weather test
    def test_current_weather(self):
        """Test current weather tool"""
        payload = {
            "arguments": {
                "city": random.choice(self.CITIES)
            }
        }

        with self.client.post(
            "/tools/call?name=weather_us_current",
            json=payload,
            catch_response=True
        ) as response:
            try:
                # Check if response contains text content
                if "text" in response.text:
                    response.success()
                else:
                    response.failure(f"Invalid current weather response -> {response.text}")
            except Exception as e:
                response.failure(str(e))
