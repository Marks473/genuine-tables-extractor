from bs4 import BeautifulSoup, Tag
import CellType

class Cell:
    """
    Класс-обертка для ячеек таблицы (<td> или <th>), полученных из BeautifulSoup.
    Предоставляет удобный доступ к атрибутам и структуре тегов ячейки.
    """

    def __init__(self, bs4_tag: Tag):
        if not isinstance(bs4_tag, Tag):
            raise TypeError("Конструктор класса Cell ожидает объект bs4.element.Tag")

        self._data = bs4_tag
        self._rowspan = int(bs4_tag.get("rowspan", 1))
        self._colspan = int(bs4_tag.get("colspan", 1))
        self._rowspan_original = self._rowspan  # Сохраняем исходное значение
        self._colspan_original = self._colspan  # Сохраняем исходное значение
        self._classCell = CellType.ClassCell.CELL_NOT_DEFINE # По умолчанию
        self._content = self._extract_all_content(self.data)
        self._tags = self._extract_all_tags(self._data)
        self._type = CellType.type(contents=self._content, tags=self._tags)
        self._detailType = CellType.detailType(contents=self._content, tags=self._tags)

    # --- Геттеры и Сеттеры (Properties) ---
    @property
    def data(self) -> Tag:
        """Геттер для получения объекта bs4.element.Tag."""
        return self._data

    @property
    def type(self) -> str:
        """Геттер для получения тип данных (результат классификации из CellType)."""
        return self._type

    @property
    def detailType(self) -> str:
        """Геттер для получения тип данных (результат классификации из CellType)."""
        return self._detailType

    @detailType.setter
    def detailType(self, value: CellType.DetailedDataType):
        self._detailType = value

    @property
    def rowspan(self) -> int:
        """Геттер для получения текущего значения rowspan."""
        return self._rowspan

    @rowspan.setter
    def rowspan(self, value: int):
        """Сеттер для изменения значения rowspan."""
        if not isinstance(value, int) or value < 0:
            raise ValueError("rowspan должен быть целым числом не меньше 0")
        self._rowspan = value

    @property
    def colspan(self) -> int:
        """Геттер для получения текущего значения colspan."""
        return self._colspan

    @colspan.setter
    def colspan(self, value: int):
        """Сеттер для изменения значения colspan."""
        if not isinstance(value, int) or value < 1:
            raise ValueError("colspan должен быть целым числом больше 0")
        self._colspan = value

    @property
    def colspan_original(self) -> int:
        """Геттер для получения исходного значения colspan_original."""
        return self._colspan_original

    @colspan_original.setter
    def colspan_original(self, value: int):
        """Сеттер для изменения значения colspan_original."""
        if not isinstance(value, int) or value < 1:
            raise ValueError("colspan_original должен быть целым числом больше 0")
        self._colspan_original = value

    @property
    def rowspan_original(self) -> int:
        """Геттер для получения исходного значения rowspan."""
        return self._rowspan_original

    @rowspan_original.setter
    def rowspan_original(self, value: int):
        """Сеттер для изменения значения rowspan_original."""
        if not isinstance(value, int) or value < 1:
            raise ValueError("rowspan_original должен быть целым числом больше 0")
        self._rowspan_original = value

    @property
    def classCell(self) -> CellType.ClassCell:
        """Геттер для получения класса ячейки."""
        return self._classCell

    @classCell.setter
    def classCell(self, value: CellType.ClassCell):
        """Сеттер для установки класса ячейки."""
        if not isinstance(value, CellType.ClassCell):
            raise TypeError("сellType должен быть класса CellType.ClassCell")
        self._classCell = value

    @property
    def tags(self) -> set:
        """Геттер для получения множества всех тегов внутри ячейки."""
        return self._tags

    def _extract_all_tags(self, element: Tag) -> set:
        """Рекурсивно получает все имена тегов из элемента и его дочерних элементов."""

        # Мы ожидаем на входе только теги. Если пришел не тег, вернем пустое множество.
        if not isinstance(element, Tag):
            return set()
        # Начинаем с тега текущего элемента
        all_tags = {element.name}

        # Рекурсивно проходим по всем дочерним элементам
        for child in element.children:
            # Рекурсивно вызываем функцию ТОЛЬКО для дочерних элементов, которые являются тегами
            if isinstance(child, Tag):
                all_tags.update(self._extract_all_tags(child))

        return all_tags

    def _extract_all_content(self, element: Tag) -> str:
        """
        Извлекает все текстовое содержимое из элемента Tag и его дочерних элементов.
        """
        if not isinstance(element, Tag):
            return ""

        text_content = element.get_text(separator=' ', strip=True)
        return text_content

    @property
    def content(self) -> str:
        return self._content