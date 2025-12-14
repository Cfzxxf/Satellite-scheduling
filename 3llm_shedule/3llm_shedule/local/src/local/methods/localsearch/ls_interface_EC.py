import numpy as np
import time
from .ls_evolution import Evolution
import warnings
from joblib import Parallel, delayed
from .evaluator_accelerate import add_numba_decorator
import re

"""
连接 LS、Evolution 和评估的中间层
这个文件里的 InterfaceEC 类就是 LS 里的“进化算子接口”：
接收当前种群 → 调用 Evolution 让 LLM 生成新算法 → 用 evaluator_accelerate 改写代码并加速 → 调用 problem.evaluate() 打分。
"""


class InterfaceEC:
    def __init__(
        self,
        pop_size,
        m,
        api_endpoint,
        api_key,
        llm_model,
        debug_mode,
        interface_prob,
        select,
        n_p,
        **kwargs,
    ):
        # -------------------- RZ: use local LLM --------------------
        assert "use_local_llm" in kwargs
        assert "url" in kwargs
        # -----------------------------------------------------------

        # LLM settings
        self.pop_size = pop_size
        self.interface_eval = interface_prob
        prompts = interface_prob.prompts
        self.evol = Evolution(
            api_endpoint, api_key, llm_model, debug_mode, prompts, **kwargs
        )
        self.m = m
        self.debug = debug_mode

        if not self.debug:
            warnings.filterwarnings("ignore")

        self.select = select
        self.n_p = n_p

    def code2file(self, code):
        '''将生成的算法代码字符串保存到本地文件中'''
        with open("./ael_alg.py", "w") as file:
            # Write the code to the file
            file.write(code)
        return

    def add2pop(self, population, offspring):
        '''确保适应度不重复的前提下将新个体加入种群'''
        for ind in population:
            if ind["objective"] == offspring["objective"]:
                if self.debug:
                    print("duplicated result, retrying ... ")
                return False
        population.append(offspring)
        return True

    def check_duplicate(self, population, code):
        '''比较代码内容来检查新算法是否与种群中现有算法重复'''
        for ind in population:
            if code == ind["code"]:
                return True
        return False

    # def population_management(self,pop):
    #     # Delete the worst individual
    #     pop_new = heapq.nsmallest(self.pop_size, pop, key=lambda x: x['objective'])
    #     return pop_new

    # def parent_selection(self,pop,m):
    #     ranks = [i for i in range(len(pop))]
    #     probs = [1 / (rank + 1 + len(pop)) for rank in ranks]
    #     parents = random.choices(pop, weights=probs, k=m)
    #     return parents

    def population_generation(self):
        '''从头开始生成初始种群，它通过反复调用进化算子 "i1" 来创建全新的算法个体'''
        _, population = self.get_algorithm([], "i1")

        while population[0]["objective"] == None:
            _, population = self.get_algorithm([], "i1")

        return population

    def population_generation_seed(self, seeds, n_p):
        '''使用预设的种子算法来初始化种群，它并行地对所有种子算法进行性能评估，
        为每个种子算法计算适应度分数，然后将它们组装成完整的种群个体'''
        population = []

        fitness = Parallel(n_jobs=n_p)(
            delayed(self.interface_eval.evaluate)(seed["code"]) for seed in seeds
        )

        for i in range(len(seeds)):
            try:
                seed_alg = {
                    "algorithm": seeds[i]["algorithm"],
                    "code": seeds[i]["code"],
                    "objective": None,
                    "other_inf": None,
                }

                obj = np.array(fitness[i])
                seed_alg["objective"] = np.round(obj, 5)
                population.append(seed_alg)

            except Exception as e:
                print("Error in seed algorithm")
                exit()

        print("Initiliazation finished! Get " + str(len(seeds)) + " seed algorithms")

        return population

    def _get_alg(self, pop, operator):
        ''' 根据指定的进化算子生成一个新算法个体
        :param pop: 当前种群列表
        :param operator: 要使用的进化算子名称（字符串）
        :return: 父代个体列表和新生成的子代个体字典
        '''
        offspring = {
            "algorithm": None,
            "code": None,
            "objective": None,
            "other_inf": None,
        }
        
        if operator == "i1":
            parents = None
            [offspring["code"], offspring["algorithm"]] = self.evol.i1()
        
        elif operator == "e1":
            # e1 需要多个父代（通常2个）
            parents = self.select.parent_selection(pop, 2) if pop else []
            [offspring["code"], offspring["algorithm"]] = self.evol.e1(parents)
        
        elif operator == "e2":
            # e2 也需要多个父代
            parents = self.select.parent_selection(pop, 2) if pop else []
            [offspring["code"], offspring["algorithm"]] = self.evol.e2(parents)
        
        elif operator == "m1":
            parents = self.select.parent_selection(pop, 1) if pop else []
            if parents:
                [offspring["code"], offspring["algorithm"]] = self.evol.m1(parents[0])
        
        elif operator == "m2":
            parents = self.select.parent_selection(pop, 1) if pop else []
            if parents:
                [offspring["code"], offspring["algorithm"]] = self.evol.m2(parents[0])
        
        elif operator == "m3":
            # 如果 m3 未实现，可以暂时用 m2 或返回错误
            print(f"Evolution operator [m3] has not been implemented ! \n")
            return None, offspring
        
        else:
            print(f"Evolution operator [{operator}] has not been implemented ! \n")
            return None, offspring

        return parents, offspring

    def get_offspring(self, pop, operator):
        """
        生成一个子代算法个体
        """
        try:
            p, offspring = self._get_alg(pop, operator)

            # Regular expression pattern to match function definitions
            pattern = r"def\s+(\w+)\s*\(.*\):"

            # Search for function definitions in the code
            match = re.search(pattern, offspring["code"])

            function_name = match.group(1)

            code = add_numba_decorator(
                program=offspring["code"], function_name=function_name
            )

            n_retry = 1
            while self.check_duplicate(pop, code):
                if self.debug:
                    print("duplicated code, wait 1 second and retrying ... ")
                p, offspring = self._get_alg(pop, operator)

                # Regular expression pattern to match function definitions使用正则表达式从生成的代码中提取函数名
                pattern = r"def\s+(\w+)\s*\(.*\):"

                # Search for function definitions in the code
                match = re.search(pattern, offspring["code"])

                function_name = match.group(1)

                code = add_numba_decorator(
                    program=offspring["code"], function_name=function_name
                )

                if n_retry > 3:
                    break

                n_retry += 1
            # self.code2file(offspring['code'])
            # 进行性能评估，获得适应度分数，并保留5位小数
            fitness = self.interface_eval.evaluate(code)
            offspring["objective"] = np.round(fitness, 5)

        except Exception as e:
            # print(e)

            offspring = {
                "algorithm": None,
                "code": None,
                "objective": None,
                "other_inf": None,
            }
            p = None

        # Round the objective values
        return p, offspring

    def get_algorithm(self, pop, operator):
        """
        并行地调用 get_offspring 多次，生成一批子代算法（offspring），然后把父代和子代分别整理返回
        """
        from multiprocessing import TimeoutError
        import concurrent.futures
        from joblib.externals.loky.process_executor import TerminatedWorkerError

        results = []
        try:
            results = Parallel(n_jobs=self.n_p, timeout=20)(
                delayed(self.get_offspring)(pop, operator) for _ in range(self.pop_size)
            )
            # for result in results:
            #     if isinstance(result, (TimeoutError, concurrent.futures.TimeoutError)):
            #         print("Timeout occurred for a job.")
            #     else:
            #         results_collected.append(result)
        except (TimeoutError, concurrent.futures.TimeoutError, TerminatedWorkerError):
            print("Overall Timeout or terminate error  occurred")

        time.sleep(2)

        out_p = []
        out_off = []

        for p, off in results:
            out_p.append(p)
            out_off.append(off)
        return out_p, out_off

    # def get_algorithm(self,pop,operator, pop_size, n_p):

    #     # perform it pop_size times with n_p processes in parallel
    #     p,offspring = self._get_alg(pop,operator)
    #     while self.check_duplicate(pop,offspring['code']):
    #         if self.debug:
    #             print("duplicated code, wait 1 second and retrying ... ")
    #         time.sleep(1)
    #         p,offspring = self._get_alg(pop,operator)
    #     self.code2file(offspring['code'])
    #     try:
    #         fitness= self.interface_eval.evaluate()
    #     except:
    #         fitness = None
    #     offspring['objective'] =  fitness
    #     #offspring['other_inf'] =  first_gap
    #     while (fitness == None):
    #         if self.debug:
    #             print("warning! error code, retrying ... ")
    #         p,offspring = self._get_alg(pop,operator)
    #         while self.check_duplicate(pop,offspring['code']):
    #             if self.debug:
    #                 print("duplicated code, wait 1 second and retrying ... ")
    #             time.sleep(1)
    #             p,offspring = self._get_alg(pop,operator)
    #         self.code2file(offspring['code'])
    #         try:
    #             fitness= self.interface_eval.evaluate()
    #         except:
    #             fitness = None
    #         offspring['objective'] =  fitness
    #         #offspring['other_inf'] =  first_gap
    #     offspring['objective'] = np.round(offspring['objective'],5)
    #     #offspring['other_inf'] = np.round(offspring['other_inf'],3)
    #     return p,offspring
