import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import os

# ==========================================
# 1. 設定與讀檔
# ==========================================
YEAR = "2024年上"
CSV_FILENAME = f'{YEAR}.csv'  # 請確認你的 CSV 檔名是否正確

# 手動設定的平均參考值 (可自行修改)
AVG_BABIP_VAL = 0.307
AVG_ISO_VAL = 0.092
AVG_P_PA_VAL = 3.829

def main():
    # 檢查檔案是否存在，若無則嘗試抓目錄下第一個 CSV
    target_file = CSV_FILENAME
    if not os.path.exists(target_file):
        csv_files = [f for f in os.listdir() if f.endswith('.csv')]
        if csv_files:
            target_file = csv_files[0]
            print(f"找不到 {CSV_FILENAME}，改為讀取：{target_file}")
        else:
            print("錯誤：找不到任何 CSV 檔案。")
            return

    df = pd.read_csv(target_file, encoding='utf-8-sig')
    df = df.fillna(0)

    # 設定中文字型 (根據你的作業系統調整)
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False

    # ==========================================
    # 圖表 1: 風格散佈圖 (BABIP vs ISO)
    # ==========================================
    fig1, ax1 = plt.subplots(figsize=(10, 8))

    # 點大小標準化
    scale_factor = 1000
    max_full_pa = df['Full_PA'].max() if df['Full_PA'].max() > 0 else 1
    max_end_pa = df['End_PA'].max() if df['End_PA'].max() > 0 else 1

    s_red = (df['Full_PA'] / max_full_pa) * scale_factor
    s_blue = (df['End_PA'] / max_end_pa) * scale_factor

    # 繪圖
    ax1.scatter(df['BABIP'], df['ISO'], s=s_red, c='red', alpha=0.3, label='全季 PA 權重')
    ax1.scatter(df['BABIP'], df['ISO'], s=s_blue, c='blue', alpha=0.3, label='季末 PA 權重')

    # 參考線
    ax1.axvline(x=AVG_BABIP_VAL, color='gray', linestyle='--', linewidth=1, label=f'Avg BABIP ({AVG_BABIP_VAL})')
    ax1.axhline(y=AVG_ISO_VAL, color='gray', linestyle='--', linewidth=1, label=f'Avg ISO ({AVG_ISO_VAL})')

    ax1.set_xlabel('BABIP (場內安打率)')
    ax1.set_ylabel('ISO (純長打率)')
    ax1.set_title('打者型態分佈：全季 vs 季末 (點大小代表出賽數)')
    ax1.legend()

    # 強制原點在左下附近
    ax1.set_xlim(left=0)
    ax1.set_ylim(bottom=0)

    fig1.savefig(f'{YEAR}打者型態分布.png', dpi=300)
    print(f"已輸出：{YEAR}打者型態分布.png")

    # ==========================================
    # 圖表 2: 產能柱狀圖 (Total PA 排序, tOPS+ 上色)
    # ==========================================
    fig2, ax2 = plt.subplots(figsize=(12, 6))

    # 依據 End_PA 排序
    df_sorted = df.sort_values(by='End_PA', ascending=False)

    # 顏色映射：tOPS+
    v_min = df_sorted['tOPS+'].min()
    v_max = df_sorted['tOPS+'].max()
    if v_min > 99: v_min = 0
    if v_max < 101: v_max = 200
    
    norm = mcolors.TwoSlopeNorm(vmin=v_min, vcenter=100, vmax=v_max)
    cmap = plt.cm.coolwarm

    bars = ax2.bar(df_sorted['球員名稱'], df_sorted['Full_PA'], color=cmap(norm(df_sorted['tOPS+'])))

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax2)
    cbar.set_label('tOPS+ (100 = 隊伍平均)')

    ax2.set_xlabel('球員 (依季末打席數排序)')
    ax2.set_ylabel('Total PA (全季打席數)')
    ax2.set_title('球員出賽數與進攻產能 (顏色代表 tOPS+)')
    plt.xticks(rotation=45, ha='right')

    fig2.tight_layout()
    fig2.savefig(f'{YEAR}打者 PA 對應 OPS+.png', dpi=300)
    print(f"已輸出：{YEAR}打者 PA 對應 OPS+.png")

    # ==========================================
    # 圖表 3: 纏鬥與產能圖 (Grind & Value Plot)
    # ==========================================
    # 篩選季末有打席的球員
    df_end = df[df['End_PA'] > 0].copy()

    if not df_end.empty:
        fig3, ax3 = plt.subplots(figsize=(10, 8))

        # 點大小：季末 PA
        max_e_pa = df_end['End_PA'].max()
        s_end = (df_end['End_PA'] / max_e_pa) * 800

        # 顏色：ISO
        iso_sc = ax3.scatter(
            df_end['P/PA'], 
            df_end['End_RE24/PA'], 
            s=s_end, 
            c=df_end['ISO'], 
            cmap='viridis',
            alpha=0.8, 
            edgecolors='black',
            linewidth=0.5
        )

        # [修正] 計算全隊平均 RE24/PA (加權平均)
        # 公式: (所有球員的全季總 RE24) / (所有球員的全季總 PA)
        # 我們可以用 Full_RE24/PA * Full_PA 還原出個人的總 RE24
        total_season_re24 = (df['Full_RE24/PA'] * df['Full_PA']).sum()
        total_season_pa = df['Full_PA'].sum()
        
        if total_season_pa > 0:
            team_avg_re24_pa = total_season_re24 / total_season_pa
        else:
            team_avg_re24_pa = 0.0

        # 參考線 1 (水平): 全隊平均 RE24/PA
        ax3.axhline(y=team_avg_re24_pa, color='red', linestyle='--', linewidth=1.5, 
                    label=f'Team Avg RE24/PA ({team_avg_re24_pa:.3f})')
        
        # 參考線 2 (鉛垂): 使用者設定的平均 P/PA
        ax3.axvline(x=AVG_P_PA_VAL, color='gray', linestyle=':', linewidth=1.5, 
                    label=f'Avg P/PA ({AVG_P_PA_VAL})')

        # Colorbar
        cbar3 = plt.colorbar(iso_sc, ax=ax3)
        cbar3.set_label('ISO (純長打率)')

        ax3.set_xlabel('P/PA (平均纏鬥球數)')
        ax3.set_ylabel('End_RE24/PA (季末得分期望值貢獻)')
        ax3.set_title('季末戰力分析：纏鬥 vs 實質貢獻 (點大小=季末 PA, 顏色=ISO)')
        ax3.legend(loc='upper left')
        ax3.grid(True, linestyle=':', alpha=0.6)

        fig3.savefig(f'{YEAR}打者PPA對應RE24.png', dpi=300)
        print(f"已輸出：{YEAR}打者PPA對應RE24.png")
    else:
        print("警告：沒有季末出賽數據，跳過圖表 3。")

if __name__ == "__main__":
    main()