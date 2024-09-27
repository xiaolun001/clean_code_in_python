# 使用 Poetry 管理虚拟环境
通过 pyproject.toml 文件来管理 Python 项目的依赖和配置是现代 Python 项目的常见做法之一，特别是借助工具如 Poetry，你可以使用这些工具根据 pyproject.toml 创建和管理虚拟环境。

## 1.1 安装 Poetry

```bash
pip install poetry
```

## 1.2 初始化 pyproject.toml
在项目根目录下运行以下命令来初始化 pyproject.toml 文件：
```bash
cd your_project_root
poetry init
```
Poetry 会引导你填写项目名称、版本、作者、依赖等信息，完成后会生成 pyproject.toml 文件。

## 1.3 安装依赖和创建虚拟环境
使用以下命令安装依赖并自动创建和激活虚拟环境：
```bash
cd your_project_root
poetry install
```
这将会根据 pyproject.toml 中的依赖创建一个虚拟环境。如果 pyproject.toml 中没有依赖，Poetry 会根据你的 Python 版本创建一个基础虚拟环境。

## 1.4 激活虚拟环境
Poetry 默认会自动管理虚拟环境。在需要手动激活虚拟环境时，你可以使用以下命令，当然这里同样需要进入你使用 Poetry 管理的项目的根目录：
```bash
cd your_project_root
poetry shell
```

## 1.5 添加新依赖
在项目中添加依赖时，使用以下命令：

```bash
cd your_project_root
poetry add <package-name>
```
Poetry 会自动更新 pyproject.toml 并安装相应的依赖。

## 1.6 退出虚拟环境
你可以通过运行以下命令退出虚拟环境：
```bash
exit
```