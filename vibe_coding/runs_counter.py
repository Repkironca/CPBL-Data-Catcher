import requests as rq
import json
import datetime

class GetScore:
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }

    # 網址後綴代碼
    suffix = {
        2018: "Fq", 2019: "Sf", 2020: "KS", 2021: "fi", 
        2022: "dG", 2023: "sk", 2024: "xa", 2025: "JO"
    }

    def __init__(self, start_date: tuple, end_date: tuple):
        # 將 tuple (yyyy, mm, dd) 轉換為 datetime 物件以便計算
        self._start_date = datetime.date(*start_date)
        self._end_date = datetime.date(*end_date)
        
        self._now = self._start_date
        self._url = None
        
        # 統計數據
        self._total_games = 0
        self._total_runs_scored = 0   # 總得分
        self._total_runs_allowed = 0  # 總失分

    def url_get(self):
        """
        根據當前日期 self._now 生成對應的 API URL
        """
        y = self._now.year
        m = self._now.month
        d = self._now.day
        
        # 取得該年份對應的代碼，若無則預設為 2025 的 JO (或可拋出錯誤)
        su = self.suffix.get(y, "JO")
        
        # f-string 格式化日期，自動補零
        self._url = f"https://www.rebas.tw/api/seasons/CPBL-{y}-{su}/games?start={y}-{m:02d}-{d:02d}"

    def raw_content_by_get(self, url: str): 
        """
        發送 GET 請求並回傳 JSON 資料
        """
        try:
            # 使用 Session 可以保持連線設定 (雖在此例中非必須，但為好習慣)
            response = rq.get(url, headers=self.header, timeout=10)
            
            if response.status_code != 200:
                print(f"[Error] 請求失敗: {url} (Status: {response.status_code})")
                return None
                
            return response.json()
            
        except rq.exceptions.RequestException as e:
            print(f"[Error] 連線錯誤: {e}")
            return None
        except json.JSONDecodeError:
            print(f"[Error] JSON 解析失敗: {url}")
            return None

    def count_score(self, game_list):
        """
        分析單週比賽列表，累加富邦悍將的得分與失分
        """
        target_team = "悍"  # 富邦悍將的簡寫

        for game in game_list:
            # 1. 檢查比賽是否已結束
            status = game.get("info", {}).get("status")
            if status != "FINISHED":
                continue

            home_data = game.get("home", {})
            away_data = game.get("away", {})
            
            home_abbr = home_data.get("abbr")
            away_abbr = away_data.get("abbr")
            
            # 2. 判斷是否有富邦悍將參與
            if home_abbr != target_team and away_abbr != target_team:
                continue

            self._total_games += 1
            
            # 3. 根據主客場計算得分與失分
            try:
                home_score = int(home_data.get("runs", 0))
                away_score = int(away_data.get("runs", 0))
                
                if home_abbr == target_team:
                    # 富邦是主隊
                    self._total_runs_scored += home_score
                    self._total_runs_allowed += away_score
                else:
                    # 富邦是客隊
                    self._total_runs_scored += away_score
                    self._total_runs_allowed += home_score
                    
            except ValueError:
                print("[Warning] 分數資料格式錯誤，跳過此場比賽")
                continue

    def next_date(self):
        """
        將當前日期往後推一週
        """
        self._now += datetime.timedelta(days=7)

    def analyze(self):
        print(f"開始分析區間: {self._start_date} 至 {self._end_date}")
        
        # 當前日期小於結束日期時持續執行
        while self._now < self._end_date:
            self.url_get()
            # print(f"Fetching: {self._url}") # Debug 用
            
            json_data = self.raw_content_by_get(self._url)
            
            if json_data and "data" in json_data:
                game_list = json_data["data"]
                self.count_score(game_list)
            else:
                # 若該週無資料或請求失敗，可選擇印出訊息或直接跳過
                pass

            self.next_date()

        # 分析結束，印出結果
        self.print_result()

    def print_result(self):
        print("-" * 30)
        print(f"分析結果 (富邦悍將):")
        print(f"總場次: {self._total_games}")
        print(f"總得分: {self._total_runs_scored}")
        print(f"總失分: {self._total_runs_allowed}")
        
        if self._total_games > 0:
            avg_scored = self._total_runs_scored / self._total_games
            avg_allowed = self._total_runs_allowed / self._total_games
            print(f"場均得分: {avg_scored:.2f}")
            print(f"場均失分: {avg_allowed:.2f}")
            
            # 額外資訊：得失分差
            diff = avg_scored - avg_allowed
            print(f"場均分差: {diff:+.2f}")
        else:
            print("此區間內無已完成的比賽資料。")
        print("-" * 30)

# --- 執行區塊 ---
if __name__ == "__main__":
    # 你可以在這裡調整日期區間 (年, 月, 日)
    # 建議 start_date 設定為週一
    start_date = (2025, 3, 24)
    end_date = (2025, 6, 30)
    
    analyzer = GetScore(start_date, end_date)
    analyzer.analyze()