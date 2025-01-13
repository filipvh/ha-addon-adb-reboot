import json
import os
import socket
import subprocess
import sys
import threading
import time
import datetime

from croniter import croniter
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

def is_valid_host(host):
    """
    Checks if the provided string is a valid IP address or hostname.
    """
    try:
        # Try to resolve the host (works for both IP and hostname)
        socket.gethostbyname(host)
        return True
    except socket.gaierror:
        return False

def reboot_device(host):
    if not is_valid_host(host):
        print(f"{host} is not a valid hostname or IP.")
        return
    with lock:
        try:
            # Build the adb command
            command_c = ["adb", "connect", f"{host}:5555"]
            command_r = ["adb", "-s", f"{host}:5555", "reboot"]
            command_d = ["adb", "disconnect"]

            # Execute the command
            subprocess.run(command_c, check=True)
            subprocess.run(command_r, check=True)
            subprocess.run(command_d, check=True)
            print(f"Reboot command sent to {host}.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to reboot {host}: {e}")
        except FileNotFoundError:
            print("adb not found. Make sure it's installed and in your PATH.")

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


    # Prepare a job list with croniter for each device
    jobs = []
    now = datetime.datetime.now()
    for item in config.reboot:
        cron = croniter(item.cron, now)
        next_run = cron.get_next(datetime.datetime)
        log_info(f"Next reboot for {item.host} scheduled for {next_run}")
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
                reboot_device(job["host"])
                # Get next scheduled run
                job["next_run"] = job["cron"].get_next(datetime.datetime)
                log_info(f"Next reboot for {job['host']} scheduled for {job['next_run']}")

        time.sleep(1)  # Sleep a bit so we don't burn CPU

if __name__ == "__main__":
    main()
