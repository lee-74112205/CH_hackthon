from opencc import OpenCC

converter = OpenCC('s2tw')  # ✅ 注意這裡直接寫 's2t'，不用加 '.json'
text = "汉字转换为繁體字"
result = converter.convert(text)
print(result)  # 漢字轉換為繁體字
