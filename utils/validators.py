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