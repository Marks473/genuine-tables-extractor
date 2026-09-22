"""
Отдельные правила проверки структуры таблицы.

Здесь собраны частные проверки, которыми пользуются стадии разбора из модуля
:mod:`Heuristic`. Вынесены отдельно, чтобы основной модуль описывал порядок
разбора, а не подробности каждой проверки.
"""

from CellType import DataType, DetailedDataType

from heuristic_errors import DataTypeError

# Типы, допустимые в ячейках переза правее его подписи
CROSS_SECTION_TAIL_TYPES = {DetailedDataType.NO_DATA}

# Типы, совместимые между собой в одном столбце
TEXT_LIKE = {DetailedDataType.LINK, DetailedDataType.STRING}


def count_merged_parents(parents: list, start: int, width: int) -> int:
    """
    Определяет, сколько подряд идущих родительских ячеек покрывает один потомок.

    Нужен для боковиков переменной глубины: строки "В." и "неодуш." вместе
    занимают ту же ширину, что одна ячейка "Тв." в следующей строке.

    Args:
        parents: список родительских ячеек
        start: индекс, с которого начинается покрытие
        width: ширина (colspan) дочерней ячейки

    Returns:
        Количество покрытых родительских ячеек либо 0, если точного покрытия нет
    """
    covered = 0
    for count, cell in enumerate(parents[start:], start=1):
        covered += cell.colspan
        if covered == width:
            return count
        if covered > width:
            break

    return 0


def is_section_divider(row: list, parents: list) -> bool:
    """
    Проверяет, является ли строка разделителем секции.

    Разделитель -- это одиночная ячейка, растянутая на всю ширину таблицы.
    Такие строки подписывают группу следующих за ними строк данных
    (например, "Skin" перед перечислением видов рака кожи) и не описывают
    структуру столбцов, поэтому при разборе заголовков их пропускают.

    Args:
        row: ячейки проверяемой строки
        parents: ячейки предыдущего уровня, задающие ширину таблицы

    Returns:
        True, если строка является разделителем секции
    """
    if len(row) != 1 or not parents:
        return False

    return row[0].colspan == sum(cell.colspan for cell in parents)


def check_cross_section(row: list) -> None:
    """
    Проверяет, что строка является перерезом -- итоговой строкой таблицы.

    Перерез устроен так: несколько пустых ячеек, ровно одна текстовая
    (подпись итога), а правее неё -- пустые ячейки либо числа.

    Функция ничего не возвращает: строка либо проходит проверку, либо
    возбуждается исключение с описанием того, что именно не сошлось.
    Вызывающий код опирается на это и ловит :class:`DataTypeError`.

    Args:
        row: ячейки проверяемой строки

    Raises:
        DataTypeError: строка не удовлетворяет описанной структуре
    """
    if not row:
        return

    labels = [index for index, cell in enumerate(row)
              if cell.detailType == DetailedDataType.STRING]

    if len(labels) != 1:
        contents = ' | '.join(cell.content for cell in row)
        raise DataTypeError(
            f'в строке таблицы \n "{contents} | " \n нет типа данных строка')

    label = labels[0]

    # Слева от подписи перерез пуст
    for cell in row[:label]:
        if cell.detailType != DetailedDataType.NO_DATA:
            raise DataTypeError(
                f'ячейка "{cell.content}" с типом данных {cell.detailType} '
                f'в срезе не соответствует типу данных "{DetailedDataType.NO_DATA}"')

    # Справа от подписи стоят итоговые значения либо пустые ячейки
    for cell in row[label + 1:]:
        if cell.detailType not in CROSS_SECTION_TAIL_TYPES and cell.type != DataType.GENUINE:
            raise DataTypeError(
                f'ячейка "{cell.content}" с типом данных {cell.detailType} '
                f'в срезе не соответствует ни пустой ячейке, ни числу')


def check_data_type_compatibility(parent_cell, child_cell) -> None:
    """
    Проверяет, что типы данных родительской и дочерней ячеек согласуются.

    В подлинной таблице столбец однороден по типу. Правила послабления:

    * совпадающие типы согласуются всегда;
    * пустая ячейка согласуется с любым типом -- как со стороны потомка,
      так и со стороны родителя;
    * текст и ссылка считаются одним типом: ссылка почти всегда подписана
      текстом и несёт ту же величину.

    Args:
        parent_cell: ячейка предыдущей строки того же столбца
        child_cell: ячейка текущей строки

    Raises:
        DataTypeError: типы несовместимы, столбец неоднороден
    """
    parent_type = parent_cell.detailType
    child_type = child_cell.detailType

    if parent_type == child_type:
        return

    if DetailedDataType.NO_DATA in (parent_type, child_type):
        return

    if parent_type in TEXT_LIKE and child_type in TEXT_LIKE:
        return

    raise DataTypeError(
        f'Несовместимые типы данных в столбце:\n'
        f'  Родительская ячейка: "{parent_cell.content}" (тип: {parent_type})\n'
        f'  Дочерняя ячейка: "{child_cell.content}" (тип: {child_type})')
