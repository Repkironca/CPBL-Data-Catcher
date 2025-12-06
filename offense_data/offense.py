import requests as rq
import datetime
import math
import os
from bs4 import BeautifulSoup
from collections import defaultdict

end_D = (2025, 7, 3)

class GetPAStats:
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

    def __init__(self, start_date: tuple, end_date: tuple, really_start_date = None):
        if (really_start_date is None):
            self._really_start_date = datetime.date(*start_date)
        else:
            self._really_start_date = datetime.date(*really_start_date)

        # 將 tuple (2025, 3, 24) 轉為 datetime 物件方便計算
        self._start_date = datetime.date(*start_date)
        self._end_date = datetime.date(*end_date)
        self._current_date = self._start_date
        self._url = None
        
        # 統計數據容器
        self._games_count = 0
        self.player_data = self.player_data = defaultdict(lambda: defaultdict(int))

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

    def end_season_PAs(self, game_list: list):
        """
        分析單週比賽列表
        """
        for game in game_list:
            # 1. 檢查比賽是否已結束
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
            tu = datetime.date(*tu)
            if (tu > self._end_date):
                continue

            self._games_count += 1
            for player in game["PA_list"]:
                player_name = player["batter"]["name"]
                RE24_total = float(player["RE24"])
                self.player_data[player_name]["full_season_PA_count"] += 1
                self.player_data[player_name]["full_season_RE24_total"] += RE24_total

                # 這是季末的比賽
                if (tu >= self._really_start_date):
                    self.player_data[player_name]["end_season_PA_count"] += 1
                    self.player_data[player_name]["end_season_RE24_total"] += RE24_total

    def parse_local_html(self):
            """
            從本機 HTML 檔案解析進階數據，並整合至 player_data
            """
            file_path = r"C:\Users\aaron\Desktop\Python\大學中文\datas\offense\2024年上.txt"
            
            if not os.path.exists(file_path):
                print(f"錯誤：找不到檔案 {file_path}")
                return

            print(f"正在讀取並解析：{file_path} ...")
            
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, "html.parser")
            tables = soup.find_all("table")

            # 定義我們要抓取的欄位名稱 (HTML header文字) 對應到 (player_data 的 key)
            # 注意：OPS+ 和 tOPS+ 在 HTML 中可能帶有特殊符號，這裡做精確匹配
            target_columns = {
                "AVG": "AVG",
                "ISO": "ISO",
                "OPS+": "OPS_plus",
                "tOPS+": "tOPS_plus",
                "BABIP": "BABIP",
                "P/PA": "P/PA"
            }

            # 遍歷 HTML 中所有的表格 (因為數據分散在不同表格)
            for table in tables:
                # 1. 解析表頭 (Header) 以確認此表格包含哪些目標數據
                thead = table.find("thead")
                if not thead:
                    continue
                
                headers = [th.get_text(strip=True).replace("<span></span>", "") for th in thead.find_all("th")]
                
                # 找出這個表格裡有哪些是我們要的欄位，並記錄 Index
                # 格式: { index: "儲存用的Key" }，例如 { 3: "AVG", 9: "OPS_plus" }
                col_indices = {}
                for idx, h_text in enumerate(headers):
                    if h_text in target_columns:
                        col_indices[idx] = target_columns[h_text]

                # 如果這個表格完全沒有我們要的數據，就跳過
                if not col_indices:
                    continue

                # 2. 解析內容 (Body)
                tbody = table.find("tbody")
                if not tbody:
                    continue

                rows = tbody.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    if not cols:
                        continue

                    # 抓取球員名字 (通常在第一個按鈕內)
                    # 結構通常是 td -> button -> text
                    try:
                        name_btn = row.find("button")
                        if not name_btn:
                            continue
                        player_name = name_btn.get_text(strip=True)
                        
                        # 排除 "球隊平均" 這種無效行
                        if "平均" in player_name:
                            continue

                        # 抓取對應欄位的數值
                        for idx, key in col_indices.items():
                            if idx < len(cols):
                                val_str = cols[idx].get_text(strip=True)
                                
                                # 嘗試轉為 float，若失敗(例如 NaN 或 -)則保持原樣或設為 0
                                try:
                                    val = float(val_str)
                                except ValueError:
                                    val = 0.0
                                
                                self.player_data[player_name][key] = val
                                
                    except Exception as e:
                        # 避免單一行解析失敗導致整個程式崩潰
                        continue

    def process_and_filter_stats(self):
            # 1. 篩選：找出不是富邦的球員 (沒有抓到 AVG 的)
            # 必須先搜集要刪除的 key，不能在迭代時刪除
            players_to_remove = [
                name for name, stats in self.player_data.items() 
                if "AVG" not in stats
            ]
            
            for name in players_to_remove:
                del self.player_data[name]

            # 2. 計算衍生數據
            for name, stats in self.player_data.items():
                # 全季 RE24/PA
                f_pa = stats["full_season_PA_count"]
                f_re = stats["full_season_RE24_total"]
                if f_pa > 0:
                    stats["full_season_RE24_per_PA"] = f_re / f_pa
                else:
                    stats["full_season_RE24_per_PA"] = 0.0

                # 季末 RE24/PA
                e_pa = stats["end_season_PA_count"]
                e_re = stats["end_season_RE24_total"]
                if e_pa > 0:
                    stats["end_season_RE24_per_PA"] = e_re / e_pa
                else:
                    stats["end_season_RE24_per_PA"] = 0.0

    def print_all_stats(self):
            # 先執行篩選與計算
            self.process_and_filter_stats()

            print("\n" + "="*140)
            # 定義表頭格式
            header_fmt = "{:<10} | {:<6} | {:<6} | {:<6} | {:<6} | {:<6} | {:<6} | {:<8} | {:<8} | {:<12} | {:<12}"
            print(header_fmt.format(
                "Name", "AVG", "ISO", "OPS+", "tOPS+", "BABIP", "P/PA", 
                "Full_PA", "End_PA", "Full_RE24/PA", "End_RE24/PA"
            ))
            print("-" * 140)

            # 格式化輸出內容
            row_fmt = "{:<10} | {:<6} | {:<6} | {:<6} | {:<6} | {:<6} | {:<6} | {:<8} | {:<8} | {:<12.3f} | {:<12.3f}"
            
            # 依據 AVG 排序 (可選)
            sorted_players = sorted(
                self.player_data.items(), 
                key=lambda item: item[1].get("AVG", 0), 
                reverse=True
            )

            for name, stats in sorted_players:
                print(row_fmt.format(
                    name,
                    str(stats.get("AVG", 0)),
                    str(stats.get("ISO", 0)),
                    str(stats.get("OPS_plus", 0)),
                    str(stats.get("tOPS_plus", 0)),
                    str(stats.get("BABIP", 0)),
                    str(stats.get("P/PA", 0)),
                    stats["full_season_PA_count"],
                    stats["end_season_PA_count"],
                    stats["full_season_RE24_per_PA"],
                    stats["end_season_RE24_per_PA"]
                ))
            
            print("="*140 + "\n")

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
                self.end_season_PAs(json_data["data"])
            
            # 前進一週 (配合 Rebas API 的特性)
            self._current_date += datetime.timedelta(days=7)
        
        print(f"Finished analyze from rebras web")
        self.parse_local_html()
        self.print_all_stats()

# 使用範例
if __name__ == "__main__":
    # 設定日期區間 (年, 月, 日)
    start = (2025, 3, 24)
    end = (2025, 6, 30)
    really_start = (2025, 6, 8)
    analyzer = GetPAStats(start, end, really_start)
    analyzer.analyze()

"""
OPS+
RE24：正負多少得分期望值
BABIP：球打進場後形成安打的機率，但要搭配擊球類型
ISO：純長打率
P/PA：纏鬥能力
"""

"""
2025 上
0324 0630

2025 下
0630 1012 0926

2024 上
0401 0703 0623

2024 下
0701 1027
"""
