import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 1. 準備數據
# 假設這是你 Excel 整理好的資料結構
# 數值代表： (季末平均 - 全季平均)
data = {
    'Team': ['統一 SEVEN-ELEVEN 獅', '中信兄弟', '台鋼雄鷹', '樂天桃猿', '味全龍'],
    
    # 2023 賽季差距
    '2025_top_ERA+': [-7.4, 55.5, 0.7, -1.3, 21.3],
    '2025_top_tERA+': [-7.2, 54.2, 0.8, -1.3, 19.8],
    
    # 2024 賽季差距
    '2025_bottom_ERA+': [28.8, -23.7, None, -26.2, -8.6],
    '2025_bottom_tERA+': [28, -23.1, None, -25.6, -7.9],
    
    # 2025 賽季差距
    '2024_top_ERA+': [-2.9, None, -48.3, -14.1, None],
    '2024_top_tERA+': [-2.7, None, -54.5, -14.2, None],
}

df = pd.DataFrame(data)

# --- 開始畫圖 ---

# 設定中文字型 (以免亂碼)
# Windows 使用 'Microsoft JhengHei', Mac 使用 'Arial Unicode MS'
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] 
plt.rcParams['axes.unicode_minus'] = False # 讓負號正常顯示

fig, ax = plt.subplots(figsize=(14, 8))

# 設定柱子的寬度和位置
teams = df['Team']
x = np.arange(len(teams))  # 隊伍的位置 [0, 1, 2, 3, 4]
width = 0.12  # 每條柱子的寬度 (因為有 6 條，所以要細一點)

# 繪製柱子 (偏移量算法：中心點向左向右排開)
# 順序：23 ERA, 23 tERA, 24 ERA, 24 tERA, 25 ERA, 25 tERA

# 2023 (左邊)
rects1 = ax.bar(x - width*2.5, df['2025_top_tERA+'], width, label='2025 上半季 ERA+ 差', color='#a1c9f4', edgecolor='white')
rects2 = ax.bar(x - width*1.5, df['2025_top_tERA+'], width, label='2025 上半季 tERA+ 差', color='#8de5a1', edgecolor='white')

# 2024 (中間)
rects3 = ax.bar(x - width*0.5, df['2025_bottom_ERA+'], width, label='2025 下半季 ERA+ 差', color='#ff9f9b', edgecolor='white')
rects4 = ax.bar(x + width*0.5, df['2025_bottom_tERA+'], width, label='2025 下半季 tERA+ 差', color='#d0bbff', edgecolor='white')

# 2025 (右邊)
rects5 = ax.bar(x + width*1.5, df['2024_top_ERA+'], width, label='2024 上半季 ERA+ 差', color='#fffea3', edgecolor='white')
rects6 = ax.bar(x + width*2.5, df['2024_top_tERA+'], width, label='2024 上半季 tERA+ 差', color='#b9f2f0', edgecolor='white')

# --- 裝飾圖表 ---

# 添加一條 0 的基準線，方便看正負
ax.axhline(0, color='black', linewidth=1, linestyle='--')

# 設定標題和標籤
ax.set_ylabel('水鬼場次平均 - 全場次平均 (數值差異)')
ax.set_title('各隊對富邦悍將全季與季末之先發投手強度差異 (ERA+ & tERA+)', fontsize=16, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(teams, fontsize=12)
ax.legend()

# 自動標示數值 (Optional)
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.1f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3 if height > 0 else -12), # 正數往上標，負數往下標
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)

autolabel(rects1)
autolabel(rects2)
autolabel(rects3)
autolabel(rects4)
autolabel(rects5)
autolabel(rects6)

plt.tight_layout()
plt.show()

# 如果要存檔
fig.savefig('analysis_result.png', dpi=300)