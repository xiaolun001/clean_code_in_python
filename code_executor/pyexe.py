from code_executor.constant import PyExeConfig
from code_executor.sync_executor import SyncCodeExecutor
from code_executor.async_executor import AsyncCodeExecutor


class PyExecutor(SyncCodeExecutor):
    def __init__(self, work_dir: str = None, is_save_obj: bool = False, **kwargs):
        super().__init__(
            PyExeConfig.session_command,
            PyExeConfig.print_cmd,
            work_dir=work_dir,
            is_save_obj=is_save_obj,
            save_obj_cmd=PyExeConfig.save_obj_cmd,
            load_obj_cmd=PyExeConfig.load_obj_cmd,
        )


class AsyncPyExecutor(AsyncCodeExecutor):
    def __init__(self, work_dir: str = None, is_save_obj: bool = False, **kwargs):
        super().__init__(
            PyExeConfig.session_command,
            PyExeConfig.print_cmd,
            work_dir=work_dir,
            is_save_obj=is_save_obj,
            save_obj_cmd=PyExeConfig.save_obj_cmd,
            load_obj_cmd=PyExeConfig.load_obj_cmd,
        )
