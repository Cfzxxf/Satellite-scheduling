class GetPrompts:
    def __init__(self):
        # 任务描述：根据卫星调度问题的特点更新任务描述
        self.prompt_task = (
            "Given a set of tasks with their coordinates, visible time windows (VTWs), "
            "and associated satellites, you need to schedule the tasks in a way that maximizes profit. "
            "Each task can only be processed within its specific time window. "
            "The goal is to find an optimal assignment of tasks to satellites while respecting the time constraints. "
            "Design a novel algorithm to select the next task to assign to a satellite, "
            "considering factors such as task urgency, profit, processing time, and satellite resources."
        )

        self.prompt_func_name = "select_next_task"
        self.prompt_func_inputs = [
            "current_task",
            "next_task",
            "unprocessed_task_ids",
            "distance_matrix",
            "profit_matrix",
        ]
        self.prompt_func_outputs = ["next_task_id"]
        self.prompt_inout_inf = (
            "'current_task' is the current task, which can be the last scheduled task. "
            "'next_task' is the next task candidate, assumed to be a random unprocessed task from the task list. "
            "'unprocessed_task_ids' is the list of task IDs for tasks that have not yet been processed. "
            "'distance_matrix' is a 2D numpy array representing the distance or transition cost between tasks, "
            "where each element indicates the transition cost from one task to another, such as the transition time from task1 to task2. "
            "'profit_matrix' is an array of task profits, where the i-th element represents the profit of the i-th task, "
            "such as the first element representing the profit of task1."
        )
        self.prompt_other_inf = (
            "All are represented as Numpy arrays or lists of objects. "
            "The goal is to return the ID of the next task to be scheduled."
        )



    def get_task(self):
        return self.prompt_task

    def get_func_name(self):
        return self.prompt_func_name

    def get_func_inputs(self):
        return self.prompt_func_inputs

    def get_func_outputs(self):
        return self.prompt_func_outputs

    def get_inout_inf(self):
        return self.prompt_inout_inf

    def get_other_inf(self):
        return self.prompt_other_inf


if __name__ == "__main__":
    # Example usage: Print task description
    getprompts = GetPrompts()
    print(getprompts.get_task())
