import unittest
from bs4 import BeautifulSoup
from Table import Table
from Cell import Cell
import CellType

# =====================================================================
# БЛОК 1: Тесты инициализации Table
# =====================================================================

class TestTableInitialization(unittest.TestCase):
    """Тесты проверки правильной инициализации Table."""

    def test_initialization_with_normal_table(self):
        """Тест 1.1: Инициализация с обычной HTML таблицей."""
        html = """
        <table>
            <tr>
                <td>A1</td>
                <td>B1</td>
            </tr>
            <tr>
                <td>A2</td>
                <td>B2</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table_tag = soup.find('table')
        table = Table(table_tag)

        # Проверяем размеры
        self.assertEqual(len(table.table), 2, "Должно быть 2 строки")
        self.assertEqual(len(table.table[0]), 2, "Должно быть 2 ячейки в первой строке")
        self.assertEqual(len(table.table[1]), 2, "Должно быть 2 ячейки во второй строке")

        # Проверяем содержимое
        self.assertEqual(table.table[0][0]._content, "A1")
        self.assertEqual(table.table[0][1]._content, "B1")
        self.assertEqual(table.table[1][0]._content, "A2")
        self.assertEqual(table.table[1][1]._content, "B2")

        print("✅ Тест 1.1: Инициализация с обычной таблицей")

    def test_initialization_with_empty_table(self):
        """Тест 1.2: Инициализация с пустой таблицей."""
        html = "<table></table>"
        soup = BeautifulSoup(html, 'html.parser')
        table_tag = soup.find('table')
        table = Table(table_tag)

        # Пустая таблица должна создать структуру [[]]
        self.assertEqual(len(table.table), 1, "Должна быть одна пустая строка")
        self.assertEqual(len(table.table[0]), 0, "Строка должна быть пустой")

        print("✅ Тест 1.2: Инициализация с пустой таблицей")

    def test_initialization_without_tr_tags(self):
        """Тест 1.3: Инициализация с таблицей без <tr> (только <td>)."""
        html = """
        <table>
            <td>Cell1</td>
            <td>Cell2</td>
            <td>Cell3</td>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table_tag = soup.find('table')
        table = Table(table_tag)

        # Должна создать одну строку со всеми ячейками
        self.assertEqual(len(table.table), 1, "Должна быть одна строка")
        self.assertEqual(len(table.table[0]), 3, "Должно быть 3 ячейки")
        self.assertEqual(table.table[0][0]._content, "Cell1")
        self.assertEqual(table.table[0][1]._content, "Cell2")
        self.assertEqual(table.table[0][2]._content, "Cell3")

        print("✅ Тест 1.3: Инициализация без <tr>")


# =====================================================================
# БЛОК 2: Тесты геттеров, сеттеров и методов Table
# =====================================================================

class TestTableGettersAndSetters(unittest.TestCase):
    """Тесты проверки геттеров, сеттеров и методов Table."""

    # --------------- Тесты getter и setter для table ---------------

    def test_getter_table_returns_structure(self):
        """Тест 2.1: Getter table возвращает правильную структуру."""
        html = """
        <table>
            <tr><td>A</td><td>B</td></tr>
            <tr><td>C</td><td>D</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = Table(soup.find('table'))

        structure = table.table
        self.assertIsInstance(structure, list)
        self.assertEqual(len(structure), 2)
        self.assertIsInstance(structure[0][0], Cell)

        print("✅ Тест 2.1: Getter table возвращает структуру")

    def test_setter_table_sets_new_structure(self):
        """Тест 2.2: Setter table устанавливает новую структуру."""
        html = "<table><tr><td>Old</td></tr></table>"
        soup = BeautifulSoup(html, 'html.parser')
        table = Table(soup.find('table'))

        # Создаем новую структуру
        new_html = "<table><tr><td>New1</td><td>New2</td></tr></table>"
        new_soup = BeautifulSoup(new_html, 'html.parser')
        new_structure = []
        for cell_tag in new_soup.find_all('td'):
            new_structure.append(Cell(cell_tag))

        table.table = [new_structure]

        self.assertEqual(len(table.table[0]), 2)
        self.assertEqual(table.table[0][0]._content, "New1")
        self.assertEqual(table.table[0][1]._content, "New2")

        print("✅ Тест 2.2: Setter table устанавливает структуру")

    def test_setter_table_with_empty_structure(self):
        """Тест 2.3: Setter table с пустой структурой."""
        html = "<table><tr><td>Data</td></tr></table>"
        soup = BeautifulSoup(html, 'html.parser')
        table = Table(soup.find('table'))

        table.table = [[]]

        self.assertEqual(len(table.table), 1)
        self.assertEqual(len(table.table[0]), 0)

        print("✅ Тест 2.3: Setter table с пустой структурой")

    # --------------- Тесты метода copy ---------------

    def test_copy_contains_same_data(self):
        """Тест 2.4: Copy содержит те же данные."""
        html = """
        <table>
            <tr><td rowspan="2">A</td><td>B</td></tr>
            <tr><td>C</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = Table(soup.find('table'))
        copied = table.copy

        # Проверяем размеры
        self.assertEqual(len(copied.table), len(table.table))
        self.assertEqual(len(copied.table[0]), len(table.table[0]))

        # Проверяем содержимое
        self.assertEqual(copied.table[0][0]._content, table.table[0][0]._content)
        self.assertEqual(copied.table[0][0].rowspan, table.table[0][0].rowspan)

        print("✅ Тест 2.4: Copy содержит те же данные")

    def test_copy_is_independent(self):
        """Тест 2.5: Copy — независимый объект (изменение не влияет на оригинал)."""
        html = "<table><tr><td>Original</td></tr></table>"
        soup = BeautifulSoup(html, 'html.parser')
        table = Table(soup.find('table'))
        copied = table.copy

        # Изменяем копию
        copied.table[0][0].rowspan = 999

        # Оригинал не должен измениться
        self.assertNotEqual(table.table[0][0].rowspan, 999)
        self.assertEqual(table.table[0][0].rowspan, 1)  # Должно быть исходное значение

        print("✅ Тест 2.5: Copy независим от оригинала")

    def test_copy_deep_copy_of_cells(self):
        """Тест 2.6: Copy выполняет глубокое копирование ячеек."""
        html = "<table><tr><td>Data</td></tr></table>"
        soup = BeautifulSoup(html, 'html.parser')
        table = Table(soup.find('table'))
        copied = table.copy

        # Проверяем, что это разные объекты
        self.assertIsNot(copied.table[0][0], table.table[0][0])

        # Изменяем атрибут ячейки в копии
        original_colspan = table.table[0][0].colspan
        copied.table[0][0].colspan = 999

        # Оригинал не должен измениться
        self.assertEqual(table.table[0][0].colspan, original_colspan)

        print("✅ Тест 2.6: Copy выполняет глубокое копирование")

    # --------------- Тесты метода flip ---------------

    def test_flip_reverses_rows(self):
        """Тест 2.7: Flip правильно переворачивает строки."""
        html = """
        <table>
            <tr><td>A</td><td>B</td><td>C</td></tr>
            <tr><td>D</td><td>E</td><td>F</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = Table(soup.find('table'))
        table.flip

        # Проверяем, что строки перевернулись
        self.assertEqual(table.table[0][0]._content, "C")  # Было справа
        self.assertEqual(table.table[0][1]._content, "B")  # Было в центре
        self.assertEqual(table.table[0][2]._content, "A")  # Было слева

        self.assertEqual(table.table[1][0]._content, "F")
        self.assertEqual(table.table[1][1]._content, "E")
        self.assertEqual(table.table[1][2]._content, "D")

        print("✅ Тест 2.7: Flip переворачивает строки")

    def test_flip_is_independent(self):
        """Тест 2.8: Flip создает независимую копию."""
        html = "<table><tr><td>A</td><td>B</td></tr></table>"
        soup = BeautifulSoup(html, 'html.parser')
        table = Table(soup.find('table'))
        table.flip

        # Изменяем перевернутую таблицу
        table.table[0][0].rowspan = 999

        # Оригинал не должен измениться
        self.assertEqual(table.table[0][0].rowspan, 999)

        print("✅ Тест 2.8: Flip независим от оригинала")

    def test_flip_with_different_row_sizes(self):
        """Тест 2.9: Flip с разным количеством ячеек в строках."""
        html = """
        <table>
            <tr><td>A</td><td>B</td><td>C</td></tr>
            <tr><td>D</td><td>E</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = Table(soup.find('table'))
        table.flip

        # Первая строка: C, B, A
        self.assertEqual(len(table.table[0]), 3)
        self.assertEqual(table.table[0][0]._content, "C")

        # Вторая строка: E, D
        self.assertEqual(len(table.table[1]), 2)
        self.assertEqual(table.table[1][0]._content, "E")

        print("✅ Тест 2.9: Flip с разными размерами строк")

    # --------------- Тесты метода transpose ---------------

    def test_transpose_simple_table(self):
        """Тест 2.10: Transpose правильно транспонирует простую таблицу."""
        html = """
        <table>
            <tr><td>A</td><td>B</td></tr>
            <tr><td>C</td><td>D</td></tr>
            <tr><td>E</td><td>F</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = Table(soup.find('table'))
        table.transpose

        # Было 3x2, стало 2x3
        self.assertEqual(len(table.table), 2, "Должно быть 2 строки")
        self.assertEqual(len(table.table[0]), 3, "Должно быть 3 ячейки")

        # Проверяем содержимое
        # Первая строка: A, C, E (была первый столбец)
        self.assertEqual(table.table[0][0]._content, "A")
        self.assertEqual(table.table[0][1]._content, "C")
        self.assertEqual(table.table[0][2]._content, "E")

        # Вторая строка: B, D, F (был второй столбец)
        self.assertEqual(table.table[1][0]._content, "B")
        self.assertEqual(table.table[1][1]._content, "D")
        self.assertEqual(table.table[1][2]._content, "F")

        print("✅ Тест 2.10: Transpose транспонирует таблицу")

    def test_transpose_swaps_rowspan_colspan(self):
        """Тест 2.11: Transpose меняет местами rowspan и colspan."""
        html = """
        <table>
            <tr><td rowspan="2" colspan="1">A</td><td>B</td></tr>
            <tr><td>C</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = Table(soup.find('table'))

        # У первой ячейки rowspan=2, colspan=1
        self.assertEqual(table.table[0][0].rowspan, 2)
        self.assertEqual(table.table[0][0].colspan, 1)

        table.transpose

        # После транспонирования должны поменяться местами
        # Ищем ячейку "A" в транспонированной таблице
        found = False
        table.table
        for row in table.table:
            for cell in row:
                if cell._content == "A":
                    self.assertEqual(cell.rowspan, 1, "rowspan должен стать 1 (был colspan)")
                    self.assertEqual(cell.colspan, 2, "colspan должен стать 2 (был rowspan)")
                    found = True
                    break

        self.assertTrue(found, "Ячейка 'A' должна быть найдена")

        print("✅ Тест 2.11: Transpose меняет rowspan и colspan")

    def test_transpose_is_independent(self):
        """Тест 2.12: Transpose создает независимую копию."""
        html = "<table><tr><td>A</td><td>B</td></tr><tr><td>C</td><td>D</td></tr></table>"
        soup = BeautifulSoup(html, 'html.parser')
        table = Table(soup.find('table'))
        table.transpose

        # Изменяем транспонированную таблицу
        table.table[0][0].rowspan = 999

        # Оригинал не должен измениться
        self.assertEqual(table.table[0][0].rowspan, 999)
        self.assertNotEqual(table.table[0][0].rowspan, 1)

        print("✅ Тест 2.12: Transpose независим от оригинала")


# =====================================================================
# БЛОК 3: Взаимодействие Cell и Table
# =====================================================================

class TestTableWithCell(unittest.TestCase):
    """Тесты взаимодействия между Table и Cell."""

    def test_get_type(self):
        """Тест 3.1: Проверка типов данных ячеек через таблицу."""
        html = "<table><tr><td>12.20.1980</td><td>текст</td></tr><tr><td>12 см</td><td>12 руб.</td></tr></table>"
        soup = BeautifulSoup(html, 'html.parser')
        table = Table(soup.find('table'))

        # Проверяем типы всех ячеек
        self.assertEqual(table.table[0][0].detailType, CellType.DetailedDataType.DATE,
                         "Должен быть DATE")
        self.assertEqual(table.table[0][1].detailType, CellType.DetailedDataType.STRING,
                         "Должен быть STRING")
        self.assertEqual(table.table[1][0].detailType, CellType.DetailedDataType.MEASUREMENT,
                         "Должен быть MEASUREMENT")
        self.assertEqual(table.table[1][1].detailType, CellType.DetailedDataType.MONEY,
                         "Должен быть MONEY")

        print("✅ Тест 3.1: Типы данных ячеек определены")

    def test_cell_content_extraction(self):
        """Тест 3.2: Проверка извлечения содержимого ячеек."""
        html = """
        <table>
            <tr>
                <td>Простой текст</td>
                <td><b>Жирный</b> и <i>курсив</i></td>
            </tr>
            <tr>
                <td><a href="#">Ссылка</a></td>
                <td><img src="img.jpg" alt="Картинка"/></td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = Table(soup.find('table'))

        # Проверяем извлечение текста
        self.assertEqual(table.table[0][0]._content, "Простой текст")
        self.assertIn("Жирный", table.table[0][1]._content)
        self.assertIn("курсив", table.table[0][1]._content)
        self.assertEqual(table.table[1][0]._content, "Ссылка")

        # Проверяем теги
        self.assertIn('b', table.table[0][1].tags)
        self.assertIn('i', table.table[0][1].tags)
        self.assertIn('a', table.table[1][0].tags)
        self.assertIn('img', table.table[1][1].tags)

        print("✅ Тест 3.2: Содержимое ячеек извлечено")

    def test_cell_rowspan_colspan_from_table(self):
        """Тест 3.3: Проверка rowspan и colspan ячеек в таблице."""
        html = """
        <table>
            <tr>
                <td rowspan="2" colspan="1">A</td>
                <td>B</td>
                <td>C</td>
            </tr>
            <tr>
                <td colspan="2">D</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = Table(soup.find('table'))

        # Ячейка "A" имеет rowspan=2, colspan=1
        self.assertEqual(table.table[0][0].rowspan, 2)
        self.assertEqual(table.table[0][0].colspan, 1)
        self.assertEqual(table.table[0][0]._content, "A")

        # Ячейка "B" имеет rowspan=1, colspan=1 (по умолчанию)
        self.assertEqual(table.table[0][1].rowspan, 1)
        self.assertEqual(table.table[0][1].colspan, 1)

        # Ячейка "D" имеет colspan=2
        self.assertEqual(table.table[1][0].colspan, 2)
        self.assertEqual(table.table[1][0].rowspan, 1)
        self.assertEqual(table.table[1][0]._content, "D")

        print("✅ Тест 3.3: rowspan и colspan считаны правильно")

    def test_modify_cell_attributes_in_table(self):
        """Тест 3.4: Проверка изменения атрибутов ячеек через таблицу."""
        html = """
        <table>
            <tr>
                <td>Cell1</td>
                <td>Cell2</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = Table(soup.find('table'))

        # Изменяем атрибуты первой ячейки
        table.table[0][0].rowspan = 5
        table.table[0][0].colspan = 3
        table.table[0][1].classCell = CellType.ClassCell.CELL_DATA

        # Проверяем изменения
        self.assertEqual(table.table[0][0].rowspan, 5)
        self.assertEqual(table.table[0][0].colspan, 3)
        self.assertEqual(table.table[0][0].classCell, CellType.ClassCell.CELL_NOT_DEFINE)

        # Проверяем, что оригинальные значения сохранены
        self.assertEqual(table.table[0][0].rowspan_original, 1)
        self.assertEqual(table.table[0][0].colspan_original, 1)

        # Вторая ячейка не должна измениться
        self.assertEqual(table.table[0][1].rowspan, 1)
        self.assertEqual(table.table[0][1].colspan, 1)
        self.assertEqual(table.table[0][1].classCell, CellType.ClassCell.CELL_DATA)

        print("✅ Тест 3.4: Атрибуты ячеек изменены")

    def test_cell_types_in_complex_table(self):
        """Тест 3.5: Проверка типов ячеек в сложной таблице со смешанным контентом."""
        html = """
        <table>
            <tr>
                <th>Название</th>
                <th>Дата</th>
                <th>Цена</th>
                <th>Процент</th>
            </tr>
            <tr>
                <td>Товар 1</td>
                <td>2024-01-15</td>
                <td>$99.99</td>
                <td>15%</td>
            </tr>
            <tr>
                <td>Товар 2</td>
                <td>15.01.2024</td>
                <td>1500 руб.</td>
                <td>20.5%</td>
            </tr>
            <tr>
                <td><a href="#">Ссылка</a></td>
                <td></td>
                <td><button>Купить</button></td>
                <td><img src="chart.png"/></td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = Table(soup.find('table'))

        # Проверяем заголовки (первая строка)
        self.assertIn('th', table.table[0][0].tags, "Заголовок должен содержать тег th")
        self.assertEqual(table.table[0][0].detailType, CellType.DetailedDataType.STRING)

        # Проверяем вторую строку данных
        self.assertEqual(table.table[1][0].detailType, CellType.DetailedDataType.STRING)  # Товар 1
        self.assertEqual(table.table[1][1].detailType, CellType.DetailedDataType.DATE)  # 2024-01-15
        self.assertEqual(table.table[1][2].detailType, CellType.DetailedDataType.MONEY)  # $99.99
        self.assertEqual(table.table[1][3].detailType, CellType.DetailedDataType.PERCENT)  # 15%

        # Проверяем третью строку данных
        self.assertEqual(table.table[2][1].detailType, CellType.DetailedDataType.DATE)  # 15.01.2024
        self.assertEqual(table.table[2][2].detailType, CellType.DetailedDataType.MONEY)  # 1500 руб.
        self.assertEqual(table.table[2][3].detailType, CellType.DetailedDataType.PERCENT)  # 20.5%

        # Проверяем четвертую строку (специальные элементы)
        self.assertEqual(table.table[3][0].detailType, CellType.DetailedDataType.LINK)  # Ссылка
        self.assertEqual(table.table[3][1].detailType, CellType.DetailedDataType.NO_DATA)  # Пустая ячейка
        self.assertEqual(table.table[3][2].type, CellType.DataType.FORM)  # Кнопка
        self.assertEqual(table.table[3][3].type, CellType.DataType.MEDIA)  # Картинка

        print("✅ Тест 3.5: Типы в сложной таблице определены")
if __name__ == '__main__':
    unittest.main(verbosity=2)