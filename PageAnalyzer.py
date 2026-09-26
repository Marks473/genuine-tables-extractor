"""
Разбор одной таблицы страницы для расширения браузера.

Решение принимается так же, как во всём конвейере и в
tools/highlight_tables.py: сначала эвристика, и если она таблицу пропустила,
-- модель. Для подлинной таблицы дополнительно строится объектная модель,
и по ней для каждой ячейки готовится подсказка.

Ячейки страницы расширение нумерует атрибутом ``data-gt-id``. Номер
доходит до объектов модели вместе с тегом, поэтому ответ описывает ячейки
теми же номерами, и расширение сразу находит нужную ячейку на странице.
"""

import pandas as pd
from bs4 import BeautifulSoup

from heuristic_errors import DataTypeError, LayoutError, TitleTypeError
from MLverification import MLVerification, get_parameters_from_table
from Table import Table
from TableExporter import TableExporter
from TableStructure import StructureTable

# Атрибут, которым расширение нумерует ячейки страницы
CELL_ID = 'data-gt-id'

HEURISTIC_ERRORS = (LayoutError, TitleTypeError, DataTypeError)


class PageAnalyzer:
    """Разбирает таблицы страницы готовой моделью."""

    def __init__(self, model: MLVerification):
        """
        Args:
            model: загруженная модель; загрузка долгая, поэтому модель
                создаётся один раз и передаётся сюда готовой
        """
        self._model = model

    def analyze(self, html: str, source: dict = None) -> dict:
        """
        Решает, подлинная ли таблица, и готовит всё, что нужно расширению.

        Args:
            html: HTML-код одной таблицы, ячейки пронумерованы атрибутом data-gt-id
            source: откуда таблица; попадает в выгрузку JSON как есть

        Returns:
            Словарь с ключами:

            * ``genuine`` -- подлинная ли таблица;
            * ``reason``  -- почему таблица не подлинная, иначе None;
            * ``cells``   -- номер ячейки -> её роль и подсказка;
            * ``export``  -- описание таблицы для выгрузки в JSON.

            Последние два ключа есть только у подлинной таблицы.
        """
        tag = BeautifulSoup(html, 'html.parser').find('table')
        if tag is None:
            return {'genuine': False, 'reason': 'в переданном коде нет таблицы'}
        table = Table(tag)

        try:
            structure = StructureTable.from_table(table)
        except HEURISTIC_ERRORS as err:
            return {'genuine': False, 'reason': str(err)}

        features = pd.DataFrame([get_parameters_from_table(table)])
        if self._model.wrapper.predict(features)[0] != 'genuine':
            return {'genuine': False,
                    'reason': 'эвристика пропустила, модель отклонила'}

        return {
            'genuine': True,
            'reason': None,
            'cells': _describe_cells(structure),
            'export': TableExporter(structure).to_dict(source),
        }


def _describe_cells(structure: StructureTable) -> dict:
    """Готовит подсказку для каждой ячейки, у которой есть номер страницы."""
    cells = {}
    for cell in structure.cells:
        number = cell.cell.data.get(CELL_ID)
        if number is None:
            continue
        cells[number] = {
            'role': cell.role,
            'lines': cell.hint(),
            'types': cell.type_line(),
            'highlight': [other.cell.data.get(CELL_ID) for other in cell.related()
                          if other.cell.data.get(CELL_ID) is not None],
        }
    return cells
