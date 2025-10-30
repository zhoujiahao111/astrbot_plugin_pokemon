# coding=utf-8
# tests/conftest.py
import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 假设这是你的机器人应用实例和数据库模型
from your_project.main import app  # 替换为你的 AstrBot 实例
from your_project.models import Base  # 替换为你的 SQLAlchemy Base

# 1. 设置异步后端
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

# 2. 创建一个全局的、隔离的内存数据库 Fixture
@pytest.fixture(scope="session")
def db_engine():
    # 使用内存 SQLite，速度快且自动清理
    engine = create_engine("sqlite:///:memory:")
    # 创建所有表
    Base.metadata.create_all(engine)
    yield engine
    # 测试结束后可以销毁
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    为每个测试函数提供一个独立的数据库会话，并在测试后回滚。
    这保证了测试之间的完全隔离。
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

# 3. 创建一个模拟事件的工厂 Fixture (借鉴 get_event)
@pytest.fixture
def mock_event_factory():
    def create_event(user_id: int, message: str, is_admin: bool = False):
        # 这里需要根据你 astrbot 的具体事件结构来模拟
        # 核心是提供 user_id 和消息内容
        # 你可以创建一个简单的 mock 对象
        from unittest.mock import MagicMock
        event = MagicMock()
        event.user.id = user_id
        event.message.content = message
        # 你可能还需要一个方法来检查用户是否为管理员
        # 假设你的权限检查依赖于某个属性
        event.user.is_admin = is_admin
        return event

    return create_event

# 4. （可选）创建一个预置数据的用户 Fixture
@pytest_asyncio.fixture(scope="function")
async def registered_user(db_session):
    from your_project.services import user_service # 假设的服务
    # 在数据库中创建一个用户，并返回其 ID
    user_id = 10001
    await user_service.register_user(db_session, user_id)
    return user_id