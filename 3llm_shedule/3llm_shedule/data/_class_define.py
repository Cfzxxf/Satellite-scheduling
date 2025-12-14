from typing import List
import bisect
import math
import random
import copy
from enum import Enum

# 定义常量
DEADLINE_THRESHOLD = 10  # 以秒为单位
SCHEDULING_CYCLE = 1 * 1800  # 30分钟调度周期
SCHEDULING_DURATION = 12 * 3600  # 12小时调度时长
TARGET_PROFIT_RATIO = 0.9  # 目标收益率80%
MAX_CYCLES = 10000  # 最大循环次数
"""*********************** 全局统计信息 ***********************************"""


class GLOBLE_INFO:
    def __init__(self):
        """静态属性"""
        # 调度数据基本信息
        self.taskTotalNum = 0
        self.taskType = None
        self.satelliteNum = 0
        self.vtwTotalNum = 0
        self.TotalProfit = 0
        self.VisibleTotalProfit = 0
        # 数据文件基本信息
        self.dataFolder = None
        # 调度任务属性
        self.isMultAEOSSP = False
        # 数据加载状态、数据统计信息
        self.isError = False
        self.taskVisibleNum = 0
        """动态属性"""
        # 调度状态数据
        self.taskFinishedNum = 0

    # 动态属性复位
    def reset(self):
        self.taskFinishedNum = 0

    # 打印实例信息
    def __repr__(self):
        return (
            f" Global INFO:\n"
            f"  - dataFolder = {self.dataFolder}, \n"
            f"  - taskTotalNum = {self.taskTotalNum}, \n"
            f"  - taskVisibleNum = {self.taskVisibleNum}, \n"
            f"  - taskType = {self.taskType}, \n"
            f"  - satelliteNum = {self.satelliteNum}, \n"
            f"  - vtwTotalNum = {self.vtwTotalNum}, \n"
            f"  - isMultAEOSSP = {self.isMultAEOSSP}\n"
            f"  - isError = {'error' if self.isError else 'success'}\n"
            f"  - taskFinishedNum = {self.taskFinishedNum}\n"
            f"  - TotalProfit = {self.TotalProfit}\n"
            f"  - VisibleTotalProfit = {self.VisibleTotalProfit}\n"
        )


"""*********************** 单个任务信息类 ***********************************"""


class Task:
    def __init__(self):
        # 数据文件读取的基本信息
        self.ID = None  # 任务 ID
        self.longitude = None  # 任务经度
        self.dimension = None  # 任务纬度
        self.profit = None  # 任务收益
        self.minProfit = None  # 任务要求的最小利润
        self.processTime = None  # 任务需求时间
        # 任务统计信息
        self.vtwNum = 0
        self.earlistTime = 0
        # 任务可见时间窗口信息
        self.vtw: List[Vtw] = []
        self.deadline = None  # 任务截止时间
        """动态属性"""
        # 任务状态信息
        self.isProcessed = False
        # 重要性和紧急度
        # self.importance = 0.0
        # self.urgency = 0.0
        # self.quadrant = 0

    def reset(self):
        self.isProcessed = False

    def get_first_vtw(self):
        """获取任务的第一个时间窗口"""
        if self.vtw:
            return self.vtw[0]
        return None

    # 打印实例信息
    def __repr__(self):
        return (
            f"Task: ID={self.ID}, "
            f"vtwNum={self.vtwNum}, "
            f"profit={self.profit}, "
            f"processTime={self.processTime}, "
            f"longitude={self.longitude}, "
            f"dimension={self.dimension}, "
            f"isProcessed={self.isProcessed}, "
        )


"""*********************** 单个可见时间窗口 VTW 类 *************************"""


class Vtw:
    def __init__(self):
        """静态属性"""
        # 数据文件读取的基本信息
        self.ID = None  # 窗口 ID
        self.start = None  # VTW 开始时间
        self.middle = None  # VTW 中间时刻
        self.end = None  # VTW 结束时间
        self.long = None  # 观测时间长度
        # 每 s 角度信息
        self.angleNum = 0
        self.angle = None
        # 归属信息
        self.taskID = None  # 归属任务ID
        self.Task = Task()  # 与任务实例绑定
        self.satelliteID = None  # 归属与哪颗卫星
        self.Satellite = Satellite()  # 与卫星实例绑定
        """动态属性"""
        # 处理 OTW 信息
        self.otws = -1  # OTW 开始时间
        self.otwe = -1  # OTW 结束时间

    # 动态属性复位
    def reset(self):
        self.otws = -1  # OTW 开始时间
        self.otwe = -1  # OTW 结束时间

    # 打印实例信息
    def __repr__(self):
        return (
            f"VTW: ID={self.ID}, "
            f"taskID={self.taskID}, "
            f"Satellite={self.satelliteID}, "
            f"start={self.start}, "
            f"end={self.end}, "
            f"long={self.long}, "
            f"angleNum={self.angleNum}, "
            f"otws={self.otws}, "
            f"otwe={self.otwe}, "
        )

    # 用于资源插入自动排序
    def __lt__(self, other):
        return self.otws < other.otws

    # 移动 OTW input ：s，成功返回true，失败返回 false
    def moveOTW(self, seconds):
        if self.otws == -1 or self.otwe == -1:
            print("ERROR: OTW is -1 -1")
            return False
        self.otws += seconds
        self.otwe += seconds
        if self.otws < self.start or self.otwe > self.end:
            self.otws -= seconds
            self.otwe -= seconds
            return False
        return True

    # 传入 OTWS ，返回该秒 time，pitch，roll 信息
    def get_angle(self, seconds):
        """
        description : 返回角度信息
        :param arg1: 传入位于窗口内的一个时间点
        :return: 时间点，pitch，roll
        """
        t1 = seconds
        seconds = seconds - self.start
        if seconds < 0 or seconds > self.long:
            print(
                "ERROR: _class_define.py : get_angle， during=",
                seconds,
                "start=",
                self.start,
                "long=",
                self.long,
                "timepoint=",
                t1,
            )
            return -1, -1, -1
        time = self.angle[seconds][0]
        pitch = self.angle[seconds][2]
        roll = self.angle[seconds][1]
        return time, pitch, roll


"""********************** 卫星资源类 *************************************"""


class SelectedVtw:
    """
    选中任务类(对窗口信息二次处理)，包含了一个 Vtw 实例和一些静态属性
    """

    def __init__(self, vtw: Vtw):
        """静态属性"""
        self.vtw: Vtw = vtw  # 窗口数据
        self.vtwID = vtw.ID  # 对应的窗口 ID
        self.taskID = vtw.taskID  # 对应的任务 ID
        self.profit = vtw.Task.profit  # 利润
        self.vtwNum = vtw.Task.vtwNum  # 观察窗口数
        self.processTime = vtw.Task.processTime  # 处理时间
        """动态属性"""
        self.TimeSlock = 0  # 时间松弛

    def reset(self):
        self.TimeSlock = 0
        self.vtw.reset()
        self.vtw.Task.reset()

    def __repr__(self):
        return f"{self.vtw}profit={self.profit}, TimeSlock={self.TimeSlock}, "

    def __lt__(self, other):
        return self.vtw.otws < other.vtw.otws


class Satellite:
    def __init__(self):
        """静态属性"""
        self.ID = None  # 资源唯一 ID
        """动态属性"""
        self.list: List[SelectedVtw] = []
        self.length = 0
        self.totalProfit = 0

    def reset(self):
        self.length = 0
        self.totalProfit = 0
        for select in self.list:
            select.reset()
        self.list = []

    def getLastOne(self):
        if self.length != 0:
            return self.list[self.length - 1].vtw
        else:
            print("ERROR: Satellite is empty")

    def sort(self):
        """
        按照vtws里task的otws从小到大排序
        """
        self.list = sorted(self.list, key=lambda select: select.vtw.otws)

    def add(self, vtw: Vtw):
        """
        description : 二分法自动按 otws 升序添加vtw
        :param vtw: Vtw 实例
        :return: 新添加的 SelectedVtw 实例
        """
        vtw.Task.isProcessed = True
        new = SelectedVtw(vtw)
        bisect.insort(self.list, new)
        self.length += 1
        self.totalProfit += new.profit
        return new

    def add_index(self, vtw: Vtw, index: int):
        """
        description : 在指定位置插入vtw
        :param vtw: Vtw 实例
        :param index: 插入位置
        :return: 新添加的 SelectedVtw 实例
        """
        if index < 0 or index > self.length:
            raise IndexError("Index out of range")
        vtw.Task.isProcessed = True
        new = SelectedVtw(vtw)
        self.list.insert(index, new)
        self.length += 1
        self.totalProfit += new.profit
        return new

    def remove_by_index(self, index: int):
        """
        description : 通过索引删除元素
        :param index: 要删除的元素索引
        :return: 被删除的 SelectedVtw 实例
        """
        if index < 0 or index >= self.length:
            raise IndexError("Index out of range")
        removed_select = self.list.pop(index)
        self.length -= 1
        self.totalProfit -= removed_select.profit
        removed_select.reset()
        return removed_select.vtw

    def remove_by_vtw(self, vtw: Vtw):
        """
        description : 通过 Vtw 实例删除元素
        :param vtw: 要删除的 Vtw 实例
        :return: 被删除的 SelectedVtw 实例
        """
        for select_vtw in self.list:
            if select_vtw.vtw == vtw:
                self.list.remove(select_vtw)
                self.length -= 1
                self.totalProfit -= select_vtw.profit
                select_vtw.reset()
                return select_vtw.vtw
        raise ValueError("vtw not found")

    def remove_by_select(self, select_vtw: SelectedVtw):
        """
        description : 通过 SelectedVtw 实例删除元素
        :param select_vtw: 要删除的 SelectedVtw 实例
        :return: None
        """
        if select_vtw in self.list:
            self.list.remove(select_vtw)
            self.length -= 1
            self.totalProfit -= select_vtw.profit
            select_vtw.reset()
        else:
            raise ValueError("not find the selected SelectedVtw")

    def __repr__(self):
        return (
            f"Satellite: ID={self.ID}, "
            f"planedNum={self.length}, "
            f"totalProfit={self.totalProfit}, "
        )


"""*********************** 插入位置统计类 ***********************************"""


class Position:
    def __init__(self):
        self.num = 0  # 插入位置个数统计
        self.index = []  # 插入位置相对编号统计
        self.otws = []  # 插入位置开始执行时间统计
        self.otwe = []  # 插入位置结束执行时间统计

    def __repr__(self):
        return (
            f"Position: num={self.num}, "
            f"index={self.index}, "
            f"otws={self.otws}, "
            f"otwe={self.otwe}, "
        )


"""*********************** 四象限统计类(已弃用) ***********************************"""


class Quadrant(Enum):
    IMPORTANT_URGENT = 1  # 重要且紧急
    IMPORTANT_NOT_URGENT = 2  # 重要不紧急
    NOT_IMPORTANT_URGENT = 3  # 不重要紧急
    NOT_IMPORTANT_NOT_URGENT = 4  # 不重要不紧急


"""*********************** 测试 ***********************************"""
if __name__ == "__main__":
    pass
