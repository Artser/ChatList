import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Минимальное PyQt приложение")
        self.setGeometry(100, 100, 400, 300)
        
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Создаем layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Добавляем метку
        label = QLabel("Привет, это минимальное PyQt приложение!")
        label.setStyleSheet("font-size: 16px; padding: 20px;")
        layout.addWidget(label)
        
        # Добавляем кнопку
        button = QPushButton("Нажми меня!")
        button.setStyleSheet("font-size: 14px; padding: 10px;")
        button.clicked.connect(self.on_button_clicked)
        layout.addWidget(button)
        
    def on_button_clicked(self):
        print("Кнопка была нажата!")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

