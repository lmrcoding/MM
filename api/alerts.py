import time
from collections import deque

REQUEST_WINDOW = 60  # seconds
SPIKE_THRESHOLD = 100  # requests per minute

recent_requests = deque()

def record_request():
    now = time.time()
    recent_requests.append(now)
    _cleanup_old_requests(now)

    if len(recent_requests) > SPIKE_THRESHOLD:
        trigger_alert(len(recent_requests))

def _cleanup_old_requests(current_time):
    while recent_requests and current_time - recent_requests[0] > REQUEST_WINDOW:
        recent_requests.popleft()

def trigger_alert(count):
    print(f"🚨 Spike Alert: {count} requests in the last minute!")
    # Optional: Add webhook/email/Slack alert here
