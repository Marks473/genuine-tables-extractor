"""
Сетка покрытия таблицы.

HTML описывает таблицу строками, а объединённые ячейки (rowspan, colspan)
сдвигают остальные ячейки строки. Поэтому по списку строк нельзя сразу
сказать, какая ячейка стоит над данной: в строке ``[Год, Продажи]`` и
строке ``[Q1, Q2]`` под "Год" на самом деле ничего нового нет, а "Q1" стоит
под "Продажи".

Сетка покрытия раскладывает таблицу на клетки: в клетке (строка, столбец)
лежит ячейка, которая эту клетку накрывает. Ячейка с rowspan = a и
colspan = b занимает a * b клеток. После этого "всё, что выше ячейки" --
это просто проход по её столбцу вверх.
"""

from Table import Table


class TableGrid:
    """
    Сетка покрытия таблицы: клетка -> ячейка, которая её накрывает.

    Размеры ячеек берутся из ``rowspan_original`` и ``colspan_original``:
    эвристика во время разбора уменьшает ``rowspan``, а исходные значения
    не трогает. Благодаря этому сетку можно строить и по размеченной таблице.
    """

    def __init__(self, table: Table):
        """
        Раскладывает строки таблицы по клеткам.

        Строки обходятся сверху вниз, каждая ячейка ставится в первую свободную
        слева клетку своей строки. Ячейка, у которой rowspan выходит за нижний
        край таблицы, обрезается по нему.

        Args:
            table: таблица, по строкам которой строится сетка
        """
        rows = [row for row in table.table if row]
        self._height = len(rows)
        self._cells = {}       # (строка, столбец) -> ячейка
        self._positions = {}   # ячейка -> её левая верхняя клетка

        for row_index, row in enumerate(rows):
            col = 0
            for cell in row:
                while (row_index, col) in self._cells:
                    col += 1

                self._positions[cell] = (row_index, col)
                rowspan = max(cell.rowspan_original, 1)
                colspan = max(cell.colspan_original, 1)
                for dr in range(rowspan):
                    if row_index + dr >= self._height:
                        break
                    for dc in range(colspan):
                        self._cells[(row_index + dr, col + dc)] = cell

                col += colspan

        self._width = max((c for _, c in self._cells), default=-1) + 1

    @property
    def height(self) -> int:
        """Число строк сетки."""
        return self._height

    @property
    def width(self) -> int:
        """Число столбцов сетки."""
        return self._width

    def cell_at(self, row: int, col: int):
        """
        Возвращает ячейку, которая накрывает клетку.

        Args:
            row: номер строки, с нуля
            col: номер столбца, с нуля

        Returns:
            Ячейку либо None, если клетка пустая (строка короче остальных)
        """
        return self._cells.get((row, col))

    def position(self, cell) -> tuple:
        """
        Возвращает левую верхнюю клетку ячейки.

        Args:
            cell: ячейка этой таблицы

        Returns:
            Пару (строка, столбец)

        Raises:
            KeyError: ячейка не принадлежит таблице
        """
        return self._positions[cell]

    def cells(self) -> list:
        """Возвращает все ячейки сетки сверху вниз, слева направо."""
        return sorted(self._positions, key=self._positions.get)

    def column_above(self, cell) -> list:
        """
        Возвращает ячейки над ячейкой в её левом столбце, сверху вниз.

        Ячейка, растянутая на несколько строк, встречается в столбце несколько
        раз, но в результат попадает один раз.

        Args:
            cell: ячейка этой таблицы

        Returns:
            Список различных ячеек выше данной
        """
        row, col = self._positions[cell]
        return _distinct(self.cell_at(r, col) for r in range(row))

    def row_left(self, cell) -> list:
        """
        Возвращает ячейки левее ячейки в её верхней строке, слева направо.

        Args:
            cell: ячейка этой таблицы

        Returns:
            Список различных ячеек левее данной
        """
        row, col = self._positions[cell]
        return _distinct(self.cell_at(row, c) for c in range(col))


def _distinct(cells) -> list:
    """Убирает пустые клетки и повторы, сохраняя порядок."""
    result = []
    for cell in cells:
        if cell is not None and cell not in result:
            result.append(cell)
    return result
