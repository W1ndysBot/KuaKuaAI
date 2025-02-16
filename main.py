# script/kuakua/main.py

import logging
import os
import sys
import aiohttp
import random

# 添加项目根目录到sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.config import owner_id
from app.api import *
from app.switch import load_switch, save_switch

# 数据存储路径，实际开发时，请将KuaKuaAI替换为具体的数据存放路径
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "KuaKuaAI",
)


# 查看功能开关状态
def load_function_status(group_id):
    return load_switch(group_id, "kuakua")


# 保存功能开关状态
def save_function_status(group_id, status):
    save_switch(group_id, "kuakua", status)


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


# 开关管理
async def kuakua_switch_manage(websocket, user_id, group_id, raw_message, role):

    # 鉴权
    if not is_authorized(role, user_id):
        return

    # 管理命令
    if raw_message == "kkai":
        # 获取开关状态
        status = load_function_status(group_id)
        # 保存开关状态
        save_function_status(group_id, not status)
        # 发送开关状态
        await send_group_msg(
            websocket, group_id, "夸夸AI开关已" + ("打开" if not status else "关闭")
        )


# 群消息处理函数
async def handle_KuaKuaAI_group_message(websocket, msg):
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        raw_message = str(msg.get("raw_message"))
        role = str(msg.get("sender", {}).get("role"))
        message_id = str(msg.get("message_id"))

        # 管理命令
        await kuakua_switch_manage(websocket, user_id, group_id, raw_message, role)

        # 如果开关开了
        if load_function_status(group_id):

            # 随机数，每句话有50%的概率被夸夸AI回答
            random_num = random.randint(0, 1)
            if random_num == 0:
                return

            # 访问夸夸AI API
            result = await access_kuakua_api(raw_message)

            result = f"[CQ:reply,id={message_id}]{result}"

            # 发送夸夸AI回答
            await send_group_msg(websocket, group_id, result)

    except Exception as e:
        logging.error(f"处理KuaKuaAI群消息失败: {e}")
        return


# 统一事件处理入口
async def handle_events(websocket, msg):
    """统一事件处理入口"""
    post_type = msg.get("post_type", "response")  # 添加默认值
    try:
        # 处理回调事件
        if msg.get("status") == "ok":
            return

        post_type = msg.get("post_type")

        # 处理元事件
        if post_type == "meta_event":
            return

        # 处理消息事件
        elif post_type == "message":
            message_type = msg.get("message_type")
            if message_type == "group":
                # 调用KuaKuaAI的群组消息处理函数
                await handle_KuaKuaAI_group_message(websocket, msg)
            elif message_type == "private":
                return

        # 处理通知事件
        elif post_type == "notice":
            return

        # 处理请求事件
        elif post_type == "request":
            return

    except Exception as e:
        error_type = {
            "message": "消息",
            "notice": "通知",
            "request": "请求",
            "meta_event": "元事件",
        }.get(post_type, "未知")

        logging.error(f"处理KuaKuaAI{error_type}事件失败: {e}")

        # 发送错误提示
        if post_type == "message":
            message_type = msg.get("message_type")
            if message_type == "group":
                await send_group_msg(
                    websocket,
                    msg.get("group_id"),
                    f"处理KuaKuaAI{error_type}事件失败，错误信息：{str(e)}",
                )
            elif message_type == "private":
                await send_private_msg(
                    websocket,
                    msg.get("user_id"),
                    f"处理KuaKuaAI{error_type}事件失败，错误信息：{str(e)}",
                )
