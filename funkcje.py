import subprocess
import re
import datetime
from time import sleep
import json
# from collections import defaultdict


class Timer:
    def __init__(self, sleeping_time):
        self.session = Timer._make_session()
        self.previous_window_name = "Desktop"
        self.active_window_name = Timer._get_active_window_name()
        self.saved_seconds_ago = datetime.timedelta(minutes=10)
        self.sleeping_time = datetime.timedelta(seconds=sleeping_time)
        self.time_diff_between_savings = datetime.timedelta()
        self.end_time = None
        self.start_time = Timer._my_timer()
        delta = self.start_time - datetime.datetime(1970, 1, 1)
        self.id = int(delta.total_seconds())

    @staticmethod
    def _make_session():
        activities = {
            "tag": "session",
            "start": datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
            "end": datetime.datetime.today(),
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
            while True:
                while next(_monitor_is_on) and self.time_limit_not_exceeded():
                    if self.window_changed():
                        self._update_activity()
                self._save_output()
                while not next(_monitor_is_on):
                    sleep(10)
        except KeyboardInterrupt:
            self._update_activity()
            self.session["end"] = Timer._my_timer()
            self._save_output()

    def time_limit_not_exceeded(self):
        self.saved_seconds_ago += self.sleeping_time
        return not self.saved_seconds_ago > self.time_diff_between_savings

    def _save_output(self):
        filename = " - ".join((self.id, self.end_time.strftime("%Y-%m-%d %H:%M:%S")))
        with open(f"outputs/{filename}.json", "w") as file:
            json.dump(self.session, file, indent=4)
        self.session["activities"].clear()

    def window_changed(self):
        self.active_window_name = Timer._get_active_window_name()
        return self.previous_window_name != self.active_window_name

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

            sleep(self.sleeping_time.seconds)


if __name__ == "__main__":
    T = Timer(3)
    T.main_loop()
