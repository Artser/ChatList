"""
Основной модуль приложения ChatList.
Содержит главное окно и весь пользовательский интерфейс.
"""
import sys
import json
import os
from typing import List, Dict, Optional, Tuple
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QCheckBox, QComboBox, QLabel, QTabWidget, QMessageBox,
    QDialog, QDialogButtonBox, QFormLayout, QProgressBar, QHeaderView,
    QMenu, QAction, QFileDialog, QInputDialog, QRadioButton, QButtonGroup,
    QSpinBox, QGroupBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

import db
import models
import network
import prompt_improver
import version
import logging

logger = logging.getLogger(__name__)


class RequestThread(QThread):
    """Поток для асинхронной отправки запросов к API."""
    finished = pyqtSignal(list)  # Список результатов
    
    def __init__(self, prompt: str, models_list: List[Dict]):
        super().__init__()
        self.prompt = prompt
        self.models_list = models_list
    
    def run(self):
        """Выполняет запросы к моделям."""
        results = network.send_prompt_to_models_async(self.prompt, self.models_list)
        self.finished.emit(results)


class PromptDialog(QDialog):
    """Диалог для добавления/редактирования промта."""
    
    def __init__(self, parent=None, prompt_data: Optional[Dict] = None):
        super().__init__(parent)
        self.prompt_data = prompt_data
        self.setWindowTitle("Редактировать промт" if prompt_data else "Создать промт")
        self.setMinimumSize(500, 300)
        
        layout = QVBoxLayout()
        
        # Поле для промта
        prompt_label = QLabel("Промт:")
        prompt_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(prompt_label)
        
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("Введите текст промта...")
        if prompt_data:
            self.prompt_edit.setText(prompt_data.get('prompt', ''))
        layout.addWidget(self.prompt_edit)
        
        # Поле для тегов
        tags_label = QLabel("Теги (через запятую):")
        layout.addWidget(tags_label)
        
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("например: наука, физика")
        if prompt_data:
            self.tags_edit.setText(prompt_data.get('tags', ''))
        layout.addWidget(self.tags_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_data(self) -> Tuple[str, Optional[str]]:
        """Возвращает данные промта из формы: (prompt, tags)."""
        prompt = self.prompt_edit.toPlainText().strip()
        tags = self.tags_edit.text().strip() or None
        return prompt, tags


class ModelDialog(QDialog):
    """Диалог для добавления/редактирования модели."""
    
    def __init__(self, parent=None, model_data: Optional[Dict] = None):
        super().__init__(parent)
        self.model_data = model_data
        self.setWindowTitle("Редактировать модель" if model_data else "Добавить модель")
        self.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.api_url_edit = QLineEdit()
        self.api_id_edit = QLineEdit()
        self.is_active_checkbox = QCheckBox()
        self.is_active_checkbox.setChecked(True)
        
        layout.addRow("Название:", self.name_edit)
        layout.addRow("API URL:", self.api_url_edit)
        layout.addRow("API ID (переменная окружения):", self.api_id_edit)
        layout.addRow("Активна:", self.is_active_checkbox)
        
        if model_data:
            self.name_edit.setText(model_data.get('name', ''))
            self.api_url_edit.setText(model_data.get('api_url', ''))
            self.api_id_edit.setText(model_data.get('api_id', ''))
            self.is_active_checkbox.setChecked(bool(model_data.get('is_active', 1)))
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def get_data(self) -> Dict:
        """Возвращает данные модели из формы."""
        return {
            'name': self.name_edit.text().strip(),
            'api_url': self.api_url_edit.text().strip(),
            'api_id': self.api_id_edit.text().strip(),
            'is_active': 1 if self.is_active_checkbox.isChecked() else 0
        }


class ImprovementThread(QThread):
    """Поток для асинхронного улучшения промта."""
    finished = pyqtSignal(str, str)  # improved_prompt, error
    
    def __init__(self, original_prompt: str, model_data: Dict):
        super().__init__()
        self.original_prompt = original_prompt
        self.model_data = model_data
    
    def run(self):
        """Выполняет улучшение промта."""
        improved, error = prompt_improver.improve_prompt(
            self.original_prompt,
            self.model_data.get('name', 'Unknown'),
            self.model_data
        )
        self.finished.emit(improved or '', error or '')


class PromptImprovementDialog(QDialog):
    """Диалог для улучшения промта с помощью AI."""
    
    def __init__(self, parent=None, original_prompt: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Улучшить промт")
        self.setMinimumSize(700, 600)
        self.original_prompt = original_prompt
        self.improved_prompt = ""
        self.model_used = None
        
        layout = QVBoxLayout()
        
        # Исходный промт (read-only)
        original_label = QLabel("Исходный промт:")
        original_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(original_label)
        
        self.original_edit = QTextEdit()
        self.original_edit.setReadOnly(True)
        self.original_edit.setPlainText(original_prompt)
        self.original_edit.setMaximumHeight(150)
        layout.addWidget(self.original_edit)
        
        # Выбор модели для улучшения
        model_layout = QHBoxLayout()
        model_label = QLabel("Модель для улучшения:")
        self.model_combo = QComboBox()
        self.load_models()
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        layout.addLayout(model_layout)
        
        # Кнопка "Улучшить"
        self.improve_button = QPushButton("Улучшить")
        self.improve_button.clicked.connect(self.start_improvement)
        layout.addWidget(self.improve_button)
        
        # Индикатор загрузки
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)
        
        # Улучшенный промт (редактируемый)
        improved_label = QLabel("Улучшенный промт:")
        improved_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(improved_label)
        
        self.improved_edit = QTextEdit()
        self.improved_edit.setPlaceholderText("Здесь появится улучшенная версия промта...")
        layout.addWidget(self.improved_edit)
        
        # Кнопки действий
        buttons_layout = QHBoxLayout()
        
        self.use_improved_button = QPushButton("Использовать улучшенный")
        self.use_improved_button.clicked.connect(self.use_improved)
        self.use_improved_button.setEnabled(False)
        buttons_layout.addWidget(self.use_improved_button)
        
        self.save_both_button = QPushButton("Сохранить оба варианта")
        self.save_both_button.clicked.connect(self.save_both)
        self.save_both_button.setEnabled(False)
        buttons_layout.addWidget(self.save_both_button)
        
        buttons_layout.addStretch()
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def load_models(self):
        """Загружает активные модели в выпадающий список."""
        active_models = db.get_active_models()
        self.model_combo.clear()
        for model in active_models:
            self.model_combo.addItem(model['name'], model)
        
        if not active_models:
            self.improve_button.setEnabled(False)
            self.progress_label.setText("Нет активных моделей для улучшения")
    
    def start_improvement(self):
        """Запускает процесс улучшения промта."""
        if not self.original_prompt.strip():
            QMessageBox.warning(self, "Ошибка", "Исходный промт не может быть пустым")
            return
        
        model_data = self.model_combo.currentData()
        if not model_data:
            QMessageBox.warning(self, "Ошибка", "Выберите модель для улучшения")
            return
        
        # Блокируем кнопку и показываем прогресс
        self.improve_button.setEnabled(False)
        self.progress_label.setText("Улучшение промта... Пожалуйста, подождите.")
        self.model_used = model_data['name']
        
        # Запускаем поток для улучшения
        self.improvement_thread = ImprovementThread(self.original_prompt, model_data)
        self.improvement_thread.finished.connect(self.on_improvement_finished)
        self.improvement_thread.start()
    
    def on_improvement_finished(self, improved_prompt: str, error: str):
        """Обработчик завершения улучшения промта."""
        self.improve_button.setEnabled(True)
        
        if error:
            self.progress_label.setText(f"Ошибка: {error}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось улучшить промт:\n{error}")
            return
        
        if not improved_prompt:
            self.progress_label.setText("Получен пустой ответ")
            QMessageBox.warning(self, "Ошибка", "Получен пустой ответ от модели")
            return
        
        # Отображаем улучшенный промт
        self.improved_prompt = improved_prompt
        self.improved_edit.setPlainText(improved_prompt)
        self.progress_label.setText("Промт успешно улучшен!")
        
        # Активируем кнопки
        self.use_improved_button.setEnabled(True)
        self.save_both_button.setEnabled(True)
    
    def use_improved(self):
        """Использует улучшенный промт (заменяет исходный)."""
        improved = self.improved_edit.toPlainText().strip()
        if not improved:
            QMessageBox.warning(self, "Ошибка", "Улучшенный промт не может быть пустым")
            return
        
        self.improved_prompt = improved
        self.accept()
    
    def save_both(self):
        """Сохраняет оба варианта промта в БД."""
        improved = self.improved_edit.toPlainText().strip()
        if not improved:
            QMessageBox.warning(self, "Ошибка", "Улучшенный промт не может быть пустым")
            return
        
        # Сохраняем исходный промт
        prompt_id = db.create_prompt(self.original_prompt)
        
        # Сохраняем улучшенную версию в историю
        db.create_prompt_version(prompt_id, improved, self.model_used)
        
        self.improved_prompt = improved
        QMessageBox.information(self, "Успех", "Оба варианта промта сохранены")
        self.accept()
    
    def get_improved_prompt(self) -> str:
        """Возвращает улучшенный промт."""
        return self.improved_prompt


class SettingsDialog(QDialog):
    """Диалог настроек приложения."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Группа "Тема"
        theme_group = QGroupBox("Тема оформления")
        theme_layout = QVBoxLayout()
        
        self.theme_group = QButtonGroup()
        self.light_theme_radio = QRadioButton("Светлая тема")
        self.dark_theme_radio = QRadioButton("Темная тема")
        
        self.theme_group.addButton(self.light_theme_radio, 0)
        self.theme_group.addButton(self.dark_theme_radio, 1)
        
        theme_layout.addWidget(self.light_theme_radio)
        theme_layout.addWidget(self.dark_theme_radio)
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Группа "Размер шрифта"
        font_group = QGroupBox("Размер шрифта")
        font_layout = QFormLayout()
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setMinimum(8)
        self.font_size_spin.setMaximum(24)
        self.font_size_spin.setValue(10)
        self.font_size_spin.setSuffix(" pt")
        
        font_layout.addRow("Размер шрифта панелей:", self.font_size_spin)
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        
        # Загружаем текущие настройки
        self.load_settings()
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def load_settings(self):
        """Загружает настройки из БД."""
        # Загружаем тему
        theme = db.get_setting('theme', 'light')
        if theme == 'dark':
            self.dark_theme_radio.setChecked(True)
        else:
            self.light_theme_radio.setChecked(True)
        
        # Загружаем размер шрифта
        font_size = db.get_setting('font_size', '10')
        try:
            self.font_size_spin.setValue(int(font_size))
        except ValueError:
            self.font_size_spin.setValue(10)
    
    def get_settings(self) -> Dict:
        """Возвращает текущие настройки из формы."""
        theme = 'dark' if self.dark_theme_radio.isChecked() else 'light'
        font_size = str(self.font_size_spin.value())
        
        return {
            'theme': theme,
            'font_size': font_size
        }
    
    def save_settings(self):
        """Сохраняет настройки в БД."""
        settings = self.get_settings()
        db.set_setting('theme', settings['theme'])
        db.set_setting('font_size', settings['font_size'])


class MainWindow(QMainWindow):
    """Главное окно приложения."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"ChatList v{version.__version__} - Сравнение ответов нейросетей")
        self.setGeometry(100, 100, 1400, 900)
        
        # Устанавливаем иконку приложения
        icon_path = 'app.ico'
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            logger.warning(f"Иконка {icon_path} не найдена")
        
        # Временная таблица результатов (в памяти)
        self.temp_results: List[Dict] = []
        self.current_prompt_id: Optional[int] = None
        
        # Инициализация БД
        db.init_database()
        
        # Загружаем настройки перед инициализацией UI
        self.load_app_settings()
        
        self.init_ui()
        self.load_prompts()
        self.load_prompts_table()
        self.load_models()
        self.load_saved_results()
        
        # Применяем настройки после создания UI
        self.apply_settings()
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Создаем вкладки
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # Вкладка 1: Работа с промтами и запросами
        request_tab = self.create_request_tab()
        tabs.addTab(request_tab, "Запросы")
        
        # Вкладка 2: Управление промтами
        prompts_tab = self.create_prompts_tab()
        tabs.addTab(prompts_tab, "Промты")
        
        # Вкладка 3: Управление моделями
        models_tab = self.create_models_tab()
        tabs.addTab(models_tab, "Модели")
        
        # Вкладка 4: Сохраненные результаты
        results_tab = self.create_results_tab()
        tabs.addTab(results_tab, "Результаты")
        
        # Меню
        self.create_menu()
    
    def create_menu(self):
        """Создает меню приложения."""
        menubar = self.menuBar()
        
        # Меню Файл
        file_menu = menubar.addMenu("Файл")
        export_action = QAction("Экспорт результатов...", self)
        export_action.triggered.connect(self.export_results)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Настройки
        settings_menu = menubar.addMenu("Настройки")
        settings_action = QAction("Настройки...", self)
        settings_action.triggered.connect(self.show_settings)
        settings_menu.addAction(settings_action)
        
        # Меню Справка
        help_menu = menubar.addMenu("Справка")
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_request_tab(self) -> QWidget:
        """Создает вкладку для работы с запросами."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Область ввода промта
        prompt_group = QWidget()
        prompt_layout = QVBoxLayout()
        prompt_group.setLayout(prompt_layout)
        
        prompt_label = QLabel("Промт:")
        prompt_label.setFont(QFont("Arial", 10, QFont.Bold))
        prompt_layout.addWidget(prompt_label)
        
        # Выбор сохраненного промта
        prompt_select_layout = QHBoxLayout()
        prompt_select_label = QLabel("Выбрать сохраненный промт:")
        self.prompt_combo = QComboBox()
        self.prompt_combo.setEditable(True)  # Делаем поиск возможным
        self.prompt_combo.setInsertPolicy(QComboBox.NoInsert)
        self.prompt_combo.currentIndexChanged.connect(self.on_prompt_selected)
        prompt_select_layout.addWidget(prompt_select_label)
        prompt_select_layout.addWidget(self.prompt_combo)
        
        # Поиск промтов
        search_prompt_button = QPushButton("Поиск")
        search_prompt_button.clicked.connect(self.search_prompts_dialog)
        prompt_select_layout.addWidget(search_prompt_button)
        prompt_select_layout.addStretch()
        prompt_layout.addLayout(prompt_select_layout)
        
        # Текстовое поле для промта
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("Введите ваш промт здесь...")
        self.prompt_edit.setMinimumHeight(100)
        prompt_layout.addWidget(self.prompt_edit)
        
        # Поле для тегов
        tags_layout = QHBoxLayout()
        tags_label = QLabel("Теги (через запятую):")
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("например: наука, физика")
        tags_layout.addWidget(tags_label)
        tags_layout.addWidget(self.tags_edit)
        prompt_layout.addLayout(tags_layout)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        self.improve_prompt_button = QPushButton("Улучшить промт")
        self.improve_prompt_button.clicked.connect(self.improve_prompt)
        self.send_button = QPushButton("Отправить запрос")
        self.send_button.clicked.connect(self.send_request)
        self.save_prompt_button = QPushButton("Сохранить промт")
        self.save_prompt_button.clicked.connect(self.save_prompt)
        buttons_layout.addWidget(self.improve_prompt_button)
        buttons_layout.addWidget(self.send_button)
        buttons_layout.addWidget(self.save_prompt_button)
        buttons_layout.addStretch()
        prompt_layout.addLayout(buttons_layout)
        
        # Обновляем состояние кнопки улучшения при изменении текста промта
        self.prompt_edit.textChanged.connect(self.update_improve_button_state)
        self.update_improve_button_state()
        
        layout.addWidget(prompt_group)
        
        # Область результатов (временная таблица)
        results_group = QWidget()
        results_layout = QVBoxLayout()
        results_group.setLayout(results_layout)
        
        results_label = QLabel("Результаты (временная таблица):")
        results_label.setFont(QFont("Arial", 10, QFont.Bold))
        results_layout.addWidget(results_label)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        results_layout.addWidget(self.progress_bar)
        
        # Таблица результатов
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Модель", "Ответ", "Открыть", "Выбрать"])
        self.results_table.horizontalHeader().setStretchLastSection(False)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.results_table.setSortingEnabled(True)  # Включаем сортировку
        self.results_table.verticalHeader().setDefaultSectionSize(80)  # Увеличиваем высоту строк
        self.results_table.setWordWrap(True)  # Включаем перенос слов
        results_layout.addWidget(self.results_table)
        
        # Кнопки для работы с результатами
        results_buttons_layout = QHBoxLayout()
        self.save_selected_button = QPushButton("Сохранить выбранные")
        self.save_selected_button.clicked.connect(self.save_selected_results)
        self.clear_button = QPushButton("Очистить")
        self.clear_button.clicked.connect(self.clear_results)
        results_buttons_layout.addWidget(self.save_selected_button)
        results_buttons_layout.addWidget(self.clear_button)
        results_buttons_layout.addStretch()
        results_layout.addLayout(results_buttons_layout)
        
        layout.addWidget(results_group)
        
        return widget
    
    def create_prompts_tab(self) -> QWidget:
        """Создает вкладку для управления промтами."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        add_prompt_button = QPushButton("Создать")
        add_prompt_button.clicked.connect(self.add_prompt)
        edit_prompt_button = QPushButton("Редактировать")
        edit_prompt_button.clicked.connect(self.edit_prompt)
        delete_prompt_button = QPushButton("Удалить")
        delete_prompt_button.clicked.connect(self.delete_prompt)
        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.load_prompts_table)
        
        buttons_layout.addWidget(add_prompt_button)
        buttons_layout.addWidget(edit_prompt_button)
        buttons_layout.addWidget(delete_prompt_button)
        buttons_layout.addWidget(refresh_button)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # Поиск
        search_layout = QHBoxLayout()
        search_label = QLabel("Поиск:")
        self.prompts_search_edit = QLineEdit()
        self.prompts_search_edit.setPlaceholderText("Поиск по тексту промта или тегам...")
        self.prompts_search_edit.textChanged.connect(self.search_prompts_table)
        search_button = QPushButton("Найти")
        search_button.clicked.connect(self.search_prompts_table)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.prompts_search_edit)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)
        
        # Таблица промтов
        self.prompts_table = QTableWidget()
        self.prompts_table.setColumnCount(4)
        self.prompts_table.setHorizontalHeaderLabels(["ID", "Дата", "Промт", "Теги"])
        self.prompts_table.horizontalHeader().setStretchLastSection(True)
        self.prompts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.prompts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.prompts_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.prompts_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.prompts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.prompts_table.setSelectionMode(QTableWidget.SingleSelection)
        self.prompts_table.setSortingEnabled(True)
        self.prompts_table.setWordWrap(True)
        self.prompts_table.verticalHeader().setDefaultSectionSize(60)
        layout.addWidget(self.prompts_table)
        
        return widget
    
    def create_models_tab(self) -> QWidget:
        """Создает вкладку для управления моделями."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        add_model_button = QPushButton("Добавить модель")
        add_model_button.clicked.connect(self.add_model)
        edit_model_button = QPushButton("Редактировать")
        edit_model_button.clicked.connect(self.edit_model)
        delete_model_button = QPushButton("Удалить")
        delete_model_button.clicked.connect(self.delete_model)
        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.load_models)
        
        buttons_layout.addWidget(add_model_button)
        buttons_layout.addWidget(edit_model_button)
        buttons_layout.addWidget(delete_model_button)
        buttons_layout.addWidget(refresh_button)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # Таблица моделей
        self.models_table = QTableWidget()
        self.models_table.setColumnCount(4)
        self.models_table.setHorizontalHeaderLabels(["Название", "API URL", "API ID", "Активна"])
        self.models_table.horizontalHeader().setStretchLastSection(True)
        self.models_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.models_table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.models_table)
        
        return widget
    
    def create_results_tab(self) -> QWidget:
        """Создает вкладку для просмотра сохраненных результатов."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Поиск
        search_layout = QHBoxLayout()
        search_label = QLabel("Поиск:")
        self.results_search_edit = QLineEdit()
        self.results_search_edit.setPlaceholderText("Поиск по тексту ответа, промту или модели...")
        self.results_search_edit.textChanged.connect(self.search_results)
        search_button = QPushButton("Найти")
        search_button.clicked.connect(self.search_results)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.results_search_edit)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)
        
        # Таблица результатов
        self.saved_results_table = QTableWidget()
        self.saved_results_table.setColumnCount(5)
        self.saved_results_table.setHorizontalHeaderLabels(["Дата", "Промт", "Модель", "Ответ", "Теги"])
        self.saved_results_table.horizontalHeader().setStretchLastSection(True)
        self.saved_results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.saved_results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.saved_results_table.setSortingEnabled(True)  # Включаем сортировку
        self.saved_results_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.saved_results_table.customContextMenuRequested.connect(self.show_results_context_menu)
        layout.addWidget(self.saved_results_table)
        
        return widget
    
    def load_prompts(self):
        """Загружает промты в выпадающий список."""
        prompts = db.get_all_prompts()
        self.prompt_combo.clear()
        self.prompt_combo.addItem("-- Новый промт --", None)
        for prompt in prompts:
            display_text = f"{prompt['prompt'][:50]}... ({prompt['date']})" if len(prompt['prompt']) > 50 else prompt['prompt']
            self.prompt_combo.addItem(display_text, prompt['id'])
    
    def load_prompts_table(self):
        """Загружает промты в таблицу."""
        prompts = db.get_all_prompts()
        self.prompts_table.setRowCount(len(prompts))
        
        for row, prompt in enumerate(prompts):
            self.prompts_table.setItem(row, 0, QTableWidgetItem(str(prompt['id'])))
            self.prompts_table.setItem(row, 1, QTableWidgetItem(prompt.get('date', '')))
            
            prompt_item = QTableWidgetItem(prompt.get('prompt', ''))
            prompt_item.setFlags(prompt_item.flags() | Qt.TextWordWrap)
            self.prompts_table.setItem(row, 2, prompt_item)
            
            self.prompts_table.setItem(row, 3, QTableWidgetItem(prompt.get('tags', '')))
    
    def load_models(self):
        """Загружает модели в таблицу."""
        models_list = db.get_all_models()
        self.models_table.setRowCount(len(models_list))
        
        for row, model in enumerate(models_list):
            self.models_table.setItem(row, 0, QTableWidgetItem(model['name']))
            self.models_table.setItem(row, 1, QTableWidgetItem(model['api_url']))
            self.models_table.setItem(row, 2, QTableWidgetItem(model['api_id']))
            
            checkbox = QCheckBox()
            checkbox.setChecked(bool(model['is_active']))
            checkbox.stateChanged.connect(lambda state, m_id=model['id']: self.toggle_model_active(m_id, state))
            self.models_table.setCellWidget(row, 3, checkbox)
    
    def load_saved_results(self):
        """Загружает сохраненные результаты."""
        results = db.get_all_results()
        self.saved_results_table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            self.saved_results_table.setItem(row, 0, QTableWidgetItem(result.get('created_at', '')))
            self.saved_results_table.setItem(row, 1, QTableWidgetItem(result.get('prompt', '')))
            self.saved_results_table.setItem(row, 2, QTableWidgetItem(result.get('model_name', '')))
            self.saved_results_table.setItem(row, 3, QTableWidgetItem(result.get('response_text', '')))
            self.saved_results_table.setItem(row, 4, QTableWidgetItem(result.get('tags', '')))
    
    def on_prompt_selected(self, index):
        """Обработчик выбора промта из списка."""
        prompt_id = self.prompt_combo.itemData(index)
        if prompt_id:
            prompt = db.get_prompt_by_id(prompt_id)
            if prompt:
                self.prompt_edit.setText(prompt['prompt'])
                self.tags_edit.setText(prompt.get('tags', ''))
    
    def update_improve_button_state(self):
        """Обновляет состояние кнопки улучшения промта."""
        prompt_text = self.prompt_edit.toPlainText().strip()
        has_text = bool(prompt_text)
        self.improve_prompt_button.setEnabled(has_text)
    
    def improve_prompt(self):
        """Открывает диалог улучшения промта."""
        prompt_text = self.prompt_edit.toPlainText().strip()
        if not prompt_text:
            QMessageBox.warning(self, "Ошибка", "Введите промт для улучшения")
            return
        
        # Проверяем наличие активных моделей
        active_models = db.get_active_models()
        if not active_models:
            QMessageBox.warning(self, "Ошибка", "Нет активных моделей для улучшения промта")
            return
        
        # Открываем диалог улучшения
        dialog = PromptImprovementDialog(self, prompt_text)
        if dialog.exec_() == QDialog.Accepted:
            improved_prompt = dialog.get_improved_prompt()
            if improved_prompt:
                # Заменяем исходный промт на улучшенный
                self.prompt_edit.setPlainText(improved_prompt)
                QMessageBox.information(self, "Успех", "Промт улучшен и подставлен в поле ввода")
    
    def save_prompt(self):
        """Сохраняет промт в базу данных."""
        prompt_text = self.prompt_edit.toPlainText().strip()
        if not prompt_text:
            QMessageBox.warning(self, "Ошибка", "Промт не может быть пустым")
            return
        
        tags = self.tags_edit.text().strip() or None
        db.create_prompt(prompt_text, tags)
        self.load_prompts()
        self.load_prompts_table()
        QMessageBox.information(self, "Успех", "Промт сохранен")
    
    def send_request(self):
        """Отправляет запрос во все активные модели."""
        prompt_text = self.prompt_edit.toPlainText().strip()
        if not prompt_text:
            QMessageBox.warning(self, "Ошибка", "Введите промт")
            return
        
        # Получаем активные модели
        active_models = db.get_active_models()
        if not active_models:
            QMessageBox.warning(self, "Ошибка", "Нет активных моделей")
            return
        
        # Сохраняем промт, если его еще нет
        if not self.current_prompt_id:
            tags = self.tags_edit.text().strip() or None
            self.current_prompt_id = db.create_prompt(prompt_text, tags)
            self.load_prompts()
        
        # Очищаем предыдущие результаты
        self.clear_results()
        
        # Показываем прогресс
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Неопределенный прогресс
        self.send_button.setEnabled(False)
        
        # Запускаем поток для отправки запросов
        self.request_thread = RequestThread(prompt_text, active_models)
        self.request_thread.finished.connect(self.on_requests_finished)
        self.request_thread.start()
    
    def on_requests_finished(self, results: List[Dict]):
        """Обработчик завершения запросов."""
        self.progress_bar.setVisible(False)
        self.send_button.setEnabled(True)
        
        # Обновляем временную таблицу
        self.temp_results = results
        self.update_results_table()
    
    def update_results_table(self):
        """Обновляет таблицу результатов."""
        self.results_table.setRowCount(len(self.temp_results))
        
        for row, result in enumerate(self.temp_results):
            model_name = result.get('model_name', 'Unknown')
            response = result.get('response', '')
            error = result.get('error')
            
            if error:
                response = f"Ошибка: {error}"
            
            # Колонка "Модель"
            self.results_table.setItem(row, 0, QTableWidgetItem(model_name))
            
            # Колонка "Ответ" - многострочный текст
            response_item = QTableWidgetItem(response)
            response_item.setFlags(response_item.flags() | Qt.TextWordWrap)  # Включаем перенос слов
            self.results_table.setItem(row, 1, response_item)
            
            # Колонка "Просмотр" - кнопка для просмотра полного ответа в markdown
            view_button = QPushButton("Открыть")
            view_button.clicked.connect(lambda checked, r=row: self.view_full_response(r))
            self.results_table.setCellWidget(row, 2, view_button)
            
            # Колонка "Выбрать" - чекбокс
            checkbox = QCheckBox()
            checkbox.setChecked(True)  # По умолчанию выбрано
            self.results_table.setCellWidget(row, 3, checkbox)
    
    def view_full_response(self, row: int):
        """Открывает диалог для просмотра полного ответа в форматированном markdown."""
        if row < 0 or row >= len(self.temp_results):
            return
        
        result = self.temp_results[row]
        model_name = result.get('model_name', 'Unknown')
        response = result.get('response', '')
        error = result.get('error')
        
        if error:
            response = f"Ошибка: {error}"
        
        # Создаем диалог для просмотра
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Ответ от {model_name}")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # Метка с названием модели
        model_label = QLabel(f"<b>Модель:</b> {model_name}")
        model_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(model_label)
        
        # Текстовое поле с ответом в формате markdown (только для чтения)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Arial", 10))
        
        # Конвертируем markdown в HTML для форматированного отображения
        try:
            import markdown
            # Конвертируем markdown в HTML
            html_content = markdown.markdown(
                response,
                extensions=['extra', 'codehilite', 'nl2br'],
                extension_configs={
                    'codehilite': {
                        'css_class': 'highlight',
                        'use_pygments': False
                    }
                }
            )
            
            # Добавляем базовые стили для улучшения отображения
            styled_html = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        font-size: 11pt;
                        line-height: 1.6;
                        padding: 10px;
                        color: #333;
                    }}
                    h1, h2, h3, h4, h5, h6 {{
                        color: #2c3e50;
                        margin-top: 1em;
                        margin-bottom: 0.5em;
                    }}
                    code {{
                        background-color: #f4f4f4;
                        padding: 2px 4px;
                        border-radius: 3px;
                        font-family: 'Courier New', monospace;
                        font-size: 0.9em;
                    }}
                    pre {{
                        background-color: #f4f4f4;
                        padding: 10px;
                        border-radius: 5px;
                        overflow-x: auto;
                        border-left: 3px solid #3498db;
                    }}
                    pre code {{
                        background-color: transparent;
                        padding: 0;
                    }}
                    blockquote {{
                        border-left: 4px solid #3498db;
                        margin: 0;
                        padding-left: 15px;
                        color: #555;
                    }}
                    ul, ol {{
                        margin: 0.5em 0;
                        padding-left: 2em;
                    }}
                    a {{
                        color: #3498db;
                        text-decoration: none;
                    }}
                    a:hover {{
                        text-decoration: underline;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 1em 0;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f2f2f2;
                        font-weight: bold;
                    }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            text_edit.setHtml(styled_html)
        except ImportError:
            # Если markdown не установлен, отображаем как обычный текст
            text_edit.setPlainText(response)
        except Exception as e:
            # В случае ошибки конвертации, отображаем как обычный текст
            logger.error(f"Ошибка конвертации markdown: {e}")
            text_edit.setPlainText(response)
        
        layout.addWidget(text_edit)
        
        # Кнопка закрытия
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(dialog.close)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def save_selected_results(self):
        """Сохраняет выбранные результаты в БД."""
        if not self.current_prompt_id:
            QMessageBox.warning(self, "Ошибка", "Нет активного промта")
            return
        
        selected_results = []
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 3)  # Чекбокс теперь в колонке 3
            if checkbox and checkbox.isChecked():
                result = self.temp_results[row]
                model_id = result.get('model_id')
                response = result.get('response')
                if model_id and response:
                    selected_results.append({
                        'prompt_id': self.current_prompt_id,
                        'model_id': model_id,
                        'response_text': response
                    })
        
        if not selected_results:
            QMessageBox.warning(self, "Ошибка", "Не выбрано ни одного результата")
            return
        
        count = db.save_results(selected_results)
        QMessageBox.information(self, "Успех", f"Сохранено результатов: {count}")
        self.load_saved_results()
        self.clear_results()
    
    def clear_results(self):
        """Очищает временную таблицу результатов."""
        self.temp_results = []
        self.results_table.setRowCount(0)
        self.current_prompt_id = None
    
    def add_model(self):
        """Добавляет новую модель."""
        dialog = ModelDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                models.create_model(**data)
                self.load_models()
                QMessageBox.information(self, "Успех", "Модель добавлена")
            except ValueError as e:
                QMessageBox.warning(self, "Ошибка", str(e))
    
    def edit_model(self):
        """Редактирует выбранную модель."""
        selected_rows = self.models_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите модель для редактирования")
            return
        
        row = selected_rows[0].row()
        model_name = self.models_table.item(row, 0).text()
        models_list = db.get_all_models()
        model_data = next((m for m in models_list if m['name'] == model_name), None)
        
        if not model_data:
            return
        
        dialog = ModelDialog(self, model_data)
        if dialog.exec_() == QDialog.Accepted:
            new_data = dialog.get_data()
            try:
                models.update_model(model_data['id'], **new_data)
                self.load_models()
                QMessageBox.information(self, "Успех", "Модель обновлена")
            except ValueError as e:
                QMessageBox.warning(self, "Ошибка", str(e))
    
    def delete_model(self):
        """Удаляет выбранную модель."""
        selected_rows = self.models_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите модель для удаления")
            return
        
        row = selected_rows[0].row()
        model_name = self.models_table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить модель '{model_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            models_list = db.get_all_models()
            model_data = next((m for m in models_list if m['name'] == model_name), None)
            if model_data:
                models.delete_model(model_data['id'])
                self.load_models()
                QMessageBox.information(self, "Успех", "Модель удалена")
    
    def toggle_model_active(self, model_id: int, state: int):
        """Переключает активность модели."""
        models.toggle_model_active(model_id)
    
    def search_results(self):
        """Поиск в сохраненных результатах."""
        query = self.results_search_edit.text().strip()
        if query:
            results = db.search_results(query)
        else:
            results = db.get_all_results()
        
        self.saved_results_table.setRowCount(len(results))
        for row, result in enumerate(results):
            self.saved_results_table.setItem(row, 0, QTableWidgetItem(result.get('created_at', '')))
            self.saved_results_table.setItem(row, 1, QTableWidgetItem(result.get('prompt', '')))
            self.saved_results_table.setItem(row, 2, QTableWidgetItem(result.get('model_name', '')))
            self.saved_results_table.setItem(row, 3, QTableWidgetItem(result.get('response_text', '')))
            self.saved_results_table.setItem(row, 4, QTableWidgetItem(result.get('tags', '')))
    
    def export_results(self):
        """Экспортирует результаты в файл."""
        selected_rows = self.saved_results_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите результаты для экспорта")
            return
        
        # Диалог выбора формата и файла
        file_path, file_type = QFileDialog.getSaveFileName(
            self, "Экспорт результатов", "",
            "Markdown (*.md);;JSON (*.json)"
        )
        
        if not file_path:
            return
        
        # Собираем данные выбранных результатов
        export_data = []
        for row_index in selected_rows:
            row = row_index.row()
            export_data.append({
                'date': self.saved_results_table.item(row, 0).text(),
                'prompt': self.saved_results_table.item(row, 1).text(),
                'model': self.saved_results_table.item(row, 2).text(),
                'response': self.saved_results_table.item(row, 3).text(),
                'tags': self.saved_results_table.item(row, 4).text()
            })
        
        # Экспорт
        try:
            if file_type == "Markdown (*.md)":
                self.export_to_markdown(file_path, export_data)
            else:
                self.export_to_json(file_path, export_data)
            QMessageBox.information(self, "Успех", "Результаты экспортированы")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта: {str(e)}")
    
    def export_to_markdown(self, file_path: str, data: List[Dict]):
        """Экспортирует данные в Markdown."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# Экспорт результатов ChatList\n\n")
            for item in data:
                f.write(f"## {item['model']} - {item['date']}\n\n")
                f.write(f"**Промт:** {item['prompt']}\n\n")
                f.write(f"**Ответ:**\n{item['response']}\n\n")
                if item['tags']:
                    f.write(f"**Теги:** {item['tags']}\n\n")
                f.write("---\n\n")
    
    def export_to_json(self, file_path: str, data: List[Dict]):
        """Экспортирует данные в JSON."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def search_prompts_dialog(self):
        """Открывает диалог поиска промтов."""
        from PyQt5.QtWidgets import QInputDialog
        query, ok = QInputDialog.getText(self, "Поиск промтов", "Введите текст для поиска:")
        if ok and query:
            prompts = db.search_prompts(query)
            if prompts:
                # Обновляем список промтов
                self.prompt_combo.clear()
                self.prompt_combo.addItem("-- Новый промт --", None)
                for prompt in prompts:
                    display_text = f"{prompt['prompt'][:50]}... ({prompt['date']})" if len(prompt['prompt']) > 50 else prompt['prompt']
                    self.prompt_combo.addItem(display_text, prompt['id'])
                QMessageBox.information(self, "Результаты поиска", f"Найдено промтов: {len(prompts)}")
            else:
                QMessageBox.information(self, "Результаты поиска", "Промты не найдены")
    
    def search_prompts_table(self):
        """Поиск промтов в таблице."""
        query = self.prompts_search_edit.text().strip()
        if query:
            prompts = db.search_prompts(query)
        else:
            prompts = db.get_all_prompts()
        
        self.prompts_table.setRowCount(len(prompts))
        for row, prompt in enumerate(prompts):
            self.prompts_table.setItem(row, 0, QTableWidgetItem(str(prompt['id'])))
            self.prompts_table.setItem(row, 1, QTableWidgetItem(prompt.get('date', '')))
            
            prompt_item = QTableWidgetItem(prompt.get('prompt', ''))
            prompt_item.setFlags(prompt_item.flags() | Qt.TextWordWrap)
            self.prompts_table.setItem(row, 2, prompt_item)
            
            self.prompts_table.setItem(row, 3, QTableWidgetItem(prompt.get('tags', '')))
    
    def add_prompt(self):
        """Добавляет новый промт."""
        dialog = PromptDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            prompt_text, tags = dialog.get_data()
            if prompt_text:
                db.create_prompt(prompt_text, tags)
                self.load_prompts()
                self.load_prompts_table()
                QMessageBox.information(self, "Успех", "Промт создан")
    
    def edit_prompt(self):
        """Редактирует выбранный промт."""
        selected_rows = self.prompts_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите промт для редактирования")
            return
        
        row = selected_rows[0].row()
        prompt_id = int(self.prompts_table.item(row, 0).text())
        prompt = db.get_prompt_by_id(prompt_id)
        
        if not prompt:
            return
        
        dialog = PromptDialog(self, prompt)
        if dialog.exec_() == QDialog.Accepted:
            prompt_text, tags = dialog.get_data()
            if prompt_text:
                db.update_prompt(prompt_id, prompt_text, tags)
                self.load_prompts()
                self.load_prompts_table()
                QMessageBox.information(self, "Успех", "Промт обновлен")
    
    def delete_prompt(self):
        """Удаляет выбранный промт."""
        selected_rows = self.prompts_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите промт для удаления")
            return
        
        row = selected_rows[0].row()
        prompt_id = int(self.prompts_table.item(row, 0).text())
        prompt_text = self.prompts_table.item(row, 2).text()
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить промт?\n\n{prompt_text[:100]}...",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            db.delete_prompt(prompt_id)
            self.load_prompts()
            self.load_prompts_table()
            QMessageBox.information(self, "Успех", "Промт удален")
    
    def show_models_context_menu(self, position):
        """Показывает контекстное меню для таблицы моделей."""
        menu = QMenu(self)
        
        edit_action = QAction("Редактировать", self)
        edit_action.triggered.connect(self.edit_model)
        menu.addAction(edit_action)
        
        delete_action = QAction("Удалить", self)
        delete_action.triggered.connect(self.delete_model)
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        refresh_action = QAction("Обновить", self)
        refresh_action.triggered.connect(self.load_models)
        menu.addAction(refresh_action)
        
        menu.exec_(self.models_table.viewport().mapToGlobal(position))
    
    def show_results_context_menu(self, position):
        """Показывает контекстное меню для таблицы результатов."""
        menu = QMenu(self)
        
        export_action = QAction("Экспортировать", self)
        export_action.triggered.connect(self.export_results)
        menu.addAction(export_action)
        
        menu.addSeparator()
        
        delete_action = QAction("Удалить", self)
        delete_action.triggered.connect(self.delete_selected_result)
        menu.addAction(delete_action)
        
        menu.exec_(self.saved_results_table.viewport().mapToGlobal(position))
    
    def delete_selected_result(self):
        """Удаляет выбранный результат."""
        selected_rows = self.saved_results_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите результат для удаления")
            return
        
        row = selected_rows[0].row()
        result_id_item = self.saved_results_table.item(row, 0)
        if not result_id_item:
            # Нужно получить ID из БД
            prompt_text = self.saved_results_table.item(row, 1).text()
            results = db.search_results(prompt_text)
            if results:
                result_id = results[0].get('id')
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось найти результат")
                return
        else:
            # Получаем ID из данных
            results = db.get_all_results()
            if row < len(results):
                result_id = results[row]['id']
            else:
                return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Удалить этот результат?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            db.delete_result(result_id)
            self.load_saved_results()
            QMessageBox.information(self, "Успех", "Результат удален")
    
    def load_app_settings(self):
        """Загружает настройки приложения из БД."""
        self.app_theme = db.get_setting('theme', 'light')
        font_size_str = db.get_setting('font_size', '10')
        try:
            self.app_font_size = int(font_size_str)
        except ValueError:
            self.app_font_size = 10
    
    def apply_settings(self):
        """Применяет настройки к интерфейсу."""
        # Применяем тему
        if self.app_theme == 'dark':
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QTextEdit, QLineEdit, QComboBox {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 5px;
                }
                QPushButton {
                    background-color: #404040;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 5px 15px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QPushButton:pressed {
                    background-color: #353535;
                }
                QPushButton:disabled {
                    background-color: #2b2b2b;
                    color: #888888;
                }
                QTableWidget {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    gridline-color: #555555;
                    border: 1px solid #555555;
                }
                QTableWidget::item {
                    background-color: #3c3c3c;
                    color: #ffffff;
                }
                QTableWidget::item:selected {
                    background-color: #505050;
                    color: #ffffff;
                }
                QHeaderView::section {
                    background-color: #404040;
                    color: #ffffff;
                    padding: 5px;
                    border: 1px solid #555555;
                }
                QTabWidget::pane {
                    background-color: #2b2b2b;
                    border: 1px solid #555555;
                }
                QTabBar::tab {
                    background-color: #404040;
                    color: #ffffff;
                    padding: 8px 20px;
                    border: 1px solid #555555;
                    border-bottom: none;
                }
                QTabBar::tab:selected {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QTabBar::tab:hover {
                    background-color: #505050;
                }
                QCheckBox {
                    color: #ffffff;
                }
                QCheckBox::indicator {
                    background-color: #3c3c3c;
                    border: 1px solid #555555;
                }
                QCheckBox::indicator:checked {
                    background-color: #0078d4;
                }
                QLabel {
                    color: #ffffff;
                }
                QMenuBar {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QMenuBar::item {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QMenuBar::item:selected {
                    background-color: #404040;
                }
                QMenu {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
                QMenu::item:selected {
                    background-color: #505050;
                }
                QDialog {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QGroupBox {
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 3px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
                QRadioButton {
                    color: #ffffff;
                }
                QRadioButton::indicator {
                    background-color: #3c3c3c;
                    border: 1px solid #555555;
                    border-radius: 7px;
                }
                QRadioButton::indicator:checked {
                    background-color: #0078d4;
                }
                QSpinBox {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 3px;
                }
            """)
        else:
            # Светлая тема (стандартная)
            self.setStyleSheet("")
        
        # Применяем размер шрифта
        font = QFont("Arial", self.app_font_size)
        self.setFont(font)
        
        # Обновляем шрифты для всех виджетов
        self.update_fonts()
    
    def update_fonts(self):
        """Обновляет шрифты для всех элементов интерфейса."""
        font = QFont("Arial", self.app_font_size)
        
        # Обновляем шрифты для основных элементов
        if hasattr(self, 'prompt_edit'):
            self.prompt_edit.setFont(font)
        if hasattr(self, 'results_table'):
            self.results_table.setFont(font)
        if hasattr(self, 'prompts_table'):
            self.prompts_table.setFont(font)
        if hasattr(self, 'models_table'):
            self.models_table.setFont(font)
        if hasattr(self, 'saved_results_table'):
            self.saved_results_table.setFont(font)
        if hasattr(self, 'tags_edit'):
            self.tags_edit.setFont(font)
        if hasattr(self, 'prompt_combo'):
            self.prompt_combo.setFont(font)
        
        # Обновляем шрифты для всех дочерних виджетов
        self.update_children_fonts(self.centralWidget(), font)
    
    def update_children_fonts(self, widget, font):
        """Рекурсивно обновляет шрифты для всех дочерних виджетов."""
        if widget is None:
            return
        
        # Обновляем шрифт для виджетов, которые поддерживают setFont
        if isinstance(widget, (QTextEdit, QLineEdit, QComboBox, QLabel, QPushButton, QTableWidget)):
            widget.setFont(font)
        
        # Рекурсивно обновляем для всех дочерних виджетов
        for child in widget.findChildren(QWidget):
            if isinstance(child, (QTextEdit, QLineEdit, QComboBox, QLabel, QPushButton, QTableWidget)):
                child.setFont(font)
    
    def show_settings(self):
        """Показывает диалог настроек."""
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            dialog.save_settings()
            # Перезагружаем настройки
            self.load_app_settings()
            # Применяем новые настройки
            self.apply_settings()
            QMessageBox.information(self, "Успех", "Настройки сохранены. Изменения применены.")
    
    def show_about(self):
        """Показывает диалог 'О программе'."""
        about_text = f"""
        <h2>ChatList v{version.__version__}</h2>
        <p><b>Приложение для сравнения ответов разных нейросетей на один промт</b></p>
        
        <p>ChatList позволяет отправлять один и тот же промт в несколько нейросетей одновременно и сравнивать их ответы.</p>
        
        <h3>Основные возможности:</h3>
        <ul>
            <li>📝 Отправка промтов в несколько нейросетей одновременно</li>
            <li>💾 Сохранение промтов и результатов в базе данных SQLite</li>
            <li>🔍 Поиск и сортировка по всем таблицам</li>
            <li>📊 Временная таблица результатов с возможностью выбора для сохранения</li>
            <li>🎯 Поддержка различных API: OpenAI, DeepSeek, Groq, OpenRouter</li>
            <li>📤 Экспорт результатов в Markdown и JSON</li>
            <li>⚙️ Управление моделями через удобный интерфейс</li>
            <li>🤖 AI-ассистент для улучшения промтов</li>
            <li>🎨 Настройка темы оформления и размера шрифта</li>
        </ul>
        
        <h3>Технологии:</h3>
        <p>Разработано с использованием:</p>
        <ul>
            <li>Python 3.11+</li>
            <li>PyQt5</li>
            <li>SQLite</li>
            <li>Requests</li>
        </ul>
        
        <p><i>Версия: {version.__version__}</i></p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("О программе")
        msg.setTextFormat(Qt.RichText)
        msg.setText(about_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec_()


def main():
    """Точка входа в приложение."""
    logger.info(f"Запуск ChatList v{version.__version__}")
    
    app = QApplication(sys.argv)
    
    # Устанавливаем иконку для всего приложения
    icon_path = 'app.ico'
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        logger.warning(f"Иконка {icon_path} не найдена")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
