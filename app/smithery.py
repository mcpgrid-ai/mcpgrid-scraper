import requests
import time
from lxml import html
from pathlib import Path

from .constants import SECURED_PARAMETERS_PATTERNS_LIST, WEB_HEADERS


class SmithreApi():
    __api_endpoint = "https://registry.smithery.ai/servers"
    __web_endpoint = "https://smithery.ai/server/"
    
    def __init__(self, api_key):
        self.http_client = requests.Session()
        headers = {
            "Authorization": "Bearer " + api_key
        }
        self.http_client.headers.update(headers)
        
    def get_all_servers(self):
        servers = []
        page = 0
        print("Scraping servers using api")
        while True:
            page += 1
            print(f"Page {page}")
            params = {
                "page": page,
                "pageSize": 100
            }
            res = self.http_client.get(self.__api_endpoint, params=params)           
            servers += res.json()["servers"]
            if page >= res.json()["pagination"]["totalPages"]:
                break
        
        return servers
    
    def get_server_data(self, server_name):
        for i in range(4):
            res = self.http_client.get(self.__api_endpoint + "/" + server_name)
            if res.status_code == 200:
                break
            elif res.status_code == 500:
                return {"exists": False}
            elif res.status_code not in [429, 502, 503, 504]:
                print(res.status_code)
                raise Exception(f"{res.status_code} status received")
            self.http_client.cookies.clear()
            print("Pause")
            time.sleep(60)
            
        try:
            result = res.json()
        except Exception as e:
            print(res.status_code)
            print(res.text)
            raise e
        
        server_data = {
            "tools": self.process_tools(result["tools"]),
            "settings": self.process_settings(result["connections"]),
            "iconUrl": result["iconUrl"],
            "exists": True
        }
        return server_data
    
    def get_server_data_web(self, server_name):
        is_valid_html = False
        for i in range(0, 3):
            try:
                res = self.http_client.get(self.__web_endpoint + server_name, headers=WEB_HEADERS)
            except requests.exceptions.TooManyRedirects as e:
                return {"exists": False}
            except Exception as e:
                time.sleep(5)
                continue
            if res.status_code == 404:
                return {"exists": False}
            tree = html.fromstring(res.text)
            is_valid_html = len(tree.xpath('//div[contains(@class, "items-start")]//h1')) > 0
            if is_valid_html:
                break
            # timestamp = int(time.time())
            # Path("./errors/").mkdir(exist_ok=True)
            # with open(f'./errors/{server_name}_{res.status_code}_{timestamp}.html', "w+") as f:
            #     f.write(res.text)
            time.sleep(5)
            print("Request error, retry...")
        
        if not is_valid_html:
            return {"exists": False, "is_valid_html": False, "html": res.text}
        official_el = tree.xpath('//h1[./span[@class="truncate"] and ./*[name()="svg"] ]')
        is_official = len(official_el) > 0
        github_urls = tree.xpath('//div[./h3]/a[contains(@href, "https://github.com")]/@href')
        github_url = github_urls[0] if len(github_urls) > 0 else ""
        return {
            "isOfficial": is_official,
            "githubUrl": github_url,
            "exists": True
        }
        
    def process_tools(self, tools):
        processed_tools = []
        if tools is None:
            return processed_tools
        for origin_tool_data in tools:
            tool_data = {
                "id": origin_tool_data["name"],
                "description": origin_tool_data["description"] if "description" in origin_tool_data else "",
                "parameters": []
            }
            if "inputSchema" in origin_tool_data and "properties" in origin_tool_data["inputSchema"]:
                for parameter_name in origin_tool_data["inputSchema"]["properties"]:
                    parameter_data = {
                        "name": parameter_name,
                        "type": origin_tool_data["inputSchema"]["properties"][parameter_name]["type"] if "type" in origin_tool_data["inputSchema"]["properties"][parameter_name] else "",
                        "description": origin_tool_data["inputSchema"]["properties"][parameter_name]["description"] if "description" in origin_tool_data["inputSchema"]["properties"][parameter_name] else ""
                    }
                    tool_data["parameters"].append(parameter_data)
            
            processed_tools.append(tool_data)
        return processed_tools
    
    def process_settings(self, connections):
        if len(connections) == 0:
            return []
        processed_settings = []
        http_settings = list(filter(lambda x: x["type"] == "http", connections))
        if len(http_settings) == 0:
            settings = connections[0]["configSchema"]
        else:
            settings = http_settings[0]["configSchema"]
            
        if "properties" in settings:
            for origin_property in settings["properties"]:
                is_secured = False
                for el in SECURED_PARAMETERS_PATTERNS_LIST:
                    if el in origin_property.lower():
                        is_secured = True
                        break
                
                setting = {
                    "name": origin_property,
                    "secured": is_secured,
                    "required": "required" in settings and origin_property in settings["required"],
                    "description": settings["properties"][origin_property]["description"] if "description" in settings["properties"][origin_property] else ""
                }
                processed_settings.append(setting)
        
        return processed_settings
