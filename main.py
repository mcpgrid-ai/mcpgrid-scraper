import json
import os
import time
from dotenv import load_dotenv
from google.cloud import storage

from app.smithery import SmithreApi


def main():
    load_dotenv()
    api_key = os.getenv("SMITHERY_API_KEY")
    bucket_name = os.getenv("STORAGE_BACKET_NAME")
    bucket_folder = os.getenv("STORAGE_BACKET_FOLDER")
    storage_account_key = os.getenv("STORAGE_SERVICE_ACCOUNT_KEY")
    
    app = SmithreApi(api_key)
    # storage_client = storage.Client.from_service_account_json(storage_account_key)
    storage_client = storage.Client()
    
    servers_list = app.get_all_servers()

    for server in servers_list:
        timestamp = int(time.time()*1000)
        server_name = server["qualifiedName"]
        print(f"Server {server_name}")
        server_data_res = {
            "title": server["displayName"],
            "description": server["description"]
        }
        
        server_html_data = app.get_server_data_web(server_name)
        if not server_html_data["exists"]:
            print("Server doesn't exists")
            continue
        
        server_data_res["isOfficial"] = server_html_data["isOfficial"]
        server_data_res["githubUrl"] = server_html_data["githubUrl"]
    
        server_data = app.get_server_data(server_name)
        if not server_data["exists"]:
            print("Server doesn't exists")
            continue
        
        server_data_res["logo"] = server_data["iconUrl"]
        server_data_res["tools"] = server_data["tools"]
        server_data_res["settings"] = server_data["settings"]
        server_data_res["original_api_data"] = server_data
        server_data_res["updated_at"] = timestamp
        
        filename = server_name.replace("/", "_")
        destination_file_name = f"{bucket_folder}/{filename}.json"
        blob = storage_client.bucket(bucket_name).blob(destination_file_name)
        blob.upload_from_string(json.dumps(server_data_res), content_type='application/json')
        
        print(f"File uploaded to gs://{bucket_name}/{destination_file_name}")
        time.sleep(1)
        
    

if __name__ == "__main__":
    main()
