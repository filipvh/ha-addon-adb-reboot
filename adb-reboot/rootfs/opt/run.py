import json
import os
import sys
import threading
import time
import datetime

from croniter import croniter
from ppadb.client import Client as AdbClient
from pydantic import ValidationError, BaseModel

CONFIG_PATH = "/data/options.json"
lock = threading.Lock()

class RebootConfig(BaseModel):
    host: str
    cron: str  # e.g., "0 3 * * *" for every day at 3:00 AM

class Config(BaseModel):
    reboot: list[RebootConfig]

def log_error(message):
    print(f"ERROR: {message}", file=sys.stderr)

def log_info(message):
    print(f" INFO: {message}", file=sys.stderr)

def reboot_device(client, host):
    with lock:
        device = client.device(host)
        if device:
            log_info(f"[{datetime.datetime.now()}] Rebooting {device.serial}")
            device.reboot()
        else:
            log_info(f"[{datetime.datetime.now()}] Failed to connect to {host}")

def main():
    log_info("Starting ADB reboot service...")
    if not os.path.exists(CONFIG_PATH):
        log_error("Configuration file not found!")
        sys.exit(1)

    # Load the JSON config
    try:
        with open(CONFIG_PATH, "r") as f:
            config_data = json.load(f)
            config = Config(**config_data)
    except (json.JSONDecodeError, ValidationError) as e:
        log_error(e)
        sys.exit(1)

    # Connect to ADB server
    client = AdbClient(host="127.0.0.1", port=5037)

    # Prepare a job list with croniter for each device
    jobs = []
    now = datetime.datetime.now()
    for item in config.reboot:
        cron = croniter(item.cron, now)
        next_run = cron.get_next(datetime.datetime)
        jobs.append({
            "host": item.host,
            "cron": cron,
            "next_run": next_run
        })

    log_info("Starting cron-based scheduling loop...")
    while True:
        now = datetime.datetime.now()
        for job in jobs:
            if now >= job["next_run"]:
                reboot_device(client, job["host"])
                # Get next scheduled run
                job["next_run"] = job["cron"].get_next(datetime.datetime)
                log_info(f"Next reboot for {job['host']} scheduled for {job['next_run']}")

        time.sleep(1)  # Sleep a bit so we don't burn CPU

if __name__ == "__main__":
    main()
