import unittest

import CellType
import Heuristic
from bs4 import BeautifulSoup

from CellType import ClassCell
from Table import Table, write_to_excel

class test_head(unittest.TestCase):
    """Тест для проверки простых подлых таблиц"""
    @classmethod
    def setUpClass(cls):
        html_path = "table_for_test.html"
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
        cls.tables = soup.find_all("table", recursive=True)

    def test_1_head(self):
        """Тест 1_1"""
        table = Table(self.tables[0]).copy
        try:
            Heuristic.vertical_check(table)
            table_data = table.table
            self.assertEqual(table_data[0][0].classCell, ClassCell.CELL_TITLE, f'{table_data[0][0].content} должен быть заголовком')
            self.assertEqual(table_data[3][3].classCell, ClassCell.CELL_TITLE, f'{table_data[3][3].content} должен быть заголовком')
            self.assertEqual(table_data[1][4].classCell, ClassCell.CELL_TITLE, f'{table_data[1][4].content} должен быть заголовком')
            self.assertEqual(table_data[0][-1].classCell, ClassCell.CELL_TITLE,
                             f'{table_data[0][-1].content} должен быть заголовком')
            self.assertNotEqual(table_data[4][5].classCell, ClassCell.CELL_TITLE,
                             f'{table_data[4][5].content} не должен быть заголовком')
        except(Exception) as err:
            self.fail(f"Функция vertical_check() неожиданно выбросила исключение: {err}")
        print("✅ Тест 1")

    def test_2_head(self):
        table = Table(self.tables[1]).copy
        with self.assertRaises(Heuristic.LayoutError) as err:
            Heuristic.vertical_check(table)
        self.assertTrue('Одежда' in str(err.exception))

        print("✅ Тест 2")

    def test_11_head(self):
        table = Table(self.tables[10]).copy
        with self.assertRaises(Heuristic.DataTypeError) as err:
            Heuristic.vertical_check(table)
        self.assertTrue('PHOTO' in str(err.exception))
        print("✅ Тест 2")

    def test_14_head(self):
        table = Table(self.tables[13]).copy
        with self.assertRaises(Heuristic.LayoutError) as err:
            Heuristic.vertical_check(table)
        self.assertTrue('B' in str(err.exception))


class test_data(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        html_path = "table_for_test.html"
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
        cls.tables = soup.find_all("table", recursive=True)

    def test_1_data(self):
        """Тест 1_1"""
        table = Table(self.tables[0]).copy
        try:
            Heuristic.vertical_check(table)
            table_data = table.table
            self.assertEqual(table_data[4][3].classCell, ClassCell.CELL_DATA, f'{table_data[4][3].content} должен быть ячейкой - данных')
            self.assertEqual(table_data[5][2].classCell, ClassCell.CELL_DATA, f'{table_data[5][2].content} должен быть ячейкой - данных')
            self.assertEqual(table_data[-2][-1].classCell, ClassCell.CELL_DATA, f'{table_data[-1][-1].content} должен быть ячейкой - данных')
        except(Exception) as err:
            self.fail(f"Функция vertical_check() неожиданно выбросила исключение: {err}")
        print("✅ Тест 1")
    def test_8_data(self):
        table = Table(self.tables[7]).copy
        try:
            Heuristic.vertical_check(table)
            table_data = table.table
            self.assertEqual(table_data[4][3].classCell, ClassCell.CELL_DATA, f'{table_data[4][3].content} должен быть ячейкой - данных')
            self.assertEqual(table_data[5][2].classCell, ClassCell.CELL_DATA, f'{table_data[5][2].content} должен быть ячейкой - данных')
            self.assertEqual(table_data[-2][-1].classCell, ClassCell.CELL_DATA, f'{table_data[-1][-1].content} должен быть ячейкой - данных')
        except(Exception) as err:
            self.fail(f"Функция vertical_check() неожиданно выбросила исключение: {err}")
        print("✅ Тест 1")

    def test_9_data(self):
        table = Table(self.tables[8]).copy
        try:
            Heuristic.vertical_check(table)
            table_data = table.table
            self.assertEqual(table_data[2][3].classCell, ClassCell.CELL_DATA, f'{table_data[2][3].content} должен быть ячейкой - данных')
            self.assertEqual(table_data[3][2].classCell, ClassCell.CELL_DATA, f'{table_data[3][2].content} должен быть ячейкой - данных')
            self.assertEqual(table_data[-2][-1].classCell, ClassCell.CELL_DATA, f'{table_data[-2][-1].content} должен быть ячейкой - данных')
        except(Exception) as err:
            self.fail(f"Функция vertical_check() неожиданно выбросила исключение: {err}")
        print("✅ Тест 1")
    def test_10_data(self):
        table = Table(self.tables[9]).copy
        with self.assertRaises(Heuristic.DataTypeError) as err:
            Heuristic.vertical_check(table)
        self.assertTrue('Олег' in str(err.exception))
    def test_12_data(self):
        table = Table(self.tables[11]).copy
        with self.assertRaises(Heuristic.DataTypeError) as err:
            Heuristic.vertical_check(table)
        self.assertTrue('Upload' in str(err.exception))

    def test_13_data(self):
        table = Table(self.tables[12]).copy
        try:
            Heuristic.vertical_check(table)
        except(Exception) as err:
            self.fail(f"Функция vertical_check() неожиданно выбросила исключение: {err}")

class test_result(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        html_path = "table_for_test.html"
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
        cls.tables = soup.find_all("table", recursive=True)

    def test_1_result(self):
        table = Table(self.tables[0]).copy
        try:
            Heuristic.vertical_check(table)
            table_data = table.table
            self.assertEqual(table_data[-1][3].classCell, ClassCell.CELL_RESULT, f'{table_data[4][3].content} должен быть ячейкой - результатов')
            self.assertEqual(table_data[-1][2].classCell, ClassCell.CELL_RESULT, f'{table_data[5][2].content} должен быть ячейкой - результатов')
            self.assertNotEqual(table_data[-2][-1].classCell, ClassCell.CELL_RESULT, f'{table_data[-1][-1].content} не должен быть ячейкой - результатов')
        except(Exception) as err:
            self.fail(f"Функция vertical_check() неожиданно выбросила исключение: {err}")
        print("✅ Тест 1")

    def test_4_result(self):
        table = Table(self.tables[3]).copy
        with self.assertRaises(Heuristic.DataTypeError) as err:
            Heuristic.vertical_check(table)
        self.assertTrue('Меню' in str(err.exception))

    def test_5_head(self):
        table = Table(self.tables[4]).copy
        with self.assertRaises(Heuristic.LayoutError) as err:
            Heuristic.vertical_check(table)
        self.assertTrue('должен быть на всю ширину таблицы' in str(err.exception))
    def test_6_head(self):
        table = Table(self.tables[5]).copy
        try:
            Heuristic.vertical_check(table)
            table_data = table.table
            self.assertEqual(table_data[-1][3].classCell, ClassCell.CELL_RESULT,
                             f'{table_data[-1][3].content} должен быть ячейкой - результатов')
            self.assertEqual(table_data[-1][3].classCell, ClassCell.CELL_RESULT,
                             f'{table_data[-1][3].content} должен быть ячейкой - результатов')
            self.assertEqual(table_data[-1][0].classCell, ClassCell.CELL_RESULT,
                                f'{table_data[-1][1].content}  должен быть ячейкой - результатов')
        except(Exception) as err:
            self.fail(f"Функция vertical_check() неожиданно выбросила исключение: {err}")
    def test_7_head(self):
        table = Table(self.tables[6]).copy
        try:
            Heuristic.vertical_check(table)
            table_data = table.table
            self.assertEqual(table_data[-1][3].classCell, ClassCell.CELL_RESULT,
                             f'{table_data[-1][3].content} должен быть ячейкой - результатов')
            self.assertEqual(table_data[-1][3].classCell, ClassCell.CELL_RESULT,
                             f'{table_data[-1][3].content} должен быть ячейкой - результатов')
            self.assertEqual(table_data[-1][0].classCell, ClassCell.CELL_RESULT,
                                f'{table_data[-1][1].content}  должен быть ячейкой - результатов')
        except(Exception) as err:
            self.fail(f"Функция vertical_check() неожиданно выбросила исключение: {err}")


class test_sidebar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        html_path = "table_for_test.html"
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
        cls.tables = soup.find_all("table", recursive=True)

    def test_1_result(self):
        table = Table(self.tables[0]).copy
        try:
            Heuristic.vertical_check(table)
            table_data = table.table
            self.assertEqual(table_data[4][0].classCell, ClassCell.CELL_SIDEBAR,
                             f'{table_data[4][0].content} должен быть ячейкой - боковик')
            self.assertEqual(table_data[7][0].classCell, ClassCell.CELL_SIDEBAR,
                             f'{table_data[7][0].content} должен быть ячейкой - боковик')
            self.assertEqual(table_data[9][1].classCell, ClassCell.CELL_SIDEBAR,
                             f'{table_data[9][1].content} должен быть ячейкой - боковик')
            self.assertEqual(table_data[9][2].classCell, ClassCell.CELL_DATA,
                                f'{table_data[9][2].content}  должен быть ячейкой - данных')
        except(Exception) as err:
            self.fail(f"Функция vertical_check() неожиданно выбросила исключение: {err}")
        print("✅ Тест 1")

    def test_3_head(self):
        table = Table(self.tables[2]).copy
        with self.assertRaises(Heuristic.LayoutError) as err:
            Heuristic.vertical_check(table)
        self.assertTrue('Q1' in str(err.exception))
        print("✅ Тест 3")

    def test_15_sidebar(self):
        table = Table(self.tables[14]).copy
        good_table = Heuristic.get_genuine(table)


    def test_16_sidebar(self):
        table = Table(self.tables[15]).copy
        good_table = Heuristic.get_genuine(table)


class test_wiktionary(unittest.TestCase):
    """Таблицы со страницы Викисловаря «Шаблоны словоизменений/Глаголы»: все подлинные"""
    @classmethod
    def setUpClass(cls):
        html_path = "table_for_test.html"
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
        cls.tables = soup.find_all("table", recursive=True)

    def _assert_genuine(self, index):
        table = Table(self.tables[index]).copy
        try:
            return Heuristic.get_genuine(table)
        except(Exception) as err:
            self.fail(f"Функция get_genuine() неожиданно выбросила исключение: {err}")

    def test_17_conjugation_types(self):
        """Таблица типов спряжения"""
        table_data = self._assert_genuine(16).table
        self.assertEqual(table_data[1][0].classCell, ClassCell.CELL_SIDEBAR,
                         f'{table_data[1][0].content} должен быть ячейкой - боковик')
        self.assertEqual(table_data[2][0].classCell, ClassCell.CELL_DATA,
                         f'{table_data[2][0].content} должен быть ячейкой - данных')
        self.assertEqual(table_data[7][1].classCell, ClassCell.CELL_DATA,
                         f'{table_data[7][1].content} должен быть ячейкой - данных')

    def test_18_consonant_alternation(self):
        """Стандартные чередования согласных"""
        self._assert_genuine(17)

    def test_19_stress_present(self):
        """Образцы основных схем ударения настоящего времени"""
        self._assert_genuine(18)

    def test_20_stress_past(self):
        """Образцы основных схем ударения прошедшего времени"""
        self._assert_genuine(19)


if __name__ == '__main__':
    unittest.main(verbosity=2)