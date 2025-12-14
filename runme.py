from src.optimization import *
from evaluation import *
from llm_interface import LLMInterface  # 适配大语言模型接口
from model_management import ModelManager  # 模型管理

print("智能优化架构初始化")

# 参数初始化
paras = Paras()

# 设置参数
paras.set_paras(
    method="local",  # 优化方法 ['ael', 'local']
    problem="satellite_scheduling",  # 优化问题类型 ['satellite_scheduling', 'resource_allocation']
    llm_api_endpoint="api.yourllmendpoint.com",  # 设置LLM接口地址
    llm_api_key="your-llm-api-key",  # 设置API密钥
    llm_model="gpt-4o-mini",  # 选择LLM模型
    ec_pop_size=10,  # 每个种群中的样本数
    ec_n_pop=5,  # 并行处理的种群数量
    exp_n_proc=4,  # 使用的CPU核数
    exp_debug_mode=True,  # 启用调试模式
)

# 初始化
evolution = Evolution(paras)

# 运行进化过程
evolution.run()

# 结果评估
evaluation = Evaluation(paras)
evaluation.evaluate()

# 反馈迭代优化
feedback = ModelManager(paras)
feedback.iterate_feedback()

print("智能优化架构执行完毕")
