"""*************************************************************************************
@note    : 工具类集合
@note    : plot 绘制 VTW、OTW 可视化工具
@note    : log 打印调试信息到文件
@note    : lots of tools functions
@time     : 2025/03/20 09:11:03
*************************************************************************************"""

import matplotlib.pyplot as plt
from matplotlib import lines
import matplotlib.patches as patches
from ._class_define import *
import json
import os

# -*- coding: utf-8 -*-
import os, csv


def csv_put(path="./cvs_printf.csv", allow_new_columns=False, **cols):
    """
    像 print 一样使用：csv_put("log.csv", ratio=profit/total, gen=10)
    - 第一次调用会写入表头（列名就是你传的参数名）
    - 后续调用自动在文件末尾追加一行
    - 如果出现新列名：
        allow_new_columns=False(默认)：报错，提醒你保持列一致
        allow_new_columns=True：自动扩展表头并重写文件（简单安全）
    """
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    row = {k: cols[k] for k in cols}

    file_exists = os.path.exists(path) and os.path.getsize(path) > 0
    if not file_exists:
        # 新文件：写表头+第一行
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(row.keys()))
            w.writeheader()
            w.writerow(row)
        return

    # 已存在：读取现有表头
    with open(path, "r", newline="", encoding="utf-8-sig") as fr:
        reader = csv.reader(fr)
        try:
            header = next(reader)
        except StopIteration:
            header = []

    header_set = set(header)
    new_cols = [k for k in row if k not in header_set]

    if new_cols and not allow_new_columns:
        raise ValueError(
            f"CSV 现有列：{header}，本次新列：{new_cols}。"
            "如需自动扩展表头，请传 allow_new_columns=True。"
        )

    if new_cols and allow_new_columns:
        # 读入旧数据
        with open(path, "r", newline="", encoding="utf-8-sig") as fr:
            dr = csv.DictReader(fr)
            rows = list(dr)
        # 扩展表头并重写
        header += [c for c in new_cols if c not in header]
        with open(path, "w", newline="", encoding="utf-8-sig") as fw:
            dw = csv.DictWriter(fw, fieldnames=header)
            dw.writeheader()
            for r in rows:
                dw.writerow(r)
            # 写入当前新行（补齐缺失列为空字符串）
            dw.writerow({k: row.get(k, "") for k in header})
        return

    # 无新列：直接追加
    with open(path, "a", newline="", encoding="utf-8-sig") as fa:
        dw = csv.DictWriter(fa, fieldnames=header)
        dw.writerow({k: row.get(k, "") for k in header})


def csv_clear(
    path="./view/data.csv", keep_header: bool = False, encoding: str = "utf-8-sig"
) -> None:
    """
    清空指定 CSV 文件。
    - keep_header=False：整个文件清空；
    - keep_header=True：保留首行表头，仅清除数据行（若没有表头，则变成空文件）。

    参数
    ----
    path : CSV 文件路径
    keep_header : 是否保留表头行
    encoding : 文件编码（默认 utf-8-sig，适合与 Excel 互通）
    """
    # 文件不存在：直接创建空文件后返回
    if not os.path.exists(path):
        with open(path, "w", encoding=encoding, newline="") as _:
            pass
        return

    if not keep_header:
        # 直接截断为 0 字节
        with open(path, "w", encoding=encoding, newline="") as _:
            pass
        return

    # 保留表头：读出第一行作为 header
    header = None
    with open(path, "r", encoding=encoding, newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            header = None

    # 重写文件：写回表头（如果存在）
    with open(path, "w", encoding=encoding, newline="") as f:
        if header:
            writer = csv.writer(f)
            writer.writerow(header)


"""*********************** brief: 打印调试工具函数 ***********************************"""
import logging as log

log.basicConfig(filename="./log/debug.log", level=log.INFO, filemode="w")

"""brief: log打印任务数据"""


def logTasks(tasks: Task):
    for task in tasks:
        log.info(task)


"""brief: log打印任务数据"""


def logVtws(vtws: Vtw):
    for vtw in vtws:
        log.info(vtw)


"""brief: 打印任务集合数据"""


def printTasks(tasks: List[Task]):
    for task in tasks:
        print(task)


"""brief: 打印窗口集合数据"""


def printVtws(vtws: List[Vtw]):
    for vtw in vtws:
        print(vtw)


"""brief: 打印卫星调度情况集合"""


def printSatellite(satellite: Satellite):
    print(satellite)
    for info in satellite.list:
        print(info)
    print("\n")


"""brief: 打印卫星调度情况集合"""


def printSatellites(satellites: List[Satellite]):
    for s in satellites:
        printSatellite(s)


"""brief: 对OTW按otws升序排序"""


def sortOtws(list: List[Vtw]):
    list = sorted(list, key=lambda Order: Order.otws)


def format_time(seconds):
    """格式化时间显示"""
    days = seconds // (24 * 3600)
    hours = (seconds % (24 * 3600)) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{days}天 {hours:02d}:{minutes:02d}:{secs:02d}"


"""*********************** brief: 数据处理存储工具函数 ***********************************"""


def transDataTime(intTime, date="2013-04-20"):
    """
    description : 将时间转化成易懂形式
    :param arg1: intTime：一天的相对s数
    :param arg2: data：年月日前缀
    :return: 例如："2013-04-20 12:00:00"
    """
    hours = int(intTime // 3600)
    minutes = int((intTime % 3600) // 60)
    seconds = intTime % 60
    time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
    strDataTime = f"{date} {time_str}"
    return strDataTime


def writeOrderToJson(orderList: List[Vtw], jsonPath="./log/plan.json"):
    """
    description : 按指定格式将 orderList 写入json文件
    :param arg1: Order List 集合数据
    :param arg2: json 文件地址
    """
    orders_data = {}
    for order in orderList:
        window_start = transDataTime(order.start)
        start_time = transDataTime(order.otws)
        end_time = transDataTime(order.otwe)
        window_end = transDataTime(order.end)
        orders_data[str(order.Task.ID)] = {
            "satellite": f"Satellite_{order.satellite}",
            "window_start": window_start,
            "start_time": start_time,
            "end_time": end_time,
            "window_end": window_end,
            "profit": order.Task.profit,
        }
    with open(jsonPath, "w") as json_file:
        json.dump(orders_data, json_file, indent=4)


"""*********************** brief: 可视化绘制工具 ***********************************"""


class PLOT:
    """
    description : 绘制 VTW 和 OTW 的工具类
    :param arg1: 属性配置、单个、多个 VTW 绘制
    """

    def __init__(self):
        # 配置参数
        self.title = "AEOSSP VTW & OTW"
        self.grid = False
        self.vtwTest = True
        self.otwText = False
        self.callsNum = 0
        self.vtwStyle = "square"
        # 辅助绘制的变量
        self.y_positions = []
        self.current_y = 0
        self.min_start = float("inf")
        self.max_end = float("-inf")

    def reset(self):
        self.y_positions = []
        self.current_y = 0
        self.min_start = float("inf")
        self.max_end = float("-inf")

    def add_annotations(self):
        plt.title(self.title)
        plt.grid(self.grid)
        self.ax.text(
            1.05,
            0.96,
            "VTW",
            color="black",
            fontsize=8,
            ha="center",
            bbox=dict(facecolor="white", edgecolor="black"),
            transform=self.ax.transAxes,
        )
        self.ax.text(
            1.05,
            0.9,
            "OTW",
            color="black",
            fontsize=8,
            ha="center",
            bbox=dict(facecolor="lightblue", edgecolor="black"),
            transform=self.ax.transAxes,
        )
        self.ax.set_xlabel("Satellite_Timeline/s")
        self.ax.set_ylabel("Task_VTW/ID")

    def style(self, index=0):
        if index == 1:
            self.vtwStyle = "line"
            self.vtwTest = True
            self.otwText = False
        elif index == 2:
            pass
        else:
            self.vtwTest = True
            self.otwText = True
            self.vtwStyle = "square"

    def show(self):
        self.add_annotations()
        plt.show()

    def showVtwTest(self, show=True):
        self.vtwTest = True

    def showOtwTest(self, show=True):
        self.otwTextTest = True

    def single_order(self, order: Vtw, line=0):
        """
        description : 绘制单个 Order
        :param arg1: order, Order 数据
        :param arg2: line：0，根据任务 ID 自动 y 轴，1-n 指定 y 轴显示
        """
        start, end, otws, otwe = order.start, order.end, order.otws, order.otwe
        self.min_start = min(self.min_start, start)
        self.max_end = max(self.max_end, end)
        if order.Task.ID not in self.y_positions:
            self.y_positions.append(order.Task.ID)
        index = self.y_positions.index(order.Task.ID)
        current_y = 0.5 * index
        if line != 0:
            current_y = 0.5 * line
        # VTW
        if self.vtwStyle == "square":
            self.ax.add_patch(
                patches.Rectangle(
                    (start, current_y),
                    end - start,
                    0.4,
                    edgecolor="black",
                    facecolor="white",
                    lw=1,
                )
            )
        elif self.vtwStyle == "line":
            self.ax.add_line(
                lines.Line2D(
                    [start, end],
                    [current_y + 0.25, current_y + 0.25],
                    color="black",
                    linewidth=3,
                )
            )
        if self.vtwTest:
            self.ax.text(
                (start + end) / 2,
                current_y + 0.15,
                f"t{order.Task.ID}",
                ha="center",
                fontsize=10,
                color="black",
            )
        # OTW
        if otws != -1 and otwe != -1:
            self.ax.add_patch(
                patches.Rectangle(
                    (otws, current_y),
                    otwe - otws,
                    0.4,
                    edgecolor="black",
                    facecolor="lightblue",
                    lw=2,
                )
            )
            if self.otwText:
                self.ax.text(
                    (otws + otwe) / 2,
                    current_y + 0.3,
                    f"t{order.Task.ID}",
                    ha="center",
                    fontsize=8,
                    color="green",
                )
        # x, y show range
        self.ax.set_xlim(self.min_start - 20, self.max_end + 20)
        self.ax.set_ylim(0, current_y + 0.5)

    def two_order(self, order1, order2, line=0):
        """
        description : 绘制两个 VTW 及其 OTW 可视化关系
        :param arg1: order1
        :param arg2: order2
        :param arg3: line
        """
        self.single_order(order1, line)
        self.single_order(order2, line)
        self.show()

    def list_order(self, list: List[Vtw], line=0, sort=False):
        """
        description : 绘制 List[Vtw] 窗口
        :param arg1: List[Vtw] 窗口数据
        :param arg2: line
        :param arg3: sort，false 原始顺序绘制，true 按 start 升序排序
        """
        if sort:
            list = sorted(list, key=lambda Order: Order.start)
        taskID = []
        for vtw in list:
            if vtw.taskID not in taskID:
                taskID.append(vtw.taskID)
        list = sorted(list, key=lambda vtw: taskID.index(vtw.taskID))
        for vtw in list:
            self.single_order(vtw, line)

    def single_task(self, task: Task, line=0):
        """
        description : 绘制单个 Task
        :param arg1: task, Task 数据
        :param arg2: line：0，根据任务 ID 自动 y 轴，1-n 指定 y 轴显示
        """
        for vtw in task.vtw:
            self.single_order(vtw, line)

    def list_task(self, list: List[Task], line=0, sort=False):
        """
        description : 绘制 List[Task] 窗口
        :param arg1: List[Task] 窗口数据
        :param arg2: line
        :param arg3: sort，false 原始顺序绘制，true 按 start 升序排序
        """
        if sort:
            list = sorted(list, key=lambda Task: Task.earlistTime)
        for task in list:
            self.single_task(task, line)

    def list_select(self, list: List[SelectedVtw], line=0, sort=False):
        """
        description : 绘制 List[SelectedVtw] 窗口
        :param arg1: List[SelectedVtw] 窗口数据
        :param arg2: line
        :param arg3: sort，false 原始顺序绘制，true 按 otws 升序排序
        """
        if sort:
            list = sorted(list, key=lambda SelectedVtw: SelectedVtw.vtw.otws)
        for select in list:
            self.single_order(select.vtw, line)

    def close(self):
        if self.fig is not None:
            plt.close(self.fig)

    def __saveImg(self, img_name, img_folder="./step"):
        if not os.path.exists(img_folder):
            os.makedirs(img_folder)
        self.title = f"step: {self.callsNum}"
        self.add_annotations()
        file_path = os.path.join(img_folder, img_name)
        plt.savefig(file_path)
        plt.close()

    def __call__(self, data, line=0, sort=False, mode="show"):
        """
        description : 自动判断数据类型并选择相应的绘制方法
        :param data: 数据，支持单个 Order，单个 TaskOrder，多个 Order，多个 TaskOrder
        :param line: y轴位置，默认为 0
        :param sort: 是否按 start 升序排序
        """
        self.reset()
        self.fig, self.ax = plt.subplots()
        self.callsNum += 1
        if isinstance(data, Vtw):
            self.single_order(data, line)
        elif isinstance(data, Task):
            self.single_task(data, line)
        elif isinstance(data, list):
            if all(isinstance(item, Vtw) for item in data):
                self.list_order(data, line, sort)
            elif all(isinstance(item, Task) for item in data):
                self.list_task(data, line, sort)
            elif all(isinstance(item, SelectedVtw) for item in data):
                self.list_select(data, line, sort)
        else:
            raise TypeError("Unsupported data type.")
        if mode == "show":
            self.show()
        elif mode == "img":
            self.__saveImg(f"img_{self.callsNum}.png")


# default
plot = PLOT()


# @ HACK
def plot_two_vtw(order1, order2):
    """
    description : 绘制两个 VTW 及其 OTW 可视化关系（已弃用）(建议使用 plot)
    :param arg1: （已弃用）
    :param arg2: （已弃用）
    """
    start1, end1, otws1, otwe1 = order1.start, order1.end, order1.otws, order1.otwe
    start2, end2, otws2, otwe2 = order2.start, order2.end, order2.otws, order2.otwe
    fig, ax = plt.subplots()
    ax.add_patch(
        patches.Rectangle(
            (start1, 1), end1 - start1, 0.5, edgecolor="black", facecolor="white", lw=1
        )
    )
    ax.add_patch(
        patches.Rectangle(
            (start2, 0), end2 - start2, 0.5, edgecolor="black", facecolor="white", lw=1
        )
    )
    if otws1 is not None and otwe1 is not None:
        ax.add_patch(
            patches.Rectangle(
                (otws1, 1),
                otwe1 - otws1,
                0.5,
                edgecolor="black",
                facecolor="blue",
                lw=1,
            )
        )
    if otws2 is not None and otwe2 is not None:
        ax.add_patch(
            patches.Rectangle(
                (otws2, 0),
                otwe2 - otws2,
                0.5,
                edgecolor="black",
                facecolor="blue",
                lw=1,
            )
        )
    ax.set_xlim(min(start1, start2) - 5, max(end1, end2) + 5)
    ax.set_ylim(-0.5, 1.5)
    ax.text(
        (start1 + end1) / 2,
        0.75,
        f"t{order1.ID}",
        ha="center",
        fontsize=10,
        color="black",
    )
    ax.text(
        (start2 + end2) / 2,
        -0.25,
        f"t{order2.ID}",
        ha="center",
        fontsize=10,
        color="black",
    )
    ax.set_title("TWO VTWS AND OTWS")
    ax.get_yaxis().set_visible(False)
    plt.show()


"""*********************** brief: 测试 ***********************************"""
if __name__ == "__main__":
    pass
