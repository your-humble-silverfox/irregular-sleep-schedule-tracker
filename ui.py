import json
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTimeEdit,
    QPushButton,
    QStackedWidget,
    QLineEdit
)
from PyQt6.QtCore import Qt, QDate, QDateTime, QTime
from datetime import datetime, timedelta
from pathlib import Path
import sys
from logic import *
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
import matplotlib.patches as mpatches

# ! Максимально проклятый костыль, нужный во славу нужды, часть первая - константы !
# TODO: Переписать лог прогноза и сравнения с этой шляпы при первой же возможности
LAST_PROGNOSIS_PATH = Path("prediction_last_string.txt")

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
        self.setMinimumSize(800,450)

        self.logic = AppLogic
        
        main_layout = QVBoxLayout(self)

        self.stack = QStackedWidget()

        self.main_page = QWidget()
        self.wakeup_page = QWidget()
        self.sleep_page = QWidget()

        self.stack.addWidget(self.main_page)
        self.stack.addWidget(self.wakeup_page)
        self.stack.addWidget(self.sleep_page)

        self.wokeup_btn = QPushButton("Проснулся")
        self.wokeup_btn.setMinimumHeight(50)
        self.wokeup_btn.clicked.connect(self.wokeup_clicked)

        self.update_stats_btn = QPushButton("Обновить данные")
        self.update_stats_btn.setMinimumHeight(50)
        self.update_stats_btn.clicked.connect(self.update_data)
        

        # ! Максимально проклятый костыль часть 2 - условия !
        # TODO: исправить при первой возможности
        if LAST_PROGNOSIS_PATH.is_file():
            with open(LAST_PROGNOSIS_PATH, 'r') as file:
                label_text = file.read()

            self.assumption = QLabel(label_text)
        else:
            self.assumption = QLabel("Недостаточно данных для прогноза периода активности")

        self.figure = Figure(figsize=(8,2), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumHeight(120)

        self.get_wakeup_time = QTimeEdit()
        self.get_wakeup_time.setDisplayFormat("HH:mm")
        self.handling_wakeup = False
        self.get_wakeup_time.findChild(QLineEdit).returnPressed.connect(self.set_wakeup_time)

        self.get_sleep_time = QTimeEdit()
        self.get_sleep_time.setDisplayFormat("HH:mm")
        self.handling_sleep = False
        self.get_sleep_time.findChild(QLineEdit).returnPressed.connect(self.set_sleep_time)
        
        self.fell_asleep_btn = QPushButton("Уснул")
        self.fell_asleep_btn.setMinimumHeight(50)
        self.fell_asleep_btn.clicked.connect(self.fell_asleep_clicked)

        self.main_screen_buttons = QHBoxLayout()
        self.main_screen_buttons.addWidget(self.wokeup_btn)
        self.main_screen_buttons.addWidget(self.fell_asleep_btn)
        self.main_screen_buttons.addWidget(self.update_stats_btn)
        
        self.main_page.setLayout(QVBoxLayout())
        self.main_page.layout().addWidget(self.canvas)
        self.main_page.layout().addWidget(self.assumption)
        self.main_page.layout().addLayout(self.main_screen_buttons)

        self.logging_buttons_wake = QHBoxLayout()
        self.back_button_wake = QPushButton("Назад")
        self.back_button_wake.clicked.connect(self.back_clicked)
        self.logging_buttons_wake.layout().addWidget(self.back_button_wake)

        self.logging_buttons_sleep = QHBoxLayout()
        self.back_button_sleep = QPushButton("Назад")
        self.back_button_sleep.clicked.connect(self.back_clicked)
        self.logging_buttons_sleep.layout().addWidget(self.back_button_sleep)

        self.wakeup_page.setLayout(QVBoxLayout())
        self.wakeup_entry = QHBoxLayout()
        self.wakeup_entry.addWidget(QLabel("Введи время пробуждения"))
        self.wakeup_entry.addWidget(self.get_wakeup_time)
        self.wakeup_page.layout().addLayout(self.wakeup_entry)
        self.wakeup_page.layout().addLayout(self.logging_buttons_wake)

        self.sleep_page.setLayout(QVBoxLayout())
        self.sleep_entry = QHBoxLayout()
        self.sleep_entry.addWidget(QLabel("Введи время засыпания"))
        self.sleep_entry.addWidget(self.get_sleep_time)
        self.sleep_page.layout().addLayout(self.sleep_entry)
        self.sleep_page.layout().addLayout(self.logging_buttons_sleep)

        main_layout.addWidget(self.stack)
        

    def wokeup_clicked(self):
        self.stack.setCurrentWidget(self.wakeup_page)

    def update_data(self):
        self.logic.load_data()
        self.logic.durations_calculators()
        self.prognosis_string = self.logic.window_prediction()
        self.assumption.setText(self.prognosis_string)
        self.draw_gantt()

    def back_clicked(self):
        self.stack.setCurrentWidget(self.main_page)

    def set_wakeup_time(self):

        if self.handling_wakeup:
            return
        
        
        self.handling_wakeup = True
        current_date = QDate.currentDate()
        current_time = QTime.currentTime()
        wakeup_time = self.get_wakeup_time.time()

        if wakeup_time > current_time:
            current_date = current_date.addDays(-1)
        
        timestamp = QDateTime(current_date,wakeup_time)
        with open("sleep_log.json","r",encoding="UTF-8") as file:
            log = json.load(file)

        log.append({"ts":timestamp.toString(),"type":"wake","source":"manual"})

        with open("sleep_log.json","w",encoding="UTF-8") as file:
            json.dump(log,file,indent=4)
        
        self.stack.setCurrentWidget(self.main_page)
        self.handling_wakeup = False


    def set_sleep_time(self):

        if self.handling_sleep:
            return
        
        self.handling_sleep = True
        current_date = QDate.currentDate()
        current_time = QTime.currentTime()
        sleep_time = self.get_sleep_time.time()

        if sleep_time > current_time:
            current_date = current_date.addDays(-1)
        
        timestamp = QDateTime(current_date,sleep_time)
        with open("sleep_log.json","r",encoding="UTF-8") as file:
            log = json.load(file)

        log.append({"ts":timestamp.toString(),"type":"sleep","source":"manual"})

        with open("sleep_log.json","w",encoding="UTF-8") as file:
            json.dump(log,file,indent=4)
        
        self.stack.setCurrentWidget(self.main_page)
        self.handling_sleep = False


    def fell_asleep_clicked(self):
        self.stack.setCurrentWidget(self.sleep_page)

    # ! VIBE-CODED STUFF !
    def draw_gantt(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        gantt = self.logic.prediction_gantt
        if not gantt or self.logic.awake_time is None:
            ax.text(0.5, 0.5, 'Недостаточно данных', ha='center', va='center',
                    transform=ax.transAxes)
            self.canvas.draw()
            return

        segments = []
        current_awake_start = self.logic.awake_time.toPyDateTime()
        first_sleep = gantt[0]["sleep_start"].toPyDateTime()
        segments.append((current_awake_start, first_sleep, "wake"))

        for i, cycle in enumerate(gantt):
            awake_start = cycle["awake_start"].toPyDateTime()
            sleep_start = cycle["sleep_start"].toPyDateTime()

            if i + 1 < len(gantt):
                next_awake = gantt[i + 1]["awake_start"].toPyDateTime()
                segments.append((sleep_start, next_awake, "sleep"))

            segments.append((awake_start, sleep_start, "wake"))

        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        all_dates = {yesterday}
        for start, end, _ in segments:
            for day, _, _ in self._split_across_days(start, end):
                all_dates.add(day)
        all_dates = sorted(all_dates)        

        all_dates = sorted(d for d in all_dates if d >= yesterday)

        date_to_y = {d: i for i, d in enumerate(all_dates)}

        bar_height = 0.6
        bar_bottom = 0.2
        colors = {"wake": "#C2C7DB", "sleep": "#A56AE7"}

        for start, end, kind in segments:
            for day, day_start_frac, day_end_frac in self._split_across_days(start, end):
                if day < yesterday:      # ← ignore anything older than yesterday
                    continue
                y_pos = date_to_y[day]
                ax.broken_barh(
                    [(day_start_frac, day_end_frac - day_start_frac)],
                    (y_pos + bar_bottom, bar_height),
                    facecolors=colors[kind]
                )

        def label_for(d):
            if d == yesterday:
                return "Вчера"
            if d == today:
                return "Сегодня"
            return d.strftime('%a %d %b')

        ax.set_yticks(list(date_to_y.values()))
        ax.set_yticklabels([label_for(d) for d in all_dates])
        ax.set_ylim(-0.2, len(all_dates) - 0.2)
        ax.invert_yaxis()

        hour_ticks = [h / 24 for h in range(0, 25, 2)]
        hour_labels = [f"{h:02d}:00" for h in range(0, 25, 2)]
        ax.set_xticks(hour_ticks)
        ax.set_xticklabels(hour_labels, fontsize=7)
        ax.set_xlim(0.0, 1.0)

        self.figure.subplots_adjust(top=0.82)
        ax.legend(
            handles=[
                mpatches.Patch(color='#C2C7DB', label='Бодрствование'),
                mpatches.Patch(color='#A56AE7', label='Сон'),
            ],
            loc='lower center', bbox_to_anchor=(0.5, 1.02),
            ncol=2, fontsize=8, frameon=False
        )
        ax.grid(axis='x', linestyle='--', alpha=0.4)

        self.canvas.draw()

    def _split_across_days(self, start: datetime, end: datetime):
        from datetime import timedelta

        current = start
        while current.date() < end.date():
            midnight = datetime(current.year, current.month, current.day) + timedelta(days=1)
            start_frac = (current.hour * 3600 + current.minute * 60 + current.second) / 86400
            end_frac = 1.0
            yield current.date(), start_frac, end_frac
            current = midnight

        start_frac = (current.hour * 3600 + current.minute * 60 + current.second) / 86400
        end_frac = (end.hour * 3600 + end.minute * 60 + end.second) / 86400
        yield current.date(), start_frac, end_frac