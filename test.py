import aiohttp
import logging
import asyncio


# 访问夸夸AI API
async def access_kuakua_api(message):
    url = "https://api.52vmy.cn/api/chat/quark"
    params = {"msg": message}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("data", {}).get("answer", "无法获取回答")
            else:
                logging.error(f"API请求失败，状态码: {response.status}")
                return "API请求失败"


if __name__ == "__main__":
    # 使用 asyncio.run() 来运行异步函数
    result = asyncio.run(access_kuakua_api("你好"))
    print(result)
