# Locust Load Testing for MCP Tools

## Prerequisites
- Python 3.8+
- Locust installed (`pip install locust`)

## Installation
```bash
pip install locust
```

## Running the Test

### Basic Usage
```bash
# Run with web interface
locust -f run_locust_srv.py

# Run in headless mode
locust -f run_locust_srv.py --headless -u 100 -r 10 -t 1h
```

### Parameters
- `-f run_locust_srv.py`: Specify test file
- `-u 100`: 100 concurrent users
- `-r 10`: Spawn 10 users per second
- `-t 1h`: Run for 1 hour

### Web Interface
- Open `http://localhost:8089` after starting
- Configure users, spawn rate, and host

## Test Scenarios
1. Weather Forecast Tool
   - Random cities
   - Various day ranges
   - Error case handling

2. Time Converter Tool
   - Multiple input formats
   - Timezone conversions

3. Current Weather Tool
   - Random city selection

## Monitoring
- Real-time statistics
- Response time graphs
- Error tracking

## Customization
Edit `run_locust_srv.py` to:
- Add more tools
- Modify test weights
- Adjust input parameters
