import shutil
import json
from pathlib import Path
from typing import Union, List, Literal
from collections import OrderedDict
import subprocess
import asyncio
import pprint
from loguru import logger


class AsyncCodeExecutor(object):
    def __init__(
        self,
        base_command: Union[str, List[str]] = "bash",
        print_cmd: str = 'echo "{}"',
        *,
        work_dir: str = None,
        is_save_obj: bool = False,
        save_obj_cmd: str = None,
        load_obj_cmd: str = None
    ):
        self.base_command = base_command
        self.print_cmd = print_cmd + "\n"
        self.__process = None
        self.__cmd_event = asyncio.Event()  # 用于通知process前一个输入的command是否执行完成
        self._cmd_space = OrderedDict()  # cmd_id: {cmd, stddout, stderr}
        # 下面是为了磁盘保存对象而设置
        self.work_dir = work_dir
        self.is_save_obj = is_save_obj
        self.load_obj_cmd = load_obj_cmd
        self.save_obj_cmd = save_obj_cmd
        if self.is_save_obj:
            assert self.save_obj_cmd is not None, "save_obj_cmd should be string cmd when is_save_obj is True!"
            assert self.load_obj_cmd is not None, "load_obj_cmd should be string cmd when is_save_obj is True!"
            assert self.work_dir is not None, "work_dir should be a path when is_save_obj is True!"
            Path(self.work_dir).mkdir(parents=True, exist_ok=True)
        self._executor_save_path = str(Path(self.work_dir) / "executor.json") if self.work_dir else ""

    def manage_work_dir(self, cmd: Literal["c", "d"] = "c"):
        """管理cmd变量的共享文件目录"""
        if self.is_save_obj:
            root = Path(self.work_dir)
            root.mkdir(parents=True, exist_ok=True)
            current_cmd_id = str(len(self._cmd_space) - 1)

            if cmd == "c":
                (root / current_cmd_id).mkdir(parents=True, exist_ok=True)

            if cmd == "d":
                shutil.rmtree(str(root))

    def obj_save_path(self, cmd_id: str) -> str:
        """每段代码内全局作用域中对象的保存路径"""
        return str(Path(self.work_dir) / cmd_id / "globals_object.pickle")

    async def load_obj(self, cmd_id: str):
        """在进程运行时载入每段代码内全局作用域的对象"""
        assert self.__process and self.__process.poll() is not None, "load_obj时进程必须处于运行状态!"
        logger.info(f"Start: load {cmd_id} objects ...")
        filepath = self.obj_save_path(cmd_id)
        load_obj_cmd = self.load_obj_cmd.format(filepath)
        await self._run(load_obj_cmd)
        logger.info(f"Done: load {cmd_id} objects!")

    def load(self) -> "AsyncCodeExecutor":
        """载入Executor对象和全局作用域中所有对象"""
        # 保存第一优先级的is_save_obj
        is_save_obj = self.is_save_obj
        # 载入Executor对象
        with open(f"{self._executor_save_path}", "r") as f:
            executor_state = json.load(f)

        input_kwargs = {k: v for k, v in executor_state.items() if not k.startswith("_")}
        self.__init__(**input_kwargs)
        # 恢复第一优先级的is_save_obj
        self.is_save_obj = is_save_obj

        # 最后一个cmd的全局作用域保存路径
        obj_path = self.obj_save_path(str(len(executor_state["_cmd_space"]) - 1))
        self.base_command[-1] = self.base_command[-1] + self.load_obj_cmd.format(obj_path)

        for k, v in executor_state.items():
            if k.startswith("_"):
                setattr(self, k, v)
        return self

    def save_executor(self):
        """保存Executor对象"""
        assert self.work_dir, "work_dir must be set a value, not None."
        executor_state = {k: v for k, v in self.__dict__.items() if "__" not in k}
        with open(self._executor_save_path, "w") as f:
            json.dump(executor_state, f, sort_keys=True, indent=4)

        # 添加一个.gitignore文件
        with open(str(Path(self.work_dir)/".gitignore"), "w") as f:
            f.write("*\n")

    async def start_process(self):
        self.__process = await asyncio.create_subprocess_exec(
            *self.base_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        asyncio.create_task(self.save_and_print_output(self.__process.stdout, "STDOUT: "))
        asyncio.create_task(self.save_and_print_output(self.__process.stderr, "STDERR: "))

    async def stop_process(self):
        if self.__process:
            logger.info("Attempting to terminate the process...")
            self.__process.terminate()
            try:
                await asyncio.wait_for(self.__process.wait(), timeout=10)
            except asyncio.TimeoutError:
                logger.warning("Process did not terminate in time. Killing...")
                self.__process.kill()
        logger.info("Process terminate successfully!")

        logger.info("Attempting to terminate the stderr and stdout tasks ...")
        if self.__cmd_event:
            self.__cmd_event.set()

        # set process is None
        self.__process = None
        logger.info("Stderr and stdout tasks terminate successfully!")
        if self.is_save_obj:
            self.save_executor()

    async def save_and_print_output(self, pipe: asyncio.StreamReader, prefix: str = ""):
        stdout, stderr = "", ""
        while True:
            line = await pipe.readline()
            if not line:
                break
            line = line.decode().strip()
            if line:
                if prefix.startswith("STDERR:"):
                    stderr += "\n" + line.strip()

                if prefix.startswith("STDOUT:"):
                    stdout += "\n" + line.strip() if "END_OF_EXECUTION" not in line else "\n"

                if "END_OF_EXECUTION" not in line:
                    print(f"{prefix}{line}")

                if "END_OF_EXECUTION" in line:
                    cmd_id = list(self._cmd_space)[-1]
                    self._cmd_space[cmd_id]["stderr"] = stderr.strip()
                    self._cmd_space[cmd_id]["stdout"] = stdout.strip()
                    stdout, stderr = "", ""

                if "END_OF_EXECUTION" in line or prefix.startswith("STDERR:"):
                    self.__cmd_event.set()

    async def _run(self, cmds):
        if self.__process is None:
            await self.start_process()

        self.__cmd_event.clear()

        full_command = " ".join(cmds) + "\n\n"
        cmd_id = str(len(self._cmd_space))
        # 添加cmd到cmd_space
        self._cmd_space[cmd_id] = {}
        self._cmd_space[cmd_id]["cmd"] = full_command

        if self.is_save_obj:
            self.manage_work_dir()
            full_command += self.save_obj_cmd.format(self.obj_save_path(cmd_id))

        full_command += self.print_cmd.format("END_OF_EXECUTION")
        logger.info(f"Sending command: {full_command.strip()}")

        try:
            self.__process.stdin.write(full_command.encode())
            await self.__process.stdin.drain()  # 确保代码被发送
        except BrokenPipeError:
            logger.warning("Process has terminated. Restarting...")
            await self.start_process()
            self.__process.stdin.write(full_command.encode())
            await self.__process.stdin.drain()
        except KeyboardInterrupt:
            logger.warning("\nReceived keyboard interrupt. Terminating...")
            await self.stop_process()
            raise KeyboardInterrupt()
        # Wait until execution completes
        await self.__cmd_event.wait()

    def print_cmd_space(self):
        pprint.pprint(self._cmd_space)

    async def run(self):
        while True:
            # 从外部获取命令（通过yield）
            cmds = yield
            if cmds is None:
                continue

            if isinstance(cmds, str):
                cmds = [cmds]

            try:
                await self._run(cmds)
            except Exception as e:
                logger.error(e)
                break


async def test():
    pyer = AsyncCodeExecutor(["python3", "-i", "-q", "-u"], 'print("{}")')
    # 初始化生成器
    python_code_gen = pyer.run()
    await python_code_gen.asend(None)  # 启动生成器

    # 模拟发送命令
    await python_code_gen.asend(["print('Hello from Python!')"])
    await python_code_gen.asend(["a = 1;b=2;c=3"])
    await python_code_gen.asend(["print(a + b)"])
    print(pyer._cmd_space)
    # 停止python进程
    await pyer.stop_process()


# 使用示例
if __name__ == "__main__":
    asyncio.run(test())
