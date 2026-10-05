# -*- coding: utf-8 -*-
import json
import re

with open("软科中国大学专业排名_2026.json", encoding="utf-8") as f:
    data = json.load(f)

keys = sorted({lei for cls in data.values() for lei in cls})
print("软科专业类 key 数量:", len(keys))
for k in keys:
    if any(x in k for x in ["哲学", "化学", "历史", "地理", "地质", "大气", "土木", "工商管理", "临床医学", "中医学", "外国语言", "安全科学", "动物医学", "农业工程", "公共管理", "兵器", "仪器", "交通运输", "化工"]):
        print(repr(k))
