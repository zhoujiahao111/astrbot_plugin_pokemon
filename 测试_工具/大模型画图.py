# coding=utf-8
import os.path
import time

import requests
import json
import random
import base64
import datetime


def 生成图片(用户提示词: str, key: str, 保存路径: str = "."):
    接口地址 = "https://api.siliconflow.cn/v1/images/generations"

    请求头 = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    请求体 = {
        "model": "black-forest-labs/FLUX.1-schnell",
        "prompt": 用户提示词,
        "image_size": "800x480",
        "batch_size": 1,
        "seed": random.randint(0, 9999999999),
        "num_inference_steps": 25,
        "guidance_scale": 7.5,
    }
    print("开始")
    try:
        # 发送POST请求
        响应 = requests.post(
            url=接口地址,
            headers=请求头,
            json=请求体,
            timeout=120
        )

        响应.raise_for_status()

        # 解析返回的JSON数据
        结果 = 响应.json()
        try:
            图片地址 = 结果[0]['url']
        except:
            try:
                图片地址 = 结果["data"][0]['url']
            except:
                return "错误", "获取图片结果失败, 违禁词建议使用中文." + str(结果)

        r = requests.get(图片地址, timeout=30)

        with open(保存路径, "wb") as f:
            f.write(r.content)
        print("结束", 保存路径)
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP错误: {http_err}")
        print(f"响应内容: {响应.text}")
    except requests.exceptions.RequestException as req_err:
        print(f"网络请求错误: {req_err}")
    except KeyError:
        print("错误：无法从API响应中找到预期的图片数据。请检查API返回的JSON结构。")
        # print(f"收到的原始数据: {响应数据}") # 取消注释以调试
    except Exception as e:
        print(f"发生未知错误: {e}")

    return None


if __name__ == "__main__":
    输入列表 = [
    "pixel art, 16-bit, a traditional dojo interior, polished wooden floor, shoji screen walls, no people",
    "pixel art, 8-bit, an empty city rooftop at sunset, low brick wall, cityscape silhouette in the background with orange and purple sky",
    "pixel art, 16-bit, inside a dark cave, rocky ground, glowing crystals embedded in the walls providing dim light",
    "pixel art, 8-bit, a grassy field with a dirt path, a few small flowers, clear sunny day, simple style",
    "pixel art, 16-bit, a dense forest with tall trees, shafts of sunlight filtering through the canopy, leaf-covered ground",
    "pixel art, 8-bit, a barren volcanic area, dark cracked ground, flowing lava streams in the distant background, smoke in the air",
    "pixel art, 16-bit, an empty library interior, tall wooden bookshelves filled with books, checkerboard floor, quiet atmosphere",
    "pixel art, 8-bit, a sandy beach meeting the ocean, gentle waves, clear blue sky with a few clouds",
    "pixel art, 16-bit, a snowy mountain path, sharp rocks covered in snow, pine trees, light snowfall",
    "pixel art, 8-bit, a narrow city alleyway with brick walls and a paved ground, a dumpster in the corner, night time",
    "pixel art, 16-bit, inside an abandoned factory, metal floor, pipes and gears on the walls, dusty and derelict",
    "pixel art, 8-bit, a rocky canyon floor, tall steep cliffs on both sides, a small stream flowing through the middle",
    "pixel art, 16-bit, a misty swamp with murky green water, gnarled dead trees, and hanging moss, foggy atmosphere",
    "pixel art, 8-bit, an empty gymnasium with a polished wooden basketball court, basketball hoops in the background",
    "pixel art, 16-bit, a stone courtyard of a castle, high stone walls, cobblestone ground",
    "pixel art, 8-bit, a desolate graveyard at night, a full moon in the sky, old tombstones and silhouetted spooky trees",
    "pixel art, 16-bit, a construction site, dirt ground, steel girders and unfinished concrete structures in the background",
    "pixel art, 8-bit, a quiet suburban street at night, pavement, a white picket fence, glowing streetlights",
    "pixel art, 16-bit, a city park with a paved path, a park bench, and manicured trees, buildings in the distant background",
    "pixel art, 8-bit, a field of tall grass during a thunderstorm, dark storm clouds, flashes of lightning in the sky, heavy rain",
    "pixel art, 16-bit, inside a large greenhouse, rows of potted plants, glass walls and ceiling, humid and bright",
    "pixel art, 8-bit, a desert with large sand dunes under a harsh, bright sun, heat haze effect",
    "pixel art, 16-bit, on a wooden pier extending over a calm lake, forests visible on the far shore, overcast day",
    "pixel art, 8-bit, a simple dirt crossroads in the countryside, a wooden signpost, grassy plains all around",
    "pixel art, 16-bit, a frozen river surface, surrounded by snow-covered banks and bare winter trees",
    "pixel art, 8-bit, the interior of a power plant, machinery, warning signs, and conduits on the walls, industrial feel",
    "pixel art, 16-bit, a bright meadow filled with colorful wildflowers, gentle rolling hills in the background, sunny day",
    "pixel art, 8-bit, the deck of a cargo ship, metal containers stacked in the background, open ocean visible",
    "pixel art, 16-bit, an ancient ruin with crumbling stone pillars and floors, overgrown with vines and moss",
    "pixel art, 8-bit, a simple kitchen interior, checkered tile floor, countertops and cabinets, no people"
]
    key列表 = [
        "sk-vontfncgaqzfbtcktgcmptpcfurzgakxrwrqgcnlnlgxgvjp",
        "sk-tmxnhlzzutjwosetsbovdpghqeclrtowxwvlmtrofzsyqhpz",
        "sk-kesyxxsnkctayorowzdcfgcqlqqicpnlfhksnuglhozhnwzg",
        "sk-zsediqloekydqhuiqzyczwdfsorwcdyjswtqawuwotbenfip",
        "sk-zfjxvoaugfqvhocemplzkalxmdlhvdrfrgvwjnhcybrqsjrc",
    ]

    开始数字 = 40

    for i in range(len(输入列表)):
        生成图片(
            输入列表[i],
            key=key列表[(开始数字) % len(key列表)],
            保存路径= os.path.join(
                     r"C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\images\ai背景",
                     f"bg-{开始数字}.jpg"
            )
        )
        开始数字 += 1
        time.sleep(2)