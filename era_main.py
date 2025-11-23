# 這個檔案就是讓我動態使用 package 裡面的套件，懶得寫 UI
import pandas as pd
from package.cpbl_data_get import GetData
from package.cpbl_era import GetERA

database = GetData("rebras", (2025, 3, 24), (2025, 6, 30))
erabase = GetERA(database.data)
(guardians, opponents) = erabase.find_sp(300)

file_path = []
for team in ["brothers", "hawks", "monkeys", "lions", "dragons"]:
	file_path.append(f"C:/Users/aaron/Desktop/Python/大學中文/datas/2025/{team}.txt")

guardians_path = "C:/Users/aaron/Desktop/Python/大學中文/datas/2025/guardians.txt"
era_datas_guardians = erabase.get_pitching_stats_from_local_file(guardians_path, list(guardians.keys()))
era_datas_opponents = {}

for path in file_path:
	temp = erabase.get_pitching_stats_from_local_file(path, list(opponents.keys()))
	# print(temp)
	era_datas_opponents.update(temp)

# print(guardians.keys())
# print(opponents.keys())
# print(era_datas_guardians)
# print(era_datas_opponents)

for name in guardians.keys():
	era_datas_guardians[name]["出賽場數"] = guardians[name]
for name in opponents.keys():
	era_datas_opponents[name]["出賽場數"] = opponents[name]

g_table = pd.DataFrame.from_dict(era_datas_guardians, orient='index')
g_table.index.name = "投手名稱"
o_table = pd.DataFrame.from_dict(era_datas_opponents, orient='index')
o_table.index.name = "投手名稱"

g_table.to_csv("2025-top-guardians.csv", encoding='utf-8-sig')
o_table.to_csv("2025-top-opponents.csv", encoding='utf-8-sig')

print(g_table)
print(o_table)

"""
2025 上
0324 0630

2025 下
0630 1012

2024 上
0401 0703

2024 下
0701 1027
"""