# coding=utf-8
# tests/test_pm_commands.py
import pytest


@pytest.mark.asyncio
async def test_team_query_success(app, db_session, mock_event_factory, registered_user):
    # 准备：为 registered_user 创建一个队伍
    from your_project.services import team_service
    await team_service.create_team(db_session, user_id=registered_user, team_name="梦之队")

    # 操作：模拟用户发送指令
    event = mock_event_factory(user_id=registered_user, message="/pm 队伍")
    # 假设你的 app 有一个方法可以处理事件
    response = await app.handle_event(event)

    # 断言：检查返回结果
    assert response is not None
    assert "梦之队" in response.text  # 假设响应是个包含文本的对象


@pytest.mark.asyncio
async def test_team_query_no_team(app, mock_event_factory, registered_user):
    # 准备：该用户没有任何队伍 (因为 db_session 每次都回滚)

    # 操作
    event = mock_event_factory(user_id=registered_user, message="/pm 队伍")
    response = await app.handle_event(event)

    # 断言
    assert "您还没有任何队伍" in response.text


# tests/test_pm_commands.py
import pytest


@pytest.mark.asyncio
async def test_create_team(app, db_session, mock_event_factory, registered_user):
    # 准备：无需特殊准备

    # 操作
    event = mock_event_factory(user_id=registered_user, message="/pm 新建队伍 我的第一支队伍")
    response = await app.handle_event(event)

    # 断言：检查响应和数据库状态
    assert "成功创建队伍" in response.text

    # 直接查询数据库进行验证
    from your_project.repository import team_repo
    teams = await team_repo.get_teams_by_user(db_session, user_id=registered_user)
    assert len(teams) == 1
    assert teams[0].name == "我的第一支队伍"


# tests/test_pm_commands.py
import pytest


@pytest.mark.asyncio
async def test_force_rename_by_admin(app, db_session, mock_event_factory, registered_user):
    # 准备：先给 registered_user 创建一个宝可梦
    # ... (此处省略创建宝可梦的代码) ...
    pokemon_id = 1

    # 操作：模拟管理员发送指令
    admin_id = 99999  # 假设的管理员ID
    event = mock_event_factory(user_id=admin_id,
                               message=f"/pm 强制改名 {pokemon_id} 新名字",
                               is_admin=True)
    response = await app.handle_event(event)

    # 断言
    assert "强制改名成功" in response.text


@pytest.mark.asyncio
async def test_force_rename_by_normal_user(app, mock_event_factory, registered_user):
    # 准备
    pokemon_id = 1

    # 操作：模拟普通用户发送指令
    event = mock_event_factory(user_id=registered_user,
                               message=f"/pm 强制改名 {pokemon_id} 新名字",
                               is_admin=False)
    response = await app.handle_event(event)

    # 断言
    assert "权限不足" in response.text

