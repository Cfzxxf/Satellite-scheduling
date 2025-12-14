from ._load_data import data
from ._utils import *
from ._trans_time import *

import sys
import types
import warnings
import numpy as np
from .prompts import GetPrompts


class ScheduleGreedy:
    """
    封装调度问题的贪心执行与评估。
    - greedy(eva): 使用用户的启发式算法进行一次调度，返回当前实例的收益率
    - evaluate(code_string): 动态执行用户代码并评估其表现，返回收益率作为适应度
    """

    def __init__(self) -> None:
        # 持有数据对象，方便在多个方法里使用
        self.data = data
        self.ndelay = 1
        self.running_time = 10
        self.debug_mode = False

        self.prompts = GetPrompts()

    def greedy(self, eva):
        """
        从起点开始，先强行插入一个可调度任务作为"种子"，
        之后每一步都用 eva.select_next_task 从剩余任务里选下一个最优任务，
        直到当前卫星再也装不下任何任务为止。
        最终返回总收益率。
        """
        # 1. 拿数据 & 全员复位
        self.data.reset()
        info, tasks, vtws, satellites = self.data.getAllSortData(sort=True)

        # 初始化状态
        scheduled_tasks = []  # 存储已安排任务的索引
        unprocessed_tasks = list(range(len(tasks)))  # 存储未处理任务的索引

        # 选择一个卫星
        satellite = satellites[0]

        # 构建距离矩阵和利润矩阵
        distance_matrix = build_task_distance_matrix(tasks)
        profit_matrix = [task.profit for task in tasks]  # 构建完整的利润矩阵

        # 2. 先尝试安排第一个任务作为"种子"
        seed_selected = False
        for task_index in unprocessed_tasks[:]:  # 复制列表以便删除
            task = tasks[task_index]
            if insertWaitingTask(satellite, task):
                scheduled_tasks.append(task_index)
                unprocessed_tasks.remove(task_index)
                seed_selected = True
                if self.debug_mode:
                    print(f"种子任务安排成功: 任务索引 {task_index}")
                break

        if not seed_selected:
            print("警告: 无法安排任何任务作为种子")
            return self.data.finishedRate2()

        # ---------- 主循环：用评估函数不断选下一个任务 ----------
        iteration = 0
        max_iterations = len(tasks) * 2  # 防止无限循环
        
        while len(unprocessed_tasks) > 0 and iteration < max_iterations:
            iteration += 1
            
            # 如果没有已安排的任务，随机选一个作为起点
            if not scheduled_tasks:
                # 选择第一个可安排的任务
                for task_id in unprocessed_tasks[:]:
                    task = tasks[task_id]
                    if insertWaitingTask(satellite, task):
                        scheduled_tasks.append(task_id)
                        unprocessed_tasks.remove(task_id)
                        if self.debug_mode:
                            print(f"初始任务安排成功: 任务 {task_id}")
                        break
                continue
            
            current_task = scheduled_tasks[-1]
            
            # 使用启发式选择下一个任务
            next_task_id = eva.select_next_task(
                current_task=current_task,
                next_task=None,
                unprocessed_task_ids=unprocessed_tasks,
                distance_matrix=distance_matrix,
                profit_matrix=profit_matrix,
            )
            
            # 如果启发式返回 None，使用备选策略
            if next_task_id is None:
                # print("启发式返回 None，使用备选策略")
                # 备选策略1：选择收益最高的任务
                next_task_id = max(unprocessed_tasks, 
                                key=lambda x: profit_matrix[x])
                
                # 或者备选策略2：选择转换时间最短的任务
                # candidates = []
                # for tid in unprocessed_tasks:
                #     cost = distance_matrix[current_task][tid]
                #     if not np.isinf(cost):
                #         candidates.append((tid, cost))
                # if candidates:
                #     next_task_id = min(candidates, key=lambda x: x[1])[0]
            
            # 尝试安排任务
            if next_task_id is not None and next_task_id in unprocessed_tasks:
                next_task = tasks[next_task_id]
                if insertWaitingTask(satellite, next_task):
                    scheduled_tasks.append(next_task_id)
                    if self.debug_mode:
                        print(f"安排任务成功: 任务索引 {next_task_id}")
                
                # 从待处理列表中移除（无论成功与否）
                unprocessed_tasks.remove(next_task_id)
            else:
                if self.debug_mode:
                    print(f"无效的任务ID或任务已处理: {next_task_id}")
                break
    
        return self.data.finishedRate2()

    def evaluate(self, code_string):
        """
        动态执行并评估用户提供的启发式算法代码：

        - 在独立的模块命名空间 heuristic_module 中执行 code_string，避免污染全局环境；
        - 执行成功后，调用 self.greedy(heuristic_module)；
        - greedy 内部会使用 heuristic_module 中的启发式函数（如 sort_vtws / select_next_node）；
        - 返回 greedy 的结果（当前实例的收益率 / 路径成本等）作为适应度；
        - 若执行过程中出现任意异常，返回 None，保证评估过程的鲁棒性。
        """
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")

                # 1. 创建一个新的“空模块”，作为用户代码的命名空间
                heuristic_module = types.ModuleType("heuristic_module")

                # 2. 在该模块的命名空间中执行用户提供的代码字符串
                exec(code_string, heuristic_module.__dict__)

                # 3.（可选）注册到 sys.modules，方便调试 / import
                sys.modules[heuristic_module.__name__] = heuristic_module

                # 4. 使用这个模块中的启发式函数，跑一遍贪心算法
                fitness = self.greedy(heuristic_module)
                return fitness

        except Exception:
            # 任何错误都返回 None，表示评估失败
            return None


# ======================= 示例使用 ==============================
if __name__ == "__main__":
    # info, tasks, vtws, satellites = data.getAllSortData(sort=True)
    # insertWaitingTasks(satellites[0], tasks)
    # data.finishedRate2()

    print("-- 开始加载数据 --")
    scheduler = ScheduleGreedy()

    # 示例：一个非常简单的启发式算法代码字符串
    eva = """

"""

    fitness = scheduler.evaluate(eva)
    print("示例启发式算法的收益率 / 适应度：", fitness)
