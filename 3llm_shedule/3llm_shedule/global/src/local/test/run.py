'''
Author: 方舟 10333672+c675@user.noreply.gitee.com
Date: 2025-11-20 16:46:33
LastEditors: 方舟 10333672+c675@user.noreply.gitee.com
LastEditTime: 2025-12-02 14:26:03
FilePath: \schedule_v2.0\3llm_shedule\3llm_shedule\local\src\local\test\run.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
### Test Only ###
# Set system path
import sys
import os
ABS_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_PATH = os.path.join(ABS_PATH, "..", "..")
sys.path.append(ROOT_PATH)  # This is for finding all the modules
sys.path.append(ABS_PATH)
print(ABS_PATH)
from local.local import LOCAL  # noqa: E402
from local.utils.getParas import Paras  # noqa: E402
# from evol.utils.createReport import ReportCreator
# 

# Parameter initilization #
paras = Paras() 

# Set parameters #
paras.set_paras(method = "ls",    
                ec_operators  = ['e1','e2','m1','m2','m3'], # operators in EoH
                problem = "satllite", # ['tsp_construct','bp_online','tsp_gls','fssp_gls']
                llm_api_endpoint = "api.chatanywhere.tech", # set endpoint
                llm_api_key = "sk-ZQO23Qk0HXsaUA42dJr6JknzACtQ4K7BBx7vMYwgL97lnAde",   # set your key
                llm_model = "gpt-4o-mini", # set llm
                ec_pop_size = 4,
                ec_n_pop = 2,
                exp_n_proc = 4,
                exp_debug_mode = False)

# EoH initilization
evolution = LOCAL(paras)

# run EoH
evolution.run()

# Generate EoH Report
# RC = ReportCreator(paras)
# RC.generate_doc_report()




