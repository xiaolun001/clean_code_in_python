import pytest
from code_executor.pyexe import PyExecutor, AsyncPyExecutor


def test_save():
    pyer = PyExecutor("./pyexe_test", True)
    # 初始化生成器
    python_code_gen = pyer.run()
    next(python_code_gen)  # 启动生成器

    # 模拟发送命令
    python_code_gen.send(["print('Hello from Python!')"])
    python_code_gen.send(["a = 1;b=2;c=3"])
    python_code_gen.send(["print(a + b)"])
    python_code_gen.send(["print(globals())"])
    pyer.print_cmd_space()
    # 停止python进程
    pyer.stop_process()
    assert len(pyer._cmd_space) == 4
    assert pyer._cmd_space['0']['stdout'] == 'Hello from Python!'


def test_load():
    work_dir = "./pyexe_test"
    pyer = PyExecutor(work_dir).load()
    # 初始化生成器
    python_code_gen = pyer.run()
    next(python_code_gen)  # 启动生成器

    # 模拟发送命令
    python_code_gen.send(["print(2*a + b + c)"])
    pyer.print_cmd_space()
    # 停止python进程
    pyer.stop_process()
    assert len(pyer._cmd_space) == 5
    assert pyer._cmd_space['4']['stdout'] == '7'


@pytest.mark.asyncio
async def test_async_save():
    pyer = AsyncPyExecutor("./async_pyexe_test", True)
    # 初始化生成器
    python_code_gen = pyer.run()
    await python_code_gen.asend(None)  # 启动生成器

    # 模拟发送命令
    await python_code_gen.asend(["print('Hello from Python!')"])
    await python_code_gen.asend(["a = 1;b=2;c=3"])
    await python_code_gen.asend(["print(a + b)"])
    await python_code_gen.asend(["print(globals())"])
    pyer.print_cmd_space()
    # 停止python进程
    await pyer.stop_process()
    assert len(pyer._cmd_space) == 4


@pytest.mark.asyncio
async def test_async_load():
    work_dir = "./async_pyexe_test"
    pyer = AsyncPyExecutor(work_dir).load()
    # 初始化生成器
    python_code_gen = pyer.run()
    await python_code_gen.asend(None)  # 启动生成器

    # 模拟发送命令
    await python_code_gen.asend(["print(2*a + b + c)"])
    pyer.print_cmd_space()
    # 停止python进程
    await pyer.stop_process()
    assert len(pyer._cmd_space) == 5
    assert pyer._cmd_space['4']['stdout'] == '7'
