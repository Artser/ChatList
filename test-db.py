"""
Тестовая программа для просмотра и редактирования SQLite баз данных.
Отображает список таблиц и позволяет просматривать/редактировать данные с пагинацией.
"""
import sys
import sqlite3
from typing import List, Dict, Optional, Tuple
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel, QLineEdit,
    QDialog, QDialogButtonBox, QFormLayout, QMessageBox, QFileDialog,
    QComboBox, QSpinBox, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class TableViewDialog(QDialog):
    """Диалог для просмотра и редактирования таблицы с пагинацией."""
    
    def __init__(self, parent, db_path: str, table_name: str):
        super().__init__(parent)
        self.db_path = db_path
        self.table_name = table_name
        self.current_page = 1
        self.rows_per_page = 50
        self.total_rows = 0
        
        self.setWindowTitle(f"Таблица: {table_name}")
        self.setMinimumSize(1000, 600)
        
        self.init_ui()
        self.load_table_data()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        
        # Панель управления пагинацией
        pagination_layout = QHBoxLayout()
        
        self.page_label = QLabel("Страница: 1")
        pagination_layout.addWidget(self.page_label)
        
        pagination_layout.addWidget(QLabel("Строк на странице:"))
        self.rows_spinbox = QSpinBox()
        self.rows_spinbox.setMinimum(10)
        self.rows_spinbox.setMaximum(500)
        self.rows_spinbox.setValue(self.rows_per_page)
        self.rows_spinbox.valueChanged.connect(self.on_rows_changed)
        pagination_layout.addWidget(self.rows_spinbox)
        
        self.prev_button = QPushButton("◀ Назад")
        self.prev_button.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Вперед ▶")
        self.next_button.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_button)
        
        pagination_layout.addStretch()
        
        # Кнопки CRUD
        crud_layout = QHBoxLayout()
        self.create_button = QPushButton("Создать")
        self.create_button.clicked.connect(self.create_record)
        crud_layout.addWidget(self.create_button)
        
        self.update_button = QPushButton("Обновить")
        self.update_button.clicked.connect(self.update_record)
        crud_layout.addWidget(self.update_button)
        
        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self.delete_record)
        crud_layout.addWidget(self.delete_button)
        
        crud_layout.addStretch()
        
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self.load_table_data)
        crud_layout.addWidget(self.refresh_button)
        
        layout.addLayout(pagination_layout)
        layout.addLayout(crud_layout)
        
        # Таблица данных
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # Запрещаем прямое редактирование
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def get_connection(self):
        """Получает соединение с базой данных."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_table_info(self) -> Tuple[List[str], int]:
        """Получает информацию о таблице: список колонок и количество строк."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Получаем названия колонок
        cursor.execute(f"PRAGMA table_info({self.table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Получаем количество строк
        cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
        total_rows = cursor.fetchone()[0]
        
        conn.close()
        return columns, total_rows
    
    def load_table_data(self):
        """Загружает данные таблицы с учетом пагинации."""
        try:
            columns, total_rows = self.get_table_info()
            self.total_rows = total_rows
            
            # Вычисляем пагинацию
            offset = (self.current_page - 1) * self.rows_per_page
            total_pages = (total_rows + self.rows_per_page - 1) // self.rows_per_page if total_rows > 0 else 1
            
            # Обновляем интерфейс пагинации
            self.page_label.setText(f"Страница: {self.current_page} из {total_pages} (Всего строк: {total_rows})")
            self.prev_button.setEnabled(self.current_page > 1)
            self.next_button.setEnabled(self.current_page < total_pages)
            
            # Загружаем данные
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} LIMIT ? OFFSET ?", (self.rows_per_page, offset))
            rows = cursor.fetchall()
            conn.close()
            
            # Заполняем таблицу
            self.table.setColumnCount(len(columns))
            self.table.setHorizontalHeaderLabels(columns)
            self.table.setRowCount(len(rows))
            
            for row_idx, row_data in enumerate(rows):
                for col_idx, col_name in enumerate(columns):
                    value = row_data[col_name]
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    self.table.setItem(row_idx, col_idx, item)
            
            # Настраиваем ширину колонок
            self.table.resizeColumnsToContents()
            self.table.horizontalHeader().setStretchLastSection(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")
    
    def on_rows_changed(self, value):
        """Обработчик изменения количества строк на странице."""
        self.rows_per_page = value
        self.current_page = 1
        self.load_table_data()
    
    def prev_page(self):
        """Переход на предыдущую страницу."""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_table_data()
    
    def next_page(self):
        """Переход на следующую страницу."""
        total_pages = (self.total_rows + self.rows_per_page - 1) // self.rows_per_page if self.total_rows > 0 else 1
        if self.current_page < total_pages:
            self.current_page += 1
            self.load_table_data()
    
    def create_record(self):
        """Создает новую запись."""
        try:
            columns, _ = self.get_table_info()
            
            dialog = RecordDialog(self, columns, self.table_name, mode='create')
            if dialog.exec_() == QDialog.Accepted:
                data = dialog.get_data()
                if data:
                    self.insert_record(data)
                    self.load_table_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать запись: {str(e)}")
    
    def update_record(self):
        """Обновляет выбранную запись."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите строку для редактирования")
            return
        
        try:
            row = selected_rows[0].row()
            columns, _ = self.get_table_info()
            
            # Получаем текущие значения
            current_values = {}
            for col_idx, col_name in enumerate(columns):
                item = self.table.item(row, col_idx)
                current_values[col_name] = item.text() if item else ""
            
            # Получаем первичный ключ
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            table_info = cursor.fetchall()
            pk_column = None
            for col_info in table_info:
                if col_info[5] == 1:  # pk column
                    pk_column = col_info[1]
                    break
            conn.close()
            
            if not pk_column:
                QMessageBox.warning(self, "Предупреждение", "Не найден первичный ключ для обновления")
                return
            
            dialog = RecordDialog(self, columns, self.table_name, mode='update', current_values=current_values, pk_column=pk_column)
            if dialog.exec_() == QDialog.Accepted:
                data = dialog.get_data()
                if data:
                    self.update_record_in_db(data, pk_column, current_values[pk_column])
                    self.load_table_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить запись: {str(e)}")
    
    def delete_record(self):
        """Удаляет выбранную запись."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите строку для удаления")
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы уверены, что хотите удалить эту запись?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                row = selected_rows[0].row()
                columns, _ = self.get_table_info()
                
                # Получаем первичный ключ
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({self.table_name})")
                table_info = cursor.fetchall()
                pk_column = None
                for col_info in table_info:
                    if col_info[5] == 1:  # pk column
                        pk_column = col_info[1]
                        break
                
                if not pk_column:
                    QMessageBox.warning(self, "Предупреждение", "Не найден первичный ключ для удаления")
                    conn.close()
                    return
                
                # Получаем значение первичного ключа
                pk_item = self.table.item(row, columns.index(pk_column))
                pk_value = pk_item.text() if pk_item else None
                
                if pk_value:
                    self.delete_record_from_db(pk_column, pk_value)
                    self.load_table_data()
                
                conn.close()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить запись: {str(e)}")
    
    def insert_record(self, data: Dict[str, str]):
        """Вставляет новую запись в базу данных."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ', '.join(['?' for _ in values])
        columns_str = ', '.join(columns)
        
        cursor.execute(f"INSERT INTO {self.table_name} ({columns_str}) VALUES ({placeholders})", values)
        conn.commit()
        conn.close()
    
    def update_record_in_db(self, data: Dict[str, str], pk_column: str, pk_value: str):
        """Обновляет запись в базе данных."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        set_clause = ', '.join([f"{col} = ?" for col in data.keys()])
        values = list(data.values())
        values.append(pk_value)
        
        cursor.execute(f"UPDATE {self.table_name} SET {set_clause} WHERE {pk_column} = ?", values)
        conn.commit()
        conn.close()
    
    def delete_record_from_db(self, pk_column: str, pk_value: str):
        """Удаляет запись из базы данных."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {self.table_name} WHERE {pk_column} = ?", (pk_value,))
        conn.commit()
        conn.close()


class RecordDialog(QDialog):
    """Диалог для создания/редактирования записи."""
    
    def __init__(self, parent, columns: List[str], table_name: str, mode: str = 'create', 
                 current_values: Optional[Dict[str, str]] = None, pk_column: Optional[str] = None):
        super().__init__(parent)
        self.columns = columns
        self.table_name = table_name
        self.mode = mode
        self.current_values = current_values or {}
        self.pk_column = pk_column
        
        self.setWindowTitle(f"{'Создать' if mode == 'create' else 'Редактировать'} запись в {table_name}")
        self.setMinimumWidth(400)
        
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QFormLayout()
        
        self.fields = {}
        
        for col in self.columns:
            # Пропускаем первичный ключ при создании (автоинкремент)
            if self.mode == 'create' and col == self.pk_column:
                continue
            
            field = QLineEdit()
            if self.mode == 'update' and col in self.current_values:
                field.setText(str(self.current_values[col]))
            
            if self.mode == 'update' and col == self.pk_column:
                field.setReadOnly(True)  # Первичный ключ нельзя редактировать
            
            layout.addRow(f"{col}:", field)
            self.fields[col] = field
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def get_data(self) -> Optional[Dict[str, str]]:
        """Возвращает данные из формы."""
        data = {}
        for col, field in self.fields.items():
            value = field.text().strip()
            if value:  # Сохраняем только непустые значения
                data[col] = value
        return data if data else None


class MainWindow(QMainWindow):
    """Главное окно приложения."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Просмотр SQLite базы данных")
        self.setGeometry(100, 100, 600, 500)
        
        self.db_path = None
        
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Кнопка выбора файла
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Файл базы данных не выбран")
        self.file_label.setFont(QFont("Arial", 10))
        file_layout.addWidget(self.file_label)
        
        select_button = QPushButton("Выбрать файл...")
        select_button.clicked.connect(self.select_database)
        file_layout.addWidget(select_button)
        
        layout.addLayout(file_layout)
        
        # Список таблиц
        tables_label = QLabel("Таблицы:")
        tables_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(tables_label)
        
        self.tables_list = QTableWidget()
        self.tables_list.setColumnCount(2)
        self.tables_list.setHorizontalHeaderLabels(["Таблица", "Действие"])
        self.tables_list.horizontalHeader().setStretchLastSection(True)
        self.tables_list.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.tables_list)
        
        self.setLayout(layout)
    
    def select_database(self):
        """Выбор файла базы данных."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл базы данных SQLite",
            "", "SQLite Database (*.db *.sqlite *.sqlite3);;All Files (*.*)"
        )
        
        if file_path:
            self.db_path = file_path
            self.file_label.setText(f"Файл: {file_path}")
            self.load_tables()
    
    def load_tables(self):
        """Загружает список таблиц из базы данных."""
        if not self.db_path:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем список таблиц
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            # Заполняем таблицу
            self.tables_list.setRowCount(len(tables))
            
            for row, table_name in enumerate(tables):
                # Название таблицы
                self.tables_list.setItem(row, 0, QTableWidgetItem(table_name))
                
                # Кнопка "Открыть"
                open_button = QPushButton("Открыть")
                open_button.clicked.connect(lambda checked, t=table_name: self.open_table(t))
                self.tables_list.setCellWidget(row, 1, open_button)
            
            # Настраиваем ширину колонок
            self.tables_list.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить таблицы: {str(e)}")
    
    def open_table(self, table_name: str):
        """Открывает диалог просмотра таблицы."""
        if not self.db_path:
            return
        
        dialog = TableViewDialog(self, self.db_path, table_name)
        dialog.exec_()


def main():
    """Точка входа в приложение."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

