import pandas as pd
from offense import GetPAStats

def main():
    # 1. 設定日期參數
    # 請根據你的需求修改這裡的日期
    start_date = (2024, 4, 1)
    end_date = (2025, 7, 3)
    
    # 季末起始日 (例如最後 n 場的開始日期)
    late_season_start = (2025, 6, 23) 

    print("正在初始化並執行爬蟲分析...")
    
    # 2. 實例化並執行分析
    # 注意：這裡一定要傳入 really_start_date，否則季末統計會錯誤
    analyzer = GetPAStats(start_date, end_date, really_start_date=late_season_start)
    
    # 執行 analyze()，這會做三件事：
    # (a) 爬取網路 RE24 數據
    # (b) 讀取本地 HTML 進階數據
    # (c) 執行 process_and_filter_stats() 計算衍生數據並篩除非富邦球員
    # (雖然 analyze 內部會 print 一次表格，但我們這邊主要是要拿 analyzer.player_data)
    analyzer.analyze()

    print("分析完成，開始轉換數據為 DataFrame...")

    # 3. 將字典轉換為 Pandas DataFrame
    # analyzer.player_data 的結構是 { '球員名': { 'AVG': 0.28, ... } }
    # 我們將其轉換為列表以便生成 DataFrame
    data_list = []
    
    for name, stats in analyzer.player_data.items():
        # 建立單行資料
        row = {
            "球員名稱": name,
            "AVG": stats.get("AVG", 0),
            "ISO": stats.get("ISO", 0),
            "OPS+": stats.get("OPS_plus", 0),
            "tOPS+": stats.get("tOPS_plus", 0),
            "BABIP": stats.get("BABIP", 0),
            "P/PA": stats.get("P/PA", 0),
            "Full_PA": stats.get("full_season_PA_count", 0),
            "End_PA": stats.get("end_season_PA_count", 0),
            "Full_RE24/PA": stats.get("full_season_RE24_per_PA", 0),
            "End_RE24/PA": stats.get("end_season_RE24_per_PA", 0)
        }
        data_list.append(row)

    if not data_list:
        print("警告：沒有抓取到任何球員資料，請檢查 offense.py 或 HTML 路徑。")
        return

    df = pd.DataFrame(data_list)

    # 4. 數據格式化與排序
    # (1) 排序：依照 AVG 高到低排序 (你可以依需求改成 End_RE24/PA 等)
    df = df.sort_values(by="Full_PA", ascending=False)

    # (2) 設定需要四捨五入到小數點第 3 位的欄位
    float_cols = [
        "AVG", "ISO", "OPS+", "tOPS+", "BABIP", "P/PA", 
        "Full_RE24/PA", "End_RE24/PA"
    ]
    
    # 使用 round 函數處理浮點數
    df[float_cols] = df[float_cols].round(3)

    # 5. 輸出為 CSV
    output_filename = "2025年下.csv"
    
    # encoding='utf-8-sig' 是關鍵，這樣 Excel 開啟中文才不會亂碼
    df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    
    print(f"\n成功！檔案已輸出至：{output_filename}")
    print(f"共匯出 {len(df)} 位選手資料。")
    
    # (選用) 在終端機預覽前 5 筆
    # print(df.head())

if __name__ == "__main__":
    main()