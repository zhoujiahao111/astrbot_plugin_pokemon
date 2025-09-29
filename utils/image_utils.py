# coding=utf-8
# coding=utf-8
import io
import os
import time

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import Image as PIL_Image, ImageDraw, ImageFont, ImageOps

from ..models import result


def 读取图片方法(类别: str, 名称: str, 是否转为jpg: bool = False) -> result.结果类:
    脚本目录 = os.path.dirname(os.path.abspath(__file__))

    # 构建完整的文件路径
    图片路径 = os.path.join(
        os.path.join(
            os.path.dirname(脚本目录),
            'data',
            'images',
            类别,
        ),
        名称
    )

    if not os.path.exists(图片路径):
        return result.结果类.失败方法(f"贴图文件未找到: {图片路径}")

    try:
        _, 文件后缀名 = os.path.splitext(图片路径)
        文件后缀名 = 文件后缀名.lower()

        with open(图片路径, "rb") as f:
            if 文件后缀名 == '.png' and 是否转为jpg:
                图片bytes = PIL_Image.open(f)
            else:
                return result.结果类.成功方法(io.BytesIO(f.read()))

            if 图片bytes.mode == 'RGBA' or 'A' in 图片bytes.info.get('transparency', ()):
                背景 = PIL_Image.new('RGB', 图片bytes.size, (255, 255, 255))
                背景.paste(图片bytes, (0, 0), 图片bytes)
                图片存储bytes = 背景
            else:
                图片存储bytes = 图片bytes.convert('RGB')

            图片bytes = io.BytesIO()
            图片存储bytes.save(图片bytes, format='JPEG', quality=90)
            return result.结果类.成功方法(图片bytes.getvalue())

    except FileNotFoundError:
        return result.结果类.失败方法(f"图片文件未找到: {图片路径}")
    except Exception as e:
        return result.结果类.失败方法(f"处理图片 '{图片路径}' 时发生未知错误: {e}")


def 返回字体路径方法() -> str:
    return os.path.join(
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data',
            'font'
        ),
        "default.ttc"
    )


def 通用图片构造方法(合成参数: dict) -> result.结果类:
    """
      通用的图片和文字合成函数（优化版）。

      Args:
          合成参数 (dict): ... (同原函数)

      Returns:
          bytes: ... (同原函数)

      Raises:
          ValueError: ... (同原函数)
          FileNotFoundError: ... (同原函数)
      """

    images文件夹路径 = os.path.join(
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data',
            'images'
        )
    )

    if isinstance(合成参数.get("背景图"), str):
        背景图路径 = os.path.join(images文件夹路径, 'ui', 合成参数.get("背景图"))
        if not 背景图路径:
            return result.结果类.失败方法("找不到背景图在哪, 暂时看不了队伍信息了")
        try:
            背景 = PIL_Image.open(背景图路径)
        except FileNotFoundError:
            return result.结果类.失败方法(f"背景图文件未找到: {背景图路径}")
    else:
        背景 = 合成参数.get("背景图")
        if not isinstance(背景, PIL_Image.Image):
            return result.结果类.失败方法("背景图类型不正确或未提供")

    图片元素列表 = 合成参数.get("图片元素", [])
    文字元素列表 = 合成参数.get("文字元素", [])

    所有元素 = []
    for 元素 in 图片元素列表:
        元素['类型'] = '图片'
        所有元素.append(元素)

    for 元素 in 文字元素列表:
        元素['类型'] = '文字'
        所有元素.append(元素)

    所有元素.sort(key=lambda x: x.get('图层', 0))

    image_cache = {}
    font_cache = {}

    绘制 = None

    字体路径 = 返回字体路径方法()

    for 元素 in 所有元素:
        if 元素['类型'] == '图片':
            try:
                素材图片 = None
                路径 = 元素['路径']

                # 如果路径是字符串，代表需要从文件加载，我们启用缓存
                if isinstance(路径, str):
                    if 路径 in image_cache:
                        素材图片 = image_cache[路径]
                    else:
                        完整路径 = os.path.join(images文件夹路径, 路径)
                        素材图片 = PIL_Image.open(完整路径)
                        image_cache[路径] = 素材图片  # 存入缓存
                else:  # 如果路径本身就是图片对象，直接使用
                    素材图片 = 路径

                # 复制一份图片对象进行处理，避免修改缓存中的原图
                处理后图片 = 素材图片.copy().convert('RGBA')

                if 元素.get("镜像", False):
                    处理后图片 = ImageOps.mirror(处理后图片)

                if 元素.get("大小", False):
                    处理后图片 = 处理后图片.resize(元素['大小'], PIL_Image.Resampling.LANCZOS)

                遮罩 = 元素.get("遮罩")
                背景.paste(处理后图片, 元素['位置'], mask=遮罩 or 处理后图片)

            except Exception as e:
                return result.结果类.失败方法(f"处理图片元素失败: {e}")

        elif 元素['类型'] == '文字':
            if 绘制 is None:
                绘制 = ImageDraw.Draw(背景)

            try:
                字体 = None
                字体大小 = 元素['大小']
                font_key = (字体路径, 字体大小)
                if font_key in font_cache:
                    字体 = font_cache[font_key]
                else:
                    字体 = ImageFont.truetype(字体路径, 字体大小)
                    font_cache[font_key] = 字体  # 存入缓存

            except IOError:
                print(f"警告: 无法加载字体 {字体路径}。将使用默认字体。")
                字体 = ImageFont.load_default()

            绘制.text(
                xy=元素['位置'],
                text=str(元素['内容']),
                font=字体,
                fill=元素['颜色'],
                stroke_width=元素.get("描边宽度", 0),
                stroke_fill=元素.get("描边颜色", None)
            )

    最终图片 = 背景.convert('RGB')
    图片字节流 = io.BytesIO()
    最终图片.save(图片字节流, format='JPEG', quality=100)

    return result.结果类.成功方法(图片字节流.getvalue())

def 返回雷达属性图(属性字典: dict, 大小: tuple) -> result:
    if len(属性字典) != 6:
        return result.结果类.失败方法("输入的属性数量必须为6个。")

    标签列表 = list(属性字典.keys())
    数值列表 = list(属性字典.values())

    # --- 主要修改开始 ---
    # 动态调整坐标轴范围以突出数值间的差异
    if not 数值列表:
        return result.结果类.失败方法("输入的属性字典不能为空。")

    min_val = min(数值列表)
    max_val = max(数值列表)

    if max_val == min_val:
        # 如果所有数值都相同，则设置一个从0开始的合理范围
        y_min = 0
        y_max = max_val * 1.5 if max_val > 0 else 10
    else:
        # 如果数值存在差异，则“放大”这个差异区间
        data_range = max_val - min_val
        # 设置下限：略低于最小值，以提供一些边距，但确保不小于0
        y_min = max(0, min_val - data_range * 0.5)
        # 设置上限：略高于最大值，使其接近但不到达最外围，视觉效果更好
        y_max = max_val + data_range * 0.2

    # 闭合折线
    数值闭合 = 数值列表 + [数值列表[0]]
    角度 = np.linspace(0, 2 * np.pi, len(标签列表), endpoint=False).tolist()
    角度闭合 = 角度 + [角度[0]]

    # 字体加载
    try:
        字体路径 = 返回字体路径方法()
        if 字体路径 is None:
            raise FileNotFoundError("未找到合适的中文字体")
        font_manager.fontManager.addfont(字体路径)
        字体名称 = font_manager.FontProperties(fname=字体路径).get_name()
        plt.rcParams['font.sans-serif'] = [字体名称]
        plt.rcParams['axes.unicode_minus'] = False
    except Exception as e:
        return result.结果类.失败方法(f"字体加载失败: {e}")

    # 图形大小与分辨率
    分辨率 = 100
    图尺寸 = (大小[0] / 分辨率, 大小[1] / 分辨率)
    matplotlib.use('Agg')
    图 = plt.figure(figsize=图尺寸, dpi=分辨率)
    图.patch.set_alpha(0.0)

    # 设置极坐标轴
    轴区域 = [0.22, 0.15, 0.56, 0.70]
    轴 = 图.add_axes(轴区域, projection='polar')
    轴.patch.set_alpha(0.0)

    # 绘制雷达图
    轴.plot(角度闭合, 数值闭合, color='#00BFFF', linewidth=2)
    轴.fill(角度闭合, 数值闭合, color='#00BFFF', alpha=0.3)

    # 坐标轴样式
    # --- 应用修改后的动态坐标轴范围 ---
    轴.set_ylim(y_min, y_max)
    轴.set_yticklabels([])
    轴.yaxis.grid(color='white', linestyle='--', linewidth=0.8, alpha=0.7)
    轴.xaxis.grid(color='white', linestyle='--', linewidth=0.8, alpha=0.7)

    # 属性标签
    轴.set_thetagrids(np.degrees(角度), 标签列表, color='white', fontsize=11, weight='bold')

    # 导出图片
    缓冲区 = io.BytesIO()
    try:
        plt.savefig(缓冲区, format='png', transparent=True, pad_inches=0)
        plt.close(图)
        缓冲区.seek(0)
        图像 = PIL_Image.open(缓冲区)
        return result.结果类.成功方法(图像.copy())
    finally:
        缓冲区.close()


def 图片生成处理器(
    目标方法: callable,
    *参数: any,
    **关键字参数: any
) -> result.结果类:
    """
    执行方法并处理图片结果的通用方法

    参数:
        目标方法: 要执行的目标方法
        *参数: 目标方法的位置参数
        **关键字参数: 目标方法的关键字参数

    返回:
        处理后的结果对象
    """
    # 直接执行目标方法
    原始结果 = 目标方法(*参数, **关键字参数)

    # 检查任务是否执行成功
    if not 原始结果.是否成功:
        return result.结果类.失败方法(f"操作失败: {原始结果.错误信息}")

    # 对成功的结果进行通用图片处理
    处理后的结果 = 通用图片构造方法(原始结果.数据信息)

    return 处理后的结果