"""
Тесты сетки покрытия и объектной модели таблицы.

Основа -- примеры из постановки задачи расширения браузера: что должна
показать подсказка при наведении на ячейку таблиц #1 и #6 из
table_for_test.html. Координаты везде -- как на странице, с нуля.
"""

import unittest

from bs4 import BeautifulSoup

import Heuristic
from config import TEST_TABLES_PATH
from Table import Table
from TableGrid import TableGrid
from TableStructure import (DataCell, MARK, ResultCell, SidebarCell, StructureTable,
                            TitleCell, parse_dimension)

REGIONS = '🌍 Глобальные продажи по регионам'


def texts(cells):
    return [cell.text for cell in cells]


def load_tables():
    with open(TEST_TABLES_PATH, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    return soup, soup.find_all("table", recursive=True)


class test_grid(unittest.TestCase):
    """Сетка покрытия таблицы #1"""
    @classmethod
    def setUpClass(cls):
        _, tables = load_tables()
        cls.grid = TableGrid(Table(tables[0]))

    def test_size(self):
        self.assertEqual((self.grid.height, self.grid.width), (15, 21))

    def test_cell_at(self):
        self.assertEqual(self.grid.cell_at(13, 11).content, '14200')

    def test_rowspan_is_one_cell(self):
        """Ячейка "2023" растянута на пять строк: в каждой из них тот же объект"""
        first = self.grid.cell_at(4, 0)
        self.assertEqual(first.content, '📅 2023')
        for row in range(5, 9):
            self.assertIs(self.grid.cell_at(row, 0), first)

    def test_column_above_has_no_repeats(self):
        above = self.grid.column_above(self.grid.cell_at(5, 0))
        self.assertEqual([cell.content for cell in above], ['Год'])


class test_hierarchy(unittest.TestCase):
    """Пути по заголовкам и атрибутам таблицы #1: примеры П1--П3"""
    @classmethod
    def setUpClass(cls):
        _, tables = load_tables()
        cls.structure = StructureTable.from_table(Table(tables[0]))

    def test_orientation(self):
        self.assertEqual(self.structure.orientation, 'top')

    def test_data_cell(self):
        """П1: ячейка 14200"""
        cell = self.structure.cell_at(13, 11)
        self.assertIsInstance(cell, DataCell)
        self.assertEqual(texts(cell.header_path),
                         [REGIONS, '🇨🇳 Азия', 'Электроника', 'Ноутбуки'])
        self.assertEqual(texts(cell.sidebar_path), ['📅 2024', '📈 Итого 2024'])
        self.assertEqual(cell.hint()[-1], 'ячейка области данных')
        self.assertEqual(cell.value, 14200)

    def test_title_cell(self):
        """П2: заголовок "Ноутбуки" под "США" """
        cell = self.structure.cell_at(3, 3)
        self.assertIsInstance(cell, TitleCell)
        self.assertEqual(texts(cell.header_path), [REGIONS, '🇺🇸 США', 'Электроника'])
        self.assertEqual(cell.parent.text, 'Электроника')
        self.assertEqual(cell.hint(), [
            f'Подзаголовок: "{REGIONS}" / "🇺🇸 США" / "Электроника"',
            'ячейка области заголовков'])

    def test_sidebar_cell(self):
        """П3: атрибут "Q3" в 2023 году"""
        cell = self.structure.cell_at(6, 1)
        self.assertIsInstance(cell, SidebarCell)
        self.assertEqual(cell.hint(), ['Заголовок: "Квартал"', 'Податрибут: "📅 2023"',
                                       'ячейка области атрибутов'])

    def test_children_and_data_types(self):
        electronics = self.structure.cell_at(2, 2)
        self.assertEqual(texts(electronics.children), ['Смартфоны', 'Ноутбуки'])
        self.assertEqual(len(self.structure.cell_at(3, 3).data_cells), 10)
        self.assertEqual({kind.name for kind in electronics.data_types}, {'DIMENSION'})

    def test_merged_cell_gives_one_object(self):
        self.assertIs(self.structure.cell_at(0, 2), self.structure.cell_at(0, 13))

    def test_grand_total(self):
        """Общий итог агрегирует все ячейки данных выше, включая строки "Итого 2023" и "Итого 2024" """
        cell = self.structure.cell_at(14, 2)
        self.assertIsInstance(cell, ResultCell)
        self.assertEqual(len(cell.aggregated), 10)


class test_cross_section(unittest.TestCase):
    """Перерезы таблицы #6: примеры П4 и П5"""
    @classmethod
    def setUpClass(cls):
        _, tables = load_tables()
        cls.structure = StructureTable.from_table(Table(tables[5]))

    def test_brigade_total(self):
        """П4: 91 в строке "Итого по 2-ой бригаде" """
        cell = self.structure.cell_at(10, 4)
        self.assertIsInstance(cell, ResultCell)
        self.assertEqual(texts(cell.aggregated), ['15', '26', '50'])
        self.assertEqual(cell.hint(), ['Агрегирует ячеек: 3', 'ячейка является агрегацией'])

    def test_grand_total(self):
        """П5: 96 235 в строке "Итого" пропускает промежуточные итоги"""
        cell = self.structure.cell_at(19, 8)
        self.assertEqual(texts(cell.aggregated),
                         ['5 880', '6 370', '3 840', '900'] + ['3 000', '4 050', '5 000'] * 3)

    def test_label(self):
        cell = self.structure.cell_at(10, 1)
        self.assertTrue(cell.is_label)
        self.assertEqual(cell.aggregated, [])
        self.assertEqual(cell.hint(), ['подпись итоговой строки'])

    def test_sums(self):
        """Промежуточные итоги равны сумме, общий итог тестовой таблицы -- нет"""
        for row, col in ((6, 8), (10, 4)):
            cell = self.structure.cell_at(row, col)
            self.assertEqual(sum(data.value for data in cell.aggregated), cell.value)

        total = self.structure.cell_at(19, 8)
        self.assertEqual(sum(data.value for data in total.aggregated), 53140)
        self.assertEqual(total.value, 96235)


class test_structure_table(unittest.TestCase):
    """Общие свойства модели"""
    @classmethod
    def setUpClass(cls):
        cls.soup, cls.tables = load_tables()

    def test_left_orientation(self):
        """Таблица с заголовком слева разбирается повёрнутой, а координаты остаются как на странице"""
        structure = StructureTable.from_table(Table(self.tables[29]))
        self.assertEqual(structure.orientation, 'left')
        self.assertEqual((structure.height, structure.width), (6, 2))
        self.assertIsInstance(structure.cell_at(0, 0), TitleCell)
        self.assertIsInstance(structure.cell_at(0, 1), DataCell)
        self.assertEqual(texts(structure.cell_at(2, 1).header_path),
                         [structure.cell_at(2, 0).text])

    def test_source_is_not_changed(self):
        StructureTable.from_table(Table(self.tables[5]))
        self.assertEqual(self.soup.select(f'[{MARK}]'), [])

    def test_not_genuine(self):
        with self.assertRaises(Heuristic.LayoutError):
            StructureTable.from_table(Table(self.tables[1]))

    def test_every_cell_has_object(self):
        """В каждой подлинной таблице набора каждая клетка страницы ведёт к объекту"""
        for index, tag in enumerate(self.tables):
            try:
                structure = StructureTable.from_table(Table(tag))
            except (Heuristic.LayoutError, Heuristic.TitleTypeError, Heuristic.DataTypeError):
                continue
            for cell in structure.cells:
                self.assertIs(structure.cell_at(cell.row, cell.col), cell,
                              f'таблица {index}, ячейка {cell!r}')


class test_parse_dimension(unittest.TestCase):
    """Разбор записи числа по тем же правилам, что и тип DIMENSION"""

    def test_formats(self):
        cases = {
            '12': 12, '-12': -12, '12,5': 12.5, '5 880': 5880, '12 123,5': 12123.5,
            ',78': 0.78, '1,368,524': 1368524, '1.368.524,5': 1368524.5,
        }
        for text, expected in cases.items():
            self.assertAlmostEqual(parse_dimension(text), expected, msg=text)

    def test_ambiguous_comma(self):
        """154,977 -- дробное число: так его понимает и определение типа"""
        self.assertAlmostEqual(parse_dimension('154,977'), 154.977)

    def test_not_a_number(self):
        self.assertIsNone(parse_dimension('Итого'))
