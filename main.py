import asyncio
from openai import AsyncOpenAI

# 举例：这里用的是“某个代理服务”的 key 和 base_url（你要按自己服务商的文档来填）
openai_client = AsyncOpenAI(
    api_key="sk-ZQO23Qk0HXsaUA42dJr6JknzACtQ4K7BBx7vMYwgL97lnAde",
    base_url="https://api.chatanywhere.tech",  # 比如 xxxx/v1 之类
    timeout=60.0,
)

async def call_model_1(prompt: str):
    resp = await openai_client.chat.completions.create(
        model="gpt-4o-mini",  # 很多代理也是兼容这个名字，如果不兼容就用它们文档里的模型名
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content

async def call_model_2(prompt: str):
    resp = await openai_client.chat.completions.create(
        model="gpt-4.1",  # 同上，按代理服务说明改
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content

async def main():
    task = "用一句话解释量子纠缠是什么？"

    try:
        results = await asyncio.gather(
            call_model_1(task),
            call_model_2(task)
        )
        print("=== 模型 1 输出 ===")
        print(results[0])
        print("\n=== 模型 2 输出 ===")
        print(results[1])
    except Exception as e:
        print("调用代理出错：", repr(e))

if __name__ == "__main__":
    asyncio.run(main())
