# 這個檔案就是讓我動態使用 package 裡面的套件，懶得寫 UI

from package.cpbl_data_get import GetData

obj = GetData("rebras", (2025, 6, 30), (2025, 10, 12))
print(obj.data)