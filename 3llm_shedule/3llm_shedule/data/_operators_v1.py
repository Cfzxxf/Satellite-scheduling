from ._class_define import *
from ._trans_time import getInsertPosition, insertNewOrder
import random


class OperatorManager:
    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.remove_operators = [
            self.remove_task_random,
            self.remove_task_low_profit,
            self.remove_task_widest_vtw,
            self.remove_task_non_urgent,
        ]
        self.insert_operators = [
            self.insert_task_random,
            self.insert_task_high_profit,
            self.insert_task_urgent,
            self.insert_task_narrowest_vtw,
        ]

    def _as_task(self, item):
        """无论传进来的是 SelectedVtw 还是 Task，都返回真正的 Task。"""
        try:
            vtw = getattr(item, "vtw", None)
            if vtw is not None and hasattr(vtw, "Task"):
                return vtw.Task
        except Exception:
            pass
        return item

    def _remove_and_enqueue(self, selected):
        for s in selected:
            self.scheduler.satellite.remove_by_select(s)
            self.scheduler.wait_tasks.append(s.vtw.Task)

    def _insert_waiting_tasks(self, queue):
        for task in queue[:]:
            if task.isProcessed:
                continue
            for vtw in task.vtw:
                if vtw.Task.isProcessed:
                    continue
                position = getInsertPosition(self.scheduler.satellite, vtw)
                if position.num == 0:
                    continue
                vtw.otws, vtw.otwe = position.otws[0], position.otwe[0]
                if insertNewOrder(self.scheduler.satellite, vtw, position.index[0]):
                    queue.remove(task)
                    break

    # ----------------- 局部搜索算子（已有） -----------------
    def remove_task_random(self, num=5):
        if self.scheduler.satellite.length == 0:
            return
        tasks = random.sample(
            self.scheduler.satellite.list, min(num, self.scheduler.satellite.length)
        )
        self._remove_and_enqueue(tasks)

    def remove_task_widest_vtw(self, num=5):
        if self.scheduler.satellite.length == 0:
            return
        tasks = sorted(
            self.scheduler.satellite.list,
            key=lambda sel: getattr(self._as_task(sel), "processTime", float("inf")),
            reverse=True,
        )[:num]
        self._remove_and_enqueue(tasks)

    def remove_task_non_urgent(self, num=5):
        if self.scheduler.satellite.length == 0:
            return
        tasks = sorted(
            self.scheduler.satellite.list,
            key=lambda sel: getattr(
                self._as_task(sel),
                "urgency",
                getattr(self._as_task(sel), "TimeSlock", float("inf")),
            ),
            reverse=False,
        )[:num]
        self._remove_and_enqueue(tasks)

    def remove_task_low_profit(self, num=5):
        if self.scheduler.satellite.length == 0:
            return
        tasks = sorted(
            self.scheduler.satellite.list,
            key=lambda sel: getattr(self._as_task(sel), "profit", 0),
        )[:num]
        self._remove_and_enqueue(tasks)

    def insert_task_random(self):
        random.shuffle(self.scheduler.wait_tasks)
        self._insert_waiting_tasks(self.scheduler.wait_tasks)

    def insert_task_narrowest_vtw(self):
        self.scheduler.wait_tasks.sort(key=lambda x: x.processTime, reverse=False)
        self._insert_waiting_tasks(self.scheduler.wait_tasks)

    def insert_task_urgent(self):
        def get_min_vtw_duration(task):
            if hasattr(task, "vtw") and task.vtw:
                return min(vtw.end - vtw.start for vtw in task.vtw)
            return float("inf")

        self.scheduler.wait_tasks.sort(key=get_min_vtw_duration, reverse=False)
        self._insert_waiting_tasks(self.scheduler.wait_tasks)

    def insert_task_high_profit(self):
        self.scheduler.wait_tasks.sort(key=lambda x: x.profit, reverse=True)
        self._insert_waiting_tasks(self.scheduler.wait_tasks)

    # ----------------- 新增：全局搜索算子 -----------------

    # ----------------- 局部插入操作（新增） -----------------
    def local_insert_try(self, task, max_remove=2):
        """最小扰动地为 task 寻找插入机会：
        1) 直接尝试插入
        2) 失败→逐步移除少量低优先级任务（非紧急/低收益），再尝试插入
        成功返回 True；否则 False。
        """
        if getattr(task, "isProcessed", False):
            return True
        # 先尝试直接插入
        for vtw in getattr(task, "vtw", []):
            if getattr(vtw.Task, "isProcessed", False):
                continue
            position = getInsertPosition(self.scheduler.satellite, vtw)
            if position.num > 0:
                vtw.otws, vtw.otwe = position.otws[0], position.otwe[0]
                if insertNewOrder(self.scheduler.satellite, vtw, position.index[0]):
                    return True
        # 逐步小规模清理并重试
        removal_strategies = [
            self.remove_task_non_urgent,
            self.remove_task_low_profit,
            self.remove_task_random,
        ]
        backup_wait = list(self.scheduler.wait_tasks)
        for k in range(1, max_remove + 1):
            for strat in removal_strategies:
                # 记录当前调度以便必要时回滚（由上层做更完整的快照；这里尽量轻量）
                try:
                    strat(num=k)
                    for vtw in getattr(task, "vtw", []):
                        if getattr(vtw.Task, "isProcessed", False):
                            continue
                        position = getInsertPosition(self.scheduler.satellite, vtw)
                        if position.num > 0:
                            vtw.otws, vtw.otwe = position.otws[0], position.otwe[0]
                            if insertNewOrder(
                                self.scheduler.satellite, vtw, position.index[0]
                            ):
                                return True
                except Exception:
                    pass
            # 尝试失败后，恢复等待队列顺序，避免放大扰动
            self.scheduler.wait_tasks = list(backup_wait)
        return False

    # ----------------- 简单“全局”修复算子（新增，可被RL调用） -----------------
    def global_destroy_repair(self, remove_num=6):
        """先破坏后修复：移除一批非关键任务，再按高收益与紧急度插回。"""
        if self.scheduler.satellite.length == 0:
            return
        # 破坏：混合移除
        half = max(1, remove_num // 2)
        self.remove_task_low_profit(num=half)
        self.remove_task_non_urgent(num=remove_num - half)
        # 修复：重要/紧急/高收益优先
        queue = sorted(
            self.scheduler.wait_tasks,
            key=lambda t: (
                -(getattr(t, "importance", 0)),
                -(getattr(t, "urgency", 0)),
                getattr(t, "profit", 0),
            ),
            reverse=False,
        )
        self._insert_waiting_tasks(queue)
