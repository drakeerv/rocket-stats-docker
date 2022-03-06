import subprocess
import threading
import psutil
import time
import git
import sys
import os

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

lock = threading.Lock()
threads = []
server_process = None
build_process = None

#internal db

def check_for_updates(repo, lock):
    lock.acquire()
    print(f"Starting {repo['name']} Loop")

    if not os.path.exists(repo["path"]): os.makedirs(repo["path"])

    if not os.path.exists(os.path.join(repo["path"], ".git")) and len(os.listdir(repo["path"])) == 0:
        origin = git.Repo.clone_from(repo["url"], repo["path"]).remotes.origin
        repo["init_callback"]()
    else:
        origin = git.Repo(repo["path"]).remotes.origin
        repo["exist_callback"]()

    repo["start_callback"]()
    lock.release()

    while True:
        fetch = origin.fetch()[0]
        if fetch.old_commit != None:
            print(f"Read new code on {repo['name']}")
            repo["pull_callback"](origin)

        time.sleep(10)

def run_repo(repo, command):
    begin_dir = os.getcwd()

    if not os.path.exists(repo["path"]): os.makedirs(repo["path"])
    os.chdir(repo["path"])
    process = psutil.Process(subprocess.Popen(command, shell=True).pid)
    os.chdir(begin_dir)

    return process

def read_file_repo(repo, file):
    begin_dir = os.getcwd()

    if not os.path.exists(repo["path"]): os.makedirs(repo["path"])
    os.chdir(repo["path"])
    with open(file, "r") as file: data = file.read()
    os.chdir(begin_dir)

    return data

def install_server():
    global repos

    if "server" in repos.keys():
        process = run_repo(repos["server"], f"pip3 install -r requirements.txt")

    while not process.status() == psutil.STATUS_ZOMBIE:
        time.sleep(1)

    if process.is_running():
        process.kill()

def start_server():
    global server_process, repos

    if server_process == None and "server" in repos.keys():
        server_process = run_repo(repos["server"], f"{sys.executable} main.py")

def stop_server():
    global server_process

    if server_process != None and server_process.is_running():
        server_process.kill()
        server_process = None

def install_build():
    global repos

    if "client" in repos.keys():
        process = run_repo(repos["client"], "npm i")

    while process.is_running():
        time.sleep(1)

def init_build():
    install_build()
    start_build()

def start_build():
    global build_process, repos

    if build_process == None and "client" in repos.keys():
        build_process = run_repo(repos["client"], "npm run build")

def stop_build():
    global build_process

    if build_process != None and build_process.is_running():
        build_process.kill()
        build_process = None

def server_callback(origin):
    global repos

    print("Restarting Server")
    stop_server()

    data = read_file_repo(repos["server"], "requirements.txt")
    origin.pull()
    if read_file_repo(repos["server"], "requirements.txt") != data: install_build()

    print("Starting Server")
    start_server()

def client_callback(origin):
    global repos

    print("Building Client")

    data = read_file_repo(repos["client"], "package.json")
    origin.pull()
    if read_file_repo(repos["client"], "package.json") != data: install_build()

    start_build()

repos = {
    "server": {
        "name": "Server",
        "url": "https://github.com/drakeerv/rocket-stats-server.git",
        "path": os.path.join(CURRENT_PATH, "app/server"),
        "init_callback": install_server,
        "exist_callback": lambda: None,
        "start_callback": start_server,
        "pull_callback": server_callback
    },
    "client" : {
        "name": "Client",
        "url": "https://github.com/drakeerv/rocket-stats-client.git",
        "path": os.path.join(CURRENT_PATH, "app/server/client"),
        "init_callback": init_build,
        "exist_callback": lambda: None,
        "start_callback": lambda: None,
        "pull_callback": client_callback,
    }
}

for repo in repos.values():
    thread = threading.Thread(target=check_for_updates, args=[repo, lock], daemon=True, name=repo["name"])
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()