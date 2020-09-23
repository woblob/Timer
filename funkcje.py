import subprocess
import re
import datetime
from time import sleep
import json
# from collections import defaultdict


class Timer:
    def __init__(self, sleeping_time):
        self.today = datetime.datetime.today()
        self.session = self._make_session()
        self.previous_window_name = "Desktop"
        self.active_window_name = Timer._get_active_window_name()
        self.start_time = None
        self.end_time = None
        self.sleeping_time = sleeping_time

    # @property
    # def active_window_name(self):
    #     return Timer._get_active_window_name()
    #
    # @active_window_name.setter
    # def active_window_name(self, val):
    #     self.active_window_name = val

    def _make_session(self):
        activities = {
            "tag": "session",
            "start": self.today.strftime("%Y-%m-%d %H:%M:%S"),
            "end": None,
            "activities": dict()
        }
        return activities

    @staticmethod
    def _make_activity(name):
        activity = {
            "tag": "activity",
            "name": name,
            "entries": [],
        }
        return activity

    def _make_entry(self):
        self.end_time = Timer._my_timer()
        entry = {
            "tag": "entry",
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.start_time = Timer._my_timer()
        return entry

    def _update_activity(self):
        activities = self.session["activities"]
        pwn = self.previous_window_name
        if pwn not in activities:
            activities[pwn] = Timer._make_activity(pwn)

        new_entry = self._make_entry()
        activities[pwn]["entries"].append(new_entry)
        self.previous_window_name = self.active_window_name

    def main_loop(self):
        self.start_time = Timer._my_timer()
        try:
            _monitor_is_on = self._monitor_is_on()
            while next(_monitor_is_on):
                self.active_window_name = Timer._get_active_window_name()
                if self.previous_window_name != self.active_window_name:
                    self._update_activity()

        except KeyboardInterrupt:
            self._update_activity()
            self._save_output()

    def _save_output(self):
        filename = self.end_time
        with open(f"outputs/{filename}.json", "w") as file:
            json.dump(self.session, file, indent=4)

    @staticmethod
    def _my_timer():
        return datetime.datetime.now()

    @staticmethod
    def _get_active_window_name():
        window_id = Timer._get_active_window_id()
        name = Timer._get_window_name(window_id)
        return name

    @staticmethod
    def _get_active_window_id():
        with subprocess.Popen(['xprop', '-root', '_NET_ACTIVE_WINDOW'],
                              stdout=subprocess.PIPE) as root:
            stdout, stderr = root.communicate()
        m = re.search(b'^_NET_ACTIVE_WINDOW.* (\w+), 0x\w+\n$', stdout)
        if m is None:
            return None
        window_id = m.group(1)
        return window_id

    @staticmethod
    def _get_window_name(id_num):
        with subprocess.Popen(['xprop', '-id', id_num, 'WM_NAME'],
                              stdout=subprocess.PIPE) as window:
            stdout, stderr = window.communicate()
        match = re.match(b"WM_NAME\(\w+\) = (?P<name>.+)$", stdout)
        if match is not None:
            name = match.group("name").strip(b'"').decode("utf-8")
            return name or None
        return None

    def _monitor_is_on(self):
        while True:
            with subprocess.Popen(['xset', 'q'],
                                  stdout=subprocess.PIPE) as xset_dpms:
                stdout, stderr = xset_dpms.communicate()
            match = re.search(b'Monitor is (?P<status>.+)$', stdout)
            if match is not None:
                status = match.group("status")
                yield status == b'On'
            else:
                yield False

            sleep(self.sleeping_time)

if __name__ == "__main__":
    T = Timer(3)
    T.main_loop()