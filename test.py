from orc_api import Arc_api
import time
arc_api = Arc_api()
start_time = time.time()
a = arc_api.ocr_text(373,371,449,388)
b = arc_api.ocr_text(82,347,165,364)
print("--- %s seconds ---" % (time.time() - start_time))
print(a)