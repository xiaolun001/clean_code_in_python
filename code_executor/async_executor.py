# 本代码由deepseek v2.5 将ch2PythonicCode/basic_process.py转换为异步代码
from typing import Union, List
from collections import OrderedDict
import subprocess
import asyncio
from loguru import logger


class AsyncCodeExecutor(object):
    def __init__(self, base_command: Union[str, List[str]] = "bash", print_cmd: str = 'echo "{}"'):
        self.base_command = base_command
        self.print_cmd = print_cmd + "\n"
        self.process = None
        self.cmd_space = OrderedDict()  # cmd_id, cmd, stdout, stderr
        self.cmd_event = asyncio.Event()  # 用于通知命令执行完成

    async def start_process(self):
        self.process = await asyncio.create_subprocess_exec(
            *self.base_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        asyncio.create_task(self.save_and_print_output(self.process.stdout, "STDOUT: "))
        asyncio.create_task(self.save_and_print_output(self.process.stderr, "STDERR: "))

    async def stop_process(self):
        if self.process:
            logger.info("Attempting to terminate the process...")
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=10)
            except asyncio.TimeoutError:
                logger.warning("Process did not terminate in time. Killing...")
                self.process.kill()
        logger.info("Process terminate successfully!")

        # set process to None
        self.process = None
        logger.info("Stderr and stdout thread terminate successfully!")

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
                    cmd_id = list(self.cmd_space)[-1]
                    self.cmd_space[cmd_id]["stderr"] = stderr.strip()
                    self.cmd_space[cmd_id]["stdout"] = stdout.strip()
                    stdout, stderr = "", ""
                    self.cmd_event.set()  # 通知命令执行完成

    async def run(self):
        while True:
            # 从外部获取命令（通过yield）
            args = yield
            if args is None:
                continue

            if self.process is None:
                await self.start_process()

            self.cmd_event.clear()  # 清除事件标志

            full_command = " ".join(args) + "\n\n"
            cmd_id = str(len(self.cmd_space))
            # 添加cmd到cmd_space
            self.cmd_space[cmd_id] = {}
            self.cmd_space[cmd_id]["cmd"] = full_command

            full_command += self.print_cmd.format("END_OF_EXECUTION")
            logger.info(f"Sending command: {full_command.strip()}")

            try:
                self.process.stdin.write(full_command.encode())
                await self.process.stdin.drain()  # 确保代码被发送
            except BrokenPipeError:
                logger.warning("Process has terminated. Restarting...")
                await self.start_process()
                self.process.stdin.write(full_command.encode())
                await self.process.stdin.drain()
            except KeyboardInterrupt:
                logger.warning("\nReceived keyboard interrupt. Terminating...")
                await self.stop_process()
                break

            # 等待命令执行完成
            await self.cmd_event.wait()


# 使用示例
if __name__ == "__main__":

    async def main():
        # Python command runner
        pyer = AsyncCodeExecutor(["python3", "-i", "-q", "-u"], 'print("{}")')

        # 初始化生成器
        python_code_gen = pyer.run()
        await python_code_gen.asend(None)  # 启动生成器

        # 模拟发送命令
        await python_code_gen.asend(["print('Hello from Python!')"])
        await python_code_gen.asend(["a = 1;b=2"])
        await python_code_gen.asend(["print(a + b)"])
        await python_code_gen.asend(["print(a + b"])
        await python_code_gen.asend(["print(a + b)"])

        print(pyer.cmd_space)
        # 停止python进程
        await pyer.stop_process()

    asyncio.run(main())
