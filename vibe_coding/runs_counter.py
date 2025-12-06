import requests as rq
import datetime
import math

end_D = (2025, 7, 3)

class GetRunStats:
    # 模擬瀏覽器的 Header
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }

    # 年份對應的 URL 後綴
    suffix = {
        2018: "Fq", 2019: "Sf", 2020: "KS", 2021: "fi", 
        2022: "dG", 2023: "sk", 2024: "xa", 2025: "JO"
    }

    def __init__(self, start_date: tuple, end_date: tuple):
        # 將 tuple (2025, 3, 24) 轉為 datetime 物件方便計算
        self._start_date = datetime.date(*start_date)
        self._end_date = datetime.date(*end_date)
        self._current_date = self._start_date
        self._url = None
        
        # 統計數據容器
        self._games_count = 0
        self._total_runs_scored = 0  # 總得分
        self._total_runs_allowed = 0 # 總失分
        self._run_differentials = [] # 每一場的得失分差 (用於計算標準差)

    def _url_get(self):
        """
        產生 Rebas API 的 URL
        """
        y, m, d = self._current_date.year, self._current_date.month, self._current_date.day
        su = self.suffix.get(y, "JO") 
        # 保持你原本的 URL 格式
        self._url = f"https://www.rebas.tw/api/seasons/CPBL-{y}-{su}/games?start={y}-{m:02d}-{d:02d}"

    def raw_content_by_get(self, url: str): 
        """
        爬蟲核心：發送 GET 請求並回傳 JSON
        """
        try:
            s = rq.Session()
            response = s.get(url, headers=self.header)
            response.raise_for_status() # 檢查 HTTP 錯誤
            return response.json()
        except Exception as e:
            print(f"Error fetching data from {url}: {e}")
            return None

    def _process_games(self, game_list: list):
        """
        分析單週比賽列表，提取富邦悍將的得分與失分
        """
        for game in game_list:
            # 1. 檢查比賽是否已結束
            # (參考 games.json 與 cpbl_era.py 的邏輯)
            status = game.get("info", {}).get("status")
            if status != "FINISHED":
                continue

            home_data = game.get("home", {})
            away_data = game.get("away", {})
            
            home_abbr = home_data.get("abbr")
            away_abbr = away_data.get("abbr")

            # 2. 確認富邦悍將 ("悍") 是否參賽
            if home_abbr != "悍" and away_abbr != "悍":
                continue

            date = game["info"]["started_at"].split()[0]
            tu = tuple(map(int, date.split("-")))
            if (tu > end_D):
                continue
                
            # 3. 取得比分
            try:
                home_score = int(home_data.get("runs", 0))
                away_score = int(away_data.get("runs", 0))
            except ValueError:
                continue # 防止資料錯誤

            # 4. 判斷主客場並分配 得分/失分
            if home_abbr == "悍":
                runs_scored = home_score
                runs_allowed = away_score
            else: # 客場
                runs_scored = away_score
                runs_allowed = home_score
            
            # 5. 紀錄數據
            self._total_runs_scored += runs_scored
            self._total_runs_allowed += runs_allowed
            self._run_differentials.append(runs_scored - runs_allowed)
            self._games_count += 1

    def analyze(self):
        """
        主程式：遍歷日期區間，抓取並分析數據
        """
        print(f"Start analyze from {self._start_date} to {self._end_date}")
        
        # 當前日期小於結束日期時，持續迴圈
        while self._current_date < self._end_date:
            self._url_get()
            # print(f"Fetching: {self._url}") # Debug 用
            
            json_data = self.raw_content_by_get(self._url)
            
            if json_data and "data" in json_data:
                self._process_games(json_data["data"])
            
            # 前進一週 (配合 Rebas API 的特性)
            self._current_date += datetime.timedelta(days=7)
        
        self._print_stats()

    def _print_stats(self):
        """
        計算並印出最終統計結果
        """
        if self._games_count == 0:
            print("在此區間內找不到已完成的富邦悍將比賽。")
            return

        # 計算平均值
        avg_rs = self._total_runs_scored / self._games_count
        avg_ra = self._total_runs_allowed / self._games_count
        avg_diff = sum(self._run_differentials) / self._games_count
        
        # 計算得失分差的標準差 (Standard Deviation)
        # 公式：sqrt( sum((x - mean)^2) / N )
        variance = sum((x - avg_diff) ** 2 for x in self._run_differentials) / self._games_count
        std_dev = math.sqrt(variance)

        print("-" * 30)
        print(f"【富邦悍將 區間戰績統計】")
        print(f"統計場數: {self._games_count} 場")
        print("-" * 30)
        print(f"總得分  : {self._total_runs_scored}")
        print(f"總失分  : {self._total_runs_allowed}")
        print("-" * 30)
        print(f"場均得分      : {avg_rs:.2f}")
        print(f"場均失分      : {avg_ra:.2f}")
        print(f"場均得失分差  : {avg_diff:.2f}")
        print(f"得失分差標準差: {std_dev:.2f}")
        print("-" * 30)

# 使用範例
if __name__ == "__main__":
    # 設定日期區間 (年, 月, 日)
    start = (2025, 4, 1)
    end = (2025, 7, 3)
    
    analyzer = GetRunStats(start, end)
    analyzer.analyze()