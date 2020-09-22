import subprocess
import re
import datetime


def make_session(time):
    activities = {
        "tag": "session",
        "start": time,
        "end": None,
        "activities": dict()
    }
    return activities

def make_activity(NAME):
    activity = {
        "tag": "activity",
        "name": NAME,
        "entries": dict(),
    }
    return activity

def make_entry(START, END):
    s = START.strftime("%Y-%m-%d %H:%M:%S")
    e = END.strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "tag": "entry",
        "start_time": s,
        "end_time": e,
    }
    return entry

def get_active_window_title():
#     WM_WINDOW_ROLE(STRING) = "browser"
    with subprocess.Popen(['xprop', '-root', '_NET_ACTIVE_WINDOW'], stdout=subprocess.PIPE) as root:
        stdout, stderr = root.communicate()
        m = re.search(b'^_NET_ACTIVE_WINDOW.* ([\w]+)\, 0x\w+\n$', stdout)
        if m is None:
            return None
        window_id = m.group(1)
#     just check id
#     if no id in dictionary then look for it 
    with subprocess.Popen(['xprop', '-id', window_id, 'WM_NAME'], stdout=subprocess.PIPE) as window:
        stdout, stderr = window.communicate()
        match = re.match(b"WM_NAME\(\w+\) = (?P<name>.+)$", stdout)
        if match is not None:
            name = match.group("name").strip(b'"').decode("utf-8")
    return name or None

def get_active_window_id():
#     WM_WINDOW_ROLE(STRING) = "browser"
    with subprocess.Popen(['xprop', '-root', '_NET_ACTIVE_WINDOW'], stdout=subprocess.PIPE) as root:
        stdout, stderr = root.communicate()
    m = re.search(b'^_NET_ACTIVE_WINDOW.* ([\w]+)\, 0x\w+\n$', stdout)
    if m is None:
        return None
    window_id = m.group(1)
    return window_id

def get_active_window_title2(ID):
#     if no id in set then look for it 
    with subprocess.Popen(['xprop', '-id', ID, 'WM_NAME'], stdout=subprocess.PIPE) as window:
        stdout, stderr = window.communicate()
    match = re.match(b"WM_NAME\(\w+\) = (?P<name>.+)$", stdout)
    if match is not None:
        name = match.group("name").strip(b'"').decode("utf-8")
    return name or None

def monitor_is_on():
    while True:
        with subprocess.Popen(['xset', 'q'], stdout=subprocess.PIPE) as root:
            stdout, stderr = root.communicate()
            match = re.search(b'Monitor is (?P<status>.+)$', stdout)
            if match is not None:
                status = match.group("status")
                yield status == b'On'
            else:
                yield False

def prepare_session(data):
    today = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    session = make_session(today)
    data[today] = session

    return session

def mytimer():
    return datetime.datetime.now()

def update_activity(activs, name, start, end):
    if name not in activs:
        activs[name] = make_activity(name)

    entries = activs[name]["entries"]
    new_entry_num = len(entries)
    entries[new_entry_num] = make_entry(start, end)
    
def main_loop(activities):
    previous_window_name = 'Desktop'
    start_time = mytimer()
    for _ in range(10): # 60 * 10
        active_window_name = get_active_window_title()
        if previous_window_name != active_window_name:
            end_time = mytimer()
            update_activity(activities, previous_window_name, start_time, end_time)
            start_time = mytimer()
            
            previous_window_name = active_window_name
        sleep(1)
    
    end_time = mytimer()
    update_activity(activities, previous_window_name, start_time, end_time)
    with open("outputs/filename.json", "w") as file:
        json.dump(DATA, file, indent=4)
        
        