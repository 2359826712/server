from orc_api import Arc_api
arc_api = Arc_api()

a = arc_api.ocr_text(0,0,1600,900)
print(a)