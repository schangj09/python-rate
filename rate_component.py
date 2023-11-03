from enum import Enum
from threading import RLock
import json as json
import time


configStr = '''[
{"route" : "GET slowCall", "maxCount" : 100, "refillRate" : 30},
{"route" : "GET fastCall", "maxCount" : 2000, "refillRate" : 2000}
]'''

class Const(Enum):
	# Config fields
	ROUTE = "route"
	MAX_COUNT = "maxCount"
	REFILL_RATE = "refillRate"
	
	# result fields and values
	RESULT = "result"
	REMAINING = "remaining"
	ACCEPT = "accept"
	REJECT = "reject"

	# constants
	MILLIS_PER_MINUTE = 60000


## Class: RouteCounts
## Holds the configured maxCount and refillRate rates, as well as the number of tokens
## available. Methods for taking and restoring tokens based on the time of requests.
class RouteCounts:
	lock = RLock()

	## RouteCounts constructor
	## route: the name of the route
	## maxCount: the max number of tokens to refill for a route
	## refillRate: the number of tokens per minute to refill the counter
	def __init__(self, route:str, maxCount:int, refillRate:int):
		self.route = route
		self.maxCount = maxCount
		self.refillRate = refillRate
		self.count = maxCount
		self.refillMillis = int(Const.MILLIS_PER_MINUTE.value / refillRate)
		now = int(time.time() * 1000)
		self.start = now - now%self.refillMillis
		self.lastRestoreTime = self.start

	## Method: take
	## Decrement the available tokens and return the remaining tokens for this route.
	## Returns -1 if there are no available tokens.
	def take(self) -> int:
		with self.lock:
			if self.count <= 0:
				self.count = 0
				return -1
			else:
				self.count -= 1
				return self.count

	## Method: refill
	## Increment the available tokens by an amount based on the rate of new tokens, the maximum 
	## token count (the maxCount value) and the last time refill was called.
	## 
	## This can be called on a timer at any interval needed. Alternatively, refill can be called just
	## before calling "take" to ensure the tokens are incremented whenever needed.
	##
	## To do: use better synchronization for multi-threading - should be able to make this work
	## with only a "compareAndSet" method on self.count (don't need to guard on self.lastRestoreTime
	## because any competing threads would set it to the same value anyway)
	def refill(self):
		with self.lock:
			now = int(time.time() * 1000)
			# special case if tokens is full, then just update lastRestore
			if (self.count == self.maxCount):
				self.lastRestoreTime = now - now%self.refillMillis
			else:
				diff = now - self.lastRestoreTime
				# increment is the number of tokens to add to the count
				increment = int(diff/self.refillMillis)
				if self.count + increment > self.maxCount:
					increment = self.maxCount - self.count

				print(f'now: {now}, diff: {diff}, increment:{increment}, oldcount:{self.count}')
				# only update lastRestore if the count changes so we accumulate time in case the polling
				# is faster than the rate
				if increment > 0:
					self.lastRestoreTime = now - now%self.refillMillis
				self.count = self.count + increment
				print(f'count:{self.count}, lastRestore:{self.lastRestoreTime}')

## Class: RateComponent
## Class that provides a rate counter and take method for every configured route.
## 
class RateComponent:
	configJson = json.loads(configStr)
	counts = {}
	for c in configJson:
		counts[c[Const.ROUTE.value]] = RouteCounts(c[Const.ROUTE.value], c[Const.MAX_COUNT.value], c[Const.REFILL_RATE.value])

	## Method: take
	## Check the available tokens for a route and decrement counter if tokens are available.
	## Returns 0 if route is unknown. Otherwise, returns json string indicating if the 
	## request can be handled and how many tokens are remaining.
	def take(self, route: str) -> str:
		if (route not in self.counts) :
			return 0
		else:
			self.counts[route].refill()
			remaining = self.counts[route].take()

		if remaining >= 0:
			accept = Const.ACCEPT.value
		else:
			accept = Const.REJECT.value
			remaining = 0
		answer = {Const.RESULT.value: accept, Const.REMAINING.value: remaining}
		return json.dumps (answer)

	## Method: refill
	## Increments all route token counters based on their rate of restoration and the last time refill was
	## called.
	def refillAll(self):
		for rc in self.counts:
			self.counts[rc].refill()



