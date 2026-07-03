from ui import *
import sys
from PyQt6.QtWidgets import QApplication, QStackedWidget
from pathlib import Path
from logic import AppLogic

CONFIG_PATH = Path("config.json")

app = QApplication(sys.argv)

stack = QStackedWidget()
logic = AppLogic()
main_window = MainWindow(AppLogic=logic)

def switch_to_main():
    stack.setCurrentWidget(main_window)
    main_window.switch_to_wakeup()

config_window = ConfigWindow(switch_to_main=switch_to_main)

stack.addWidget(config_window)
stack.addWidget(main_window)
if CONFIG_PATH.is_file():
    stack.setCurrentWidget(main_window)
else:
    stack.setCurrentWidget(config_window)

stack.setWindowTitle("Трекер Нерегулярного Цикла Сна")
stack.show()

sys.exit(app.exec())