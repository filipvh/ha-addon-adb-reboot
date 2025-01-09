import json
import os
import sys
import threading
import time

import schedule
from ppadb.client import Client as AdbClient
from pydantic import ValidationError, BaseModel

CONFIG_PATH = "/data/options.json"
lock = threading.Lock()

class RebootConfig(BaseModel):
    host: str
    cron: str

class Config(BaseModel):
    reboot: list[RebootConfig]

def log_error(message):
    print(f"ERROR: {message}", file=sys.stderr)

def reboot_device(client, host):
    with lock:
        device = client.device(host)
        if device:
            print(f"Rebooting {device.serial}")
            device.reboot()
        else:
            print(f"Failed to connect to {host}")

def main():
    if not os.path.exists(CONFIG_PATH):
        log_error("Configuration file not found!")
        sys.exit(1)

    try:
        with open(CONFIG_PATH, "r") as f:
            config_data = json.load(f)
            config = Config(**config_data)
    except (json.JSONDecodeError, ValidationError) as e:
        log_error(e)
        sys.exit(1)

    # Connect to ADB server
    client = AdbClient(host="127.0.0.1", port=5037)

    # Schedule reboots
    for item in config.reboot:
        schedule.every().day.at(item.cron).do(reboot_device, client, item.host)

    # Keep the script running and check the schedule
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
