from ._class_define import *  # noqa: F403
from ._load_data import data
from ._utils import *
import logging
import numpy as np
import time

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
"""*********************** brief: 转换时间计算公式 **********************************************"""


def calcTransTime(prePitch, preRoll, curPitch, curRoll):
    """
    description : 根据角度计算转化时间
    :param arg1: 前一个窗口的角度
    :param arg2: 后一个窗口的角度
    :return: 转化时间
    """
    total_differ = abs(preRoll - curRoll) + abs(prePitch - curPitch)
    if total_differ >= 90:
        time = total_differ / 3 + 22
    elif 60 <= total_differ < 90:
        time = total_differ / 2.5 + 16
    elif 30 <= total_differ < 60:
        time = total_differ / 2 + 10
    elif 10 < total_differ < 30:
        time = total_differ / 1.5 + 5
    else:
        time = 35 / 3.0
    return time


"""******************* brief: 插入任务 ****************************"""


def insertWaitingTasks(satellite: Satellite, queue: List[Task]):
    """按给定队列按顺序尝试插入每个任务的可用 vtw"""
    notProcess: List[Vtw] = []
    vtws: list[Vtw] = []
    for task in queue:
        vtws.extend(task.vtw)
    for vtw in vtws:
        if not insertToSatellite(vtw):
            notProcess.append(vtw)


def insertWaitingTask(satellite: Satellite, task: Task):
    """
    description : 计算 new_One 的可行插入点位置
    :param arg1: 单个卫星satellite
    :param arg2: 单个任务task
    :return: 是否插入成功，成功返回true，否则false
    """
    notProcessed: List[Vtw] = []
    notProcessed = task.vtw
    for vtw in notProcessed:
        if insertToSatellite(vtw):
            return True
    return False


def try_insert_to_all_windows(self, task, temperature=1000.0, cooling_rate=0.9):
    """
    尝试将任务插入其所有可用时间窗，选择提升全局收益最大的位置
    并用模拟退火算法决定是否接受新解。
    """
    if task.isProcessed or not hasattr(task, "vtw") or not task.vtw:
        return False

    best_profit = -float("inf")
    best_vtw = None
    best_state = None

    # 1. 保存当前全局状态
    saved_state = self.save_state()
    old_profit = sum(sat.totalProfit for sat in self.satellites)
    inserted = False

    # 2. 遍历所有可用时间窗
    for vtw in task.vtw:
        if vtw.end < self.task_manager.current_time:
            continue
        self.restore_state(saved_state)  # 回退到初始状态
        task.isProcessed = False
        success = insertToSatellite(vtw)
        if success:
            new_profit = sum(sat.totalProfit for sat in self.satellites)
            if new_profit > best_profit:
                best_profit = new_profit
                best_vtw = vtw
                best_state = self.save_state()
            inserted = True

    # 3. 模拟退火判断是否接受新解
    if best_state and inserted:
        self.restore_state(best_state)
        delta = best_profit - old_profit
        if delta < 0:
            import math, random

            if random.random() >= math.exp(delta / (temperature + 1e-8)):
                self.restore_state(saved_state)
                return False
        return True
    else:
        self.restore_state(saved_state)
        return False


"""******************* brief: 插入时间窗 ****************************"""


def insertToSatellite(vtw: Vtw):
    """
    description : 传入 vtw 紧前安排策略到相应卫星
    :param arg1: 某个可见窗口 vtw
    :return: 是否调度成功
    """
    if vtw.Task.isProcessed:
        return False
    if vtw.Satellite.length == 0:
        vtw.otws = vtw.start
        vtw.otwe = vtw.otws + vtw.Task.processTime
        vtw.Satellite.add(vtw)
        return True
    position = getInsertPosition(vtw.Satellite, vtw)
    if position.num == 0:
        return False
    vtw.otws = position.otws[0]
    vtw.otwe = position.otwe[0]
    index = position.index[0]
    insertNewVtw(vtw.Satellite, vtw, index)
    return True


def removeFromSatellite(vtw: Vtw):
    """
    description : 删除某个已调度任务
    :param arg1: 可见时间窗口 vtw
    """
    vtw.Satellite.remove_by_vtw(vtw)


"""******************* brief: 获取插入点位置、插入一个合法结点 ****************************"""


def getInsertPosition(s: Satellite, new_One: Vtw) -> Position:
    """
    description : 计算 new_One 的可行插入点位置
    :param arg1: 已经调度列表
    :param arg2: 插入监测新vtw
    :return: Position 实例：插入点信息
    """
    updataTimeSlack(s.list)
    position = Position()
    for i in range(s.length):
        cur = s.list[i].vtw
        # 处理末尾情况
        if i == s.length - 1:
            if cur.otwe < new_One.end:
                ots = getEarliestTime(cur, new_One)
                if ots != -1:
                    ote = ots + new_One.Task.processTime
                    position.num += 1
                    position.otws.append(ots)
                    position.otwe.append(ote)
                    position.index.append(i + 1)
        if cur.otws > new_One.start:
            # 处理首位情况
            if i == 0:
                ots = new_One.start
            # 处理居中情况
            else:
                pre = s.list[i - 1].vtw
                if pre.otwe >= new_One.end:
                    break
                ots = getEarliestTime(pre, new_One)
            if ots != -1:
                ote = ots + new_One.Task.processTime
                new_One.otws = ots
                new_One.otwe = ote
                time = getEarliestTime(new_One, cur)
                if time == -1:
                    continue
                if cur.otws + s.list[i].TimeSlock < time:
                    continue
                position.num += 1
                position.otws.append(ots)
                position.otwe.append(ote)
                position.index.append(i)
    new_One.otws = -1
    new_One.otwe = -1
    return position


def insertNewVtw(s: Satellite, new_vtw: Vtw, index: int):
    """
    description : 将 new_vtw 插入到 SelectList 的第 index 位置处
    :param arg1: SelectList 某个规划方案列表
    :param arg2: new_vtw 新插入计划
    :param arg2: 新插入位置
    """
    s.add_index(new_vtw, index)
    pre = s.list[index].vtw
    for i in range(index + 1, s.length):
        cur = s.list[i].vtw
        new_s = getEarliestTime(pre, cur)
        if new_s == -1:
            print("ERROR: insertNewvtw mistake")
            break
        cur.otws = new_s
        cur.otwe = new_s + cur.Task.processTime
        pre = cur


"""**************** brief: 获取最晚开始时间和最早开始时间 ***************************"""


def getEarliestTime(pre: Vtw, cur: Vtw):
    """
    获取 cur vtw 相对于 pre 的最早可执行时间
    :param arg1: 前一个已经安排的 vtw
    :param arg2: 需要寻找最早开始时间的 vtw
    :return: cur vtw 相对于已经安排的 pre 的最早开始时间点
    """
    _, prePitch, preRoll = pre.get_angle(pre.otws)
    prev_otwe = pre.otwe

    return binary_search(prePitch, preRoll, prev_otwe, cur)


def binary_search(prePitch, preRoll, prev_otwe, cur: Vtw):
    """
    在 cur 时间窗口范围内使用二分查找，寻找最早可执行时间
    :param prePitch: 前一个窗口的俯仰角
    :param preRoll: 前一个窗口的滚转角
    :param prev_otwe: 前一个窗口的实际结束时间
    :param cur: 当前窗口
    :return: 最早可执行时间点，找不到则返回 -1
    """
    low = max(prev_otwe, cur.start)
    high = cur.end - cur.Task.processTime
    bestTime = -1

    while low <= high:
        mid = (low + high) // 2
        cur_angle = cur.get_angle(mid)

        # 该时间点姿态不可行，跳过
        if cur_angle == (-1, -1, -1):
            low = mid + 1
            continue

        _, curPitch, curRoll = cur_angle
        transTime = calcTransTime(prePitch, preRoll, curPitch, curRoll)
        diffTime = mid - prev_otwe

        # 若可行，记录并继续尝试找更早的
        if diffTime >= transTime:
            bestTime = mid
            high = mid - 1
        else:
            low = mid + 1

    return bestTime


def getShortestTransTime(task_i: Task, task_j: Task, consider_windows=True):
    """
    计算两个任务间的最短转换时间
    :param task_i: 任务 i
    :param task_j: 任务 j
    :param consider_windows: 是否考虑时间窗口约束
    :return: 最短转换时间，及对应的 VTW 对象
    """
    if task_i.vtwNum == 0 or task_j.vtwNum == 0:
        return float("inf"), None, None

    min_trans_time = float("inf")
    best_pair = (None, None)

    for vtw_i in task_i.vtw:
        for vtw_j in task_j.vtw:
            # 方案1：纯角度转换（不考虑时间窗口）
            if not consider_windows:
                # 使用中间时刻的角度
                time_i = max(
                    vtw_i.start,
                    vtw_i.middle
                    if hasattr(vtw_i, "middle")
                    else vtw_i.start + vtw_i.long // 2,
                )
                time_j = max(
                    vtw_j.start,
                    vtw_j.middle
                    if hasattr(vtw_j, "middle")
                    else vtw_j.start + vtw_j.long // 2,
                )

                angle_i = vtw_i.get_angle(time_i)
                angle_j = vtw_j.get_angle(time_j)

                if angle_i == (-1, -1, -1) or angle_j == (-1, -1, -1):
                    continue

                _, pitch_i, roll_i = angle_i
                _, pitch_j, roll_j = angle_j

                trans_time = calcTransTime(pitch_i, roll_i, pitch_j, roll_j)

                if trans_time < min_trans_time:
                    min_trans_time = trans_time
                    best_pair = (vtw_i, vtw_j)

            # 方案2：考虑时间窗口约束
            else:
                # 尝试所有可能的执行时间组合
                for offset_i in [
                    0,
                    vtw_i.long // 2,
                    vtw_i.long - 1,
                ]:  # 开始、中间、结束
                    for offset_j in [0, vtw_j.long // 2, vtw_j.long - 1]:
                        time_i = vtw_i.start + offset_i
                        time_j = vtw_j.start + offset_j

                        # 确保时间点在窗口内
                        if time_i >= vtw_i.end or time_j >= vtw_j.end:
                            continue

                        angle_i = vtw_i.get_angle(time_i)
                        angle_j = vtw_j.get_angle(time_j)

                        if angle_i == (-1, -1, -1) or angle_j == (-1, -1, -1):
                            continue

                        _, pitch_i, roll_i = angle_i
                        _, pitch_j, roll_j = angle_j

                        # 计算转换时间
                        trans_time = calcTransTime(pitch_i, roll_i, pitch_j, roll_j)

                        # 考虑时间间隔
                        time_gap = max(0, time_j - (time_i + task_i.processTime))
                        total_time = trans_time + time_gap

                        if total_time < min_trans_time:
                            min_trans_time = total_time
                            best_pair = (vtw_i, vtw_j)

    if min_trans_time == float("inf"):
        return float("inf"), None, None

    return min_trans_time, best_pair[0], best_pair[1]


def getLatestTime(pre: Vtw, cur: Vtw):
    """
    description : 前一个 VTW 的 OTW 已经固定的情况下，获取当前任务的最晚开始时间点：二分法查找
    :param arg1: 前一个已经安排的 vtw
    :param arg2: 需要寻找最晚开始时间的 vtw
    :return: cur vtw 相对于已经安排的 pre 的最晚开始时间点
    """
    _, prePitch, preRoll = pre.get_angle(pre.otws)
    if pre.otws < cur.end:
        high = pre.otws - cur.Task.processTime
    else:
        high = cur.end - cur.Task.processTime
    low = cur.start
    bestTime = -1
    while low <= high:
        mid = (low + high) // 2
        cur_angle = cur.get_angle(mid)
        if cur_angle == (-1, -1, -1):
            low = mid + 1
            continue
        _, curPitch, curRoll = cur_angle
        transTime = calcTransTime(prePitch, preRoll, curPitch, curRoll)
        diffTime = pre.otws - mid - cur.Task.processTime
        if diffTime >= transTime:
            bestTime = mid
            low = mid + 1
        else:
            high = mid - 1
    return bestTime


"""*********************** brief: 更新时间松弛 ***********************************"""


# 临时移动策略
def tempMove(vtw: Vtw, slack):
    vtw.otws += slack
    vtw.otwe += slack


def updataTimeSlack(select: List[SelectedVtw]):
    """
    description : 更新 select 中每个 SelectedVtw 的 TimeSlock
    :param arg1: 已经调度的 SelectedVtw 列表
    """
    if not select:
        logging.debug("selectvtw List is None (调度列表为空)")
        return
    pre = select[-1]
    pre.TimeSlock = (pre.vtw.end - pre.processTime) - pre.vtw.otws
    for cur in reversed(select[:-1]):
        tempMove(pre.vtw, pre.TimeSlock)
        latest_time = getLatestTime(pre.vtw, cur.vtw)
        if latest_time == -1:
            tempMove(pre.vtw, -pre.TimeSlock)
            # print("WARNING: Time Slack is 0")
            continue
        cur.TimeSlock = latest_time - cur.vtw.otws
        tempMove(pre.vtw, -pre.TimeSlock)
        pre = cur


def tempMoveVtw(vtw: Vtw, slack) -> Vtw:
    """深拷贝策略"""
    new_vtw = copy.deepcopy(vtw)
    new_vtw.otws += slack
    new_vtw.otwe += slack
    return new_vtw


def updataTimeSlack_v1(select: List[SelectedVtw]):
    """
    description : 更新时间松弛（暂时只考虑延迟时间松弛）(深拷贝)
    :param arg1: 规划方案调度列表集合
    """
    if not select:
        return
    pre = select[-1]
    pre.TimeSlock = (pre.vtw.end - pre.processTime) - pre.vtw.otws
    temp = tempMoveVtw(pre.vtw, pre.TimeSlock)
    for cur in reversed(select[:-1]):
        latest_time = getLatestTime(temp, cur.vtw)
        if latest_time == -1:
            # print("WARNING: Time Slack is 0")
            continue
        cur.TimeSlock = latest_time - cur.vtw.otws
        temp = tempMoveVtw(cur.vtw, cur.TimeSlock)


"""*********************** brief: 冲突检测 ***********************************"""


def isConfict(vtw1: Vtw, vtw2: Vtw):
    """
    description : 传入两个已经调度的窗口，判断是否冲突
    :return: 返回是否合法
    """
    if vtw1.otws == -1 or vtw2.otws == -1:
        print("ERROR: vtw is not value")
        return False
    confict = False
    if vtw1.otws <= vtw2.otwe and vtw2.otws <= vtw1.otwe:
        confict = True
    if vtw1.otws > vtw2.otws:
        temp = vtw1
        vtw1 = vtw2
        vtw2 = temp
    _, prePitch, perRoll = vtw1.get_angle(vtw1.otws)
    _, curPitch, curRoll = vtw2.get_angle(vtw2.otws)
    trans = calcTransTime(prePitch, perRoll, curPitch, curRoll)
    diff = vtw2.otws - vtw1.otwe
    if trans > diff:
        confict = True
    return confict


"""******************* brief: 贪婪算法获取初始解 ********************************************"""


def InitSolution(vtws: List[Vtw], mode="greedy"):
    """
    description : 遍历 vtws 逐一紧前安排任务
    :param arg1: vtws 列表
    :param arg2: 窗口排序模式
    :return: 返回没有调度成功的任务实例列表
    """
    waitTasks: List[Task] = []
    finished = 0
    if mode == "null":
        pass
    elif mode == "greedy":
        vtws = sorted(vtws, key=lambda vtw: vtw.start)
    elif mode == "random":
        random.shuffle(vtws)
    for cur in vtws:
        if cur.Task.isProcessed:
            continue
        if cur.Satellite.length == 0:
            cur.otws = cur.start
            cur.otwe = cur.otws + cur.Task.processTime
            finished += 1
            cur.Satellite.add(cur)
            continue
        pre = cur.Satellite.getLastOne()
        time = getEarliestTime(pre, cur)
        if time != -1:
            cur.otws = time
            cur.otwe = time + cur.Task.processTime
            finished += 1
            cur.Satellite.add(cur)
    for vtw in vtws:
        if not vtw.Task.isProcessed:
            if not any(task == vtw.Task for task in waitTasks):
                waitTasks.append(vtw.Task)
    print(f"init: finished tasks {finished}")
    print(f"init: waiting  tasks {len(waitTasks)}\n")
    return waitTasks


"""******************** brief: 可见窗口冲突统计函数 ********************************"""


def vtw_conflicts_bisect(vtw: Vtw, array: list[Vtw]):
    """
    description : 二分法查找 vtw 与 list[vtw] 冲突情况
    :param arg1: 冲突查询 vtw
    :param arg2: 按 start 排序后的 vtw 集合
    :return: 返回与 vtw 冲突的 vtw 集合
    """
    conflicting_vtws = []
    start_times = [o.start for o in array]
    idx = bisect.bisect_left(start_times, vtw.end)
    for i in range(idx):
        o = array[i]
        if o.end > vtw.start:
            conflicting_vtws.append(o)
    return conflicting_vtws


def vtw_conflicts_traverse(vtw: Vtw, array: list[Vtw]):
    """
    description : 遍历法查询 vtw 冲突情况
    :param arg1: 冲突查询 vtw
    :param arg2: 随意 vtw 检测列表
    :return: 返回与 vtw 冲突的 vtw 集合
    """
    conflicting_vtws = []
    for o in array:
        if o.start < vtw.end and vtw.start < o.end:
            conflicting_vtws.append(o)
    return conflicting_vtws


"""*********************** brief: 过渡时间工具函数 ***********************************"""


def getTransAndDiff(vtw1: Vtw, vtw2: Vtw):
    """
    description : 打印两个已经调度窗口的转化时间和间隔时间
    :return: transTime, diffTime
    """
    if vtw1.otws == -1 or vtw2.otws == -1:
        print("ERROR: vtw is not value")
        return -1, -1
    confict = False
    if vtw1.otws <= vtw2.otwe and vtw2.otws <= vtw1.otwe:
        confict = True
    if vtw1.otws > vtw2.otws:
        temp = vtw1
        vtw1 = vtw2
        vtw2 = temp
    _, prePitch, perRoll = vtw1.get_angle(vtw1.otws)
    _, curPitch, curRoll = vtw2.get_angle(vtw2.otws)
    trans = calcTransTime(prePitch, perRoll, curPitch, curRoll)
    diff = vtw2.otws - vtw1.otwe
    if trans > diff:
        confict = True
    if confict:
        print("ERROR: 重叠或不满足转化要求")
    else:
        print(f"transTime:{trans}s  diffTime: {diff}s")
        return trans, diff
    return -1, -1


"""******************* brief: selectList 移动函数 ********************************"""


def moveOTW(vtw: Vtw, seconds: int):
    vtw.otws += seconds
    vtw.otwe += seconds
    if vtw.otwe > vtw.end or vtw.otws < vtw.start:
        vtw.otws -= seconds
        vtw.otwe -= seconds
        return False
    return True


def moveSelectList(list: List[SelectedVtw], index: int, moveSeconds):
    if moveSeconds > list[index].TimeSlock:
        print("moveSeconds out of range")
        return False
    moveOTW(list[index].vtw, moveSeconds)
    pre = list[index].vtw
    for select in list[index + 1 :]:
        cur = select.vtw
        time = getEarliestTime(pre, cur)
        if time == -1:
            print("ERROR: moveSelectList")
            return False
        if time == cur.otws:
            break
        else:
            cur.otws = time
            cur.otwe = time + cur.Task.processTime
        pre = cur


def moveSelectList_V1(list: List[SelectedVtw], select: SelectedVtw, moveSeconds: int):
    try:
        index = list.index(select)
    except ValueError:
        print("Selectvtw not found in list.")
        return False
    if moveSeconds > list[index].TimeSlock:
        print("moveSeconds out of range")
        return False
    moveOTW(list[index].vtw, moveSeconds)
    pre = list[index].vtw
    for select in list[index + 1 :]:
        cur = select.vtw
        time = getEarliestTime(pre, cur)
        if time == -1:
            print("ERROR: moveSelectList")
            return False
        if time == cur.otws:
            break
        else:
            cur.otws = time
            cur.otwe = time + cur.Task.processTime
        pre = cur


"""******************* brief: 获取调度简要信息 ********************************"""


def calculate_profit_matrix(tasks: List[Task], task_ids: List[int]) -> List[float]:
    """
    Calculate a profit matrix for the tasks.
    Each element at index [i] represents the profit of task i.

    :param tasks: A list of tasks and id of unfinished tasks.
    :return: task 的收益矩阵，元素和序号（ID）对应.
    """
    profit_matrix = []

    # Calculate profit for each task
    for id in task_ids:
        profit_matrix.append(tasks[id].profit)

    return profit_matrix


def build_task_distance_matrix(tasks: List[Task], mode="angle_only"):
    """
    构建改进版距离矩阵
    :param tasks: 任务列表
    :return: 距离矩阵
    Args:
        mode:
            'angle_only' - 只考虑角度转换（类似地理距离）
            'time_aware' - 考虑时间窗口约束
            'hybrid' - 混合模式
    """
    n = len(tasks)
    dist_matrix = np.full((n, n), float("inf"))

    for i in range(n):
        dist_matrix[i][i] = 0

        for j in range(n):
            if i == j:
                continue

            if mode == "angle_only":
                consider_windows = False
            elif mode == "time_aware":
                consider_windows = True
            else:  # hybrid
                # 首先尝试纯角度，如果失败则尝试时间感知
                trans_time_angle, _, _ = getShortestTransTime(tasks[i], tasks[j], False)
                if trans_time_angle == float("inf"):
                    trans_time, _, _ = getShortestTransTime(tasks[i], tasks[j], True)
                else:
                    trans_time = trans_time_angle

            if mode != "hybrid":
                trans_time, _, _ = getShortestTransTime(
                    tasks[i], tasks[j], consider_windows
                )

            dist_matrix[i][j] = trans_time

    return dist_matrix


def analyze_distance_matrix_corrected(dist_matrix):
    """修正版分析函数
    :param dist_matrix: 距离矩阵
    :return: 有效值掩码
    """
    n = len(dist_matrix)
    
    print("=== 距离矩阵分析（修正版）===")
    print(f"矩阵大小: {n} × {n}")
    
    # 创建掩码
    mask_inf = np.isinf(dist_matrix)
    mask_diag = np.eye(n, dtype=bool)
    mask_nan = np.isnan(dist_matrix)
    
    # 统计各类值
    total_elements = n * n
    inf_count = np.sum(mask_inf)
    diag_count = n  # 对角线有n个元素
    nan_count = np.sum(mask_nan)
    
    print(f"总元素数: {total_elements}")
    print(f"INF值数量: {inf_count} ({inf_count/total_elements*100:.2f}%)")
    print(f"对角线零值: {diag_count} ({diag_count/total_elements*100:.2f}%)")
    print(f"NaN值数量: {nan_count} ({nan_count/total_elements*100:.2f}%)")
    
    # 有效值（非INF、非NaN、非对角线）
    mask_valid = ~mask_inf & ~mask_nan & ~mask_diag
    valid_count = np.sum(mask_valid)
    valid_values = dist_matrix[mask_valid]
    
    print(f"有效值数量: {valid_count} ({valid_count/total_elements*100:.2f}%)")
    
    if valid_count > 0:
        print(f"\n有效转换时间统计:")
        print(f"  最小值: {np.min(valid_values):.2f}秒")
        print(f"  最大值: {np.max(valid_values):.2f}秒")
        print(f"  平均值: {np.mean(valid_values):.2f}秒")
        print(f"  中位数: {np.median(valid_values):.2f}秒")
        print(f"  标准差: {np.std(valid_values):.2f}秒")
        
        # 分布统计
        bins = [0, 10, 30, 60, 120, 300, 600, 1800, 3600, float('inf')]
        bin_labels = ['<10s', '10-30s', '30-60s', '1-2min', '2-5min', '5-10min', '10-30min', '30-60min', '>60min']
        
        hist, _ = np.histogram(valid_values, bins=bins)
        print(f"\n转换时间分布:")
        for i, (count, label) in enumerate(zip(hist, bin_labels)):
            percentage = count / valid_count * 100
            print(f"  {label}: {count}个 ({percentage:.1f}%)")
    else:
        print("警告: 没有找到任何有效值！")
        print("可能原因:")
        print("  1. 所有任务对都无法转换")
        print("  2. getShortestTransTime函数总是返回inf")
        print("  3. 数据加载有问题")
    
    return mask_valid


"""*********************** brief: 测试 ***********************************"""
if __name__ == "__main__":
    plot.showVtwTest()
    info, tasks, vtws, satellites = data.getAllSortData(sort=True)
    # 任务安排测试
    # print("Arrange with VTWS (PS)")
    # vtws = sorted(vtws, key=lambda Task : Task.Task.profit)
    # for vtw in vtws:
    #     insertToSatellite(vtw)

    # for task in tasks:
    #     insertWaitingTask(satellites[0], task)

    # insertWaitingTask(satellites[0], tasks[0])

    # insertWaitingTasks(satellites[0], tasks)
    # data.finishedRate2()

    # 距离矩阵测试
    print("模式1: 纯角度转换")
    dist_angle = build_task_distance_matrix(tasks, mode='angle_only')
    analyze_distance_matrix_corrected(dist_angle)
    
    print("\n模式2: 时间感知")
    dist_time = build_task_distance_matrix(tasks, mode='time_aware')
    analyze_distance_matrix_corrected(dist_time)

