import requests
import threading
import time
import random
import sys

BASE_URL = "http://localhost:9097"
CONCURRENCY = 50
REQUESTS_PER_THREAD = 10

def setup_game(game_name):
    try:
        res = requests.post(f"{BASE_URL}/createNewGame", json={
            "game_name": game_name,
            "account": "admin",
            "b_zone": "1",
            "s_zone": "1",
            "rating": 1
        })
        if res.status_code != 200:
            print(f"Setup failed for {game_name}: {res.text}")
    except Exception as e:
        print(f"Setup failed: {e}")

def worker(thread_id, results):
    game_name = f"game_{thread_id}"
    
    latencies = []
    session = requests.Session()
    
    for i in range(REQUESTS_PER_THREAD):
        account = f"user_{i}"
        
        # Insert
        start = time.time()
        try:
            res = session.post(f"{BASE_URL}/insert", json={
                "game_name": game_name,
                "account": account,
                "b_zone": "1",
                "s_zone": "1",
                "rating": random.randint(1, 100)
            })
            if res.status_code != 200:
                print(f"Insert Error: {res.text}")
        except Exception as e:
            print(f"Req Error: {e}")
        latencies.append((time.time() - start) * 1000)

        # Query
        start = time.time()
        try:
            res = session.post(f"{BASE_URL}/query", json={
                "game_name": game_name,
                "account": account,
                "online_duration": 10,
                "cnt": 1
            })
            if res.status_code != 200:
                print(f"Query Error: {res.text}")
        except Exception as e:
            print(f"Req Error: {e}")
        latencies.append((time.time() - start) * 1000)
        
    results[thread_id] = latencies

def run_test():
    print(f"Pre-creating {CONCURRENCY} games...")
    # Pre-create games to avoid measuring table creation overhead
    # We can do this in parallel to speed up setup, but we don't measure it.
    setup_threads = []
    for i in range(CONCURRENCY):
        t = threading.Thread(target=setup_game, args=(f"game_{i}",))
        setup_threads.append(t)
        t.start()
    
    for t in setup_threads:
        t.join()
        
    print("Setup complete. Starting benchmark...")
    
    threads = []
    results = [[] for _ in range(CONCURRENCY)]
    
    start_global = time.time()
    
    for i in range(CONCURRENCY):
        t = threading.Thread(target=worker, args=(i, results))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    end_global = time.time()
    total_time = end_global - start_global
    
    all_latencies = [l for sublist in results for l in sublist]
    if not all_latencies:
        print("No results.")
        return

    avg_latency = sum(all_latencies) / len(all_latencies)
    max_latency = max(all_latencies)
    p95_latency = sorted(all_latencies)[int(len(all_latencies) * 0.95)]
    
    print("\n--- Performance Report ---")
    print(f"Total Requests: {len(all_latencies)}")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Throughput: {len(all_latencies) / total_time:.2f} req/s")
    print(f"Average Latency: {avg_latency:.2f}ms")
    print(f"95th % Latency: {p95_latency:.2f}ms")
    print(f"Max Latency: {max_latency:.2f}ms")
    
    if avg_latency > 50:
        print("WARNING: Average latency exceeds 50ms requirement!")
    else:
        print("SUCCESS: Performance requirement met.")

if __name__ == "__main__":
    run_test()
