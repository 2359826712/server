from orc_api import Arc_api
import time
arc_api = Arc_api()
start_time = time.time()
a = arc_api.ocr_recognize(54,48,123,68,det = False)
print("--- %s seconds ---" % (time.time() - start_time))
print(a) 