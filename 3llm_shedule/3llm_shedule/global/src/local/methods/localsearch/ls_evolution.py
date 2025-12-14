import re
import time
from ...llm.interface_LLM import InterfaceLLM

"""
用 LLM 生成/修改算法的“演化核心”
用大语言模型（LLM）来“生成/改造算法代码”，并抽取出「算法描述 + Python 函数代码」，供外面的进化框架调用。
"""


class Evolution:
    def __init__(self, api_endpoint, api_key, model_LLM, debug_mode, prompts, **kwargs):
        # -------------------- RZ: use local LLM --------------------
        assert "use_local_llm" in kwargs
        assert "url" in kwargs
        self._use_local_llm = kwargs.get("use_local_llm")
        self._url = kwargs.get("url")
        # -----------------------------------------------------------
        # prompt 拆分
        # set prompt interface
        # getprompts = GetPrompts()
        # 算法函数名叫什么
        self.prompt_task = prompts.get_func_name()
        self.prompt_func_name = prompts.get_func_name()
        # 函数输入有哪些
        self.prompt_func_inputs = prompts.get_func_inputs()
        # 输出有哪些
        self.prompt_func_outputs = prompts.get_func_outputs()
        # 输入输出约束
        self.prompt_inout_inf = prompts.get_inout_inf()
        # 其他补充信息
        self.prompt_other_inf = prompts.get_other_inf()
        # 把输入、输出名字拼成字符串
        if len(self.prompt_func_inputs) > 1:
            self.joined_inputs = ", ".join(
                "'" + s + "'" for s in self.prompt_func_inputs
            )
        else:
            self.joined_inputs = "'" + self.prompt_func_inputs[0] + "'"

        if len(self.prompt_func_outputs) > 1:
            self.joined_outputs = ", ".join(
                "'" + s + "'" for s in self.prompt_func_outputs
            )
        else:
            self.joined_outputs = "'" + self.prompt_func_outputs[0] + "'"

        # set LLMs
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.model_LLM = model_LLM
        self.debug_mode = debug_mode  # close prompt checking

        # -------------------- RZ: use local LLM --------------------
        if self._use_local_llm:
            self.interface_llm = LocalLLM(self._url)
        else:
            self.interface_llm = InterfaceLLM(
                self.api_endpoint,
                self.api_key,
                self.model_LLM,
                self._use_local_llm,
                self._url,
                self.debug_mode,
            )

    def get_prompt_i1(self):
        """
        帮你拼出一条给大模型用的英文提示词（prompt），专门用在 i1 这个“从零生成新算法”的算子上。
        """
        prompt_content = (
            self.prompt_task + "\n"
            "First, describe your new algorithm and main steps in one sentence. \
The description must be inside a brace. Next, implement it in Python as a function named \
"
            + self.prompt_func_name
            + ". This function should accept "
            + str(len(self.prompt_func_inputs))
            + " input(s): "
            + self.joined_inputs
            + ". The function should return "
            + str(len(self.prompt_func_outputs))
            + " output(s): "
            + self.joined_outputs
            + ". "
            + self.prompt_inout_inf
            + " "
            + self.prompt_other_inf
            + "\n"
            + "Do not give additional explanations."
        )
        return prompt_content

    def get_prompt_e1(self, indivs):
        """
        把若干个已有算法（每个有“自然语言描述 + 代码”）整理成一段文本，再加上一段严格的函数接口说明，拼成一条完整的英文 prompt，要求大模型：
        看懂这些已有算法；
        基于它们，设计一个形式完全不同的新算法；
        先用 {} 一句话描述算法，再实现为一个指定名字、指定输入输出的 Python 函数；
        不要多写解释。
        """
        prompt_indiv = ""
        for i in range(len(indivs)):
            prompt_indiv = (
                prompt_indiv
                + "No."
                + str(i + 1)
                + " algorithm and the corresponding code are: \n"
                + indivs[i]["algorithm"]
                + "\n"
                + indivs[i]["code"]
                + "\n"
            )

        prompt_content = (
            self.prompt_task + "\n"
            "I have "
            + str(len(indivs))
            + " existing algorithms with their codes as follows: \n"
            + prompt_indiv
            + "Please help me create a new algorithm that has a totally different form from the given ones. \n"
            "First, describe your new algorithm and main steps in one sentence. \
The description must be inside a brace. Next, implement it in Python as a function named \
"
            + self.prompt_func_name
            + ". This function should accept "
            + str(len(self.prompt_func_inputs))
            + " input(s): "
            + self.joined_inputs
            + ". The function should return "
            + str(len(self.prompt_func_outputs))
            + " output(s): "
            + self.joined_outputs
            + ". "
            + self.prompt_inout_inf
            + " "
            + self.prompt_other_inf
            + "\n"
            + "Do not give additional explanations."
        )
        return prompt_content

    def get_prompt_e2(self, indivs):
        """
        把一批已有算法（描述+代码）整理成文字 → 要求 LLM：
        先总结这些算法的共同 backbone 思想，再基于此设计一个“形式不同但受其启发的新算法”，
        并实现为一个指定名字、指定输入输出的 Python 函数。
        """
        prompt_indiv = ""
        for i in range(len(indivs)):
            prompt_indiv = (
                prompt_indiv
                + "No."
                + str(i + 1)
                + " algorithm and the corresponding code are: \n"
                + indivs[i]["algorithm"]
                + "\n"
                + indivs[i]["code"]
                + "\n"
            )

        prompt_content = (
            self.prompt_task + "\n"
            "I have "
            + str(len(indivs))
            + " existing algorithms with their codes as follows: \n"
            + prompt_indiv
            + "Please help me create a new algorithm that has a totally different form from the given ones but can be motivated from them. \n"
            "Firstly, identify the common backbone idea in the provided algorithms. Secondly, based on the backbone idea describe your new algorithm in one sentence. \
The description must be inside a brace. Thirdly, implement it in Python as a function named \
"
            + self.prompt_func_name
            + ". This function should accept "
            + str(len(self.prompt_func_inputs))
            + " input(s): "
            + self.joined_inputs
            + ". The function should return "
            + str(len(self.prompt_func_outputs))
            + " output(s): "
            + self.joined_outputs
            + ". "
            + self.prompt_inout_inf
            + " "
            + self.prompt_other_inf
            + "\n"
            + "Do not give additional explanations."
        )
        return prompt_content

    def get_prompt_m1(self, indiv1):
        """
        给大模型构造一条英文提示词，把一个已有算法的“描述+代码”作为输入，
        让它在此基础上生成一个“形式不同但可视作原算法修改版”的新算法，
        并按指定函数名、输入输出格式用 Python 实现出来。
        """
        prompt_content = (
            self.prompt_task + "\n"
            "I have one algorithm with its code as follows. \
Algorithm description: "
            + indiv1["algorithm"]
            + "\n\
Code:\n\
"
            + indiv1["code"]
            + "\n\
Please assist me in creating a new algorithm that has a different form but can be a modified version of the algorithm provided. \n"
            "First, describe your new algorithm and main steps in one sentence. \
The description must be inside a brace. Next, implement it in Python as a function named \
"
            + self.prompt_func_name
            + ". This function should accept "
            + str(len(self.prompt_func_inputs))
            + " input(s): "
            + self.joined_inputs
            + ". The function should return "
            + str(len(self.prompt_func_outputs))
            + " output(s): "
            + self.joined_outputs
            + ". "
            + self.prompt_inout_inf
            + " "
            + self.prompt_other_inf
            + "\n"
            + "Do not give additional explanations."
        )
        return prompt_content

    def get_prompt_m2(self, indiv1):
        """
        给大模型构造一条英文提示，把一个已有算法的“描述 + 代码”作为输入，
        让它先识别该算法的关键参数，再在“评分函数参数设置不同”的前提下生成一个新算法，
        并按指定函数名、输入输出格式用 Python 实现出来。
        """
        prompt_content = (
            self.prompt_task + "\n"
            "I have one algorithm with its code as follows. \
Algorithm description: "
            + indiv1["algorithm"]
            + "\n\
Code:\n\
"
            + indiv1["code"]
            + "\n\
Please identify the main algorithm parameters and assist me in creating a new algorithm that has a different parameter settings of the score function provided. \n"
            "First, describe your new algorithm and main steps in one sentence. \
The description must be inside a brace. Next, implement it in Python as a function named \
"
            + self.prompt_func_name
            + ". This function should accept "
            + str(len(self.prompt_func_inputs))
            + " input(s): "
            + self.joined_inputs
            + ". The function should return "
            + str(len(self.prompt_func_outputs))
            + " output(s): "
            + self.joined_outputs
            + ". "
            + self.prompt_inout_inf
            + " "
            + self.prompt_other_inf
            + "\n"
            + "Do not give additional explanations."
        )
        return prompt_content

    def _get_alg(self, prompt_content):
        """
        把 prompt 发给 LLM 拿到回复后，用正则从中抽取出“算法描述”和“Python 代码”，
        在必要时最多重试 3 次，最终返回整理好的 [代码字符串（附带输出变量名）, 算法描述]。
        """
        response = self.interface_llm.get_response(prompt_content)

        algorithm = re.findall(r"\{(.*)\}", response, re.DOTALL)
        if len(algorithm) == 0:
            if "python" in response:
                algorithm = re.findall(r"^.*?(?=python)", response, re.DOTALL)
            elif "import" in response:
                algorithm = re.findall(r"^.*?(?=import)", response, re.DOTALL)
            else:
                algorithm = re.findall(r"^.*?(?=def)", response, re.DOTALL)

        code = re.findall(r"import.*return", response, re.DOTALL)
        if len(code) == 0:
            code = re.findall(r"def.*return", response, re.DOTALL)

        n_retry = 1
        while len(algorithm) == 0 or len(code) == 0:
            if self.debug_mode:
                print(
                    "Error: algorithm or code not identified, wait 1 seconds and retrying ... "
                )

            response = self.interface_llm.get_response(prompt_content)

            algorithm = re.findall(r"\{(.*)\}", response, re.DOTALL)
            if len(algorithm) == 0:
                if "python" in response:
                    algorithm = re.findall(r"^.*?(?=python)", response, re.DOTALL)
                elif "import" in response:
                    algorithm = re.findall(r"^.*?(?=import)", response, re.DOTALL)
                else:
                    algorithm = re.findall(r"^.*?(?=def)", response, re.DOTALL)

            code = re.findall(r"import.*return", response, re.DOTALL)
            if len(code) == 0:
                code = re.findall(r"def.*return", response, re.DOTALL)

            if n_retry > 3:
                break
            n_retry += 1

        algorithm = algorithm[0]
        code = code[0]

        code_all = code + " " + ", ".join(s for s in self.prompt_func_outputs)

        return [code_all, algorithm]

    def i1(self):
        """
        先用 get_prompt_i1 生成“从零设计新算法”的 prompt，
        然后调用 _get_alg 让 LLM 生成对应的算法代码和描述，最后把 [code_all, algorithm] 返回出去。
        """
        prompt_content = self.get_prompt_i1()

        if self.debug_mode:
            print(
                "\n >>> check prompt for creating algorithm using [ i1 ] : \n",
                prompt_content,
            )
            print(">>> Press 'Enter' to continue")
            input()

        [code_all, algorithm] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm]

    def e1(self, parents):
        """
        先用 get_prompt_e1(parents) 基于多个父代算法构造“生成全新算法”的 prompt，
        在 debug_mode 下可打印并人工检查，然后调用 _get_alg 让 LLM 产出新的算法代码与描述，
        最后把 [code_all, algorithm] 返回给外部使用。
        """
        prompt_content = self.get_prompt_e1(parents)

        if self.debug_mode:
            print(
                "\n >>> check prompt for creating algorithm using [ e1 ] : \n",
                prompt_content,
            )
            print(">>> Press 'Enter' to continue")
            input()

        [code_all, algorithm] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm]

    def e2(self, parents):
        """
        先用 get_prompt_e2(parents) 基于多个父代算法构造“先提炼共同 backbone 思想再创新”的 prompt，
        若开启 debug_mode 则打印供人工检查，然后调用 _get_alg 让 LLM 生成对应的新算法代码和描述，
        最后将 [code_all, algorithm] 返回。"""
        prompt_content = self.get_prompt_e2(parents)

        if self.debug_mode:
            print(
                "\n >>> check prompt for creating algorithm using [ e2 ] : \n",
                prompt_content,
            )
            print(">>> Press 'Enter' to continue")
            input()

        [code_all, algorithm] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm]

    def m1(self, parents):
        """
        基于给定父代算法，用 get_prompt_m1 构造“结构/形式修改版”的提示词，
        必要时打印检查后调用 _get_alg 让 LLM 生成一个新的修改版算法，并返回 [code_all, algorithm]。
        """
        prompt_content = self.get_prompt_m1(parents)

        if self.debug_mode:
            print(
                "\n >>> check prompt for creating algorithm using [ m1 ] : \n",
                prompt_content,
            )
            print(">>> Press 'Enter' to continue")
            input()

        [code_all, algorithm] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm]

    def m2(self, parents):
        """
        基于给定父代算法，用 get_prompt_m2 构造“参数设置（尤其评分函数参数）改动版”的提示词，
        必要时打印检查后调用 _get_alg 让 LLM 生成一个新的参数变体算法，并返回 [code_all, algorithm]。
        """
        prompt_content = self.get_prompt_m2(parents)

        if self.debug_mode:
            print(
                "\n >>> check prompt for creating algorithm using [ m2 ] : \n",
                prompt_content,
            )
            print(">>> Press 'Enter' to continue")
            input()

        [code_all, algorithm] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm]
