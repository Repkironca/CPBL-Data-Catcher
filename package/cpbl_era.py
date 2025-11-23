from bs4 import BeautifulSoup
import json
from .errors import CrawlerError, StatusError

class GetERA():

	# data 應該要是整個半季的比賽，dict{tuple, json}
	def __init__(self, data: dict) -> None:
		self.raw_data = data
		self.total_games = 0

	def find_sp(self, game_count: int, data = None) -> tuple[dict, dict]:
		if (data is None):
			data = self.raw_data

		counter = 0
		guardians_starting_pitcher = {}
		opponents_starting_pitcher = {}
		for _, week_game_list in data.items():
			if (counter >= game_count):
				break
			week_game_list.reverse()
			for game in week_game_list:
				home = game["home"]["abbr"]
				away = game["away"]["abbr"]
				status =  game["info"]["status"]
				if (counter >= game_count):
					break
				if (home != "悍" and away != "悍"):
					continue
				if (status != "FINISHED"):
					continue

				self.total_games += 1
				guardians_top = (away == "悍")
				top_inning = game["PA_list"][0]["pitcher"]["name"]
				index = 1
				switch = (game["PA_list"][index]["PA_order"] <= game["PA_list"][index-1]["PA_order"])
				first_round = (game["PA_list"][index-1]["PA_round"] == 1)
				while (not (switch and first_round)):
					index += 1
					switch = (game["PA_list"][index]["PA_order"] <= game["PA_list"][index-1]["PA_order"])
					first_round = (game["PA_list"][index-1]["PA_round"] == 1)
				bottom_inning = game["PA_list"][index]["pitcher"]["name"]

				# print(f"DEBUG: {away}, {guardians_top}")
				if (guardians_top):
					if (guardians_starting_pitcher.get(bottom_inning, -1) == -1):
						guardians_starting_pitcher[bottom_inning] = 1
					else:
						guardians_starting_pitcher[bottom_inning] += 1
					if (opponents_starting_pitcher.get(top_inning, -1) == -1):
						opponents_starting_pitcher[top_inning] = 1
					else:
						opponents_starting_pitcher[top_inning] += 1
				else:
					if (guardians_starting_pitcher.get(top_inning, -1) == -1):
						guardians_starting_pitcher[top_inning] = 1
					else:
						guardians_starting_pitcher[top_inning] += 1
					if (opponents_starting_pitcher.get(bottom_inning, -1) == -1):
						opponents_starting_pitcher[bottom_inning] = 1
					else:
						opponents_starting_pitcher[bottom_inning] += 1

				counter += 1
				
		return (guardians_starting_pitcher, opponents_starting_pitcher)

	def get_pitching_stats_from_local_file(self, file_path: str, target_pitchers: list[str]) -> dict[str, dict]:
	    try:
	        with open(file_path, "r", encoding="utf-8") as f:
	            html_content = f.read()
	    except FileNotFoundError:
	        print(f"錯誤：找不到檔案 {file_path}")
	        return {}

	    soup = BeautifulSoup(html_content, "html.parser")
	    result = {}
	    
	    tables = soup.find_all("table")
	    
	    for table in tables:
	        thead = table.find("thead")
	        if not thead:
	        	continue
	        
	        headers = [th.get_text(strip=True) for th in thead.find_all("th")]
	        
	        # 確認我們要的東西在這裡
	        if "ERA+" in headers and "tERA+" in headers:
	            erap_idx = -1
	            terap_idx = -1
	            name_idx = 0
	            
	            for i, h in enumerate(headers):
	                if h == "ERA+": erap_idx = i
	                elif h == "tERA+": terap_idx = i
	            
	            # 開始解析這個表格的 Body
	            tbody = table.find("tbody")
	            if not tbody:
	            	continue
	            
	            rows = tbody.find_all("tr")
	            
	            for row in rows:
	                cols = row.find_all("td")
	                if not cols:
	                	continue
	                
	                if len(cols) <= max(erap_idx, terap_idx):
	                	continue

	                raw_name = cols[name_idx].get_text(strip=True)
	                
	                # 比對名字
	                matched_name = None
	                for target in target_pitchers:
	                    if target in raw_name:
	                        matched_name = target
	                        break
	                
	                if matched_name:
	                    try:
	                        val_erap_str = cols[erap_idx].get_text(strip=True)
	                        val_terap_str = cols[terap_idx].get_text(strip=True)
	                        
	                        def parse_float(val_str):
	                            if val_str in ["-", "NaN", "Infinity", ""]:
	                                return 0.0
	                            return float(val_str)

	                        erap = parse_float(val_erap_str)
	                        terap = parse_float(val_terap_str)
	                        
	                        result[matched_name] = {"ERA+": erap, "tERA+": terap}
	                        # print(f"成功抓取: {matched_name} ERA+: {erap}")
	                        
	                    except Exception as e:
	                        print(f"解析 {matched_name} 數據時發生錯誤: {e}")

	    return result