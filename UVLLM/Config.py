import os

# 项目根目录路径
PROJECT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..")

TIMEOUT = 2

REPAIR_TIME = 7200
# 基准测试目录直接指向ErrorSet
BENCHMARKS = os.path.join(PROJECT_PATH, "ErrorSet")
WORK_DIR = os.path.join(PROJECT_PATH, "workdir")
PATCH_DIR = os.path.join(PROJECT_PATH, "patch")

LOG_PATH = os.path.join(PROJECT_PATH, "logs/UVLLM.log")
