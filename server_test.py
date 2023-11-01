# test commands for exercising server
import urllib.request
import time



###########
# test the RateComponent
reload (rate_component)
from rate_component import RateComponent
r = RateComponent()
for i in range(20): r.take("GET slowCall")


###########
# test out the server

url = 'http://localhost:8080/take/?route=GET%20fastCall'
print(urllib.request.urlopen(url).read())
for i in range(50): print(urllib.request.urlopen(url).read())


url = 'http://localhost:8080/take/?route=GET%20slowCall'
for i in range(15):
	time.sleep(0.5)
	print(urllib.request.urlopen(url).read())
