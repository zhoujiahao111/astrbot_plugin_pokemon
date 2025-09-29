# coding=utf-8
def 验证用户qq方法(用户qq: str):
    if isinstance(用户qq, int):
        return 用户qq

    if 用户qq.isdigit():
        return int(用户qq)

    # 测试号
    if 用户qq.lower() == "astrbot":
        return 10001

    raise ValueError(f"无效的会话.用户qq格式: {用户qq}")

def 验证qq群方法(群号: str):
    if isinstance(群号, int):
        return 群号

    if 群号.isdigit():
        return int(群号)

    return False