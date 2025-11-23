import requests as rq
import json
from .errors import CrawlerError, StatusError

class GetData():
	header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
	}

	suffix = {2018:"Fq", 2019:"Sf", 2020:"KS", 2021:"fi", 
				2022:"dG", 2023:"sk", 2024:"xa", 2025:"JO"}

	def __init__(self, target: str, start_date: tuple, end_date: tuple):
		self.tar = target
		self.data = {}
		self._url = None
		self.start_date = start_date
		self.end_date = end_date
		self._raw_content = None
		self._complete_games = 0
		self._now = start_date

		if (target == "rebras"):
			self.analyze()

	# return a week
	def raw_content_by_get(self, url: str, start_date: tuple): 
		s = rq.Session()
		s.headers.update(self.header)
		print(f"Trying to get from {start_date}")
		try:	
			self._raw_content = rq.get(url, timeout = 8)
			if (self._raw_content.status_code != 200):
				raise StatusError(url, self._raw_content.status_code)
		except StatusError as e:
			print(f"Expected Error. \n{e}")

		except rq.exceptions.ConnectionError as e:
			print(f"Connection Error. You dont even get a freaking net, or the url isnt even exist\n{e}")
			
		else:
			print(f"Happy duck! request succeed!")
			if (self._raw_content != None):
				json_data = self._raw_content.json()
				return json_data
			else:
				print("Error. Content isnt detected")

	@staticmethod
	def date_trans(raw: str):
		tmp = raw.split()
		if (len(tmp) == 0):
			return
		date = tmp[0]
		tmp = list(map(int, date.split("-")))
		return (tmp[0], tmp[1], tmp[2])

	@property
	def now(self):
		return self._now
	
	@now.setter
	def now(self, new_date: tuple):
		if (type(new_date) != tuple):
			pass
		if (len(new_date) != 3):
			pass
		self._now = new_date

	@staticmethod
	def days_of_month(m: int):
		if (m in [1, 3, 5, 7, 8, 10, 12]):
			return 31
		if (m in [4, 6, 9, 11]):
			return 30
		if (m%4==0 and m%100 != 0):
			return 29
		else:
			return 28

	"""
	把 self._now 換到下一個比賽日，就加七天
	對，python 有 datetime library，但我就很懶
	known bug: 其實跨年後，你的日期絕對不是開季第一天
	我知道這麼做會爛掉，所以請你他喵的不要這麼做
	"""
	def next_date(self):
		y, m, d = self.now[0], self.now[1], self.now[2]
		d += 7
		if (d > self.days_of_month(m)):
			d -= self.days_of_month(m)
			m += 1
		if (m > 12):
			m -= 12
			y += 1
		self.now = (y, m, d)
		return (y, m, d)
	
	"""
	會給你 self._now 所對應到的 api request url
	"""
	def url_get(self):
		# https://www.rebas.tw/api/seasons/CPBL-2025-JO/games?start=2025-04-21
		y, m, d = self.now[0], self.now[1], self.now[2]
		su = self.suffix[y]
		self._url = f"https://www.rebas.tw/api/seasons/CPBL-{y}-{su}/games?start={y}-{m:02d}-{d:02d}" 
		return self._url

	"""
	因為我很懶惰，所以你的 _start_date 和 _end_date
	必須要是一週的起始點
	判斷那個太麻煩了
	"""
	def analyze(self):
		print(f"Start analyze from {self.start_date} to {self.end_date}")
		self._now = self.start_date
		while (self._now < self.end_date):
			self.url_get() # 他吃的是 now
			json_data = self.raw_content_by_get(self._url, self._now)
			self.data[self._now] = json_data["data"]
			self.next_date()
			print(f"finish analyzing, there're {len(self.data)} weeks in total")