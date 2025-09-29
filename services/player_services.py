# coding=utf-8
from ..core import database
from ..utils import image_utils, text_utils
from ..models import result
from ..models.enums import 表名类
from ..services import pokemon_services
from ..models.session import 会话类
from ..dtos import 伙伴管理器, 伙伴模型, 宝可梦图鉴管理器

async def 判断用户是否注册方法(用户qq: int) -> result.结果类:
    db = await database.获取数据库对象()

    return await db.单次查询方法(
        {
            "表名": 表名类.用户表,
            "查询数据": "用户ID",
            "条件": {
                "用户ID": 用户qq
            }
        }
    )

def 输出初始伙伴组合信息方法(初始伙伴: 伙伴管理器) -> str:
    结果列表 = [
        "/pm 领养 [编号] 或 [组合名称]\n",
        "请从下面选择一个组合：\n",
        "--------------------\n"
    ]

    for 序号, 名称 in enumerate(初始伙伴.获取所有组合名称(), 1):
        结果列表.append(f"{序号} - {名称}\n")

    结果列表.append("\n--------------------")
    结果列表.append("\n例如: /pm 领养 1")

    return "\n".join(结果列表)


def 输出伙伴组合详细信息方法(
    初始伙伴: 伙伴管理器,
    宝可梦图鉴: 宝可梦图鉴管理器,
    选择: str,
    存储数据: str,
    页数: int = 1
) -> tuple[str | list, str | None, bool, int]:
    try:
        if type(选择) is int or str(选择).isdigit():
            try:
                组合名称 = list(初始伙伴.获取所有组合名称())[int(选择) - 1]
            except:
                return "请确定输入的是合法的序号, 或改为输入组合名称", None, False, 页数

        elif 选择 == "上一页":
            页数 = max(1, 页数 - 1)
            组合名称 = 存储数据
        elif 选择 == "下一页":
            页数 = 页数 + 1
            组合名称 = 存储数据
        else:
            结果 = text_utils.名称模糊匹配方法(初始伙伴.获取所有组合名称(), 选择, 是否返回索引=False)

            if 结果.是否成功:
                组合名称 = 选择
            else:
                return 结果.错误信息, None, False, 页数

    except Exception as e:
        print("领养指令 解析输入时存在错误:", str(e))
        return "解析输入时产生了未知错误", None, False, 页数

    伙伴模型列表: [伙伴模型] = 初始伙伴.根据名称获取伙伴列表(组合名称)

    if 伙伴模型列表 is None:
        return "输入的组合名称似乎不正确, 建议检查一下", None, False, 页数

    if len(伙伴模型列表) > 3:
        初始索引 = (页数 - 1) * 5
        # 防止页数超出范围导致索引越界
        if 初始索引 >= len(伙伴模型列表) or 初始索引 < 0:
            return "已经没有下一页或上一页了哦~", 组合名称, False, 页数
        伙伴模型列表: [伙伴模型] = 伙伴模型列表[初始索引: 初始索引 + 5]

    结果列表 = [
        "/pm 领养 [编号] 或 [宝可梦名称]\n输入「/pm 领养 返回」]即可再次选择组合\n▶️ 请从下面选择一名宝可梦："
    ]

    for 序号, i in enumerate(伙伴模型列表, 1):
        索引 = i.索引
        名称 = i.名称

        if 索引 is None or 名称 is None:
            return "组合内的宝可梦信息读取失败, 建议联系机器人的管理员", None, False, 页数

        宝可梦模型 = 宝可梦图鉴.根据编号获取宝可梦(索引+1)

        结果 = image_utils.读取图片方法(类别="pokemon", 名称=宝可梦模型.贴图, 是否转为jpg=True)
        if 结果.是否成功:
            贴图数据: bytes = 结果.数据信息
        else:
            return f"{名称}似乎没有贴图, 请联系管理员", None, False, 页数

        结果列表.append((
            贴图数据,
            序号,
            宝可梦模型.简介
        ))

    return 结果列表, 组合名称, True, 页数

async def 执行用户注册方法(
    会话: 会话类,
    选择: str,
    存储数据: str,
    是否新用户: bool
) -> tuple[str, bool]:
    try:
        伙伴模型列表: list[伙伴模型] = 会话.json管理器.初始伙伴.根据名称获取伙伴列表(存储数据)

        索引 = None
        # 检查'选择'是数字还是字符串
        选择 = str(选择).lstrip('#/')
        if str(选择).isdigit():
            选择索引 = int(选择) - 1  # 用户输入从1开始，列表索引从0开始
            if 0 <= 选择索引 < len(伙伴模型列表):
                索引 = 伙伴模型列表[选择索引].索引
            else:
                return "输入数字无效，请选择列表中的有效序号", False

        else:
            # 按名称进行模糊匹配
            所有名称列表 = [item['名称'] for item in 伙伴模型列表 if '名称' in item]
            结果 = text_utils.名称模糊匹配方法(
                所有名称列表,
                str(选择),
                是否返回索引=True
            )

            if 结果.是否成功:
                # 匹配成功后，通过匹配到的名称反向查找原始'索引'值
                匹配到的名称 = 结果.数据信息[0]
                for 伙伴 in 伙伴模型列表:
                    if 伙伴['名称'] == 匹配到的名称:
                        索引 = 伙伴['索引']
                        break
            else:
                return "找不到与输入名称匹配的宝可梦", False

    except KeyError:
        return "配置项不存在", False
    except ValueError:
        return "输入的内容并不是数字哦", False
    except IndexError:
        return "序号超出范围", False
    except Exception as e:
        return "输入错误: "+str(e), False

    结果 = pokemon_services.宝可梦生成方法(会话=会话, 编号=str(索引+1))

    if 结果.是否成功:
        宝可梦数据: dict = 结果.数据信息
    else:
        return "宝可梦图鉴好像丢失了呢, 请联系管理员", False

    宝可梦数据["用户ID"] = int(会话.用户qq)

    结果 = await pokemon_services.注册宝可梦存储方法(
        会话,
        宝可梦数据,
        是否新用户
    )

    if 结果.是否成功:
        return 结果.数据信息, True
    else:
        print("注册宝可梦时出错:", 结果.错误信息)
        return "登记领取信息出错了, 请联系管理员", False
