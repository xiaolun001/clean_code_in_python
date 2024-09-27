import textwrap
from sync_executor import SyncCodeExecutor


class PyExecutor(SyncCodeExecutor):
    def __init__(self, work_dir: str = None, is_save_obj: bool = False, **kwargs):
        init_code = textwrap.dedent("""
        import numpy as np
        import pandas as pd
        import dill
        import matplotlib.pyplot as plt

        def save_object(filename):
            variables = globals().copy()
            filtered_variables = {name: value for name, value in variables.items() if not name.startswith('__')}
            with open(filename, 'wb') as f:
                dill.dump(filtered_variables, f)

        def load_object(filename):
            with open(filename, "rb") as f:
                vars = dill.load(f)
                globals().update(vars)
        """)
        super().__init__(
            ["python3", "-i", "-q", "-u", "-c", init_code],  # 启动一个 Python 交互式会话
            'print("{}")',
            work_dir=work_dir,
            is_save_obj=is_save_obj,
            save_obj_cmd="save_object('{}')\n",
            load_obj_cmd="load_object('{}')\n",
        )


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


if __name__ == '__main__':
    test_save()
    test_load()
