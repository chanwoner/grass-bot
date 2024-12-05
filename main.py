import os
import uuid
import aiohttp
import argparse
from datetime import datetime, timezone
from colorama import *
import random  # 添加在文件开头的import部分
from aiohttp_socks import ProxyConnector

green = Fore.LIGHTGREEN_EX
red = Fore.LIGHTRED_EX
magenta = Fore.LIGHTMAGENTA_EX
white = Fore.LIGHTWHITE_EX
black = Fore.LIGHTBLACK_EX
reset = Style.RESET_ALL
yellow = Fore.LIGHTYELLOW_EX


class Grass:
    def __init__(self, userid, proxy):
        self.userid = userid
        self.proxy = proxy
        self.ses = None
        self.connection_duration = (60 * 60 * 3) + 20 # 设置连接持续时间为3小时(10800秒)

    def log(self, msg):
        now = datetime.now(tz=timezone.utc).isoformat(" ").split(".")[0]
        print(f"{black}[{now}] {reset}{msg}{reset}")

    @staticmethod
    async def ipinfo(proxy=None):
        async with aiohttp.ClientSession() as client:
            result = await client.get("https://api.ipify.org/", proxy=proxy)
            return await result.text()

    async def start(self):
        max_retry = 10
        retry = 1
        proxy = self.proxy
        if proxy is None:
            proxy = await Grass.ipinfo()
        browser_id = uuid.uuid5(uuid.NAMESPACE_URL, proxy)
        useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        headers = {
            "Host": "proxy2.wynd.network:4650",
            "Connection": "Upgrade",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "User-Agent": useragent,
            "Upgrade": "websocket",
            "Origin": "chrome-extension://lkbnfiajjmbhnfledhphioinpickokdi",
            "Sec-WebSocket-Version": "13",
            "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
        }
        while True:
            try:
                if retry >= max_retry:
                    self.log(f"{yellow}max retrying reacted, skip the proxy !")
                    await self.ses.close()
                    return
                
                self.log(f"{self.userid}开始与服务器建立连接...")
                connector = ProxyConnector.from_url(proxy)
                self.ses = aiohttp.ClientSession(connector=connector)
                async with self.ses.ws_connect(
                    "wss://proxy2.wynd.network:4650/",
                    headers=headers,    
                    timeout=1000,
                    autoclose=False,
                ) as wss:
                    res = await wss.receive_json()
                    auth_id = res.get("id")
                    if auth_id is None:
                        self.log(f"{red}auth id is None")
                        return None
                    auth_data = {
                        "id": auth_id,
                        "origin_action": "AUTH",
                        "result": {
                            "browser_id": browser_id.__str__(),
                            "user_id": self.userid,
                            "user_agent": useragent,
                            "timestamp": int(datetime.now().timestamp()),
                            "device_type": "desktop",
                            "version": "4.29.0"
                        },
                    }
                    await wss.send_json(auth_data)
                    self.log(f"{green}成功连接 {white}到服务器!")
                    retry = 1
                    connection_start_time = datetime.now()
                    while True:
                        if (datetime.now() - connection_start_time).total_seconds() >= self.connection_duration:
                            self.log(f"{yellow}连接已持续{self.connection_duration/3600}小时，准备重新建立连接...")
                            break
                        
                        ping_data = {
                            "id": uuid.uuid4().__str__(),
                            "version": "1.0.0",
                            "action": "PING",
                            "data": {},
                        }
                        await wss.send_json(ping_data)
                        self.log(f"{white}发送 {green}ping {white}到服务器 !")
                        pong_data = {"id": "F3X", "origin_action": "PONG"}
                        await wss.send_json(pong_data)
                        self.log(f"{white}发送 {magenta}pong {white}到服务器 !")
                        await countdown(120)
            except KeyboardInterrupt:
                await self.ses.close()
                exit()
            except Exception as e:
                self.log(f"{red}error : {white}{e}")
                retry += 1
                if retry >= max_retry:
                    self.log(f"{yellow}max retrying reacted, skip the proxy !")
                    await self.ses.close()
                    return
                continue


async def countdown(t):
    for i in range(t, 0, -1):
        minute, seconds = divmod(i, 60)
        hour, minute = divmod(minute, 60)
        seconds = str(seconds).zfill(2)
        minute = str(minute).zfill(2)
        hour = str(hour).zfill(2)
        print(f"waiting for {hour}:{minute}:{seconds} ", flush=True, end="\r")
        await asyncio.sleep(1)


async def main():
    arg = argparse.ArgumentParser()
    arg.add_argument(
        "--proxy", "-P", default="proxies.txt", help="Custom proxy input file "
    )
    args = arg.parse_args()
    os.system("cls" if os.name == "nt" else "clear")

    print(
        f"""
    {red}grass 第二季超稳定无限多开脚本由[志贤说]开源，免费使用
    {red}持续更新web3撸毛项目，欢迎关注
    {white}Gihub: {green}github.com/zx-meet
    {white}微信: {green}caba_9527
    {green}祝你好运！！！
          """
    )

    userid = open("userid.txt", "r").read()
    if len(userid) <= 0:
        print(f"{red}错误 : {white}请先输入您的用户ID!")
        exit()
    if not os.path.exists(args.proxy):
        print(f"{red}{args.proxy} 未找到，请确保 {args.proxy} 可用！")
        exit()
    proxies = open(args.proxy, "r").read().splitlines()
    if len(proxies) <= 0:
        proxies = [None]
    
    # 创建任务列表时添加延迟和日志
    tasks = []
    total_proxies = len(proxies)
    
    for index, proxy in enumerate(proxies, 1):
        # 为每个代理添加2-10秒的随机延迟
        delay = random.uniform(2, 10)
        tasks.append(asyncio.create_task(Grass(userid, proxy).start()))
        print(f"{green}第 {index}/{total_proxies} 个代理任务已创建{reset}")

        if index != total_proxies:
            print(f"{white}等待 {green}{delay:.2f}秒{white} 后开始创建第{index+1}个代理任务")
            await asyncio.sleep(delay)
        
    print(f"{magenta}所有代理任务已创建，开始执行...{reset}")
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        import asyncio
        if os.name == "nt":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        exit()
