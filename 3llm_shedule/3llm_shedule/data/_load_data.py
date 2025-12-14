from ._class_define import *
import os
import numpy as np

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))  # 项目根目录
type = 1


class LOAD_DATAS:
    """
    description : 数据加载类
    :param arg1: 传入数据文件夹地址，文件夹命名需要符合特定格式
    :param arg2: {调度数据类型}_s{卫星数}_t{任务数量}
    :return: 加载了数据的实例对象
    """

    def __init__(
        self, data_folder=os.path.join(ROOT_DIR, "database/Single/area_s1_t200")
    ):
        self.data_folder = data_folder
        # 数据信息及数据集合
        self.Info = GLOBLE_INFO()  # 全局数据信息
        self.taskList: List[Task] = []  # 任务类集合
        self.vtwList: List[Vtw] = []  # 窗口类集合
        self.satList: List[Satellite] = []  # 资源类集合
        self.vtwID = -1  # 可见时间窗口ID
        # 分析加载数据流程
        self.__get_global_Info(data_folder)
        self.__init_satellite()
        self.__load_data()
        # self.getVisTaskList()

    def getVisTaskList(self) -> List[Task]:
        """
        description : 筛选出有可见时间窗口的任务，并重新调整任务ID
        :return: 包含可见时间窗口的任务列表（ID已重新调整）
        """
        visible_tasks = []
        new_id = 0
        for task in self.taskList:
            if task.vtwNum > 0:  # 如果任务有可见时间窗口
                task.ID = new_id
                new_id += 1
                visible_tasks.append(task)
            else:
                # 这里可以添加额外的清理逻辑（如果需要）
                pass
        return visible_tasks

    def sortTaskList(self) -> List[Task]:
        """
        description : 对 self.taskList 元素进行重新排序
        :return: 按 start 升序后的 self.taskList
        """
        self.taskList = sorted(
            self.taskList,
            key=lambda task: (
                task.vtwNum == 0,
                task.vtw[0].start if task.vtwNum > 0 else float("inf"),
            ),
        )
        return self.taskList

    def sortVtwList(self) -> List[Vtw]:
        """
        description : 对 self.vtwList 元素进行重新排序
        :return: 按 start 升序后的 self.vtwList
        """
        self.vtwList = sorted(self.vtwList, key=lambda Order: Order.start)
        return self.vtwList

    def getCopyTaskList(self) -> List[Task]:
        """
        description : 获取一份 taskList 副本数据
        :return: taskList 副本数据
        """
        return copy.deepcopy(self.taskList)

    def getCopyVtwList(self) -> List[Vtw]:
        """
        description : 获取一份 vtwList 副本数据
        :return: taskList 副本数据
        """
        return copy.deepcopy(self.vtwList)

    def getSatellite(self, index: int = None):
        """
        description : 获取 Resources ：Satellite 数据
        :param arg1: 资源标号：index
        :return: 相应 index 的 Resource 实例对象数据
        """
        if index == None:
            return self.satList
        else:
            if index < 0 or index > self.Info.satelliteNum - 1:
                print("ERROR: load_dada.py : get_Satellite")
                return -1
            return self.satList[index]

    def getAllSortData(self, sort=True):
        """
        description : 获取排序后的所有数据内容
        :return: info, tasks, vtws, satellites
        """
        if sort:
            return self.Info, self.sortTaskList(), self.sortVtwList(), self.satList
        else:
            return self.Info, self.taskList, self.vtwList, self.satList

    def finishedRate(self):
        """
        description : 计算并打印任务完成率
        :return: 相对任务总数的任务完成率 和 相对可见任务总数的任务完成率
        """
        for s in self.satList:
            self.Info.taskFinishedNum += s.length
        rate1 = (self.Info.taskFinishedNum / self.Info.taskTotalNum) * 100
        rate2 = (self.Info.taskFinishedNum / self.Info.taskVisibleNum) * 100
        rate1 = round(rate1, 2)
        rate2 = round(rate2, 2)
        print(
            f"taskNum: {self.Info.taskTotalNum} visibleTask: {self.Info.taskVisibleNum} finished: {self.Info.taskFinishedNum}"
        )
        print(f"task finished rate: {rate1}% (full)  {rate2}% (visible)\n")

    def finishedRate2(self):
        """
        description : 计算并打印任务完成率
        :return: 相对任务总数的任务完成率 和 相对可见任务总数的任务完成率
        """
        profit = 0
        self.Info.taskFinishedNum = 0
        for task in self.taskList:
            if task.isProcessed:
                profit += task.profit
                self.Info.taskFinishedNum += 1
        rate1 = (profit / self.Info.VisibleTotalProfit) * 100
        rate1 = round(rate1, 2)
        print(
            f"taskNum: {self.Info.taskTotalNum} visibleTask: {self.Info.taskVisibleNum} finished: {self.Info.taskFinishedNum}"
        )
        print(
            f"TotalProfit: {self.Info.VisibleTotalProfit} profit: {profit} rate: {rate1}%\n"
        )
        return rate1

    def finishedRate3(self, satellite: Satellite):
        """
        description : 计算并打印任务完成率
        :return: 相对任务总数的任务完成率 和 相对可见任务总数的任务完成率
        """
        finished_tasks = 0
        finished_tasks = sum(1 for task in self.taskList if task.isProcessed)
        completion_rate1 = (
            finished_tasks / self.Info.taskTotalNum if self.Info.taskTotalNum > 0 else 0
        )
        completion_rate2 = (
            finished_tasks / self.Info.taskVisibleNum
            if self.Info.taskVisibleNum > 0
            else 0
        )
        profit_rate1 = (
            satellite.totalProfit / self.Info.TotalProfit
            if self.Info.TotalProfit > 0
            else 0
        )
        profit_rate2 = (
            satellite.totalProfit / self.Info.VisibleTotalProfit
            if self.Info.VisibleTotalProfit > 0
            else 0
        )
        print(
            f"所有任务完成率: {finished_tasks}/{self.Info.taskTotalNum} = {completion_rate1:.2%}"
        )  # 打印任务完成率
        print(
            f"利润率:     {satellite.totalProfit:.2f}/{self.Info.TotalProfit:.2f} = {profit_rate1:.2%}"
        )  # 打印利润率
        print(
            f"可见任务完成率: {finished_tasks}/{self.Info.taskVisibleNum} = {completion_rate2:.2%}"
        )  # 打印任务完成率
        print(
            f"利润率:     {satellite.totalProfit:.2f}/{self.Info.VisibleTotalProfit:.2f} = {profit_rate2:.2%}"
        )  # 打印利润率

    def getTasksVtws(self, tasks: List[Task], sort=False) -> List[Vtw]:
        """
        description : 根据任务list提取这些任务的可见窗口list
        :param arg1: 任务集合
        :return: 该任务集合对应的vtw集合
        """
        vtws: List[Vtw] = []
        for task in tasks:
            for vtw in task.vtw:
                vtws.append(vtw)
        if sort:
            vtws = sorted(vtws, key=lambda Order: Order.start)
        return vtws

    def reset(self):
        """
        description : 动态数据清理与复位
        :return: describe what is returned
        """
        self.Info.reset()
        for task in self.taskList:
            task.reset()
        for vtw in self.vtwList:
            vtw.reset()
        for sat in self.satList:
            sat.reset()

    """*******以下方法用于从原始数据文件提取数据到类并初始化一些基本信息：不建议修改(私有方法) ***********"""

    def __get_global_Info(self, data_folder):
        """
        读取文件名称信息
        """
        folder_name = data_folder.split("/")[-1]
        self.Info.dataFolder = folder_name
        task_type = folder_name.split("_")[0]
        self.Info.taskType = task_type
        satellite_task_part = folder_name.split("_")[1:]
        if len(satellite_task_part) >= 2:
            satellite_str = satellite_task_part[0]
            task_str = satellite_task_part[1]
            if satellite_str.startswith("s") and task_str.startswith("t"):
                self.Info.satelliteNum = int(satellite_str[1:])
                self.Info.taskTotalNum = int(task_str[1:])
                if self.Info.satelliteNum > 1:
                    self.Info.isMultAEOSSP = True
            else:
                self.Info.isError = True
                print("Error: Folder name format is incorrect.")
        else:
            self.Info.isError = True
            print("Error: Folder name format is incorrect.")

    def __init_satellite(self):
        """
        创建卫星列表
        """
        for i in range(self.Info.satelliteNum):
            s = Satellite()
            s.ID = i
            self.satList.append(s)

    def __load_data(self):
        print("\n--开始加载数据--")
        self.__read_task_data(self.data_folder + "/tasklist.txt")
        for i in range(1, self.Info.satelliteNum + 1):
            attitude = self.data_folder + f"/outputattitude_{i}.txt"
            window = self.data_folder + f"/outputtimewindow_{i}.txt"
            self.__read_vtw_data(
                file_path=window, angle_datas=self.__read_angle_data(file_path=attitude)
            )
        print(self.Info)

    def __read_task_data(self, file_path: str):
        """
        读取任务文件数据
        """
        with open(file_path, "r") as file:
            lines = file.readlines()  # 读取所有行，每行为一个元素
            task_order = None
            for line in lines:
                data = line.split()  # 本行按空格分割数据，作为列表的元素
                if len(data) == 6:
                    if task_order:
                        self.taskList.append(task_order)
                        if type:
                            self.Info.TotalProfit += task_order.profit
                    task_order = Task()
                    task_order.ID = int(data[0])
                    task_order.longitude = float(data[1])
                    task_order.dimension = float(data[2])
                    task_order.profit = int(data[3])
                    task_order.minProfit = int(data[4])
                    task_order.processTime = int(data[5])
                elif len(data) == 4:
                    continue
            if task_order:
                self.taskList.append(task_order)
                if type:
                    self.Info.TotalProfit += task_order.profit
                    self.Info.VisibleTotalProfit += task_order.profit

    def __read_vtw_data(self, file_path: str, angle_datas):
        """
        读取可见时间窗口文件数据
        """
        blockID = -1
        with open(file_path, "r") as file:
            lines = file.readlines()
            vtw_order = None
            satellite_ID = -1
            task_ID = -1
            for line in lines:
                line = line.strip()  # 移除字符串开头和结尾的空白字符
                if not line:
                    continue
                if line.isdigit():
                    task_ID = int(line)
                elif len(line.split()) >= 6:  # 按空白字符将字符串分割成列表不同元素
                    if vtw_order:
                        self.vtwList.append(vtw_order)
                    vtw_order = Vtw()
                    curTask = self.taskList[task_ID]
                    self.vtwID += 1
                    self.Info.vtwTotalNum += 1
                    blockID += 1
                    vtw_order.ID = self.vtwID
                    vtw_order.angle = angle_datas[blockID]
                    vtw_order.angleNum = len(vtw_order.angle)
                    vtw_order.start, vtw_order.middle, vtw_order.end, vtw_order.long = (
                        self.__process_vtw_line(line)
                    )
                    vtw_order.taskID = task_ID
                    vtw_order.Task = curTask
                    vtw_order.satelliteID = satellite_ID - 1
                    vtw_order.Satellite = self.satList[satellite_ID - 1]
                    if curTask.vtwNum == 0:
                        self.Info.taskVisibleNum += 1
                        self.Info.VisibleTotalProfit += curTask.profit
                        curTask.earlistTime = vtw_order.start
                        if not type:
                            self.Info.TotalProfit += curTask.profit
                    curTask.vtwNum += 1
                    self.taskList[task_ID].vtw.append(vtw_order)
                elif line.startswith("s") and len(line) > 1 and line[1:].isdigit():
                    satellite_ID = int(line[1:])
                else:
                    self.Info.isError = True
                    print(f"Unrecognized line format: {line}")
            if vtw_order:
                self.vtwList.append(vtw_order)

    def __process_vtw_line(self, line):
        parts = line.split()
        start_h, start_m, start_s = map(float, parts[3:6])
        end_h, end_m, end_s = map(float, parts[9:12])
        start = int(start_h * 3600 + start_m * 60 + math.ceil(start_s))
        end = int(end_h * 3600 + end_m * 60 + math.floor(end_s))
        long = end - start + 1
        middle = int((start + end) / 2)
        return start, middle, end, long

    def __read_angle_data(self, file_path):
        blocks = []
        current_block = []
        with open(file_path, "r") as file:
            for line in file:
                line = line.strip()
                if line == "":
                    if current_block:
                        blocks.append(current_block)
                        current_block = []
                else:
                    useInfo = self.__process_angle_line(line)
                    current_block.append(useInfo)
            if current_block:
                blocks.append(current_block)
            for i in range(len(blocks)):
                if len(blocks[i]) > 2:
                    blocks[i] = blocks[i][1:-1]
        return blocks

    def __process_angle_line(self, line):
        parts = line.split()
        start_h, start_m, start_s = map(float, parts[3:6])
        start = int(start_h * 3600 + start_m * 60 + math.ceil(start_s))
        result = [start, float(parts[6]), float(parts[7])]
        return result


# 创建默认实例并作为模块属性导出
data = LOAD_DATAS()


"""*********************** brief: 测试 ***********************************"""
if __name__ == "__main__":

    # 实例 1：通过任务查询数据信息
    # satellite = task.vtw.Satellite
    # print(data.taskList)
    task = data.taskList[0]
    print(task.vtw[0].Satellite.list)
    # for scheduled_task in task.vtw[0].Satellite.tasks:
    #     print(scheduled_task)
    # for vtw in task.vtw:
    #     print(vtw)
    # print("\n")

    # # 实例 2：通过窗口查询数据信息
    # for vtw in data.vtwList:
    #     print(vtw)
    # print("\n")

    # # 实例 3：查询某个 VTW 全部角度信息
    # one_vtw = data.vtwList[0]
    # print(one_vtw)
    # for angle in one_vtw.angle:
    #     print(angle)

    # # 实例 4：查询某个 VTW 相对 s 数角度信息
    # two_vtw = data.vtwList[0]
    # print(two_vtw)
    # seconds = 2
    # time, pitch, roll = two_vtw.get_angle(seconds + two_vtw.start)
    # print(f"第 {seconds} s 的 time: {time} pitch: {pitch} roll: {roll}")

    # satellite = data.satList[0]
    # print(satellite)
    # print(data.Info.TotalProfit)
