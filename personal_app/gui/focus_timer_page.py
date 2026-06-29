from PySide6.QtCore import QTimer
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QLineEdit, QPushButton

from personal_app.gui.widgets import Compartment, subtle_button


class FocusTimerPage(Compartment):
    def __init__(self) -> None:
        super().__init__("Focus Timer", "A simple egg timer for focused work sessions.", "Focus Timer")
        self.seconds_left = 25 * 60
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.tick)

        duration_row = QHBoxLayout()
        duration_row.addWidget(QLabel("Minutes"))
        self.minutes = QLineEdit("25")
        self.minutes.setValidator(QIntValidator(1, 180, self))
        self.minutes.setMaximumWidth(64)
        self.minutes.editingFinished.connect(self.reset)
        duration_row.addWidget(self.minutes)
        duration_row.addStretch(1)

        self.clock = QLabel()
        self.clock.setObjectName("FocusClock")
        self.clock.setMinimumHeight(70)

        controls = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.pause_button = subtle_button("Pause")
        reset_button = subtle_button("Reset")
        self.start_button.clicked.connect(self.start)
        self.pause_button.clicked.connect(self.pause)
        reset_button.clicked.connect(self.reset)
        controls.addWidget(self.start_button)
        controls.addWidget(self.pause_button)
        controls.addWidget(reset_button)
        controls.addStretch(1)

        self.layout.addLayout(duration_row)
        self.layout.addWidget(self.clock, 1)
        self.layout.addLayout(controls)
        self._update_clock()

    def start(self) -> None:
        if self.seconds_left <= 0:
            self.reset()
        self.timer.start()
        self.start_button.setEnabled(False)

    def pause(self) -> None:
        self.timer.stop()
        self.start_button.setEnabled(True)

    def reset(self) -> None:
        self.timer.stop()
        try:
            minutes = max(1, min(180, int(self.minutes.text())))
        except ValueError:
            minutes = 25
        self.minutes.setText(str(minutes))
        self.seconds_left = minutes * 60
        self.start_button.setEnabled(True)
        self._update_clock()

    def tick(self) -> None:
        self.seconds_left = max(0, self.seconds_left - 1)
        self._update_clock()
        if self.seconds_left == 0:
            self.pause()
            QApplication.beep()
            self.clock.setText("Time complete")

    def _update_clock(self) -> None:
        minutes, seconds = divmod(self.seconds_left, 60)
        self.clock.setText(f"{minutes:02d}:{seconds:02d}")
