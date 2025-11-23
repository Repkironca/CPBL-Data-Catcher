import requests as rq
import json
from .errors import CrawlerError, StatusError

class GetWR():
	header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
	}

	suffix = {2018:"Fq", 2019:"Sf", 2020:"KS", 2021:"fi", 
				2022:"dG", 2023:"sk", 2024:"xa", 2025:"JO"}

	def __init__(self, start_date: tuple, end_date: tuple):
		self._url = None
		self._start_date = start_date
		self._end_date = end_date
		self._raw_content = None
		self._complete_games = 0
		self._win = 0
		self._lose = 0
		self._tie = 0
		self._now = start_date
		self._game_result = []

	"""
	主要的 request
	回傳一個 json 檔案
	範圍是一週
	"""

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

	"""
	吃進一週的比賽 json 檔 (理論上你要餵 json_data["data"])
	吐出一個 tuple
	(參與場數, 勝場, 敗場, 和場, li: list)
	li = {(W/L/T 簡寫, 日期), ...}
	"""
	def count_game(self, week_game, sd: tuple):
		week_game.reverse()
		total_game = len(week_game)
		complete = 0
		joined_game = 0
		win = 0
		lose = 0
		tie = 0
		temp_list = [("L", (24, 3, 30))]

		for it in week_game:
			hold_date = self.date_trans(it["info"]["started_at"])
			"""
			if (hold_date > self._end_date):
				continue
			if (hold_date < self._start_date):
				continue
			"""
			home = it["home"]["abbr"]
			away = it["away"]["abbr"]
			status =  it["info"]["status"]
			winner_side = it["info"]["winner_side"]
			if (status != "FINISHED"):
				continue
			complete += 1
			if (home == "悍" or away == "悍"):
				joined_game += 1
				if ((home == "悍" and winner_side == "HOME") or (away == "悍" and winner_side == "AWAY")):
					win += 1
					self._win += 1
					temp_list.append(("W", self.date_trans(it["info"]["started_at"])))
				elif ((home == "悍" and winner_side == "AWAY") or (away == "悍" and winner_side == "HOME")):
					lose += 1
					self._lose += 1
					temp_list.append(("L", self.date_trans(it["info"]["started_at"])))
				elif (winner_side == "TIE"):
					tie += 1
					self._tie += 1
					temp_list.append(("T", self.date_trans(it["info"]["started_at"])))

		for it in temp_list:
			self._game_result.append(it)
		
		self._complete_games += joined_game
		print(f"There're {total_game} games in week {sd}, guardians have joined {joined_game}, won {win} games, lost {lose} games, and {tie} games are tie.")
		return (joined_game, win, lose, tie, temp_list)

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
		print(f"Start analyze from {self._start_date} to {self._end_date}")
		self._now = self._start_date
		while (self._now < self._end_date):
			self.url_get()
			json_data = self.raw_content_by_get(self._url, self._now)
			game_list = json_data["data"]
			ret = self.count_game(game_list, self._now)
			self.next_date()
		print(f"There're {self._complete_games} games in the given range")

	"""
	若把每 ran 天作為一組，算出每組內的勝率
	再回傳整年下來，考慮所有組別後的勝率平均與標準差
	"""
	def standard_discrete(self, ran):
		data = []
		N = len(self._game_result)
		raw_sum = 0
		delta_sum = 0

		for l in range(0, N-ran+1, 1):
			win = 0
			total = 0
			for i in range(l, l+ran):
				it = self._game_result[i]
				if (it[0] != 'T'):
					total += 1
				if (it[0] == 'W'):
					win += 1
			data.append(round(win/total, 9))
			raw_sum += round(win/total, 9)

		M = len(data)
		avg = round(raw_sum / M, 9)
		for it in data:
			delta_sum += round((it-avg)*(it-avg), 9)

		std = round((delta_sum/M) ** 0.5, 9)
		tar_avg = data[M-1]
		diff = round((tar_avg-avg)/std, 9)

		print(f"Range = {ran}, Average = {round(avg, 5)}, Standard Discrete = {round(std, 5)}")
		print(f"Winning rate in last {ran} games = {round(tar_avg, 5)}, delta = {round(diff, 5)}")
		return (avg, std, tar_avg, diff)


