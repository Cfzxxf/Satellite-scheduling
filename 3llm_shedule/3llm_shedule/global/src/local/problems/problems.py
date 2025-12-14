# from machinelearning import *
# from mathematics import *
# from optimization import *
# from physics import *
import os
import sys

# run.py: .../3llm_shedule/local/src/local/test/run.py
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
# PROJECT_ROOT = .../3llm_shedule 这一层
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
"""
根据传入的参数 paras 加载特定的优化问题
"""


class Probs:
    def __init__(self, paras):
        if not isinstance(paras.problem, str):
            self.prob = paras.problem
            print("- Prob local loaded ")
        elif paras.problem == "satllite":
            from data.run import ScheduleGreedy

            self.prob = ScheduleGreedy()
        else:
            print("problem " + paras.problem + " not found!")

    def get_problem(self):
        return self.prob
