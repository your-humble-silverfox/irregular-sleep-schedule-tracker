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
        delta_sleep = self.average_sleep - self.config["target_sleep_seconds"]
        delta_awake = self.average_awake - self.config["target_awake_seconds"]

        comparison_result = {
            "average_cycle": average_cycle,
            "target_cycle": target_cycle,
            "delta_sleep": delta_sleep,
            "delta_awake": delta_awake,
            "delta_cycle": delta_cycle,
            "average_sleep": self.average_sleep,
            "average_awake": self.average_awake
        }
        
        # * "// 3600" - в часы, % 3600 // 60 - в минуты *
        average_awake_string = f"{int(abs(self.average_awake // 3600)):02d}:{int((abs(self.average_awake %3600) //60)):02d}"
        average_sleep_string = f"{int(abs(self.average_sleep // 3600)):02d}:{int((abs(self.average_sleep %3600) //60)):02d}"
        average_cycle_string = f"{int(abs(average_cycle // 3600)):02d}:{int((abs(average_cycle%3600)//60)):02d}"

        delta_awake_string = f"{int(delta_awake // 3600):02d}:{int((abs(delta_awake % 3600) // 60)):02d}"
        delta_sleep_string = f"{int(delta_sleep // 3600):02d}:{int((abs(delta_sleep % 3600) // 60)):02d}"
        delta_cycle_string = f"{int(delta_cycle // 3600):02d}:{int((abs(delta_cycle % 3600) // 60)):02d}"

        comparsion_result_string = "\n".join((
            f"В среднем бодрствуешь {average_awake_string}, отклоняешься от цели на {delta_awake_string}",
            f"В среднем спишь {average_sleep_string}, отклоняешься от цели на {delta_sleep_string}",
            f"В среднем цикл {average_cycle_string}, отклоняешься от цели на {delta_cycle_string}"
        ))

        with open('comparison_last_string.txt', 'w') as file:
            file.write(comparsion_result_string)
        
        return comparsion_result_string

    # ? Может быть сделать словарь ?
    # TODO: Добавить логирование данных с целью визуализации
    def window_prediction(self):

        prediction_string = ""

        if self.is_awake:
            predicted_sleep = self.awake_time.addSecs(int(self.average_awake))
            predicted_awake = predicted_sleep.addSecs(int(self.average_sleep))
            
        else:
            predicted_awake = self.sleep_time.addSecs(int(self.average_sleep))
            predicted_sleep = predicted_awake.addSecs(int(self.average_sleep))

        for i in range(7):
            
            awake_day = predicted_awake.toString('d')
            awake_month = predicted_awake.toString('MMMM')
            awake_hour = predicted_awake.toString('hh:mm')

            sleep_day = predicted_sleep.toString('d')
            sleep_month = predicted_sleep.toString('MMMM')
            sleep_hour = predicted_sleep.toString('hh:mm')
            
            prediction_string += (
                f"Проснешься примерно {awake_day} {awake_month} в {awake_hour}, "
                f"будешь активен до {sleep_day} {sleep_month} {sleep_hour} \n"
            )

            predicted_awake = predicted_sleep.addSecs(int(self.average_sleep))
            predicted_sleep = predicted_awake.addSecs(int(self.average_awake))


        with open('prediction_last_string.txt', 'w') as file:
            file.write(prediction_string)

        return prediction_string