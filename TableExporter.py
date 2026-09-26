"""
Выгрузка подлинной таблицы в JSON и Excel.

Всё нужное уже есть в объектной модели :class:`StructureTable`, поэтому
выгрузка ничего не вычисляет сама, а только обходит объекты: каждая ячейка
становится записью, пути -- списками текстов, подзаголовки и податрибуты --
деревьями.

Координаты и порядок строк берутся такими, как таблица стоит на странице,
даже если эвристика разбирала её повёрнутой. Формат JSON описан в
документации расширения браузера, docs/json_format.md.
"""

import copy
import io

from Cell import Cell
from Table import Table, write_to_excel
from TableStructure import ResultCell, StructureTable

# Версия формата JSON: меняется, если меняется смысл полей
FORMAT_VERSION = 'genuine-table/1'


class TableExporter:
    """Превращает объектную модель таблицы в JSON или файл Excel."""

    def __init__(self, structure: StructureTable):
        """
        Args:
            structure: объектная модель подлинной таблицы
        """
        self._structure = structure

    def to_dict(self, source: dict = None) -> dict:
        """
        Собирает описание таблицы для выгрузки в JSON.

        Args:
            source: откуда взята таблица, например адрес и заголовок страницы
                и номер таблицы на ней. Записывается как есть

        Returns:
            Словарь, который можно передать json.dump
        """
        structure = self._structure
        return {
            'format': FORMAT_VERSION,
            'source': source or {},
            'orientation': structure.orientation,
            'size': {'rows': structure.height, 'cols': structure.width},
            'header': [_node(cell) for cell in structure.titles if cell.parent is None],
            'sidebar': [_node(cell) for cell in structure.sidebars if cell.parent is None],
            'cells': [_record(cell) for cell in structure.cells],
        }

    def to_xlsx(self, colored: bool = True) -> bytes:
        """
        Записывает таблицу в файл Excel в памяти.

        Используется та же функция, что и в остальной программе,
        :func:`Table.write_to_excel`: объединения ячеек сохраняются, заливка
        показывает класс ячейки.

        Args:
            colored: заливать ли ячейки цветом их класса

        Returns:
            Содержимое файла .xlsx
        """
        return tables_to_xlsx([self._structure], colored=colored)

    def page_table(self) -> Table:
        """
        Таблица в ориентации страницы, ячейки которой несут класс из эвристики.

        Returns:
            Таблицу, которую понимает :func:`Table.write_to_excel`
        """
        return Table([[_excel_cell(cell) for cell in row] for row in self._structure.rows])


def tables_to_xlsx(structures: list, sheet_names: list = None, colored: bool = True) -> bytes:
    """
    Записывает несколько таблиц в один файл Excel, каждую на свой лист.

    Args:
        structures: объектные модели таблиц
        sheet_names: имена листов по одному на таблицу; по умолчанию
            Таблица_1, Таблица_2 и так далее
        colored: заливать ли ячейки цветом их класса

    Returns:
        Содержимое файла .xlsx
    """
    tables = [TableExporter(structure).page_table() for structure in structures]
    buffer = io.BytesIO()
    write_to_excel(tables=tables, output_excel_path=buffer, colored=colored,
                   sheet_names=sheet_names)
    return buffer.getvalue()


def _node(cell) -> dict:
    """Узел дерева заголовков или атрибутов вместе со всеми потомками."""
    children = sorted(cell.children, key=lambda child: (child.row, child.col))
    return {
        'text': cell.text,
        'cell': [cell.row, cell.col],
        'children': [_node(child) for child in children],
    }


def _record(cell) -> dict:
    """Запись об одной ячейке."""
    record = {
        'row': cell.row,
        'col': cell.col,
        'rowspan': cell.rowspan,
        'colspan': cell.colspan,
        'text': cell.text,
        'role': cell.role,
        'type': cell.data_type.name,
        'detail_type': cell.detail_type.name,
        'header_path': [title.text for title in cell.header_path],
        'sidebar_path': [attribute.text for attribute in cell.sidebar_path],
    }
    if isinstance(cell, ResultCell):
        record['aggregates'] = [[data.row, data.col] for data in cell.aggregated]
    return record


def _excel_cell(cell) -> Cell:
    """
    Ячейка для записи в Excel в ориентации страницы.

    Размеры повёрнутой при разборе ячейки поменяны местами, а тег хранит
    исходные. Поэтому ячейка создаётся заново по копии тега, и ей
    переносится класс, который проставила эвристика.
    """
    page_cell = Cell(copy.copy(cell.cell.data))
    page_cell.classCell = cell.cell.classCell
    return page_cell
