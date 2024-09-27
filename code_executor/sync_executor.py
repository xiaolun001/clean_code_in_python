# 使用threading.Thread来实时打印subprocess.Popen的stdout和stderr
import fire
import shutil
from pathlib import Path
from typing import Union, List, Literal
from collections import OrderedDict
import io
import subprocess
import threading
from loguru import logger


class SyncCodeExecutor(object):
    def __init__(
        self,
        base_command: Union[str, List[str]] = "bash",
        print_cmd: str = 'echo "{}"',
        *,
        work_dir: str = None,
        is_save_vars: bool = False,
        save_load_vars_cmd: str = None,
    ):
        self.base_command = base_command
        self.print_cmd = print_cmd + "\n"
        self.process = None
        self.stdin_thread = None
        self.stdout_thread = None
        self.stderr_thread = None
        self.cmd_event = threading.Event()  # 用于通知process前一个输入的command是否执行完成
        self.cmd_space = OrderedDict()  # cmd_id: {cmd, stddout, stderr}
        # 下面是为了磁盘保存对象而设置
        self.work_dir = work_dir or f"./{base_command}"
        self.is_save_vars = is_save_vars
        self.save_load_vars_cmd = save_load_vars_cmd
        if self.is_save_vars:
            assert self.save_load_vars_cmd is not None

    def manage_work_dir(self, cmd: Literal["c", "d"] = "c"):
        """管理cmd变量的共享文件目录"""
        if self.is_save_vars:
            root = Path(self.work_dir)
            root.mkdir(parents=True, exist_ok=True)
            current_cmd_id = str(len(self.cmd_space) - 1)

            if cmd == "c":
                (root / current_cmd_id).mkdir(parents=True, exist_ok=True)

            if cmd == "d":
                shutil.rmtree(str(root))

    def start_process(self, command):
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.stdout_thread = threading.Thread(
            target=self.save_and_print_output, args=(self.process.stdout, "STDOUT: "), daemon=True
        )
        self.stderr_thread = threading.Thread(
            target=self.save_and_print_output, args=(self.process.stderr, "STDERR: "), daemon=True
        )

        self.stdout_thread.start()
        self.stderr_thread.start()

    def stop_process(self):
        if self.process:
            logger.info("Attempting to terminate the process...")
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("Process did not terminate in time. Killing...")
                self.process.kill()
        logger.info("Process terminate successfully!")

        logger.info("Attempting to terminate the stderr and stdout thread ...")
        if self.cmd_event:
            self.cmd_event.set()

        # Wait until the thread terminates.
        if self.stderr_thread:
            self.stderr_thread.join()

        if self.stdout_thread:
            self.stdout_thread.join()

        # set process, thread is None
        self.process = None
        self.stdout_thread = None
        self.stderr_thread = None
        logger.info("Stderr and stdout thread terminate successfully!")

    def save_and_print_output(self, pipe: io.TextIOWrapper, prefix: str = ""):
        stdout, stderr = "", ""
        for line in iter(pipe.readline, ""):
            line = line.strip()
            if line:

                if prefix.startswith("STDERR:"):
                    stderr += "\n" + line.strip()

                if prefix.startswith("STDOUT:"):
                    stdout += "\n" + line.strip() if "END_OF_EXECUTION" not in line else "\n"

                if "END_OF_EXECUTION" not in line and "HISTORY_VARS" not in line:
                    print(f"{prefix}{line}")

                if "END_OF_EXECUTION" in line:
                    cmd_id = list(self.cmd_space)[-1]
                    self.cmd_space[cmd_id]["stderr"] = stderr.strip()
                    self.cmd_space[cmd_id]["stdout"] = stdout.strip()
                    stdout, stderr = "", ""

                if "END_OF_EXECUTION" in line or prefix.startswith("STDERR:"):
                    self.cmd_event.set()

    def _run(self, cmds):
        if self.process is None:
            self.start_process(self.base_command)

        self.cmd_event.clear()

        full_command = " ".join(cmds) + "\n\n"
        cmd_id = str(len(self.cmd_space))
        # 添加cmd到cmd_space
        self.cmd_space[cmd_id] = {}
        self.cmd_space[cmd_id]["cmd"] = full_command
        self.manage_work_dir()

        full_command += self.print_cmd.format("END_OF_EXECUTION")
        logger.info(f"Sending command: {full_command.strip()}")

        try:
            self.process.stdin.write(full_command)
            self.process.stdin.flush()  # 确保代码被发送
        except BrokenPipeError:
            logger.warning("Process has terminated. Restarting...")
            self.start_process(self.base_command)
            self.process.stdin.write(full_command)
            self.process.stdin.flush()
        except KeyboardInterrupt:
            logger.warning("\nReceived keyboard interrupt. Terminating...")
            self.stop_process()
            raise KeyboardInterrupt()
        # Wait until execution completes
        self.cmd_event.wait()

    def run(self):
        while True:
            # 从外部获取命令（通过yield）
            cmds = yield
            if cmds is None:
                continue
            try:
                self._run(cmds)
            except Exception:
                break


def test():
    pyer = SyncCodeExecutor(["python3", "-i", "-q", "-u"], 'print("{}")')
    # 初始化生成器
    python_code_gen = pyer.run()
    next(python_code_gen)  # 启动生成器

    # 模拟发送命令
    python_code_gen.send(["print('Hello from Python!')"])
    python_code_gen.send(["a = 1;b=2;c=3"])
    python_code_gen.send(["print(a + b)"])
    python_code_gen.send(["print(a + b"])
    print(pyer.cmd_space)
    # 停止python进程
    pyer.stop_process()


# 使用示例
if __name__ == "__main__":
    fire.Fire(test)
