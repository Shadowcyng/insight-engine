# test_load_balancer.py
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

# Point this to any public route (even one that returns a 401 or 404 works, 
# because Nginx still has to route the traffic to a worker to get that error)
URL = "http://localhost/api/v1/login" 

def send_request(request_id: int):
    # Minor comment: We use built-in urllib to keep this script dependency-free
    req = urllib.request.Request(URL, method="POST") 
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Request {request_id:02d}: {response.getcode()} OK")
    except urllib.error.HTTPError as e:
        # We expect a 422 or 401 here since we aren't sending valid login data
        print(f"Request {request_id:02d}: {e.code} {e.reason}")
    except Exception as e:
        print(f"Request {request_id:02d}: Failed - {e}")

if __name__ == "__main__":
    print(f"Firing 12 concurrent requests to Nginx at {URL}...\n")
    
    # Spin up 4 threads to hit the server simultaneously
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(send_request, range(1, 13))
        
    print("\nTest complete. Check your Docker terminal logs!")