from orc_api import Arc_api
import time
arc_api = Arc_api()
start_time = time.time()
a = arc_api.ocr_text(269,353,328,373)
print("--- %s seconds ---" % (time.time() - start_time))
print(a) 