import json
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTimeEdit,
    QPushButton,
    QStackedWidget
)
from PyQt6.QtCore import Qt, QDate, QDateTime, QTime
from datetime import datetime
from pathlib import Path
import sys
from logic import *

class ConfigWindow(QWidget):
    def __init__(self, switch_to_main, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.switch_to_main = switch_to_main
        self.setWindowTitle("Настройка Трекера Нерегулярного Сна")
        self.setMinimumSize(400,200)
        input_layout = QVBoxLayout()
        layout = QVBoxLayout(self)

        self.target_sleep_time_input = QTimeEdit()
        self.target_sleep_time_input.setDisplayFormat("HH:mm")
        self.target_sleep_time_input.editingFinished.connect(lambda: self.tolerance_input.setFocus())

        self.target_awake_time_input = QTimeEdit()
        self.target_awake_time_input.setDisplayFormat("HH:mm")
        self.target_awake_time_input.editingFinished.connect(lambda: self.target_sleep_time_input.setFocus())
        
        self.tolerance_input = QTimeEdit()
        self.tolerance_input.setDisplayFormat("HH:mm")
        self.tolerance_input.editingFinished.connect(self.continue_clicked)

        awake = QHBoxLayout()
        awake.addWidget(QLabel("Желаемое длина бодрствования:"))
        awake.addWidget(self.target_awake_time_input)

        sleep = QHBoxLayout()
        sleep.addWidget(QLabel("Желаемое время сна:"))
        sleep.addWidget(self.target_sleep_time_input)

        tolerance = QHBoxLayout()
        tolerance.addWidget(QLabel("Максимально допустимое отклонение автодогадок:"))
        tolerance.addWidget(self.tolerance_input)
        
        input_layout.addLayout(awake)
        input_layout.addLayout(sleep)
        input_layout.addLayout(tolerance)

        continue_btn = QPushButton("Сохранить настройки")
        continue_btn.setMinimumHeight(50)
        continue_btn.clicked.connect(self.continue_clicked)

        layout.addWidget(QLabel("Введите конфигурационные параметры"),alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(input_layout)
        layout.addStretch()
        layout.addWidget(continue_btn)

        self.setTabOrder(self.target_awake_time_input, self.target_sleep_time_input)
        self.setTabOrder(self.target_sleep_time_input, self.tolerance_input)
        self.setTabOrder(self.tolerance_input, continue_btn)

    def continue_clicked(self):
        start_time = datetime.now()
        config = {
            "target_sleep_time": self.target_sleep_time_input.time().toString(),
            "target_sleep_seconds": (((self.target_sleep_time_input.time().hour() * 60) + self.target_sleep_time_input.time().minute())*60),
            "target_awake_time": self.target_awake_time_input.time().toString(),
            "target_awake_seconds": (((self.target_awake_time_input.time().hour() * 60) + self.target_awake_time_input.time().minute())*60),
            "tolerance":(((self.tolerance_input.time().hour()*60) + self.tolerance_input.time().minute())*60)
        }

        with open("config.json","w",encoding="UTF-8") as file:
            json.dump(config,file,indent=4)
        
        initial_data = []

        with open("sleep_log.json","w",encoding="UTF-8") as file:
            json.dump(initial_data,file,indent=4)

        self.switch_to_main()

class MainWindow(QWidget, AppLogic):
    def __init__(self, AppLogic, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Трекер Нерегулярного Сна")
        self.setMinimumSize(600,350)

        self.logic = AppLogic
        
        main_layout = QVBoxLayout(self)

        self.stack = QStackedWidget()

        self.main_page = QWidget()
        self.wakeup_page = QWidget()

        self.stack.addWidget(self.main_page)
        self.stack.addWidget(self.wakeup_page)

        self.wokeup_btn = QPushButton("Проснулся")
        self.wokeup_btn.setMinimumHeight(50)
        self.wokeup_btn.clicked.connect(self.wokeup_clicked)

        self.update_stats_btn = QPushButton("Обновить данные")
        self.update_stats_btn.setMinimumHeight(50)
        self.update_stats_btn.clicked.connect(self.update_data)

        self.assumption = QLabel("Недостаточно данных для прогноза периода активности")

        self.actual_v_target = QLabel("Недостаточно данных для сравнения с целевыми значениями")

        self.get_wakeup_time = QTimeEdit()
        self.get_wakeup_time.setDisplayFormat("HH:mm")
        self.handling_wakeup = False
        self.get_wakeup_time.editingFinished.connect(self.set_wakeup_time)
        
        self.fell_asleep_btn = QPushButton("Уснул")
        self.fell_asleep_btn.setMinimumHeight(50)
        self.fell_asleep_btn.clicked.connect(self.fell_asleep_clicked)

        self.main_screen_buttons = QHBoxLayout()
        self.main_screen_buttons.addWidget(self.wokeup_btn)
        self.main_screen_buttons.addWidget(self.fell_asleep_btn)
        self.main_screen_buttons.addWidget(self.update_stats_btn)
        
        self.main_page.setLayout(QVBoxLayout())
        self.main_page.layout().addWidget(self.assumption)
        self.main_page.layout().addWidget(self.actual_v_target)
        self.main_page.layout().addLayout(self.main_screen_buttons)

        self.wakeup_page.setLayout(QHBoxLayout())
        self.wakeup_page.layout().addWidget(QLabel("Введи время пробуждения"))
        self.wakeup_page.layout().addWidget(self.get_wakeup_time)

        main_layout.addWidget(self.stack)
        
    def switch_to_wakeup(self):
        self.stack.setCurrentWidget(self.wakeup_page)

    def wokeup_clicked(self):
        self.switch_to_wakeup()

    def update_data(self):
        self.logic.load_data()
        self.logic.durations_calculators()
        data = self.logic.drift_calculator()
        # «Спишь в среднем 11ч42м (-18м от цели), 
        # бодрствуешь 16ч15м (+15м). Цикл 27ч57м, 
        # убегаешь на +3ч57м каждые сутки».  
        prediction = self.logic.window_prediction()

        # TODO: переписать созданиме этой строки по аналогии с prediction
        drift_string = f"В среднем цикл {abs(int(data["average_cycle"])//3600):02d}:{(abs(int(data["average_cycle"])%3600)//60):02d}, отклоняешься от цели на {int(data["delta_cycle"])//3600:02d}:{(abs(int(data["delta_cycle"])%3600)//60):02d} \nВ среднем спишь {abs(int(data["average_sleep"])//3600):02d}:{(abs(int(data["average_sleep"])%3600)//60):02d}, отклоняешься от цели на {int(data["delta_sleep"])//3600:02d}:{(abs(int(data["delta_sleep"])%3600)//60):02d} \nВ среднем бодрствуешь {abs(int(data["average_awake"])//3600):02d}:{(abs(int(data["average_awake"])%3600)//60):02d}, отклоняешься от цели на {int(data["delta_awake"]//3600):02d}:{(abs(int(data["delta_awake"])%3600)//60):02d}"
        self.actual_v_target.setText(drift_string)
        self.assumption.setText(prediction)

    def set_wakeup_time(self):

        if self.handling_wakeup:
            return
        
        else:
            self.handling_wakeup = True
            current_date = QDate.currentDate()
            wakeup_time = self.get_wakeup_time.time()
            
            timestamp = QDateTime(current_date,wakeup_time)
            with open("sleep_log.json","r",encoding="UTF-8") as file:
                log = json.load(file)

            log.append({"ts":timestamp.toString(),"type":"wake","source":"manual"})

            with open("sleep_log.json","w",encoding="UTF-8") as file:
                json.dump(log,file,indent=4)
            
            self.handling_wakeup = False
            self.stack.setCurrentWidget(self.main_page)

    def fell_asleep_clicked(self):
        current_date = QDate.currentDate()
        current_time = QTime.currentTime()

        timestamp = QDateTime(current_date,current_time)

        with open("sleep_log.json","r",encoding="UTF-8") as file:
                log = json.load(file)

        log.append({"ts":timestamp.toString(),"type":"sleep","source":"manual"})

        with open("sleep_log.json","w",encoding="UTF-8") as file:
            json.dump(log,file,indent=4)