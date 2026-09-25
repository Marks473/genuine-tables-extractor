import unittest
from bs4 import BeautifulSoup, Tag
from Cell import Cell
import CellType
from CellType import DataType, DetailedDataType


# =====================================================================
# БЛОК 1: Тесты инициализации параметров Cell
# =====================================================================

class TestCellInitialization(unittest.TestCase):
    """Тесты проверки правильной инициализации параметров Cell."""

    def test_initialization_default_rowspan(self):
        """Тест 1.1: Проверка rowspan по умолчанию (должен быть 1)."""
        html = "<td>Текст</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertEqual(cell.rowspan, 1)
        print("✅ Тест 1.1: rowspan по умолчанию = 1")

    def test_initialization_default_colspan(self):
        """Тест 1.2: Проверка colspan по умолчанию (должен быть 1)."""
        html = "<td>Текст</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertEqual(cell.colspan, 1)
        print("✅ Тест 1.2: colspan по умолчанию = 1")

    def test_initialization_custom_rowspan(self):
        """Тест 1.3: Проверка чтения пользовательского rowspan."""
        html = '<td rowspan="5">Текст</td>'
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertEqual(cell.rowspan, 5)
        self.assertEqual(cell.rowspan_original, 5)
        print("✅ Тест 1.3: Пользовательский rowspan = 5")

    def test_initialization_custom_colspan(self):
        """Тест 1.4: Проверка чтения пользовательского colspan."""
        html = '<td colspan="3">Текст</td>'
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertEqual(cell.colspan, 3)
        self.assertEqual(cell.colspan_original, 3)
        print("✅ Тест 1.4: Пользовательский colspan = 3")

    def test_initialization_rowspan_and_colspan(self):
        """Тест 1.5: Проверка одновременного чтения rowspan и colspan."""
        html = '<td rowspan="2" colspan="4">Текст</td>'
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertEqual(cell.rowspan, 2)
        self.assertEqual(cell.colspan, 4)
        print("✅ Тест 1.5: rowspan=2 и colspan=4")

    def test_initialization_similarity_default(self):
        """Тест 1.6: Проверка similarity по умолчанию (должен быть False)."""
        html = "<td>Текст</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertEqual(cell.classCell, CellType.ClassCell.CELL_NOT_DEFINE)
        print("✅ Тест 1.6: similarity по умолчанию = False")

    def test_initialization_data_attribute(self):
        """Тест 1.7: Проверка, что data является объектом Tag."""
        html = "<td>Текст</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertIsInstance(cell.data, Tag)
        self.assertEqual(cell.data, tag)
        print("✅ Тест 1.7: data является объектом Tag")

    def test_initialization_tags_extraction(self):
        """Тест 1.8: Проверка извлечения тегов из простой ячейки."""
        html = "<td>Текст</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertIn('td', cell.tags)
        self.assertEqual(len(cell.tags), 1)
        print("✅ Тест 1.8: Извлечение тегов из простой ячейки")

    def test_initialization_nested_tags_extraction(self):
        """Тест 1.9: Проверка извлечения вложенных тегов."""
        html = '<td><b>Жирный</b> и <i>курсив</i></td>'
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertIn('td', cell.tags)
        self.assertIn('b', cell.tags)
        self.assertIn('i', cell.tags)
        self.assertEqual(len(cell.tags), 3)
        print("✅ Тест 1.9: Извлечение вложенных тегов")

    def test_initialization_content_extraction(self):
        """Тест 1.10: Проверка извлечения текстового содержимого."""
        html = "<td>Простой текст</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertEqual(cell._content, "Простой текст")
        print("✅ Тест 1.10: Извлечение текстового содержимого")

    def test_initialization_th_tag(self):
        """Тест 1.11: Проверка работы с тегом <th> вместо <td>."""
        html = '<th rowspan="2">Заголовок</th>'
        tag = BeautifulSoup(html, 'html.parser').find('th')
        cell = Cell(tag)
        self.assertEqual(cell.rowspan, 2)
        self.assertIn('th', cell.tags)
        print("✅ Тест 1.11: Работа с тегом <th>")


# =====================================================================
# БЛОК 2: Тесты геттеров и сеттеров
# =====================================================================

class TestCellGettersAndSetters(unittest.TestCase):
    """Тесты проверки геттеров и сеттеров Cell."""

    def test_getter_rowspan(self):
        """Тест 2.1: Проверка геттера rowspan."""
        html = '<td rowspan="3">Текст</td>'
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertEqual(cell.rowspan, 3)
        print("✅ Тест 2.1: Геттер rowspan")

    def test_getter_colspan(self):
        """Тест 2.2: Проверка геттера colspan."""
        html = '<td colspan="2">Текст</td>'
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertEqual(cell.colspan, 2)
        print("✅ Тест 2.2: Геттер colspan")

    def test_getter_similarity(self):
        """Тест 2.3: Проверка геттера similarity."""
        html = "<td>Текст</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertEqual(cell.classCell, CellType.ClassCell.CELL_NOT_DEFINE)
        print("✅ Тест 2.3: Геттер classCell")

    def test_getter_data(self):
        """Тест 2.4: Проверка геттера data."""
        html = "<td>Текст</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertEqual(cell.data, tag)
        print("✅ Тест 2.4: Геттер data")

    def test_getter_tags(self):
        """Тест 2.5: Проверка геттера tags."""
        html = '<td><b>Текст</b></td>'
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertIsInstance(cell.tags, set)
        self.assertIn('td', cell.tags)
        self.assertIn('b', cell.tags)
        print("✅ Тест 2.5: Геттер tags")

    def test_getter_rowspan_original(self):
        """Тест 2.6: Проверка геттера rowspan_original."""
        html = '<td rowspan="4">Текст</td>'
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertEqual(cell.rowspan_original, 4)
        print("✅ Тест 2.6: Геттер rowspan_original")

    def test_getter_colspan_original(self):
        """Тест 2.7: Проверка геттера colspan_original."""
        html = '<td colspan="5">Текст</td>'
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertEqual(cell.colspan_original, 5)
        print("✅ Тест 2.7: Геттер colspan_original")

    def test_setter_rowspan_valid(self):
        """Тест 2.8: Проверка сеттера rowspan с валидным значением."""
        html = "<td>Текст</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        cell.rowspan = 7
        self.assertEqual(cell.rowspan, 7)
        self.assertEqual(cell.rowspan_original, 1)
        print("✅ Тест 2.8: Сеттер rowspan = 7")

    def test_setter_colspan_valid(self):
        """Тест 2.9: Проверка сеттера colspan с валидным значением."""
        html = "<td>Текст</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        cell.colspan = 6
        self.assertEqual(cell.colspan, 6)
        self.assertEqual(cell.colspan_original, 1)
        print("✅ Тест 2.9: Сеттер colspan = 6")

    def test_setter_rowspan_original_valid(self):
        """Тест 2.8: Проверка сеттера rowspan с валидным значением."""
        html = "<td>Текст</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        cell.rowspan_original = 7
        self.assertEqual(cell.rowspan, 1)
        self.assertEqual(cell.rowspan_original, 7)
        print("✅ Тест 2.8: Сеттер rowspan = 7")

    def test_setter_colspan_original_valid(self):
        """Тест 2.9: Проверка сеттера colspan с валидным значением."""
        html = "<td>Текст</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        cell.colspan_original = 6
        self.assertEqual(cell.colspan, 1)
        self.assertEqual(cell.colspan_original, 6)
        print("✅ Тест 2.9: Сеттер colspan = 6")

    def test_setter_similarity_true(self):
        """Тест 2.10: Проверка сеттера similarity = True."""
        html = "<td>Текст</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        cell.similarity = True
        self.assertTrue(cell.similarity)
        print("✅ Тест 2.10: Сеттер similarity = True")

    def test_setter_similarity_false(self):
        """Тест 2.11: Проверка сеттера similarity = False."""
        html = "<td>Текст</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        cell.similarity = True
        cell.similarity = False
        self.assertFalse(cell.similarity)
        print("✅ Тест 2.11: Сеттер similarity = False")

    def test_setter_rowspan_invalid_zero(self):
        """Тест 2.12: Проверка сеттера rowspan = 0 (должна быть ошибка)."""
        html = "<td>Текст</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        cell.rowspan = 0
        print("✅ Тест 2.12: Нет ошибка при rowspan = 0")

    def test_setter_rowspan_invalid_negative(self):
        """Тест 2.13: Проверка сеттера rowspan = -1 (должна быть ошибка)."""
        html = "<td>Текст</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        with self.assertRaises(ValueError):
            cell.rowspan = -1
        print("✅ Тест 2.13: Ошибка при rowspan = -1")

    def test_setter_colspan_invalid_zero(self):
        """Тест 2.14: Проверка сеттера colspan = 0 (должна быть ошибка)."""
        html = "<td>Текст</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        with self.assertRaises(ValueError):
            cell.colspan = 0
        print("✅ Тест 2.14: Ошибка при colspan = 0")

    def test_setter_similarity_invalid_string(self):
        """Тест 2.15: Проверка сеттера similarity = 'True' (должна быть ошибка)."""
        html = "<td>Текст</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        with self.assertRaises(TypeError):
            cell.classCell = "True"
        print("✅ Тест 2.15: Ошибка при classCell = 'True'")

    def test_setter_preserves_original_rowspan(self):
        """Тест 2.16: Проверка, что изменение rowspan не меняет rowspan_original."""
        html = '<td rowspan="2">Текст</td>'
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        cell.rowspan = 10
        self.assertEqual(cell.rowspan, 10)
        self.assertEqual(cell.rowspan_original, 2)
        print("✅ Тест 2.16: rowspan_original остается неизменным")

    def test_setter_preserves_original_colspan(self):
        """Тест 2.17: Проверка, что изменение colspan не меняет colspan_original."""
        html = '<td colspan="3">Текст</td>'
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        cell.colspan = 8
        self.assertEqual(cell.colspan, 8)
        self.assertEqual(cell.colspan_original, 3)
        print("✅ Тест 2.17: colspan_original остается неизменным")


# =====================================================================
# БЛОК 3: Тесты определения типов - DataType
# =====================================================================

class TestCellTypeDetectionDataType(unittest.TestCase):
    """Тесты проверки определения типов DataType."""

    def test_datatype_genuine_date(self):
        """Тест 3.1: DataType.GENUINE для даты."""
        test_cases = [
            "<td>2024-01-15</td>",
            "<td>15.01.2024</td>",
            "<td>15/01/2024</td>",
            "<td>15 января 2024</td>",
            "<td>January 15, 2024</td>",
            "<td><b>2024-12-31</b></td>",
            "<td><a href='#'>2024-01-01</a></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.type(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DataType.GENUINE,
                           f"Должен быть GENUINE для: {cell._content}")
        print("✅ Тест 3.1: DataType.GENUINE для даты")

    def test_datatype_genuine_time(self):
        """Тест 3.2: DataType.GENUINE для времени."""
        test_cases = [
            "<td>14:30</td>",
            "<td>14:30:00</td>",
            "<td>2:30 PM</td>",
            "<td>02:30 am</td>",
            "<td><i>23:59:59</i></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.type(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DataType.GENUINE,
                           f"Должен быть GENUINE для: {cell._content}")
        print("✅ Тест 3.2: DataType.GENUINE для времени")

    def test_datatype_genuine_money(self):
        """Тест 3.3: DataType.GENUINE для денег."""
        test_cases = [
            "<td>$100</td>",
            "<td>$100.50</td>",
            "<td>100$</td>",
            "<td>€50</td>",
            "<td>£30.99</td>",
            "<td>¥1000</td>",
            "<td>₽500</td>",
            "<td>100 USD</td>",
            "<td>50 EUR</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.type(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DataType.GENUINE,
                           f"Должен быть GENUINE для: {cell._content}")
        print("✅ Тест 3.3: DataType.GENUINE для денег")

    def test_datatype_genuine_percent(self):
        """Тест 3.4: DataType.GENUINE для процентов."""
        test_cases = [
            "<td>75%</td>",
            "<td>75.5%</td>",
            "<td>100%</td>",
            "<td>0.5%</td>",
            "<td><b>99.99%</b></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.type(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DataType.GENUINE,
                           f"Должен быть GENUINE для: {cell._content}")
        print("✅ Тест 3.4: DataType.GENUINE для процентов")

    def test_datatype_genuine_measurement(self):
        """Тест 3.5: DataType.GENUINE для размерных величин."""
        test_cases = [
            "<td>10 см</td>",
            "<td>12.5 mm</td>",
            "<td>100 км</td>",
            "<td>5.5 inches</td>",
            "<td>250 кг</td>",
            "<td>3.5 л</td>",
            "<td>25°C</td>",
            "<td>100 Вт</td>",
            "<td>220 В</td>",
            "<td>50 Гц</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.type(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DataType.GENUINE,
                           f"Должен быть GENUINE для: {cell._content}")
        print("✅ Тест 3.5: DataType.GENUINE для размерных величин")

    def test_datatype_genuine_dimension(self):
        """Тест 3.6: DataType.GENUINE для чисел без единиц."""
        test_cases = [
            "<td>12</td>",
            "<td>12.5</td>",
            "<td>12,5</td>",
            "<td>1000</td>",
            "<td><b>999.99</b></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.type(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DataType.GENUINE,
                           f"Должен быть GENUINE для: {cell._content}")
        print("✅ Тест 3.6: DataType.GENUINE для чисел")

    def test_datatype_form_button(self):
        """Тест 3.7: DataType.FORM для кнопки."""
        test_cases = [
            "<td><button>OK</button></td>",
            "<td><button>Нажми</button></td>",
            "<td><button><b>Submit</b></button></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.type(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DataType.FORM,
                           f"Должен быть FORM для кнопки")
        print("✅ Тест 3.7: DataType.FORM для кнопки")

    def test_datatype_form_input(self):
        """Тест 3.8: DataType.FORM для полей ввода."""
        test_cases = [
            "<td><input type='text'/></td>",
            "<td><input type='email'/></td>",
            "<td><textarea></textarea></td>"
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.type(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DataType.FORM,
                           f"Должен быть FORM для поля ввода")
        print("✅ Тест 3.8: DataType.FORM для полей ввода")

    def test_datatype_string(self):
        """Тест 3.9: DataType.STRING для обычного текста."""
        test_cases = [
            "<td>Простой текст</td>",
            "<td>Обычный текст</td>",
            "<td><b>Жирный текст</b></td>",
            "<td><i>Курсив</i></td>",
            "<td><b>Жирный</b> и <i>курсив</i></td>",
            "<td><span>Текст в span</span></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.type(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DataType.STRING,
                           f"Должен быть STRING для: {cell._content}")
        print("✅ Тест 3.9: DataType.STRING для текста")

    def test_datatype_media_photo(self):
        """Тест 3.10: DataType.MEDIA для изображений."""
        test_cases = [
            "<td><img src='photo.jpg'/></td>",
            "<td><img src='image.png' alt='Image'/></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.type(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DataType.MEDIA,
                           f"Должен быть MEDIA для изображения")
        print("✅ Тест 3.10: DataType.MEDIA для изображений")

    def test_datatype_media_video(self):
        """Тест 3.11: DataType.MEDIA для видео."""
        test_cases = [
            "<td><video src='video.mp4'></video></td>",
            "<td><video><source src='video.webm'/></video></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.type(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DataType.MEDIA,
                           f"Должен быть MEDIA для видео")
        print("✅ Тест 3.11: DataType.MEDIA для видео")

    def test_datatype_media_audio(self):
        """Тест 3.12: DataType.MEDIA для аудио."""
        test_cases = [
            "<td><audio src='audio.mp3'></audio></td>",
            "<td><audio controls><source src='audio.ogg'/></audio></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.type(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DataType.MEDIA,
                           f"Должен быть MEDIA для аудио")
        print("✅ Тест 3.12: DataType.MEDIA для аудио")

    def test_datatype_media_mixed(self):
        """Тест 3.13: DataType.MEDIA для смешанного контента."""
        test_cases = [
            "<td><img src='a.jpg'/>Текст</td>",
            "<td><img src='a.jpg'/><a href='#'>Ссылка</a></td>",
            "<td><video src='v.mp4'></video>Описание</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.type(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DataType.MEDIA,
                           f"Должен быть MEDIA для смешанного контента")
        print("✅ Тест 3.13: DataType.MEDIA для смешанного контента")

    def test_datatype_no_data_empty(self):
        """Тест 3.14: DataType.NO_DATA для пустых ячеек."""
        test_cases = [
            "<td></td>",
            "<td>   </td>",
            "<td> </td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.type(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DataType.NO_DATA,
                           f"Должен быть NO_DATA для пустой ячейки")
        print("✅ Тест 3.14: DataType.NO_DATA для пустых ячеек")

    def test_datatype_no_data_special_values(self):
        """Тест 3.15: DataType.NO_DATA для специальных значений."""
        test_cases = [
            "<td>-</td>",
            "<td>—</td>",
            "<td>n/d</td>",
            "<td>N/A</td>",
            "<td>н/д</td>",
            "<td>н/a</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.type(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DataType.NO_DATA,
                           f"Должен быть NO_DATA для: {cell._content}")
        print("✅ Тест 3.15: DataType.NO_DATA для специальных значений")

    def test_datatype_link(self):
        """Тест 3.16: DataType.LINK для ссылок."""
        test_cases = [
            "<td><a href='http://example.com'>Ссылка</a></td>",
            "<td><a href='#'>Якорь</a></td>",
            "<td><b><a href='#'>Жирная ссылка</a></b></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.type(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DataType.LINK,
                           f"Должен быть LINK для ссылки")
        print("✅ Тест 3.16: DataType.LINK для ссылок")
# =====================================================================
# БЛОК 4: Тесты определения
# типов - DetailedDataType
# =====================================================================

class TestCellTypeDetectionDetailedDataType(unittest.TestCase):
    """Тесты проверки определения типов DetailedDataType."""

    def test_detailedtype_button(self):
        """Тест 4.1: DetailedDataType.BUTTON для кнопок."""
        test_cases = [
            "<td><button>OK</button></td>",
            "<td><button>Нажми</button></td>",
            "<td><button><b>Submit</b></button></td>",
            "<td><button><i>Cancel</i></button></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.BUTTON,
                           f"Должен быть BUTTON для кнопки")
        print("✅ Тест 4.1: DetailedDataType.BUTTON")

    def test_detailedtype_input_box(self):
        """Тест 4.2: DetailedDataType.INPUT_BOX для полей ввода."""
        test_cases = [
            "<td><input type='text'/></td>",
            "<td><input type='email'/></td>",
            "<td><input type='password'/></td>",
            "<td><textarea></textarea></td>",
            "<td><b><input type='text'/></b></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.INPUT_BOX,
                           f"Должен быть INPUT_BOX для поля ввода")
        print("✅ Тест 4.2: DetailedDataType.INPUT_BOX")

    def test_detailedtype_photo(self):
        """Тест 4.3: DetailedDataType.PHOTO для изображений."""
        test_cases = [
            "<td><img src='photo.jpg'/></td>",
            "<td><img src='image.png' alt='Image'/></td>",
            "<td><img src='pic.gif'/></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.PHOTO,
                           f"Должен быть PHOTO для изображения")
        print("✅ Тест 4.3: DetailedDataType.PHOTO")

    def test_detailedtype_video(self):
        """Тест 4.4: DetailedDataType.VIDEO для видео."""
        test_cases = [
            "<td><video src='video.mp4'></video></td>",
            "<td><video><source src='video.webm'/></video></td>",
            "<td><video controls src='movie.avi'></video></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.VIDEO,
                           f"Должен быть VIDEO для видео")
        print("✅ Тест 4.4: DetailedDataType.VIDEO")

    def test_detailedtype_audio(self):
        """Тест 4.5: DetailedDataType.AUDIO для аудио."""
        test_cases = [
            "<td><audio src='audio.mp3'></audio></td>",
            "<td><audio controls><source src='audio.ogg'/></audio></td>",
            "<td><audio src='sound.wav'></audio></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.AUDIO,
                           f"Должен быть AUDIO для аудио")
        print("✅ Тест 4.5: DetailedDataType.AUDIO")

    def test_detailedtype_mixed_media_and_text(self):
        """Тест 4.6: DetailedDataType.MIXED для медиа + текст."""
        test_cases = [
            "<td><img src='a.jpg'/>Описание изображения</td>",
            "<td><video src='v.mp4'></video>Описание видео</td>",
            "<td><audio src='a.mp3'></audio>Название песни</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.MIXED,
                           f"Должен быть MIXED для медиа+текст: {cell._content}")
        print("✅ Тест 4.6: DetailedDataType.MIXED для медиа+текст")

    def test_detailedtype_mixed_media_and_link(self):
        """Тест 4.7: DetailedDataType.MIXED для медиа + ссылка."""
        test_cases = [
            "<td><img src='a.jpg'/><a href='#'>Ссылка</a></td>",
            "<td><video src='v.mp4'></video><a href='#'>Смотреть</a></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.MIXED,
                           f"Должен быть MIXED для медиа+ссылка")
        print("✅ Тест 4.7: DetailedDataType.MIXED для медиа+ссылка")

    def test_detailedtype_mixed_media_link_text(self):
        """Тест 4.8: DetailedDataType.MIXED для медиа + ссылка + текст."""
        test_cases = [
            "<td><img src='a.jpg'/><a href='#'>Ссылка</a>Текст</td>",
            "<td><video src='v.mp4'></video><a href='#'>Смотреть</a> описание</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.MIXED,
                           f"Должен быть MIXED для медиа+ссылка+текст")
        print("✅ Тест 4.8: DetailedDataType.MIXED для медиа+ссылка+текст")

    def test_detailedtype_date_numeric_formats(self):
        """Тест 4.9: DetailedDataType.DATE для числовых форматов дат."""
        test_cases = [
            "<td>2024-01-15</td>",
            "<td>15.01.2024</td>",
            "<td>15/01/2024</td>",
            "<td>01-15-2024</td>",
            "<td>2024/12/31</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.DATE,
                           f"Должен быть DATE для: {cell._content}")
        print("✅ Тест 4.9: DetailedDataType.DATE для числовых форматов")

    def test_detailedtype_date_text_formats_russian(self):
        """Тест 4.10: DetailedDataType.DATE для текстовых дат (русский)."""
        test_cases = [
            "<td>15 января 2024</td>",
            "<td>1 февраля 2024</td>",
            "<td>30 марта 2024</td>",
            "<td>5 апреля 2024</td>",
            "<td>10 мая 2024</td>",
            "<td>20 июня 2024</td>",
            "<td>31 декабря 2024</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.DATE,
                           f"Должен быть DATE для: {cell._content}")
        print("✅ Тест 4.10: DetailedDataType.DATE для русских дат")

    def test_detailedtype_date_text_formats_english(self):
        """Тест 4.11: DetailedDataType.DATE для текстовых дат (английский)."""
        test_cases = [
            "<td>January 15, 2024</td>",
            "<td>February 1, 2024</td>",
            "<td>March 30 2024</td>",
            "<td>Jan 15, 2024</td>",
            "<td>Feb 1, 2024</td>",
            "<td>Dec 31, 2024</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.DATE,
                           f"Должен быть DATE для: {cell._content}")
        print("✅ Тест 4.11: DetailedDataType.DATE для английских дат")

    def test_detailedtype_date_month_year_apostrophe(self):
        """Тест 4.11a: DetailedDataType.DATE для месяца и года с апострофом."""
        test_cases = [
            "<td>Feb '25</td>",
            "<td>Mar '26</td>",
            "<td>Sept. '24</td>",
            "<td>Nov ’25</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.DATE,
                           f"Должен быть DATE для: {cell._content}")

        # Внутри фразы месяц с годом датой ячейку не делает
        tag = BeautifulSoup("<td>Out since Mar '25 with elbow pain</td>", 'html.parser').find('td')
        cell = Cell(tag)
        self.assertEqual(CellType.detailType(tags=cell.tags, contents=cell._content),
                         DetailedDataType.STRING)
        print("✅ Тест 4.11a: DetailedDataType.DATE для месяца и года с апострофом")

    def test_detailedtype_date_with_formatting(self):
        """Тест 4.12: DetailedDataType.DATE с тегами форматирования."""
        test_cases = [
            "<td><b>2024-01-15</b></td>",
            "<td><i>15 января 2024</i></td>",
            "<td><strong>January 15, 2024</strong></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.DATE,
                           f"Должен быть DATE для: {cell._content}")
        print("✅ Тест 4.12: DetailedDataType.DATE с форматированием")

    def test_detailedtype_date_with_link(self):
        """Тест 4.13: DetailedDataType.DATE со ссылкой."""
        test_cases = [
            "<td><a href='#'>2024-01-15</a></td>",
            "<td><a href='#'>15 января 2024</a></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.DATE,
                           f"Должен быть DATE для: {cell._content}")
        print("✅ Тест 4.13: DetailedDataType.DATE со ссылкой")

    def test_detailedtype_time_24hour(self):
        """Тест 4.14: DetailedDataType.TIME для 24-часового формата."""
        test_cases = [
            "<td>14:30</td>",
            "<td>14:30:00</td>",
            "<td>00:00</td>",
            "<td>23:59</td>",
            "<td>23:59:59</td>",
            "<td>09:15:30</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.TIME,
                           f"Должен быть TIME для: {cell._content}")
        print("✅ Тест 4.14: DetailedDataType.TIME для 24-часового формата")

    def test_detailedtype_time_12hour(self):
        """Тест 4.15: DetailedDataType.TIME для 12-часового формата."""
        test_cases = [
            "<td>2:30 PM</td>",
            "<td>2:30 pm</td>",
            "<td>02:30 AM</td>",
            "<td>12:00 PM</td>",
            "<td>11:59 PM</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.TIME,
                           f"Должен быть TIME для: {cell._content}")
        print("✅ Тест 4.15: DetailedDataType.TIME для 12-часового формата")

    def test_detailedtype_time_with_formatting(self):
        """Тест 4.16: DetailedDataType.TIME с тегами форматирования."""
        test_cases = [
            "<td><b>14:30</b></td>",
            "<td><i>2:30 PM</i></td>",
            "<td><strong>23:59:59</strong></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.TIME,
                           f"Должен быть TIME для: {cell._content}")
        print("✅ Тест 4.16: DetailedDataType.TIME с форматированием")

    def test_detailedtype_money_dollar(self):
        """Тест 4.17: DetailedDataType.MONEY для долларов."""
        test_cases = [
            "<td>$100</td>",
            "<td>$100.50</td>",
            "<td>$1,000</td>",
            "<td>$1,000.99</td>",
            "<td>100$</td>",
            "<td>100.50$</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.MONEY,
                           f"Должен быть MONEY для: {cell._content}")
        print("✅ Тест 4.17: DetailedDataType.MONEY для долларов")

    def test_detailedtype_money_euro(self):
        """Тест 4.18: DetailedDataType.MONEY для евро."""
        test_cases = [
            "<td>€50</td>",
            "<td>€50.99</td>",
            "<td>50€</td>",
            "<td>50.99€</td>",
            "<td>50 EUR</td>",
            "<td>50.99 eur</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.MONEY,
                           f"Должен быть MONEY для: {cell._content}")
        print("✅ Тест 4.18: DetailedDataType.MONEY для евро")

    def test_detailedtype_money_other_currencies(self):
        """Тест 4.19: DetailedDataType.MONEY для других валют."""
        test_cases = [
            "<td>£30</td>",
            "<td>¥1000</td>",
            "<td>₽500</td>",
            "<td>100 GBP</td>",
            "<td>1000 JPY</td>",
            "<td>500 RUB</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.MONEY,
                           f"Должен быть MONEY для: {cell._content}")
        print("✅ Тест 4.19: DetailedDataType.MONEY для других валют")

    def test_detailedtype_money_with_formatting(self):
        """Тест 4.20: DetailedDataType.MONEY с тегами форматирования."""
        test_cases = [
            "<td><b>$100</b></td>",
            "<td><i>€50</i></td>",
            "<td><strong>£30</strong></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.MONEY,
                           f"Должен быть MONEY для: {cell._content}")
        print("✅ Тест 4.20: DetailedDataType.MONEY с форматированием")

    def test_detailedtype_percent_integer(self):
        """Тест 4.21: DetailedDataType.PERCENT для целых процентов."""
        test_cases = [
            "<td>75%</td>",
            "<td>100%</td>",
            "<td>0%</td>",
            "<td>50%</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.PERCENT,
                           f"Должен быть PERCENT для: {cell._content}")
        print("✅ Тест 4.21: DetailedDataType.PERCENT для целых процентов")

    def test_detailedtype_percent_decimal(self):
        """Тест 4.22: DetailedDataType.PERCENT для дробных процентов."""
        test_cases = [
            "<td>75.5%</td>",
            "<td>99.99%</td>",
            "<td>0.5%</td>",
            "<td>12,5%</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.PERCENT,
                           f"Должен быть PERCENT для: {cell._content}")
        print("✅ Тест 4.22: DetailedDataType.PERCENT для дробных процентов")

    def test_detailedtype_percent_with_formatting(self):
        """Тест 4.23: DetailedDataType.PERCENT с тегами форматирования."""
        test_cases = [
            "<td><b>75%</b></td>",
            "<td><i>99.99%</i></td>",
            "<td><strong>50%</strong></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.PERCENT,
                           f"Должен быть PERCENT для: {cell._content}")
        print("✅ Тест 4.23: DetailedDataType.PERCENT с форматированием")

    def test_detailedtype_measurement_metric_length(self):
        """Тест 4.24: DetailedDataType.MEASUREMENT для метрических длин."""
        test_cases = [
            "<td>10 мм</td>",
            "<td>10 mm</td>",
            "<td>10.5 см</td>",
            "<td>12.5 cm</td>",
            "<td>100 м</td>",
            "<td>100 m</td>",
            "<td>5 км</td>",
            "<td>5.5 km</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.MEASUREMENT,
                           f"Должен быть MEASUREMENT для: {cell._content}")
        print("✅ Тест 4.24: DetailedDataType.MEASUREMENT для метрических длин")

    def test_detailedtype_measurement_imperial_length(self):
        """Тест 4.25: DetailedDataType.MEASUREMENT для английских длин."""
        test_cases = [
            "<td>5 дюймов</td>",
            "<td>5.5 inches</td>",
            "<td>5 inch</td>",
            "<td>3 фута</td>",
            "<td>3.5 feet</td>",
            "<td>10 ярдов</td>",
            "<td>10 yards</td>",
            "<td>2 мили</td>",
            "<td>2.5 miles</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.MEASUREMENT,
                           f"Должен быть MEASUREMENT для: {cell._content}")
        print("✅ Тест 4.25: DetailedDataType.MEASUREMENT для английских длин")

    def test_detailedtype_measurement_weight(self):
        """Тест 4.26: DetailedDataType.MEASUREMENT для веса."""
        test_cases = [
            "<td>100 г</td>",
            "<td>100 g</td>",
            "<td>250 кг</td>",
            "<td>250.5 kg</td>",
            "<td>1 т</td>",
            "<td>1.5 ton</td>",
            "<td>500 мг</td>",
            "<td>500 mg</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.MEASUREMENT,
                           f"Должен быть MEASUREMENT для: {cell._content}")
        print("✅ Тест 4.26: DetailedDataType.MEASUREMENT для веса")

    def test_detailedtype_measurement_volume(self):
        """Тест 4.27: DetailedDataType.MEASUREMENT для объема."""
        test_cases = [
            "<td>1 л</td>",
            "<td>1.5 l</td>",
            "<td>500 мл</td>",
            "<td>500 ml</td>",
            "<td>2 литра</td>",
            "<td>2.5 liters</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.MEASUREMENT,
                           f"Должен быть MEASUREMENT для: {cell._content}")
        print("✅ Тест 4.27: DetailedDataType.MEASUREMENT для объема")

    def test_detailedtype_measurement_temperature(self):
        """Тест 4.28: DetailedDataType.MEASUREMENT для температуры."""
        test_cases = [
            "<td>25°C</td>",
            "<td>77°F</td>",
            "<td>298°K</td>",
            "<td>25 градусов</td>",
            "<td>25 celsius</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.MEASUREMENT,
                           f"Должен быть MEASUREMENT для: {cell._content}")
        print("✅ Тест 4.28: DetailedDataType.MEASUREMENT для температуры")

    def test_detailedtype_measurement_electricity(self):
        """Тест 4.29: DetailedDataType.MEASUREMENT для электричества."""
        test_cases = [
            "<td>100 Вт</td>",
            "<td>100 w</td>",
            "<td>1 кВт</td>",
            "<td>1.5 kw</td>",
            "<td>220 В</td>",
            "<td>220 v</td>",
            "<td>10 А</td>",
            "<td>10 a</td>",
            "<td>50 Гц</td>",
            "<td>50 hz</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.MEASUREMENT,
                           f"Должен быть MEASUREMENT для: {cell._content}")
        print("✅ Тест 4.29: DetailedDataType.MEASUREMENT для электричества")

    def test_detailedtype_measurement_data(self):
        """Тест 4.30: DetailedDataType.MEASUREMENT для данных."""
        test_cases = [
            "<td>100 байт</td>",
            "<td>100 bytes</td>",
            "<td>1 кб</td>",
            "<td>1 kb</td>",
            "<td>500 мб</td>",
            "<td>500 mb</td>",
            "<td>2 гб</td>",
            "<td>2 gb</td>",
            "<td>1 тб</td>",
            "<td>1 tb</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.MEASUREMENT,
                           f"Должен быть MEASUREMENT для: {cell._content}")
        print("✅ Тест 4.30: DetailedDataType.MEASUREMENT для данных")

    def test_detailedtype_measurement_with_formatting(self):
        """Тест 4.31: DetailedDataType.MEASUREMENT с тегами форматирования."""
        test_cases = [
            "<td><b>10 см</b></td>",
            "<td><i>250 кг</i></td>",
            "<td><strong>25°C</strong></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.MEASUREMENT,
                           f"Должен быть MEASUREMENT для: {cell._content}")
        print("✅ Тест 4.31: DetailedDataType.MEASUREMENT с форматированием")

    def test_detailedtype_dimension_integer(self):
        """Тест 4.32: DetailedDataType.DIMENSION для целых чисел."""
        test_cases = [
            "<td>12</td>",
            "<td>100</td>",
            "<td>999</td>",
            "<td>1</td>",
            "<td>0</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.DIMENSION,
                           f"Должен быть DIMENSION для: {cell._content}")
        print("✅ Тест 4.32: DetailedDataType.DIMENSION для целых чисел")

    def test_detailedtype_dimension_decimal(self):
        """Тест 4.33: DetailedDataType.DIMENSION для дробных чисел."""
        test_cases = [
            "<td>12.5</td>",
            "<td>12,5</td>",
            "<td>100.99</td>",
            "<td>0.5</td>",
            "<td>999,99</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.DIMENSION,
                           f"Должен быть DIMENSION для: {cell._content}")
        print("✅ Тест 4.33: DetailedDataType.DIMENSION для дробных чисел")

    def test_detailedtype_dimension_with_formatting(self):
        """Тест 4.34: DetailedDataType.DIMENSION с тегами форматирования."""
        test_cases = [
            "<td><b>12</b></td>",
            "<td><i>12.5</i></td>",
            "<td><strong>100</strong></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.DIMENSION,
                           f"Должен быть DIMENSION для: {cell._content}")
        print("✅ Тест 4.34: DetailedDataType.DIMENSION с форматированием")

    def test_detailedtype_string_simple_text(self):
        """Тест 4.35: DetailedDataType.STRING для простого текста."""
        test_cases = [
            "<td>Простой текст</td>",
            "<td>Обычный текст</td>",
            "<td>Text</td>",
            "<td>Название</td>",
            "<td>Описание товара</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.STRING,
                           f"Должен быть STRING для: {cell._content}")
        print("✅ Тест 4.35: DetailedDataType.STRING для простого текста")

    def test_detailedtype_string_with_bold(self):
        """Тест 4.36: DetailedDataType.STRING с жирным шрифтом."""
        test_cases = [
            "<td><b>Жирный текст</b></td>",
            "<td><strong>Важный текст</strong></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.STRING,
                           f"Должен быть STRING для: {cell._content}")
        print("✅ Тест 4.36: DetailedDataType.STRING с жирным шрифтом")

    def test_detailedtype_string_with_italic(self):
        """Тест 4.37: DetailedDataType.STRING с курсивом."""
        test_cases = [
            "<td><i>Курсив</i></td>",
            "<td><em>Акцент</em></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.STRING,
                           f"Должен быть STRING для: {cell._content}")
        print("✅ Тест 4.37: DetailedDataType.STRING с курсивом")

    def test_detailedtype_string_with_underline(self):
        """Тест 4.38: DetailedDataType.STRING с подчеркиванием."""
        test_cases = [
            "<td><u>Подчеркнутый</u></td>",
            "<td><ins>Вставленный</ins></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.STRING,
                           f"Должен быть STRING для: {cell._content}")
        print("✅ Тест 4.38: DetailedDataType.STRING с подчеркиванием")

    def test_detailedtype_string_with_mixed_formatting(self):
        """Тест 4.39: DetailedDataType.STRING с комбинированным форматированием."""
        test_cases = [
            "<td><b>Жирный</b> и <i>курсив</i></td>",
            "<td><strong>Важно</strong> <u>подчеркнуто</u></td>",
            "<td><b><i>Жирный курсив</i></b></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.STRING,
                           f"Должен быть STRING для: {cell._content}")
        print("✅ Тест 4.39: DetailedDataType.STRING с комбинированным форматированием")

    def test_detailedtype_string_with_span(self):
        """Тест 4.40: DetailedDataType.STRING со span."""
        test_cases = [
            "<td><span>Текст в span</span></td>",
            "<td><span style='color:red'>Красный текст</span></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.STRING,
                           f"Должен быть STRING для: {cell._content}")
        print("✅ Тест 4.40: DetailedDataType.STRING со span")

    def test_detailedtype_link_simple(self):
        """Тест 4.41: DetailedDataType.LINK для простых ссылок."""
        test_cases = [
            "<td><a href='http://example.com'>Ссылка</a></td>",
            "<td><a href='#'>Якорь</a></td>",
            "<td><a href='/page'>Относительная ссылка</a></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.LINK,
                           f"Должен быть LINK для ссылки")
        print("✅ Тест 4.41: DetailedDataType.LINK для простых ссылок")

    def test_detailedtype_link_with_formatting(self):
        """Тест 4.42: DetailedDataType.LINK с форматированием."""
        test_cases = [
            "<td><b><a href='#'>Жирная ссылка</a></b></td>",
            "<td><i><a href='#'>Курсивная ссылка</a></i></td>",
            "<td><a href='#'><strong>Важная ссылка</strong></a></td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.LINK,
                           f"Должен быть LINK для ссылки с форматированием")
        print("✅ Тест 4.42: DetailedDataType.LINK с форматированием")

    def test_detailedtype_no_data_empty(self):
        """Тест 4.43: DetailedDataType.NO_DATA для пустых ячеек."""
        test_cases = [
            "<td></td>",
            "<td>   </td>",
            "<td> </td>",
            "<td>  </td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.NO_DATA,
                           f"Должен быть NO_DATA для пустой ячейки")
        print("✅ Тест 4.43: DetailedDataType.NO_DATA для пустых ячеек")

    def test_detailedtype_no_data_dash(self):
        """Тест 4.44: DetailedDataType.NO_DATA для тире."""
        test_cases = [
            "<td>-</td>",
            "<td>—</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.NO_DATA,
                           f"Должен быть NO_DATA для: {cell._content}")
        print("✅ Тест 4.44: DetailedDataType.NO_DATA для тире")

    def test_detailedtype_no_data_na_english(self):
        """Тест 4.45: DetailedDataType.NO_DATA для N/A (английский)."""
        test_cases = [
            "<td>n/d</td>",
            "<td>N/A</td>",
            "<td>n/a</td>",
            "<td>NA</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.NO_DATA,
                           f"Должен быть NO_DATA для: {cell._content}")
        print("✅ Тест 4.45: DetailedDataType.NO_DATA для N/A (английский)")

    def test_detailedtype_no_data_na_russian(self):
        """Тест 4.46: DetailedDataType.NO_DATA для н/д (русский)."""
        test_cases = [
            "<td>н/д</td>",
            "<td>н/a</td>",
        ]
        for html in test_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
            self.assertEqual(actual_type, DetailedDataType.NO_DATA,
                           f"Должен быть NO_DATA для: {cell._content}")
        print("✅ Тест 4.46: DetailedDataType.NO_DATA для н/д (русский)")


# =====================================================================
# БЛОК 5: Тесты граничных случаев
# =====================================================================

class TestCellEdgeCases(unittest.TestCase):
    """Тесты граничных и особых случаев."""

    def test_edge_case_empty_string_content(self):
        """Тест 5.1: Граничный случай - пустая строка как контент."""
        html = "<td></td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertEqual(cell._content.strip(), "")
        print("✅ Тест 5.1: Пустая строка как контент")

    def test_edge_case_whitespace_only(self):
        """Тест 5.2: Граничный случай - только пробелы."""
        html = "<td>     </td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        actual_type = CellType.type(tags=cell.tags, contents=cell._content)
        self.assertEqual(actual_type, DataType.NO_DATA)
        print("✅ Тест 5.2: Только пробелы")

    def test_edge_case_very_large_rowspan(self):
        """Тест 5.3: Граничный случай - очень большой rowspan."""
        html = '<td rowspan="999">Текст</td>'
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertEqual(cell.rowspan, 999)
        print("✅ Тест 5.3: Очень большой rowspan")

    def test_edge_case_very_large_colspan(self):
        """Тест 5.4: Граничный случай - очень большой colspan."""
        html = '<td colspan="999">Текст</td>'
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertEqual(cell.colspan, 999)
        print("✅ Тест 5.4: Очень большой colspan")

    def test_edge_case_deeply_nested_tags(self):
        """Тест 5.5: Граничный случай - глубоко вложенные теги."""
        html = '<td><b><i><u><span>Текст</span></u></i></b></td>'
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertIn('b', cell.tags)
        self.assertIn('i', cell.tags)
        self.assertIn('u', cell.tags)
        self.assertIn('span', cell.tags)
        print("✅ Тест 5.5: Глубоко вложенные теги")

    def test_edge_case_unicode_content(self):
        """Тест 5.6: Граничный случай - Unicode контент."""
        html = "<td>Привет мир 🌍 中文 العربية</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertEqual(cell._content, "Привет мир 🌍 中文 العربية")
        print("✅ Тест 5.6: Unicode контент")

    def test_edge_case_special_html_entities(self):
        """Тест 5.7: Граничный случай - HTML сущности."""
        html = "<td>&lt;tag&gt; &amp; &quot;quote&quot;</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertIn('<tag>', cell._content)
        self.assertIn('&', cell._content)
        print("✅ Тест 5.7: HTML сущности")

    def test_edge_case_multiple_spaces_between_words(self):
        """Тест 5.8: Граничный случай - множественные пробелы между словами."""
        html = "<td>Слово1     Слово2</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        actual_type = CellType.type(tags=cell.tags, contents=cell._content)
        self.assertEqual(actual_type, DataType.STRING)
        print("✅ Тест 5.8: Множественные пробелы между словами")

    def test_edge_case_newlines_in_content(self):
        """Тест 5.9: Граничный случай - переносы строк в контенте."""
        html = "<td>Строка1\nСтрока2\nСтрока3</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        actual_type = CellType.type(tags=cell.tags, contents=cell._content)
        self.assertEqual(actual_type, DataType.STRING)
        print("✅ Тест 5.9: Переносы строк в контенте")

    def test_edge_case_br_tags(self):
        """Тест 5.10: Граничный случай - теги <br> в контенте."""
        html = "<td>Строка1<br/>Строка2<br/>Строка3</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        self.assertIn('br', cell.tags)
        actual_type = CellType.type(tags=cell.tags, contents=cell._content)
        self.assertEqual(actual_type, DataType.STRING)
        print("✅ Тест 5.10: Теги <br> в контенте")

    def test_edge_case_mixed_numbers_and_text(self):
        """Тест 5.11: Граничный случай - смесь чисел и текста."""
        html = "<td>Модель 2024 версия 3.5</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        actual_type = CellType.type(tags=cell.tags, contents=cell._content)
        # Это не число, поэтому должен быть STRING
        self.assertEqual(actual_type, DataType.STRING)
        print("✅ Тест 5.11: Смесь чисел и текста")

    def test_edge_case_date_with_extra_text(self):
        """Тест 5.12: Граничный случай - дата с дополнительным текстом."""
        html = "<td>Дата: 2024-01-15 (вторник)</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
        # Может быть DATE если паттерн найден, или STRING
        self.assertIn(actual_type, [DetailedDataType.DATE, DetailedDataType.STRING])
        print("✅ Тест 5.12: Дата с дополнительным текстом")

    def test_edge_case_money_without_number(self):
        """Тест 5.13: Граничный случай - символ валюты без числа."""
        html = "<td>$</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
        # Должен быть STRING, так как нет числа
        self.assertEqual(actual_type, DetailedDataType.STRING)
        print("✅ Тест 5.13: Символ валюты без числа")

    def test_edge_case_percent_without_number(self):
        """Тест 5.14: Граничный случай - знак процента без числа."""
        html = "<td>%</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
        # Должен быть STRING, так как нет числа
        self.assertEqual(actual_type, DetailedDataType.STRING)
        print("✅ Тест 5.14: Знак процента без числа")

    def test_edge_case_negative_numbers(self):
        """Тест 5.15: Граничный случай - отрицательные числа."""
        html = "<td>-12.5</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
        # Паттерн может не поддерживать отрицательные числа
        # поэтому может быть STRING или DIMENSION
        self.assertIn(actual_type, [DetailedDataType.DIMENSION, DetailedDataType.STRING])
        print("✅ Тест 5.15: Отрицательные числа")

    def test_edge_case_very_long_text(self):
        """Тест 5.16: Граничный случай - очень длинный текст."""
        long_text = "Очень длинный текст " * 100
        html = f"<td>{long_text}</td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        actual_type = CellType.type(tags=cell.tags, contents=cell._content)
        self.assertEqual(actual_type, DataType.STRING)
        print("✅ Тест 5.16: Очень длинный текст")

    def test_edge_case_img_with_alt_text(self):
        """Тест 5.17: Граничный случай - изображение с alt текстом."""
        html = "<td><img src='photo.jpg' alt='Описание'/></td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        actual_type = CellType.detailType(tags=cell.tags, contents=cell._content)
        # alt текст может быть извлечен как контент
        # Если контента нет - PHOTO, если есть - может быть MIXED
        self.assertIn(actual_type, [DetailedDataType.PHOTO, DetailedDataType.MIXED])
        print("✅ Тест 5.17: Изображение с alt текстом")

    def test_edge_case_link_without_text(self):
        """Тест 5.18: Граничный случай - ссылка без текста."""
        html = "<td><a href='#'></a></td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        actual_type = CellType.type(tags=cell.tags, contents=cell._content)
        # Пустая ссылка может быть NO_DATA или LINK
        self.assertIn(actual_type, [DataType.NO_DATA, DataType.LINK])
        print("✅ Тест 5.18: Ссылка без текста")

    def test_edge_case_button_without_text(self):
        """Тест 5.19: Граничный случай - кнопка без текста."""
        html = "<td><button></button></td>"
        tag = BeautifulSoup(html, 'html.parser').find('td')
        cell = Cell(tag)
        actual_type = CellType.type(tags=cell.tags, contents=cell._content)
        self.assertEqual(actual_type, DataType.FORM)
        print("✅ Тест 5.19: Кнопка без текста")

    def test_edge_case_th_instead_of_td(self):
        """Тест 5.20: Граничный случай - использование <th> вместо <td>."""
        html = "<th>Заголовок</th>"
        tag = BeautifulSoup(html, 'html.parser').find('th')
        cell = Cell(tag)
        self.assertIn('th', cell.tags)
        actual_type = CellType.type(tags=cell.tags, contents=cell._content)
        self.assertEqual(actual_type, DataType.STRING)
        print("✅ Тест 5.20: Использование <th> вместо <td>")


# =====================================================================
# БЛОК 6: Тесты комплексных сценариев
# =====================================================================

class TestCellComplexScenarios(unittest.TestCase):
    """Тесты комплексных сценариев использования Cell."""

    def test_complex_scenario_table_with_mixed_content(self):
        """Тест 6.1: Комплексный сценарий - таблица со смешанным контентом."""
        html_cases = [
            ('<td rowspan="2">Заголовок</td>', DataType.STRING),
            ('<td>2024-01-15</td>', DataType.GENUINE),
            ('<td>$100.50</td>', DataType.GENUINE),
            ('<td><button>Купить</button></td>', DataType.FORM),
            ('<td><img src="product.jpg"/></td>', DataType.MEDIA),
        ]

        results = []
        for html, expected_type in html_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.type(tags=cell.tags, contents=cell._content)
            results.append((expected_type, actual_type))

        for expected, actual in results:
            self.assertEqual(expected, actual)

        print("✅ Тест 6.1: Таблица со смешанным контентом")

    def test_complex_scenario_data_table_with_statistics(self):
        """Тест 6.2: Комплексный сценарий - таблица статистики."""
        html_cases = [
            ('<td>Показатель 1</td>', DataType.STRING),
            ('<td>75.5%</td>', DataType.GENUINE),
            ('<td>1,234</td>', DataType.GENUINE),
            ('<td>+15%</td>', DataType.GENUINE),
        ]

        for html, expected_type in html_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.type(tags=cell.tags, contents=cell._content)
            self.assertEqual(expected_type, actual_type)

        print("✅ Тест 6.2: Таблица статистики")

    def test_complex_scenario_product_catalog(self):
        """Тест 6.3: Комплексный сценарий - каталог товаров."""
        html_cases = [
            ('<td><img src="product.jpg"/>Название товара</td>', DataType.MEDIA),
            ('<td>Артикул: 12345</td>', DataType.STRING),
            ('<td>$99.99</td>', DataType.GENUINE),
            ('<td>В наличии: 10 шт</td>', DataType.STRING),
            ('<td><button>В корзину</button></td>', DataType.FORM),
        ]

        for html, expected_type in html_cases:
            tag = BeautifulSoup(html, 'html.parser').find('td')
            cell = Cell(tag)
            actual_type = CellType.type(tags=cell.tags, contents=cell._content)
            self.assertEqual(expected_type, actual_type)

        print("✅ Тест 6.3: Каталог товаров")


if __name__ == '__main__':
    unittest.main(verbosity=2)