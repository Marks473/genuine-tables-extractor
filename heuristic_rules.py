"""
Отдельные правила проверки структуры таблицы.

Здесь собраны частные проверки, которыми пользуются стадии разбора из модуля
:mod:`Heuristic`. Вынесены отдельно, чтобы основной модуль описывал порядок
разбора, а не подробности каждой проверки.
"""

import CellType
from CellType import DataType, DetailedDataType

from heuristic_errors import DataTypeError


def _count_merged_parents(parents: list, start: int, width: int) -> int:
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


def _is_section_divider(row: list, parents: list) -> bool:
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


def _check_if_cross_section(row: list) -> bool:
    """
    Проверяет, является ли строка перерезом (итоговой строкой).

    Перерез должен иметь структуру:
    - N ячеек NO_DATA (N >= 0)
    - Ровно 1 ячейка STRING
    - Остальные ячейки NO_DATA или GENUINE

    Args:
        row: список ячеек строки

    Returns:
        True если строка является перерезом, False иначе
    """
    if not row:
        return False
    string_count = 0
    string_index = -1

    # Ищем STRING ячейки
    for idx, cell in enumerate(row):
        if cell.detailType == CellType.DetailedDataType.STRING:
            string_count += 1
            string_index = idx
    # Должна быть ровно одна STRING ячейка
    if string_count != 1:
        err = ''
        for cell in row:
            err += cell.content + ' | '
        raise DataTypeError(f'в строке таблицы \n "{err}" \n нет типа данных строка')

    # Проверяем ячейки до STRING - должны быть NO_DATA
    for i in range(string_index):
        a = row[0]
        if row[i].detailType != CellType.DetailedDataType.NO_DATA:
            raise DataTypeError(f'ячейка "{row[i].content}" с типом данных {row[i].content} в срезе не соответствующих типу данных "{CellType.DetailedDataType.NO_DATA}" ')

    # Проверяем ячейки после STRING - должны быть NO_DATA или GENUINE
    for i in range(string_index + 1, len(row)):
        detail_type = row[i].detailType
        data_type = row[i].type

        if detail_type != CellType.DetailedDataType.NO_DATA and \
                data_type != CellType.DataType.GENUINE:
            raise DataTypeError(f'ячейка "{row[i].content}" с типом данных {row[i].content} в срезе не соответствующих типу данных')

def _check_data_type_compatibility(parent_cell, child_cell):
    """
    Вспомогательная функция для проверки совместимости типов данных в столбце.

    Правила:
    - Если родитель имеет определенный тип, потомок должен иметь тот же или NO_DATA
    - STRING и LINK совместимы между собой
    - NO_DATA совместим со всем
    """
    old_type = parent_cell.detailType
    new_type = child_cell.detailType
    # Типы совпадают - ОК
    if old_type == new_type:
        return

    # Потомок пустой - наследует тип родителя
    if new_type == DetailedDataType.NO_DATA:
        return

    # Родитель пустой - потомок устанавливает тип
    if old_type == DetailedDataType.NO_DATA:
        return

    # STRING и LINK совместимы
    if (new_type in {DetailedDataType.LINK, DetailedDataType.STRING} and
            old_type in {DetailedDataType.LINK, DetailedDataType.STRING}):
        return

    # Несовместимые типы
    raise DataTypeError(
        f'Несовместимые типы данных в столбце:\n'
        f'  Родительская ячейка: "{parent_cell.content}" (тип: {old_type})\n'
        f'  Дочерняя ячейка: "{child_cell.content}" (тип: {new_type})')
