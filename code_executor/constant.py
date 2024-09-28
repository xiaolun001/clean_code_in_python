from textwrap import dedent
from dataclasses import dataclass


@dataclass(frozen=True)
class ExeConfig:
    session_command: list   # 启动一个 Python 或者 bash 交互式会话
    print_cmd: str
    save_obj_cmd: str = None
    load_obj_cmd: str = None
    init_code: str = None

    def __post_init__(self):
        if self.init_code is not None:
            self.session_command.append(self.init_code)


PyExeConfig = ExeConfig(
    session_command=["python3", "-i", "-q", "-u", "-c"],
    print_cmd='print("{}")',
    save_obj_cmd="save_object('{}')\n",
    load_obj_cmd="load_object('{}')\n",
    init_code=dedent("""
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
)
