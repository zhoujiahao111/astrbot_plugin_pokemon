# coding=utf-8
from pathlib import Path
import inspect
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.exc import ArgumentError
from contextlib import asynccontextmanager
from sqlalchemy import select, update, delete, insert, func, asc, desc
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.inspection import inspect
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import class_mapper

from .. import schema
from ..models import result, increment, enums
from ..schema.base import Base as 模型基础

数据库路径 = Path(__file__).resolve().parents[3] / 'plugins_db' / 'astrbot_plugin_pokemon.db'


class 数据库管理器:
    """
    一个统一、安全的数据库操作接口。
    - 查询操作是只读的。
    - 写入操作（增、删、改）是原子性的，要么全部成功，要么全部失败。
    """

    def __init__(self):
        self.引擎 = create_async_engine(f'sqlite+aiosqlite:///{数据库路径}', echo=False)
        self._会话工厂 = async_sessionmaker(self.引擎, expire_on_commit=False, class_=AsyncSession)

        self._注册的模型 = {
            '激活效果表': schema.激活效果表,
            '排行榜表': schema.排行榜表,
            '招式表': schema.招式表,
            '宝可梦表': schema.宝可梦表,
            '队伍信息表': schema.队伍信息表,
            '队伍成员表': schema.队伍成员表,
            '用户表': schema.用户表,
            '用户物品表': schema.用户物品表,
        }

    def 获取数据表方法(self, 表名):
        """
        【优化二：更健壮的方法】
        根据输入的字符串名称或枚举，返回对应的数据表类。
        """
        if isinstance(表名, enums.表名类):
            key = 表名.value
        else:
            key = str(表名)

        model_class = self._注册的模型.get(key)
        if model_class is None:
            print(f"未能找到名为 '{key}' 的已注册模型。")
        return model_class

    async def 初始化创建数据表方法(self):
        """
        【修改三：使用正确的 Base 并优化提示】
        现在 `模型基础.metadata` 持有了所有已注册模型的信息。
        """
        # 为了让 SQLAlchemy 的 Base 能够收集到所有模型，
        # 必须确保在调用此方法前，所有定义模型的 Python 文件（如 user.py, move.py）都已被导入。
        # 通常这通过在 `schema` 包的 `__init__.py` 文件中导入所有模型来实现。
        if not 模型基础.metadata.tables:
            print("警告: MetaData 中没有任何数据表被注册！请检查模型是否在 `schema/__init__.py` 中被正确导入。")
            return

        async with self.引擎.begin() as conn:
            await conn.run_sync(模型基础.metadata.create_all)

    @asynccontextmanager
    async def _获取会话(self):
        会话 = self._会话工厂()
        try:
            yield 会话
            await 会话.commit()
        except Exception as e:
            print(f"发生错误，异步事务已回滚: {e}")
            await 会话.rollback()
            raise
        finally:
            await 会话.close()

    async def 查询方法(self, 查询任务: list[dict]) -> list[result.结果类]:
        """
        安全、只读，用于执行一次或多次查询。
        每个查询任务都将被独立处理，单个任务的失败不会影响其他任务。
        支持后续任务通过元组 ("索引", <结果列表的索引>) 引用前面任务的执行结果。

        :param 查询任务: 一个包含多个查询指令的列表。每个指令是一个字典。
            示例: [
                {'表名': 表名类.用户表, '查询数据': ['用户ID', '名称']},
                {'表名': '用户表', '条件': {'名称': '张三', '分页大小': 10, '页码': 1, '排序': '用户ID DESC', '盒子序号': 'NOT NULL'}},
            ]
        :return: 一个 `结果类` 对象的列表，其长度与输入的 `查询任务` 列表相同。
        """
        最终结果 = []
        执行结果列表 = [] 
        try:
            async with self._获取会话() as 会话:
                for 任务 in 查询任务:
                    try:
                        解析结果 = _解析任务(执行结果列表, 任务)
                        if not 解析结果.是否成功:
                            最终结果.append(解析结果)
                            执行结果列表.append(None)
                            continue
                        任务 = 解析结果.数据信息
  
                        表名_输入值 = 任务.get('表名')
                        if not 表名_输入值:
                            错误详情 = "任务字典中缺少 '表名' 字段。"
                            最终结果.append(result.结果类.失败方法(错误详情))
                            执行结果列表.append(None)
                            continue

                        if isinstance(表名_输入值, enums.表名类):
                            表名 = 表名_输入值.value
                        else:
                            表名 = str(表名_输入值)

                        查询数据 = 任务.get('查询数据')
                        条件 = 任务.get('条件', {}).copy()

                        模型类 = self._注册的模型.get(表名)
                        if not 模型类:
                            错误详情 = f"错误：未找到名为 '{表名}' 的模型。"
                            最终结果.append(result.结果类.失败方法(错误详情))
                            执行结果列表.append(None)
                            continue

                        分页大小 = 条件.pop('分页大小', None)
                        页码 = 条件.pop('页码', None)
                        排序 = 条件.pop('排序', None)

                        if 查询数据:
                            if isinstance(查询数据, str):
                                查询列 = [getattr(模型类, 查询数据)]
                            elif isinstance(查询数据, list):
                                查询列 = [getattr(模型类, 列名) for 列名 in 查询数据]
                            else:
                                raise TypeError("'查询数据' 字段必须是字符串或列表类型。")
                            查询语句 = select(*查询列)
                        else:
                            查询语句 = select(模型类)

                        if 条件 and isinstance(条件, dict):
                            for 列名, 值 in 条件.items():
                                if not hasattr(模型类, 列名):
                                    raise AttributeError(f"模型 '{表名}' 中不存在用于条件的列 '{列名}'。")

                                列对象 = getattr(模型类, 列名)
                                # 此处逻辑天然支持解析后的列表，会生成 IN 查询
                                if isinstance(值, list):
                                    查询语句 = 查询语句.filter(列对象.in_(值))
                                elif isinstance(值, str):
                                    value_upper = 值.upper()
                                    if value_upper == 'NOT NULL':
                                        查询语句 = 查询语句.filter(列对象.is_not(None))
                                    elif value_upper == 'IS NULL':
                                        查询语句 = 查询语句.filter(列对象.is_(None))
                                    else:
                                        查询语句 = 查询语句.filter(列对象 == 值)
                                else:
                                    查询语句 = 查询语句.filter_by(**{列名: 值})

                        if 排序 and isinstance(排序, str):
                            排序条件列表 = []
                            for part in [p.strip() for p in 排序.split(',') if p.strip()]:
                                sort_parts = part.split()
                                列名 = sort_parts[0]
                                方向 = sort_parts[1].upper() if len(sort_parts) > 1 else 'ASC'

                                if not hasattr(模型类, 列名):
                                    raise AttributeError(f"模型 '{表名}' 中不存在用于排序的列 '{列名}'。")

                                排序列 = getattr(模型类, 列名)
                                if 方向 == 'DESC':
                                    排序条件列表.append(desc(排序列))
                                else:
                                    排序条件列表.append(asc(排序列))

                            if 排序条件列表:
                                查询语句 = 查询语句.order_by(*排序条件列表)

                        if 分页大小 is not None and 页码 is not None:
                            try:
                                page_size = int(分页大小)
                                page_num = int(页码)
                                if page_size <= 0 or page_num <= 0:
                                    raise ValueError("分页大小和页码必须是正整数。")
                                offset = (page_num - 1) * page_size
                                查询语句 = 查询语句.offset(offset).limit(page_size)
                            except (ValueError, TypeError):
                                raise ValueError("'分页大小' 和 '页码' 必须是有效的正整数。")

                        结果 = await 会话.execute(查询语句)

                        if isinstance(查询数据, list) or not 查询数据:
                            单次查询结果 = [dict(row) for row in 结果.mappings().all()]
                        else:
                            单次查询结果 = 结果.scalars().all()

                        最终结果.append(result.结果类.成功方法(单次查询结果))
                        执行结果列表.append(单次查询结果)

                    except (ValueError, TypeError, AttributeError, Exception) as e:
                        错误详情 = f"处理任务 {任务} 时出错: {e}"
                        最终结果.append(result.结果类.失败方法(错误详情))
                        执行结果列表.append(None)

        except Exception as e:
            num_processed = len(最终结果)
            num_remaining = len(查询任务) - num_processed
            error_message = f"发生致命错误，无法处理后续任务: {e}"
            for _ in range(num_remaining):
                最终结果.append(result.结果类.失败方法(error_message))

        return 最终结果

    async def 单次查询方法(self, 查询任务: dict) -> result.结果类:
        """执行单次查询的便利方法, 直接返回结果类"""
        结果列表 = await self.查询方法([查询任务])
        return 结果列表[0]

    async def join查询方法(
        self,
        查询字段: list,
        主模型,
        连接信息: list[dict] = None,
        筛选条件: list = None,
        排序规则: list = None,
        分页大小: int = None,
        页码: int = 1
    ) -> result.结果类:
        """
        一个支持多表JOIN、复杂条件、排序和分页的异步查询方法。
        """
        try:
            实际查询字段 = []
            for 字段 in 查询字段:
                try:
                    mapper = class_mapper(字段)
                    实际查询字段.extend(mapper.columns)
                except (ArgumentError, UnmappedClassError):
                    实际查询字段.append(字段)

            async with self._获取会话() as 会话:
                try:
                    主模型_orm = self.获取数据表方法(主模型)

                    查询语句 = select(*实际查询字段).select_from(主模型_orm)

                    if 连接信息:
                        for 连接 in 连接信息:
                            连接模型 = self.获取数据表方法(连接["模型"])
                            连接条件 = 连接["条件"]
                            连接类型 = 连接.get("类型", "INNER").upper()

                            if 连接类型 == "LEFT":
                                查询语句 = 查询语句.outerjoin(连接模型, 连接条件)
                            else:
                                查询语句 = 查询语句.join(连接模型, 连接条件)

                    if 筛选条件:
                        查询语句 = 查询语句.where(*筛选条件)

                    if 排序规则:
                        查询语句 = 查询语句.order_by(*排序规则)

                    if 分页大小 is not None:
                        查询语句 = 查询语句.limit(分页大小)
                        if 页码 > 0:
                            查询语句 = 查询语句.offset((页码 - 1) * 分页大小)

                    执行结果 = await 会话.execute(查询语句)
                    查询记录 = 执行结果.all()

                    数据 = [dict(记录._mapping) for 记录 in 查询记录]
                    return result.结果类.成功方法(数据)

                except Exception as e:
                    print(f"数据库会话内部发生错误: {e}")
                    import traceback
                    traceback.print_exc()
                    await 会话.rollback()
                    return result.结果类.失败方法(f"数据库查询执行失败: {e}")

        except Exception as e:
            print(f"构建查询时发生错误: {e}")
            import traceback
            traceback.print_exc()
            return result.结果类.失败方法(f"查询构建失败: {e}")

    async def 写入方法(self, 写入任务: list[dict]) -> result.结果类:
        """
        在单个事务中执行所有数据变更操作 (SQLite)。
        支持后续任务通过元组 ("索引", <结果列表的索引>) 引用前面任务的执行结果。

        :param 写入任务: 一个包含多个写入指令的列表。
        :return: 一个列表，按顺序包含每个任务的执行结果，并用结果类包装。
        """
        执行结果列表 = []

        async with self._获取会话() as 会话:
            async with 会话.begin():
                for 任务 in 写入任务:
                    解析结果 = _解析任务(执行结果列表, 任务)
                    if not 解析结果.是否成功:
                        return 解析结果
                    任务 = 解析结果.数据信息

                    try:
                        表名 = 任务['表名'].value
                        操作 = 任务['操作'].value
                    except KeyError as 异常:
                        return result.结果类.失败方法(f"任务缺少必要的字段：{异常}")

                    模型类 = self._注册的模型.get(表名)
                    if not 模型类:
                        return result.结果类.失败方法(f"错误：未找到名为 '{表名}' 的模型。")

                    主键列 = inspect(模型类).primary_key[0]

                    if 操作 == '插入':
                        try:
                            数据 = 任务['数据']
                        except KeyError:
                            return result.结果类.失败方法("插入操作需要 '数据' 字段。")

                        if isinstance(数据, list):
                            if 数据:
                                语句 = insert(模型类).values(数据).returning(主键列)
                                结果代理 = await 会话.execute(语句)
                                当前任务结果 = 结果代理.scalars().all()
                            else:
                                当前任务结果 = []
                        elif isinstance(数据, dict):
                            实例 = 模型类(**数据)
                            会话.add(实例)
                            await 会话.flush([实例])
                            当前任务结果 = getattr(实例, 主键列.name)
                        else:
                            return result.结果类.失败方法("插入操作的 '数据' 字段必须是字典或字典列表。")

                    elif 操作 == '更新':
                        try:
                            条件 = 任务['条件']
                            数据 = 任务['数据']
                        except KeyError as 异常:
                            return result.结果类.失败方法(f"更新操作需要 {异常} 字段。")

                        待更新数据 = self._处理增量更新(模型类, 数据)

                        try:
                            查询条件 = _构建查询条件(模型类, 条件)
                        except AttributeError as 异常:
                            return result.结果类.失败方法(f"构建查询条件时出错：{异常}")

                        语句 = update(模型类).where(*查询条件).values(待更新数据).returning(主键列)
                        结果代理 = await 会话.execute(语句)
                        当前任务结果 = 结果代理.scalars().all()

                    elif 操作 == "更新或写入":
                        try:
                            数据 = 任务['数据']
                            条件 = 任务.get('条件')
                            if not 条件:
                                return result.结果类.失败方法("更新或写入操作需要 '条件' 字段来确定冲突目标。")
                        except KeyError:
                            return result.结果类.失败方法("更新或写入操作需要 '数据' 字段。")

                        插入数据 = {**条件, **数据}
                        插入值 = {
                            键: 值.值 if isinstance(值, increment.增量类) else 值
                            for 键, 值 in 插入数据.items()
                        }

                        语句 = sqlite_insert(模型类).values(插入值)

                        更新集 = {}
                        for 列名, 原始值 in 数据.items():
                            列对象 = getattr(inspect(模型类).c, 列名)

                            if 列对象.primary_key:
                                continue

                            # **关键修复点 2：为"更新或写入"操作添加上/下限逻辑**
                            # 使其行为与"更新"操作中的 _处理增量更新 方法保持一致。
                            if isinstance(原始值, increment.增量类):
                                # 基础表达式是现有值 + 尝试插入但被排除的值
                                更新表达式 = 列对象 + getattr(语句.excluded, 列对象.name)

                                # 应用下限约束
                                if 原始值.下限 is not None:
                                    更新表达式 = func.max(更新表达式, 原始值.下限)

                                # 应用上限约束
                                if 原始值.上限 is not None:
                                    更新表达式 = func.min(更新表达式, 原始值.上限)

                                更新集[列对象.name] = 更新表达式
                            else:
                                更新集[列对象.name] = getattr(语句.excluded, 列对象.name)

                        冲突目标 = list(条件.keys())

                        if not 更新集:
                            语句 = 语句.on_conflict_do_nothing(index_elements=冲突目标)
                        else:
                            语句 = 语句.on_conflict_do_update(
                                index_elements=冲突目标,
                                set_=更新集
                            )

                        语句 = 语句.returning(主键列)

                        结果代理 = await 会话.execute(语句)
                        当前任务结果 = 结果代理.scalar()

                    elif 操作 == '删除':
                        try:
                            条件 = 任务['条件']
                        except KeyError:
                            return result.结果类.失败方法("删除操作需要 '条件' 字段。")

                        try:
                            查询条件 = _构建查询条件(模型类, 条件)
                        except AttributeError as 异常:
                            return result.结果类.失败方法(f"构建查询条件时出错：{异常}")

                        语句 = delete(模型类).where(*查询条件).returning(主键列)
                        结果代理 = await 会话.execute(语句)
                        当前任务结果 = 结果代理.scalars().all()

                    else:
                        return result.结果类.失败方法(f"错误：不支持的操作类型 '{操作}'。")

                    执行结果列表.append(当前任务结果)

        return result.结果类.成功方法(执行结果列表)

    def _处理增量更新(self, 模型类, 数据: dict) -> dict:
        """
        处理更新数据中的 increment.增量类 实例，将其转换为 SQLAlchemy 表达式。
        支持上限和下限约束。
        """
        处理后的值 = {}

        for 字段名, 字段值 in 数据.items():
            if isinstance(字段值, increment.增量类):
                字段 = getattr(模型类, 字段名)
                # 基础表达式
                表达式 = 字段 + 字段值.值

                if 字段值.下限 is not None:
                    表达式 = func.max(表达式, 字段值.下限)

                if 字段值.上限 is not None:
                    表达式 = func.min(表达式, 字段值.上限)

                处理后的值[字段名] = 表达式
            else:
                处理后的值[字段名] = 字段值

        return 处理后的值

def _构建查询条件(模型类, 条件: dict) -> list:
    查询条件列表 = []
    for 键, 值 in 条件.items():
        列属性 = getattr(模型类, 键, None)
        if 列属性 is None:
            raise AttributeError(f"模型 '{模型类.__name__}' 中不存在名为 '{键}' 的列。")

        if isinstance(值, list):
            查询条件列表.append(列属性.in_(值))
        else:
            查询条件列表.append(列属性 == 值)
    return 查询条件列表

def _解析任务(结果列表: list, 当前任务: dict) -> result.结果类:
    """
    返回解析替换索引后的新任务字典。
    兼容 "数据" 或 "条件" 字段为单个字典或字典列表的情况。
    新增支持二元关系索引, 如 ("索引", 0, 1) -> 结果列表[0][1]
    """
    try:
        if not isinstance(当前任务, dict):
            # print("\n\n", 当前任务)
            return result.结果类.失败方法("任务必须为字典")

        新任务 = 当前任务.copy()

        for 键 in ("条件", "数据"):
            容器 = 新任务.get(键)

            if isinstance(容器, dict):
                新容器 = 容器.copy()
                for k, v in 新容器.items():
                    if isinstance(v, tuple) and len(v) > 1 and v[0] == "索引":
                        try:
                            if len(v) == 2:
                                新容器[k] = 结果列表[v[1]]
                            elif len(v) == 3:
                                新容器[k] = 结果列表[v[1]][v[2]]
                            else:
                                return result.结果类.失败方法(f"非法格式：不支持的元组长度 {len(v)}")
                        except IndexError:
                            return result.结果类.失败方法(f"索引超出结果列表范围，操作的索引为 {v}")
                新任务[键] = 新容器

            elif isinstance(容器, list):
                新列表 = []
                for item in 容器:
                    if not isinstance(item, dict):
                        新列表.append(item)
                        continue

                    新项目 = item.copy()
                    for k, v in 新项目.items():
                        if isinstance(v, tuple) and len(v) > 1 and v[0] == "索引":
                            try:
                                if len(v) == 2:
                                    新项目[k] = 结果列表[v[1]]
                                elif len(v) == 3:
                                    新项目[k] = 结果列表[v[1]][v[2]]
                                else:
                                    return result.结果类.失败方法(f"非法格式：不支持的元组长度 {len(v)}")
                            except IndexError:
                                return result.结果类.失败方法(f"索引超出结果列表范围，操作的索引为 {v}")
                    新列表.append(新项目)
                新任务[键] = 新列表

        return result.结果类.成功方法(新任务)

    except Exception as e:
        return result.结果类.失败方法(f"解析任务时发生未知错误: {str(e)}")


_数据库实例 = None


async def 获取数据库对象() -> 数据库管理器:
    """
    获取数据库管理器的单例。
    如果实例不存在，则创建、异步初始化并返回。
    """
    global _数据库实例

    if _数据库实例 is None:
        _数据库实例 = 数据库管理器()
        await _数据库实例.初始化创建数据表方法()
    return _数据库实例