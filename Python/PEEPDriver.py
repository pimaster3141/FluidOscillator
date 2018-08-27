import time;

class PEEPDriver(threading.Thread):

	def __init__(self, eagle, updateRate):
		