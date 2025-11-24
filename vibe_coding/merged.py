import requests as rq
import json
import pandas as pd
from bs4 import BeautifulSoup
import os

# ==========================================
# 1. 設定與基礎類別
# ==========================================

BASE_FILE_PATH = "C:/Users/aaron/Desktop/Python/大學中文/datas/2024/"

# 隊伍代號對照表
TEAM_MAP = {
    "悍": "guardians",
    "龍": "dragons",
    "獅": "lions",
    "猿": "monkeys",
    "鷹": "hawks",
    "象": "brothers"
}

class GetData:
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }
    suffix = {2018: "Fq", 2019: "Sf", 2020: "KS", 2021: "fi",
              2022: "dG", 2023: "sk", 2024: "xa", 2025: "JO"}

    def __init__(self, start_date: tuple, end_date: tuple):
        self.data = {}
        self.start_date = start_date
        self.end_date = end_date
        self._now = start_date

    @staticmethod
    def days_of_month(m: int):
        if m in [1, 3, 5, 7, 8, 10, 12]: return 31
        if m in [4, 6, 9, 11]: return 30
        if m % 4 == 0 and m % 100 != 0: return 29
        return 28

    def next_date(self):
        y, m, d = self._now
        d += 7
        if d > self.days_of_month(m):
            d -= self.days_of_month(m)
            m += 1
        if m > 12:
            m -= 12
            y += 1
        self._now = (y, m, d)

    def url_get(self):
        y, m, d = self._now
        su = self.suffix.get(y, "JO")
        return f"https://www.rebas.tw/api/seasons/CPBL-{y}-{su}/games?start={y}-{m:02d}-{d:02d}"

    def run(self):
        print(f"Start crawling from {self.start_date} to {self.end_date}...")
        self._now = self.start_date
        s = rq.Session()
        s.headers.update(self.header)

        while self._now < self.end_date:
            url = self.url_get()
            try:
                resp = s.get(url, timeout=10)
                if resp.status_code == 200:
                    json_data = resp.json()
                    self.data[self._now] = json_data.get("data", [])
            except Exception as e:
                print(f"Connection Error at {self._now}: {e}")
            self.next_date()
        
        print(f"Crawling finished. Collected {len(self.data)} weeks.")
        return self.data

# ==========================================
# 2. 核心邏輯工具函式 (已修正 Bug)
# ==========================================

def get_era_from_local_file(team_name: str, target_pitchers: list) -> dict:
    file_path = f"{BASE_FILE_PATH}{team_name}.txt"
    
    if not os.path.exists(file_path):
        # print(f"Warning: File not found - {file_path}")
        return {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}

    result = {}
    tables = soup.find_all("table")

    for table in tables:
        thead = table.find("thead")
        if not thead: continue
        headers = [th.get_text(strip=True) for th in thead.find_all("th")]

        if "ERA+" in headers and "tERA+" in headers:
            erap_idx = headers.index("ERA+")
            terap_idx = headers.index("tERA+")
            name_idx = 0 
            
            tbody = table.find("tbody")
            if not tbody: continue
            
            for row in tbody.find_all("tr"):
                cols = row.find_all("td")
                if not cols: continue
                if len(cols) <= max(erap_idx, terap_idx): continue

                raw_name = cols[name_idx].get_text(strip=True)
                
                for target in target_pitchers:
                    # 這裡加上簡單的名稱修正，避免 '陳仕鵬' vs '陳仕朋' 的問題
                    # 但主要依賴 target (API名) 是否包含在 raw_name (檔案名) 中
                    if target in raw_name or raw_name in target:
                        try:
                            val_erap = cols[erap_idx].get_text(strip=True)
                            val_terap = cols[terap_idx].get_text(strip=True)
                            
                            def safe_float(v):
                                return 0.0 if v in ["-", "NaN", "Infinity", ""] else float(v)

                            result[target] = {
                                "ERA+": safe_float(val_erap), 
                                "tERA+": safe_float(val_terap)
                            }
                        except:
                            pass
                        break 
    return result

def identify_sp_in_game(game) -> tuple:
    """ 
    修正版邏輯：
    精準尋找「下半局開始」的那個打席。
    下半局開始的特徵：棒次(PA_order) 為 1，且是該隊第一輪(PA_round) 為 1。
    """
    try:
        pa_list = game.get("PA_list", [])
        if not pa_list:
            return (None, None)

        # 1. 取得主隊先發 (1局上投手)
        home_sp_name = pa_list[0]["pitcher"]["name"]
        away_sp_name = None

        # 2. 尋找客隊先發 (1局下投手)
        # 我們從 index 1 開始找，尋找第一個同時滿足 PA_order==1 和 PA_round==1 的打席
        # 這代表是「另一隊」的第一棒第一次上場，也就是下半局開始
        for i in range(1, len(pa_list)):
            pa = pa_list[i]
            # 檢查是否為第一棒，且是第一輪
            # 注意：如果是單局打超過一輪，PA_order 會是 1，但 PA_round 會是 2 (或其他)，所以會被這裡過濾掉
            if pa["PA_order"] == 1 and pa["PA_round"] == 1:
                away_sp_name = pa["pitcher"]["name"]
                break
        
        # 若找不到 (例如比賽只打半局裁定? 極少見)，則 away_sp 為 None
        return (home_sp_name, away_sp_name)

    except Exception as e:
        # print(f"Error parsing game SP: {e}")
        return (None, None)

# ==========================================
# 3. 主流程分析
# ==========================================

def run_analysis(start_date: tuple, end_date: tuple, n_late_games: int):
    # 1. 爬取
    crawler = GetData(start_date, end_date)
    raw_data_weeks = crawler.run()

    # 2. 排序
    all_sorted_games = []
    sorted_dates = sorted(raw_data_weeks.keys())
    for d in sorted_dates:
        all_sorted_games.extend(raw_data_weeks[d][::-1]) 

    # 3. 篩選
    guardians_games = []
    for game in all_sorted_games:
        if game["info"]["status"] != "FINISHED":
            continue
        h = game["home"]["abbr"]
        a = game["away"]["abbr"]
        if h == "悍" or a == "悍":
            guardians_games.append(game)

    total_g_count = len(guardians_games)
    print(f"Total Guardians games: {total_g_count}")
    
    # 4. 初始化容器
    stats = { team_code: {} for team_code in TEAM_MAP.values() }

    # 5. 分析
    late_start_index = total_g_count - n_late_games

    for idx, game in enumerate(guardians_games):
        is_late = (idx >= late_start_index)
        home_abbr = game["home"]["abbr"]
        away_abbr = game["away"]["abbr"]
        
        home_sp, away_sp = identify_sp_in_game(game)
        
        if not home_sp or not away_sp: 
            continue

        # 歸類主隊先發 (Home SP -> Home Team)
        if home_abbr in TEAM_MAP:
            t_key = TEAM_MAP[home_abbr]
            if home_sp not in stats[t_key]: stats[t_key][home_sp] = {"total": 0, "late": 0}
            stats[t_key][home_sp]["total"] += 1
            if is_late: stats[t_key][home_sp]["late"] += 1

        # 歸類客隊先發 (Away SP -> Away Team)
        if away_abbr in TEAM_MAP:
            t_key = TEAM_MAP[away_abbr]
            if away_sp not in stats[t_key]: stats[t_key][away_sp] = {"total": 0, "late": 0}
            stats[t_key][away_sp]["total"] += 1
            if is_late: stats[t_key][away_sp]["late"] += 1

    # 6. 輸出
    print("\nGenerating CSV files...")
    for team_code in stats.keys():
        pitchers_dict = stats[team_code]
        if not pitchers_dict: continue
            
        era_data = get_era_from_local_file(team_code, list(pitchers_dict.keys()))
        
        csv_data = []
        for name, data in pitchers_dict.items():
            p_era = 0.0
            p_tera = 0.0
            
            # 若爬蟲名與檔案名有出入 (如 陳仕鵬 vs 陳仕朋)，get_era_from_local_file 會嘗試比對
            # 若仍找不到，則為 0
            if name in era_data:
                p_era = era_data[name]["ERA+"]
                p_tera = era_data[name]["tERA+"]
            
            csv_data.append({
                "投手名稱": name,
                "ERA+": p_era,
                "tERA+": p_tera,
                "總出賽數": data["total"],
                "季末出賽": data["late"]
            })
            
        if csv_data:
            df = pd.DataFrame(csv_data)
            df.set_index("投手名稱", inplace=True)
            filename = f"2024_bottom_{team_code}_analysis.csv"
            df.to_csv(filename, encoding='utf-8-sig')
            print(f" -> Saved: {filename}")

if __name__ == "__main__":
    s_date = (2024, 7, 8)
    e_date = (2024, 10, 27)
    LATE_N = 19
    run_analysis(s_date, e_date, LATE_N)