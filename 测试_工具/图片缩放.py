# coding=utf-8
from PIL import Image
import os


def 调整图片分辨率(输入文件夹路径, 输出文件夹路径, 目标分辨率=(300, 300)):
    """
    批量调整图片分辨率到指定大小（正方形）

    参数:
        输入文件夹路径 (str): 包含原始图片的文件夹路径
        输出文件夹路径 (str): 保存处理后图片的文件夹路径
        目标分辨率 (int): 调整后的图片边长（默认300像素）
    """
    # 确保输出文件夹存在
    if not os.path.exists(输出文件夹路径):
        os.makedirs(输出文件夹路径)

    # 遍历输入文件夹中的所有文件
    for 文件名 in os.listdir(输入文件夹路径):
        # 检查文件是否为图片（简单判断扩展名）
        if 文件名.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            输出文件名 = 文件名[文件名.find('-')+1:]
            输入文件路径 = os.path.join(输入文件夹路径, 文件名)
            输出文件路径 = os.path.join(输出文件夹路径, 输出文件名)

            try:
                # 打开图片
                with Image.open(输入文件路径) as 图片:
                    # 调整分辨率为目标大小（300x300）
                    调整后图片 = 图片.resize(目标分辨率, Image.LANCZOS)

                    # 保存图片（保持原始格式和质量）
                    if 图片.format == 'JPEG':
                        调整后图片.save(输出文件路径, quality=95)
                    else:
                        调整后图片.save(输出文件路径)

                print(f"已处理: {文件名} -> {目标分辨率}x{目标分辨率}")
            except Exception as 错误:
                print(f"处理 {文件名} 时出错: {错误}")


import os
from PIL import Image


def mirror_and_replace_images(directory):
    """
    对指定目录下的所有图片进行镜像处理并替换原文件
    :param directory: 图片目录路径
    """
    # 遍历目录中的所有文件
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)

        try:
            # 尝试打开文件作为图片
            with Image.open(filepath) as img:
                # 进行水平镜像
                mirrored_img = img.transpose(Image.FLIP_LEFT_RIGHT)

                # 保存替换原文件
                mirrored_img.save(filepath)
                print(f"已处理并替换: {filename}")

        except Exception as e:
            # 如果不是图片文件，会抛出异常，跳过处理
            print(f"跳过非图片文件: {filename} - {str(e)}")


# 镜像图片
if __name__ == "__main__":
    target_directory = r"C:\Users\zjh\Desktop\1"
    mirror_and_replace_images(target_directory)
    print("所有图片处理完成!")


# if __name__ == "__main__":
#     # 使用示例
#     原始图片文件夹 = r"C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\images\background"
#     处理后文件夹 = r"C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\images\background1"
#
#     调整图片分辨率(原始图片文件夹, 处理后文件夹, (800, 480))