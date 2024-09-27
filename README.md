# Clean Code in Python 学习案例集

## 项目简介

在实际案例中，实践《Clean Code in Python》中的编码原则，练习编写简洁、可维护、高效的python代码。

## 学习参考

建议使用 Poetry 管理虚拟环境, 具体教程见文档[poetry](doc/poetry.md)

1. [Clean Code in Python - Second Edition: Develop maintainable and efficient code](https://www.amazon.com/Clean-Code-Python-maintainable-efficient/dp/1800560214)
2. [Tips for clean code in Python](https://pybit.es/articles/tips-for-clean-code-in-python/)

## 贡献
欢迎提交 issue 和 pull request，与我一起讨论如何进一步优化代码。

### 提交PR须知

1. 提交PR之前，请对修改的代码执行如下命令:
    ```bash
    black your_py_file_path_or_dir
    # 例如
    black ./code_executor
    black ./code_executor/sync_executor.py
    ```
