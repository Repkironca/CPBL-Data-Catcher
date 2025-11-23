class CrawlerError(Exception):
	pass

class StatusError(CrawlerError):
	def __init__(self, url, status_code):
		self.url = url
		self.status_code = status_code
		msg = f"Failed to fetch {url}. Status Code = {status_code}"
		super().__init__(msg)
		