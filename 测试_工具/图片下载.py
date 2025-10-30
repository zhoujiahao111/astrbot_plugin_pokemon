# # coding=utf-8
# import json
#
#
import os.path
import random
import time

from curl_cffi import requests

def 读取文件方法(path='') -> str:
    #path = "config.config"

    with open(path, 'r', encoding='utf-8') as f:
        return f.readlines()
#
# json字典 = json.loads(读取文件方法("宝可梦图鉴.json"))
#
# for i in json字典:
#     print(i["贴图"],end='\n')
#
#     if i["mega"]:
#         print(i["mega"],end='\n')
#     if i["极巨化"]:
#         print(i["极巨化"],end='\n')

def 图片下载方法(url: str, 名称:str) -> bool:
    路径 = os.path.join(r"C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\image", 名称)
    headers = {
    "cookie": "cf_clearance=fkrVxWq0XKYrFWszK.LskKVQYWTxHLHCFLxwgUmSET0-1753402126-1.2.1.1-E_OkmVDWRCRuttzReYf8eeQIwtFRY41cpb_qsEOQLnBUud5mrp43o_m50_01hfPMBbI2OfVVL7DHiZp4XdahWZ1iIbOS2Mk65HLJh2BD_3XC88afElPDW2wYix0DC4tCtA4Jr2f6zOQhN8SYHsq8P_nL0oKEI75rEoFDg_.J8aiYvFbeq2z9NIpBTE3DDjUq6jd2f.B3btnoHsrslpl4QrlCGPohTikB592lbwUGmj7G4dyVhvDgsBCmmE8snHRk",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
}

    try:
        r = requests.get(url, headers=headers, timeout=20, impersonate="chrome110", verify=False)
    except Exception as e:
        print("请求错误:", url, str(e))
        return False

    if not r.status_code == 200:
        print("非200错误:", url)
        print(r.text)
        return False

    try:
        with open(路径, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print("错误:", url, str(e))
        return False


    return True

url列表 = 读取文件方法("url文件")

# print(len(url列表))
# for 索引, url in enumerate(url列表):
# 最大值为 1100
for 索引 in range(1100, 1111):
    url = url列表[索引].strip()
    名称 = url[url.rfind("/")+1:]

    url = url.replace("s1", "media")

    print(f"开始下载 索引: {索引}, 文件名:{名称}")
    结果 = 图片下载方法(url, 名称)

    if not 结果:
        print(f"失败, 索引: {索引}, 文件名:{名称}")
        break

    # time.sleep(1 + (random.randint(3,9) / 10))