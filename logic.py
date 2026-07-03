import json
from PyQt6.QtCore import QDateTime


class AppLogic():
    def __init__(self):
        
        self.config = None
        self.log = None
        self.sleep_durations = []
        self.awake_durations = []
        self.average_sleep = None
        self.average_awake = None
        self.awake_time = None
        self.sleep_time = None
        self.is_awake = True
        self.sleep_found = False

    def load_data(self):
        try:
            with open("config.json", "r", encoding="UTF-8") as file:
                self.config = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = None

        try:
            with open("sleep_log.json", "r", encoding="UTF-8") as file:
                self.log = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.log = []


    def durations_calculators(self):    
        for index, item in enumerate(self.log):
            if item["type"] == "wake":
                self.awake_time = QDateTime.fromString(item["ts"])
                if self.sleep_time != None and self.sleep_time < self.awake_time:
                    self.sleep_durations.append(self.sleep_time.secsTo(self.awake_time))
            else:
                self.sleep_found = True
                self.sleep_time = QDateTime.fromString(item["ts"])
                self.awake_durations.append(self.awake_time.secsTo(self.sleep_time))
                if index == (len(self.log) - 1):
                    self.is_awake = False

    def drift_calculator(self):
        if self.sleep_found == False:
            return "Нет записей сна"
        if self.sleep_durations:
            self.average_sleep = sum(self.sleep_durations)/len(self.sleep_durations)
        else:
            self.average_sleep = 0
        if self.awake_durations:
            self.average_awake = sum(self.awake_durations)/len(self.awake_durations)
        else:
            self.average_awake = 0
        average_cycle = self.average_awake+self.average_sleep
        target_cycle = self.config["target_sleep_seconds"]+self.config["target_awake_seconds"]
        delta_cycle = average_cycle - target_cycle
        detla_sleep = self.average_sleep - self.config["target_sleep_seconds"]
        delta_awake = self.average_awake - self.config["target_awake_seconds"]

        comparison_result = {
            "average_cycle": average_cycle,
            "target_cycle": target_cycle,
            "delta_sleep": detla_sleep,
            "delta_awake": delta_awake,
            "delta_cycle": delta_cycle,
            "average_sleep": self.average_sleep,
            "average_awake": self.average_awake
        }

        return comparison_result

    
    def window_prediction(self):
        if self.is_awake:
            predicted_sleep = self.awake_time.addSecs(self.average_awake)
            return predicted_sleep
        else:
            predicted_awake = self.sleep_time.addSecs(self.average_sleep)
            return predicted_awake
