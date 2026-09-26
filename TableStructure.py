"""
Объектная модель подлинной таблицы.

Эвристика проставляет каждой ячейке класс: заголовок, боковик, данные или
перерез. Этот модуль превращает размеченную таблицу в связанные объекты,
которые знают своё место в иерархии:

* :class:`TitleCell`   -- заголовок: надзаголовок, подзаголовки, типы данных под ним;
* :class:`SidebarCell` -- атрибут (боковик): путь по заголовкам и по атрибутам;
* :class:`DataCell`    -- данные: путь по заголовкам и по атрибутам;
* :class:`ResultCell`  -- перерез: ячейки данных, которые он агрегирует.

Общее для всех ячеек описано в абстрактном классе :class:`StructureCell`,
всю таблицу собирает :class:`StructureTable`. Подсказка расширения браузера,
выгрузка в JSON и эксперименты в интерпретаторе -- это обход этих объектов:

    >>> structure = StructureTable.from_table(Table(tag))
    >>> cell = structure.cell_at(10, 4)
    >>> isinstance(cell, ResultCell), cell.aggregated

Существующие модули не меняются: объекты хранят ссылку на исходную ячейку
:class:`Cell` и берут из неё текст и тип.
"""

import re
from abc import ABC, abstractmethod

from CellType import ClassCell, DataType, DetailedDataType, DIMENSION_PATTERNS
from Heuristic import get_genuine
from Table import Table
from TableGrid import TableGrid

# Временный атрибут: по нему размеченная копия ячейки находит исходную
MARK = 'data-structure-id'

# Типы данных, которые можно складывать. Под заголовком агрегируемого
# столбца допустимы только они и пустые ячейки
NUMERIC_TYPES = {
    DetailedDataType.DIMENSION,
    DetailedDataType.MONEY,
    DetailedDataType.PERCENT,
    DetailedDataType.MEASUREMENT,
}

# Как привести запись числа к виду, понятному float(). Порядок совпадает
# с DIMENSION_PATTERNS: тип ячейки определяется по первому совпавшему
# выражению, и значение разбирается по нему же. Иначе запись "154,977"
# получила бы тип "дробное число", а значение -- 154977
_DIMENSION_NORMALIZERS = [
    lambda text: text,                                     # 1. 12
    lambda text: text.replace(',', '.'),                   # 2. 12,5
    lambda text: text,                                     # 3. 12 123
    lambda text: text.replace(',', '.'),                   # 4. 12 123,5
    lambda text: text.replace(',', '.'),                   # 5. ,78
    lambda text: text.replace(',', ''),                    # 6. 1,368,524.5
    lambda text: text.replace('.', '').replace(',', '.'),  # 7. 1.368.524,5
]


def parse_dimension(text: str):
    """
    Переводит запись числа без единиц измерения в число.

    Args:
        text: текст ячейки, например "5 880", "1,368,524" или "-12,5"

    Returns:
        Число float либо None, если запись не похожа на число
    """
    stripped = text.strip()
    for pattern, normalize in zip(DIMENSION_PATTERNS, _DIMENSION_NORMALIZERS):
        if re.match(pattern, stripped):
            return float(normalize(re.sub(r'\s+', '', stripped)))
    return None


def _format_path(cells: list) -> str:
    """Записывает путь так, как его показывает подсказка: "a" / "b"."""
    return ' / '.join(f'"{cell.text}"' for cell in cells)


class StructureCell(ABC):
    """
    Ячейка подлинной таблицы вместе с её местом в иерархии.

    Координаты ``row`` и ``col`` -- как на странице. Пути ``header_path`` и
    ``sidebar_path`` вычисляются по размеченной таблице, где заголовки всегда
    сверху, а боковик слева: таблица с заголовком слева разбирается повёрнутой.

    Объект создаётся только внутри :meth:`StructureTable.from_table`.
    """

    #: Роль ячейки в выгрузке и в ответе сервера
    role = ''
    #: Название области таблицы для подсказки
    role_name = ''

    def __init__(self, cell, row: int, col: int, rowspan: int, colspan: int):
        """
        Args:
            cell: размеченная ячейка Cell
            row, col: левая верхняя клетка на странице
            rowspan, colspan: размеры на странице
        """
        self._cell = cell
        self._row = row
        self._col = col
        self._rowspan = rowspan
        self._colspan = colspan
        self._header_path = []
        self._sidebar_path = []

    @property
    def cell(self):
        """Исходная ячейка Cell с классом, который проставила эвристика."""
        return self._cell

    @property
    def text(self) -> str:
        """Текст ячейки."""
        return self._cell.content

    @property
    def data_type(self) -> DataType:
        """Основной тип содержимого ячейки."""
        return self._cell.type

    @property
    def detail_type(self) -> DetailedDataType:
        """Детальный тип содержимого ячейки."""
        return self._cell.detailType

    @property
    def row(self) -> int:
        return self._row

    @property
    def col(self) -> int:
        return self._col

    @property
    def rowspan(self) -> int:
        return self._rowspan

    @property
    def colspan(self) -> int:
        return self._colspan

    @property
    def header_path(self) -> list:
        """Заголовки над ячейкой от самого верхнего к ближайшему."""
        return list(self._header_path)

    @property
    def sidebar_path(self) -> list:
        """Атрибуты левее ячейки от самого левого к ближайшему."""
        return list(self._sidebar_path)

    @property
    def header(self):
        """Ближайший заголовок над ячейкой либо None."""
        return self._header_path[-1] if self._header_path else None

    @property
    def attribute(self):
        """Ближайший атрибут левее ячейки либо None."""
        return self._sidebar_path[-1] if self._sidebar_path else None

    @property
    def value(self):
        """Число из ячейки, если это число без единиц измерения, иначе None."""
        if self.detail_type != DetailedDataType.DIMENSION:
            return None
        return parse_dimension(self.text)

    def type_line(self) -> str:
        """Строка подсказки с типом данных ячейки."""
        return f'Тип данных: {self.detail_type.name}'

    @abstractmethod
    def hint(self) -> list:
        """Строки подсказки, которая появляется при наведении на ячейку."""

    @abstractmethod
    def related(self) -> list:
        """Ячейки, которые подсвечиваются при наведении на эту."""

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.text!r}, row={self.row}, col={self.col})'


class TitleCell(StructureCell):
    """Заголовок столбца."""

    role = 'title'
    role_name = 'ячейка области заголовков'

    def __init__(self, *args):
        super().__init__(*args)
        self._children = []
        self._data_cells = []

    @property
    def parent(self):
        """Надзаголовок либо None, если заголовок верхний."""
        return self.header

    @property
    def children(self) -> list:
        """Подзаголовки: заголовки, для которых этот -- надзаголовок."""
        return list(self._children)

    @property
    def data_cells(self) -> list:
        """Ячейки данных, над которыми стоит этот заголовок."""
        return list(self._data_cells)

    @property
    def data_types(self) -> set:
        """Детальные типы данных в ячейках под заголовком."""
        return {cell.detail_type for cell in self._data_cells}

    def type_line(self) -> str:
        names = sorted(kind.name for kind in self.data_types)
        return 'Типы данных внутри: ' + (', '.join(names) if names else 'нет данных')

    def hint(self) -> list:
        lines = []
        if self._header_path:
            lines.append('Подзаголовок: ' + _format_path(self._header_path))
        lines.append(self.role_name)
        return lines

    def related(self) -> list:
        return self.header_path


class SidebarCell(StructureCell):
    """Атрибут -- заголовок строки (боковик)."""

    role = 'sidebar'
    role_name = 'ячейка области атрибутов'

    def __init__(self, *args):
        super().__init__(*args)
        self._children = []

    @property
    def parent(self):
        """Атрибут выше по иерархии либо None."""
        return self.attribute

    @property
    def children(self) -> list:
        """Податрибуты: атрибуты, для которых этот -- родитель."""
        return list(self._children)

    def hint(self) -> list:
        lines = []
        if self._header_path:
            lines.append('Заголовок: ' + _format_path(self._header_path))
        if self._sidebar_path:
            lines.append('Податрибут: ' + _format_path(self._sidebar_path))
        lines.append(self.role_name)
        return lines

    def related(self) -> list:
        return self.header_path + self.sidebar_path


class DataCell(StructureCell):
    """Ячейка области данных."""

    role = 'data'
    role_name = 'ячейка области данных'

    def hint(self) -> list:
        lines = []
        if self._header_path:
            lines.append('Заголовок: ' + _format_path(self._header_path))
        if self._sidebar_path:
            lines.append('Атрибут: ' + _format_path(self._sidebar_path))
        lines.append(self.role_name)
        return lines

    def related(self) -> list:
        return self.header_path + self.sidebar_path


class ResultCell(StructureCell):
    """Ячейка переза -- итоговой строки таблицы."""

    role = 'result'
    role_name = 'ячейка итоговой строки'

    def __init__(self, *args):
        super().__init__(*args)
        self._aggregated = []

    @property
    def is_label(self) -> bool:
        """Подпись итоговой строки, например "Итого по 1-ой бригаде"."""
        return self.detail_type == DetailedDataType.STRING

    @property
    def aggregated(self) -> list:
        """
        Ячейки данных, которые агрегирует этот итог.

        Пустой список у подписи, у пустой ячейки и у итога над столбцом,
        в котором есть не только числа.
        """
        return list(self._aggregated)

    def hint(self) -> list:
        if self.is_label:
            return ['подпись итоговой строки']
        if self._aggregated:
            return [f'Агрегирует ячеек: {len(self._aggregated)}',
                    'ячейка является агрегацией']
        return [self.role_name]

    def related(self) -> list:
        return self.aggregated


# Какой класс объекта соответствует классу ячейки из эвристики
CELL_CLASSES = {
    ClassCell.CELL_TITLE: TitleCell,
    ClassCell.CELL_SIDEBAR: SidebarCell,
    ClassCell.CELL_DATA: DataCell,
    ClassCell.CELL_RESULT: ResultCell,
}


class StructureTable:
    """
    Подлинная таблица как набор связанных объектов-ячеек.

    Держит две сетки. Сетка страницы -- таблица такой, какой её видит человек:
    по ней считаются координаты. Сетка разбора -- таблица такой, какой её
    разобрала эвристика: заголовки сверху, боковик слева. По ней ищутся
    заголовки выше и атрибуты левее. Если заголовок таблицы слева, эвристика
    разбирает её повёрнутой, и сетки не совпадают.
    """

    def __init__(self, cells: list, rows: list, page_grid: TableGrid,
                 orientation: str):
        """
        Сохраняет готовые части. Для создания объекта служит :meth:`from_table`.

        Args:
            cells: объекты ячеек сверху вниз, слева направо
            rows: объекты ячеек по строкам страницы
            page_grid: сетка страницы, клетки которой уже ведут к объектам
            orientation: "top" или "left"
        """
        self._cells = cells
        self._rows = rows
        self._grid = page_grid
        self._orientation = orientation

    @classmethod
    def from_table(cls, table: Table) -> 'StructureTable':
        """
        Разбирает таблицу и строит её объектную модель.

        Исходная таблица не меняется: эвристика работает с копиями ячеек,
        а временные атрибуты, по которым копии находят исходные ячейки,
        снимаются перед возвратом.

        Args:
            table: таблица в том виде, в каком она стоит на странице

        Returns:
            Объектную модель таблицы

        Raises:
            TitleTypeError, DataTypeError, LayoutError: таблица не подлинная,
                исключение эвристики передаётся без изменений
            ValueError: эвристика оставила ячейку без класса
        """
        originals = {}
        for number, cell in enumerate(c for row in table.table for c in row):
            cell.data[MARK] = str(number)
            originals[str(number)] = cell

        try:
            marked = get_genuine(table)
        finally:
            for cell in originals.values():
                cell.data.attrs.pop(MARK, None)

        parse_grid = TableGrid(marked)
        page_grid = TableGrid(table)

        # Размеченная ячейка -> исходная ячейка той же клетки страницы
        page_cell = {}
        for cell in parse_grid.cells():
            page_cell[cell] = originals[cell.data.attrs.pop(MARK)]

        same_place = all(parse_grid.position(cell) == page_grid.position(original)
                         for cell, original in page_cell.items())
        orientation = 'top' if same_place else 'left'

        objects = {}   # размеченная ячейка -> объект
        for cell, original in page_cell.items():
            if cell.classCell not in CELL_CLASSES:
                raise ValueError(
                    f'Ячейка "{cell.content}" осталась без класса после разбора')
            row, col = page_grid.position(original)
            objects[cell] = CELL_CLASSES[cell.classCell](
                cell, row, col, original.rowspan_original, original.colspan_original)

        _link_paths(parse_grid, objects)
        _link_children(objects.values())
        _link_aggregation(parse_grid, objects)

        by_original = {page_cell[cell]: obj for cell, obj in objects.items()}
        page_grid = _ObjectGrid(page_grid, by_original)
        rows = [[by_original[cell] for cell in row if cell in by_original]
                for row in table.table if row]
        cells = sorted(objects.values(), key=lambda obj: (obj.row, obj.col))

        return cls(cells, rows, page_grid, orientation)

    @property
    def orientation(self) -> str:
        """Где заголовки: "top" -- сверху, "left" -- слева."""
        return self._orientation

    @property
    def height(self) -> int:
        """Число строк на странице."""
        return self._grid.height

    @property
    def width(self) -> int:
        """Число столбцов на странице."""
        return self._grid.width

    @property
    def cells(self) -> list:
        """Все ячейки сверху вниз, слева направо."""
        return list(self._cells)

    @property
    def rows(self) -> list:
        """Ячейки по строкам таблицы в том порядке, как они записаны в HTML."""
        return [list(row) for row in self._rows]

    @property
    def titles(self) -> list:
        return [cell for cell in self._cells if isinstance(cell, TitleCell)]

    @property
    def sidebars(self) -> list:
        return [cell for cell in self._cells if isinstance(cell, SidebarCell)]

    @property
    def data(self) -> list:
        return [cell for cell in self._cells if isinstance(cell, DataCell)]

    @property
    def results(self) -> list:
        return [cell for cell in self._cells if isinstance(cell, ResultCell)]

    def cell_at(self, row: int, col: int):
        """
        Возвращает ячейку по координатам страницы.

        У объединённой ячейки любая её клетка даёт один и тот же объект.

        Args:
            row: номер строки, с нуля
            col: номер столбца, с нуля

        Returns:
            Объект ячейки либо None, если клетка пустая
        """
        return self._grid.cell_at(row, col)

    def __repr__(self) -> str:
        return (f'StructureTable({self.height} x {self.width}, '
                f'orientation={self.orientation!r})')


class _ObjectGrid:
    """Сетка страницы, клетки которой ведут к объектам, а не к ячейкам Cell."""

    def __init__(self, grid: TableGrid, objects: dict):
        self._grid = grid
        self._objects = objects
        self.height = grid.height
        self.width = grid.width

    def cell_at(self, row: int, col: int):
        return self._objects.get(self._grid.cell_at(row, col))


def _link_paths(grid: TableGrid, objects: dict) -> None:
    """
    Находит для каждой ячейки заголовки выше и атрибуты левее.

    Проход идёт по сетке разбора: заголовки -- все ячейки-заголовки над
    ячейкой в её столбце, атрибуты -- все ячейки боковика левее в её строке.
    Подпись раздела (строка из одной ячейки во всю ширину) тоже является
    заголовком и попадает в путь всех ячеек под ней.
    """
    for cell, obj in objects.items():
        obj._header_path = [objects[above] for above in grid.column_above(cell)
                            if isinstance(objects.get(above), TitleCell)]
        obj._sidebar_path = [objects[left] for left in grid.row_left(cell)
                             if isinstance(objects.get(left), SidebarCell)]


def _link_children(objects) -> None:
    """Заполняет подзаголовки, податрибуты и ячейки данных под заголовками."""
    for obj in objects:
        if isinstance(obj, (TitleCell, SidebarCell)) and obj.parent is not None:
            obj.parent._children.append(obj)
        if isinstance(obj, DataCell):
            for title in obj._header_path:
                title._data_cells.append(obj)


def _cross_section_signature(grid: TableGrid, objects: dict, row: int):
    """
    Возвращает конструкцию переза: где начинается его подпись и какой она ширины.

    Итоги одного уровня устроены одинаково: все "Итого по бригаде" подписаны
    со второго столбца шириной в три, а общее "Итого" -- с первого шириной
    в четыре. По конструкции видно, где кончается группа, которую итог
    подводит.

    Args:
        grid: сетка разбора
        objects: размеченная ячейка -> объект
        row: номер строки сетки разбора

    Returns:
        Пару (столбец начала подписи, ширина подписи) либо None, если в строке
        нет подписи переза
    """
    for col in range(grid.width):
        cell = grid.cell_at(row, col)
        obj = objects.get(cell)
        if isinstance(obj, ResultCell) and obj.is_label and grid.position(cell)[0] == row:
            return grid.position(cell)[1], cell.colspan_original
    return None


def _link_aggregation(grid: TableGrid, objects: dict) -> None:
    """
    Находит для каждого числа в перезе ячейки данных, которые оно агрегирует.

    От числа идём вверх по его столбцу и собираем ячейки данных. Проход
    останавливается на заголовке либо на перезе той же конструкции --
    предыдущем итоге того же уровня. Перезы другой конструкции проход
    пропускает, поэтому общий итог собирает все данные столбца, минуя
    промежуточные итоги.

    Итог считается агрегацией, только если под заголовком столбца одни
    числа и пустые ячейки.
    """
    for cell, obj in objects.items():
        if not isinstance(obj, ResultCell) or obj.data_type != DataType.GENUINE:
            continue
        if obj.header is None or not obj.header.data_types <= NUMERIC_TYPES | {DetailedDataType.NO_DATA}:
            continue

        row, col = grid.position(cell)
        signature = _cross_section_signature(grid, objects, row)
        collected = []
        for above in range(row - 1, -1, -1):
            other = objects.get(grid.cell_at(above, col))
            if isinstance(other, TitleCell):
                break
            if isinstance(other, ResultCell) and \
                    _cross_section_signature(grid, objects, above) == signature:
                break
            if isinstance(other, DataCell) and other not in collected:
                collected.append(other)

        obj._aggregated = collected[::-1]
