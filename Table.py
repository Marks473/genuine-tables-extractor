import os
import random
import tempfile

from Cell import Cell
import CellType
from bs4 import BeautifulSoup, Tag
import copy as copy_module
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Border, Side

class Table:
    """Таблица структуры"""

    def __init__(self, table):
        """Получение html таблицы и создания структуры"""
        if isinstance(table, list):
            self._table = table
            return
        # --- НОВЫЙ БЛОК ИСПРАВЛЕНИЯ ---
        # Ищем все tr внутри других tr и "вытаскиваем" их наружу.
        # Это исправляет некорректную вложенность, созданную BeautifulSoup
        for tr in table.find_all('tr'):
            nested_trs = tr.find_all('tr', recursive=False)
            for nested_tr in nested_trs:
                # "Вытаскиваем" вложенную строку и ставим ее ПОСЛЕ родительской
                tr.insert_after(nested_tr.extract())
        # --- КОНЕЦ БЛОКА ИСПРАВЛЕНИЯ ---
        table_span = []
        for row in table.find_all("tr"):
            if row.decode_contents().strip() == '':
                continue

            row_cells = []
            for cell in row.find_all(["td", "th"]):
                row_cells.append(Cell(cell))

            if row_cells:
                table_span.append(row_cells)
        if not table_span:
            # Резервная логика, если tr не найдены
            row_cells = []
            for cell in table.find_all(["td", "th"]):
                row_cells.append(Cell(cell))
            if row_cells:
                table_span.append(row_cells)
        if not table_span:
            table_span = [[]]
        self._table = table_span

    @property
    def table(self):
        """Получение структуры таблицы"""
        return self._table

    @table.setter
    def table(self, value):
        """Задать таблицу в той же структуре"""
        self._table = value

    @property
    def copy(self):
        """Получить ГЛУБОКУЮ копию структуры таблицы"""
        copied = []
        for i in range(len(self._table)):
            copied.append([])
            for j in range(len(self._table[i])):
                cell = self._table[i][j]
                # ВАЖНО: Создаем новый объект Cell с копией данных
                new_cell = Cell(copy_module.copy(cell.data))
                # new_cell.rowspan = cell.rowspan
                # new_cell.colspan = cell.colspan
                # new_cell.rowspan_original = cell.rowspan_original
                # new_cell.colspan_original = cell.colspan_original
                # new_cell.classCell = cell.classCell
                copied[i].append(new_cell)

        # Создаем новый Table из списка
        return Table(copied)

    @property
    def flip(self):
        """Получить таблицу отраженную относительно вертикали"""
        flipped = self.table  # Получаем копию структуры

        # Переворачиваем каждую строку
        for i in range(len(flipped)):
            flipped[i] = flipped[i][::-1]

    @property
    def transpose(self):
        """Получить транспонированную таблицу"""
        rows_data = self.table

        if not rows_data or not rows_data[0]:
            self = Table([[]])

        # Определяем размеры исходной таблицы
        rows = len(rows_data)
        cols = sum(cell.colspan for cell in rows_data[0])

        # Создаем матрицу для отслеживания занятых ячеек
        matrix = [[None for _ in range(cols)] for _ in range(rows)]

        # Заполняем матрицу данными
        for i, row in enumerate(rows_data):
            current_col = 0
            for cell in row:
                # Находим следующую свободную позицию
                while current_col < cols and matrix[i][current_col] is not None:
                    current_col += 1

                # Заполняем ячейки согласно rowspan и colspan
                for r in range(cell.rowspan):
                    for c in range(cell.colspan):
                        if i + r < rows and current_col + c < cols:
                            matrix[i + r][current_col + c] = cell

                current_col += cell.colspan

        # Транспонируем матрицу
        transposed_matrix = list(map(list, zip(*matrix)))

        # Создаем новую структуру данных
        transposed_data = []
        processed_cells = set()

        for i, row in enumerate(transposed_matrix):
            new_row = []
            for j, cell in enumerate(row):
                if cell is not None and id(cell) not in {id(c) for r, c_idx, c in
                                                         [(r, c_idx, transposed_matrix[r][c_idx])
                                                          for r in range(i) for c_idx in
                                                          range(len(transposed_matrix[r]))]
                                                         if (r, c_idx) in processed_cells}:

                    # Проверяем, не обработали ли мы уже эту ячейку
                    cell_id = (i, j, id(cell))
                    if cell_id in processed_cells:
                        continue

                    # Создаем новую ячейку с поменянными местами rowspan и colspan
                    # new_cell = Cell(copy_module.copy(cell.data))
                    cell_rowspan = cell.rowspan
                    cell.rowspan = cell.colspan  # Меняем местами
                    cell.colspan = cell_rowspan  # Меняем местами
                    cell_rowspan_original = cell.rowspan_original
                    cell.rowspan_original = cell.colspan_original  # Меняем местами
                    cell.colspan_original = cell_rowspan_original  # Меняем местами


                    new_row.append(cell)

                    # Отмечаем обработанные ячейки
                    for r in range(cell.rowspan):
                        for c in range(cell.colspan):
                            processed_cells.add((i + r, j + c, id(cell)))

            if new_row:
                transposed_data.append(new_row)
        self.table = transposed_data

    def reset_span(self):
        table_data = self.table
        for i in range(len(table_data)):
            for j in range(len(table_data[i])):
                table_data[i][j].colspan = table_data[i][j].colspan_original
                table_data[i][j].rowspan = table_data[i][j].rowspan_original

    def __repr__(self):
        """Строковое представление таблицы"""
        return f"Table({len(self._table)}x{len(self._table[0]) if self._table else 0})"

    def print(self):

        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            path = tmp.name

        write_to_excel(tables=[self], output_excel_path=path)
        os.startfile(path)


def write_to_excel(tables, output_excel_path, colored: bool = True, sheet_names=None):
    """
    Функция для записи таблиц в Excel с цветовым выделением и границами.
    Параметры:
        tables: список таблиц (объекты вашего класса, содержащие .table)
        output_excel_path: путь для сохранения Excel-файла либо файловый
            объект, например io.BytesIO, если файл нужен в памяти.
        colored: заливать ячейки цветом их класса. Без заливки остаются
            только границы и объединения ячеек.
        sheet_names: имена листов по одному на таблицу; по умолчанию
            листы называются Таблица_1, Таблица_2 и так далее.
    """
    # Определяем стили заливки
    title_fill = PatternFill(start_color="ADD8E6", end_color="ADD8E6", fill_type="solid")
    result_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    not_define_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    sidebar_fill = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
    data_fill = PatternFill(start_color="000000", end_color="000000", fill_type="solid")
    white_font = Font(color="FFFFFF")
    # --- 2. Создаем стиль для границ ---
    # Определяем стиль одной стороны границы (тонкая черная линия)
    thin_side = Side(border_style="thin", color="000000")
    # Создаем объект границы, применяя стиль ко всем четырем сторонам
    thin_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    wb = Workbook()
    if wb.active:
        wb.remove(wb.active)
    for idx, table in enumerate(tables, start=1):
        sheet_name = sheet_names[idx - 1] if sheet_names else f"Таблица_{idx}"
        ws = wb.create_sheet(title=sheet_name)

        occupied = {}
        current_row = 1

        for row_data in table.table:
            if not row_data:
                current_row += 1
                continue

            current_col = 1
            for cell_obj in row_data:
                while (current_row, current_col) in occupied:
                    current_col += 1
                target_cell = ws.cell(row=current_row, column=current_col, value=cell_obj.content)
                # --- 3. Применяем стиль границ КО ВСЕМ ячейкам ---
                target_cell.border = thin_border
                # Применяем заливку в зависимости от типа
                if colored:
                    if cell_obj.classCell == CellType.ClassCell.CELL_TITLE:
                        target_cell.fill = title_fill
                    elif cell_obj.classCell == CellType.ClassCell.CELL_DATA:
                        target_cell.fill = data_fill
                        target_cell.font = white_font
                    elif cell_obj.classCell == CellType.ClassCell.CELL_RESULT:
                        target_cell.fill = result_fill
                    elif cell_obj.classCell == CellType.ClassCell.CELL_NOT_DEFINE:
                        target_cell.fill = not_define_fill
                    elif cell_obj.classCell == CellType.ClassCell.CELL_SIDEBAR:
                        target_cell.fill = sidebar_fill
                rowspan = cell_obj.rowspan_original
                colspan = cell_obj.colspan_original
                if rowspan > 1 or colspan > 1:
                    end_row = current_row + rowspan - 1
                    end_col = current_col + colspan - 1
                    ws.merge_cells(
                        start_row=current_row,
                        start_column=current_col,
                        end_row=end_row,
                        end_column=end_col
                    )
                    # Примечание: Excel автоматически применяет стиль (включая границы)
                    # от верхней левой ячейки ко всей объединенной области.
                    # Поэтому нет необходимости проходиться по всем ячейкам в `merge_cells`.

                    for r in range(current_row, end_row + 1):
                        for c in range(current_col, end_col + 1):
                            occupied[(r, c)] = True
                else:
                    occupied[(current_row, current_col)] = True

                # Увеличиваем столбец на ширину текущей ячейки
                current_col += colspan
            current_row += 1
    wb.save(output_excel_path)