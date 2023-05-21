from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
import requests
import base64
import json
import time
import os

disable_warnings(InsecureRequestWarning)


class ValClient:
    def __init__(self, region: str = 'na', shard: str = 'na'):
        self.region: str = region
        self.shard: str = shard
        self.auth: str = ''
        self.entitlement: str = ''
        self.puuid: str = ''
        self.lockfile: str = rf"{os.getenv('LOCALAPPDATA')}\Riot Games\Riot Client\Config\lockfile"
        if not self.get_basic():
            raise Exception('Unable to get auth game may not be running')

    def get_basic(self) -> bool:
        try:
            with open(self.lockfile, 'r') as file:
                content = file.readlines()[0].split(':')
                port = content[2]
                password = content[3]
        except FileNotFoundError:
            return False
        url = f"https://127.0.0.1:{port}/entitlements/v1/token"
        userinfo_url = f'https://127.0.0.1:{port}/rso-auth/v1/authorization/userinfo'
        headers = {"Authorization": f"Basic {base64.b64encode(f'riot:{password}'.encode()).decode()}"}
        response = requests.get(url=url, headers=headers, verify=False)
        userinfo_response = requests.get(url=userinfo_url, headers=headers, verify=False)
        try:
            userinfo_response = userinfo_response.json()
            response = response.json()
        except requests.exceptions.JSONDecodeError:
            return False
        self.entitlement = response['token']
        self.auth = response['accessToken']
        self.puuid = json.loads(userinfo_response['userInfo'])['sub']
        return True

    def auto_lock(self, agent: str = 'a3bfb853-43b2-7238-a4f1-ad90e9e46bcc') -> None:
        match_id = None
        pregame_url = f'https://glz-{self.region}-1.{self.shard}.a.pvp.net/pregame/v1/players/{self.puuid}'
        headers = {
            'X-Riot-Entitlements-JWT': self.entitlement,
            'Authorization': f'Bearer {self.auth}'
        }
        while not match_id:
            response = requests.get(url=pregame_url, headers=headers).json()
            if response.get("MatchID", None) is not None:
                match_id = response['MatchID']
            time.sleep(0.05)

        pregame_select = f'https://glz-{self.region}-1.{self.shard}.a.pvp.net/pregame/v1/matches/{match_id}/select/{agent}'
        pregame_lock = f'https://glz-{self.region}-1.{self.shard}.a.pvp.net/pregame/v1/matches/{match_id}/lock/{agent}'
        while True:
            f = requests.post(pregame_select, headers=headers)
            p = requests.post(pregame_lock, headers=headers)
            print(f, p)
            time.sleep(.01)
            if f.status_code in [403, 409] or p.status_code in [403, 409]:
                break


if __name__ == "__main__":
    with open('config.json') as file:
        agents = json.load(file)["agents"]
    client = ValClient()
    while True:
        agent = input("Input the agent you want to insta lock: ").lower()
        if agents.get(agent, None) is None:
            print("Incorrect agent name")
            continue
        agent = agents[agent]
        break
    client.auto_lock(agent)
