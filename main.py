"""
Основной модуль приложения ChatList.
Содержит главное окно и весь пользовательский интерфейс.
"""
import sys
import json
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QCheckBox, QComboBox, QLabel, QSplitter, QTabWidget, QMessageBox,
    QDialog, QDialogButtonBox, QFormLayout, QProgressBar, QHeaderView,
    QMenu, QAction, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

import db
import models
import network


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


class MainWindow(QMainWindow):
    """Главное окно приложения."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChatList - Сравнение ответов нейросетей")
        self.setGeometry(100, 100, 1400, 900)
        
        # Временная таблица результатов (в памяти)
        self.temp_results: List[Dict] = []
        self.current_prompt_id: Optional[int] = None
        
        # Инициализация БД
        db.init_database()
        
        self.init_ui()
        self.load_prompts()
        self.load_models()
        self.load_saved_results()
    
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
        
        # Вкладка 2: Управление моделями
        models_tab = self.create_models_tab()
        tabs.addTab(models_tab, "Модели")
        
        # Вкладка 3: Сохраненные результаты
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
        self.prompt_combo.currentIndexChanged.connect(self.on_prompt_selected)
        prompt_select_layout.addWidget(prompt_select_label)
        prompt_select_layout.addWidget(self.prompt_combo)
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
        self.send_button = QPushButton("Отправить запрос")
        self.send_button.clicked.connect(self.send_request)
        self.save_prompt_button = QPushButton("Сохранить промт")
        self.save_prompt_button.clicked.connect(self.save_prompt)
        buttons_layout.addWidget(self.send_button)
        buttons_layout.addWidget(self.save_prompt_button)
        buttons_layout.addStretch()
        prompt_layout.addLayout(buttons_layout)
        
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
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Модель", "Ответ", "Выбрать"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
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
    
    def save_prompt(self):
        """Сохраняет промт в базу данных."""
        prompt_text = self.prompt_edit.toPlainText().strip()
        if not prompt_text:
            QMessageBox.warning(self, "Ошибка", "Промт не может быть пустым")
            return
        
        tags = self.tags_edit.text().strip() or None
        db.create_prompt(prompt_text, tags)
        self.load_prompts()
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
            
            self.results_table.setItem(row, 0, QTableWidgetItem(model_name))
            self.results_table.setItem(row, 1, QTableWidgetItem(response))
            
            checkbox = QCheckBox()
            checkbox.setChecked(True)  # По умолчанию выбрано
            self.results_table.setCellWidget(row, 2, checkbox)
    
    def save_selected_results(self):
        """Сохраняет выбранные результаты в БД."""
        if not self.current_prompt_id:
            QMessageBox.warning(self, "Ошибка", "Нет активного промта")
            return
        
        selected_results = []
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 2)
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
    
    def show_about(self):
        """Показывает диалог 'О программе'."""
        QMessageBox.about(
            self, "О программе",
            "ChatList v1.0\n\n"
            "Приложение для сравнения ответов разных нейросетей на один промт.\n\n"
            "Разработано с использованием PyQt5."
        )


def main():
    """Точка входа в приложение."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
