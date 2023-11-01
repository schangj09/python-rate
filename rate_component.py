import json as json
import time


configStr = '''[
{"route" : "GET slowCall", "burst" : 100, "sustained" : 10},
{"route" : "GET fastCall", "burst" : 300, "sustained" : 200}
]'''

## Class: RouteCounts
## Holds the configured burst and sustained rates, as well as the number of tokens
## available. Methods for taking and restoring tokens based on the time of requests.
class RouteCounts:
	MILLIS_PER_MINUTE = 60000
	
	def __init__(self, route:str, burst:int, sustained:int):
		self.route = route
		self.burst = burst
		self.sustained = sustained
		self.count = burst
		self.rate = int(self.MILLIS_PER_MINUTE / sustained)
		now = int(time.time() * 1000)
		self.start = now - now%self.rate
		self.lastRestore = self.start

	## Method: take
	## Decrement the available tokens and return the remaining tokens for this route.
	## Returns -1 if there are no available tokens.
	def take(self) -> int:
		if self.count <= 0:
			self.count = 0
			return -1
		else:
			self.count -= 1
			return self.count

	## Method: restore
	## Increment the available tokens by an amount based on the rate of new tokens, the maximum 
	## token count (the burst value) and the last time restore was called.
	## 
	## This can be called on a timer at any interval needed. Alternatively, restore can be called just
	## before calling "take" to ensure the tokens are incremented whenever needed.
	##
	## To do: handle synchronization for multi-threaded server calls.
	def restore(self):
		now = int(time.time() * 1000)
		# special case if tokes is full, then just update lastRestore
		if (self.count == self.burst):
			self.lastRestore = now - now%self.rate
		else:
			diff = now - self.lastRestore
			# increment is the number of tokens to add to the count
			increment = int(diff/self.rate)
			if self.count + increment > self.burst:
				increment = self.burst - self.count

			print(f'now: {now}, diff: {diff}, increment:{increment}, oldcount:{self.count}')
			# only update lastRestore if the count changes so we accumulate time in case the polling
			# is faster than the rate
			if increment > 0:
				self.lastRestore = now - now%self.rate
			self.count = self.count + increment
			print(f'count:{self.count}, lastRestore:{self.lastRestore}')

## Class: RateComponent
## Class that provides a rate counter and take method for every configured route.
## 
class RateComponent:
	configJson = json.loads(configStr)
	counts = {}
	for c in configJson:
		counts[c["route"]] = RouteCounts(c["route"], c["burst"], c["sustained"])

	## Method: take
	## Check the available tokens for a route and decrement counter if tokens are available.
	## Returns 0 if route is unknown. Otherwise, returns json string indicating if the 
	## request can be handled and how many tokens are remaining.
	def take(self, route: str) -> str:
		if (route not in self.counts) :
			return 0
		else:
			remaining = self.counts[route].take()

		if remaining >= 0:
			accept = "ACCEPT"
		else:
			accept = "REJECT"
			remaining = 0
		answer = {"result": accept, "remaining": remaining}
		return json.dumps (answer)

	## Method: restore
	## Increments all route token counters based on their rate of restoration and the last time restore was
	## called.
	def restore(self):
		for rc in self.counts:
			self.counts[rc].restore()



