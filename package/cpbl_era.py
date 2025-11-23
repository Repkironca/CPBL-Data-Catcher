import requests as rq
import json
from .errors import CrawlerError, StatusError

class GetERA():

	# data 應該要是整個半季的比賽，dict{tuple, json}
	def __init__(data: dict) -> None:

		self.raw_data = data