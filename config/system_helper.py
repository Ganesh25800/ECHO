from pathlib import Path
from config.database_query_helper import QueriesHelper as qh
from config.database_helper import database
from config.models_download_helper import download_brain, download_kokoro, download_classifier, download_wake_word_feature_models
import platform
import psutil
import shutil
import socket
import subprocess
import hashlib
import requests
from voice.echo_speak import Speech
import json



def helper_main():

    echo_first_run = check_echo_first_run_or_not()

    if echo_first_run:
        check_and_create_folder("database")

        database_created = database.create_database()

        if database_created:
            database.create_table(create_table_list())

        brain_7b = download_brain()
        voice = download_kokoro()
        classifier = download_classifier()
        emotion_model = download_wake_word_feature_models()

        if brain_7b and voice and classifier:   
            system_id = get_system_id()
            system_exist = database.check_system_id(qh.SEARCH_SYSTEM_WITH_UNIQUE_ID,system_id)
            
            if system_exist:
                #device already exist
                add_log = add_event_log()
                return True
            else:
                system_add = add_system()
                add_log = add_event_log()
                
                if system_add and add_log:
                    change_system_status()
                    return True
                else:
                    return False
                     
    else:
        event = add_event_log()

        if event:
            return True
        
def get_system_id():

    system_id = get_system_id1()

    return hash_system_id(system_id)

def add_system():
    os, total_ram, ram, disk_size, free_disk, internet, system_id, location, battery, memory_usage, disk_usage, ip_address = get_system_details()

    return database.add_system_or_log(qh.ADD_SYSTEM,system_id,os,total_ram,disk_size)
    

def add_event_log():
    os, total_ram, ram, disk_size, free_disk, internet, system_id, location, battery, memory_usage, disk_usage, ip_address = get_system_details()

    internet_access = 1 if internet else 0

    data = get_echo_details()
    version = data["Version"]
    
    return database.add_system_or_log(qh.ENTER_SYSTEM_LOG, system_id,ip_address, ram, free_disk, memory_usage, disk_usage,internet_access,location,battery,version)

def change_system_status():
    file_path = Path(__file__).resolve().parent.parent / "json" / "echo_first_run.json"
    data = {
        "echo_first_run" : False
    }

    try:
        with open(file_path, "w") as file:
            json.dump(data,file,indent=4)
        return True
    except:
        return None            


def get_echo_details():
    file_path = Path(__file__).resolve().parent.parent / "json" / "echo_details.json"

    try:
        with open(file_path, "r") as file:
            data = json.load(file)

        return data

    except Exception as e:
        print(f"Error reading ECHO details: {e}")
        return None

    
def create_table_list():
    query_list = [
        qh.CREATE_SYSTEM_TABLE,
        qh.CREATE_STARTUP_LOGS_TABLE,
        qh.CREATE_USERS_TABLE,
        qh.CREATE_FACE_EMBEDDINGS_TABLE,
        qh.CREATE_USER_INTERESTS_TABLE,
        qh.CREATE_CONVERSATIONS_TABLE,
        qh.CREATE_CONVERSATION_STATS_TABLE,
        qh.CREATE_CONVERSATION_EMOTIONS_TABLE
    ]

    return query_list

def check_and_create_folder(folder_path):
    folder = Path(folder_path)
    folder.mkdir(parents=True, exist_ok=True)

def get_system_details():

    os = get_os()
    total_ram = get_total_ram()
    ram, disk_size, free_disk = get_disk_and_ram_details()
    internet = is_internet_connected()
    system_id = hash_system_id(get_system_id1())
    location = get_location()
    battery = get_battery_percentage()
    memory_usage = get_memory_usage(total_ram,ram)
    disk_usage = get_disk_usage(disk_size, free_disk)
    ip_address = get_ip_address()

    return os, total_ram, ram, disk_size, free_disk, internet, system_id, location, battery, memory_usage, disk_usage, ip_address

def get_ip_address():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return None
    
def get_disk_usage(total_disk_gb, available_disk_gb):
    total_disk_gb = float(total_disk_gb)
    available_disk_gb = float(available_disk_gb)

    if total_disk_gb <= 0:
        return 0.0

    used_disk_gb = total_disk_gb - available_disk_gb
    disk_usage = (used_disk_gb / total_disk_gb) * 100

    return round(disk_usage, 2)

def get_memory_usage(total_ram_gb, available_ram_gb):
    total_ram_gb = float(total_ram_gb)
    available_ram_gb = float(available_ram_gb)

    if total_ram_gb <= 0:
        return 0.0

    used_ram_gb = total_ram_gb - available_ram_gb
    memory_usage = (used_ram_gb / total_ram_gb) * 100

    return round(memory_usage, 2)

def get_battery_percentage():
    battery = psutil.sensors_battery()

    if battery is None:
        return None

    return battery.percent

def get_location():
    try:
        response = requests.get(
            "https://ipapi.co/json/",
            timeout=5
        )

        response.raise_for_status()

        data = response.json()

        return {
            "city": data.get("city"),
            "region": data.get("region"),
            "country": data.get("country_name"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude")
        }

    except requests.RequestException:
        return None    

def get_total_ram():
    total_ram_bytes = psutil.virtual_memory().total
    total_ram_gb = total_ram_bytes / (1024 ** 3)

    return round(total_ram_gb, 2)

def is_internet_connected():
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=3)
        return True
    except OSError:
        return False
        

def get_disk_and_ram_details():

    # RAM
    ram = psutil.virtual_memory()
    available_ram_gb = ram.available / (1024 ** 3)

    # Disk
    disk = shutil.disk_usage("/")
    total_disk_gb = disk.total / (1024 ** 3)
    free_disk_gb = disk.free / (1024 ** 3)

    return (
        round(available_ram_gb, 2),
        round(total_disk_gb, 2),
        round(free_disk_gb, 2)
    )

def get_os():

    system = platform.system()

    if system == "Darwin":
        return "mac"
    elif system == "Windows":
        return "windows"
    elif system == "Linux":
        return "linux"
    else:
        return "unknown"


def check_echo_first_run_or_not():

    file_path = Path(__file__).resolve().parent.parent / "json" / "echo_first_run.json"

    if file_path.is_file():
        return False
    else:
        return True

def hash_system_id(system_id):
    return hashlib.sha256(
        system_id.encode("utf-8")
    ).hexdigest()    

def get_system_id1():

    system = platform.system()

    try:
        # macOS
        if system == "Darwin":
            result = subprocess.check_output(
                [
                    "ioreg",
                    "-rd1",
                    "-c",
                    "IOPlatformExpertDevice"
                ],
                text=True
            )

            for line in result.splitlines():
                if "IOPlatformUUID" in line:
                    return line.split("=")[1].strip().strip('"')


        # Windows
        elif system == "Windows":
            result = subprocess.check_output(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "(Get-CimInstance Win32_ComputerSystemProduct).UUID"
                ],
                text=True
            )

            return result.strip()


        # Linux
        elif system == "Linux":
            machine_id = Path("/etc/machine-id")

            if machine_id.exists():
                return machine_id.read_text().strip()


    except Exception as e:
        print(f"Unable to get system ID: {e}")

    return None    