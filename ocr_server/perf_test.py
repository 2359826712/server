from ocr_api import Arc_api
import time

arc_api = Arc_api()

print("Warm-up run...")
arc_api.ocr_text(54,48,123,68)

print("Performance run (avg of 10)...")
start_time = time.time()
for i in range(10):
    arc_api.ocr_text(54,48,123,68)
total_time = time.time() - start_time
print(f"Avg time: {total_time/10:.4f}s")
