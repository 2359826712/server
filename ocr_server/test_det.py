from ocr_api import Arc_api
import time

arc_api = Arc_api()
print("--- Warming up ---")
arc_api.ocr_text(54,48,123,68, det=True)

print("\n--- Testing det=True ---")
start_time = time.time()
res_det = arc_api.ocr_text(54,48,123,68, det=True)
print("Time det=True: %.4f seconds" % (time.time() - start_time))
print(res_det)

print("\n--- Testing det=False ---")
start_time = time.time()
res_no_det = arc_api.ocr_text(54,48,123,68, det=False)
print("Time det=False: %.4f seconds" % (time.time() - start_time))
print(res_no_det)
