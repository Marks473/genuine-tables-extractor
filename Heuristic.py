
import CellType
from Table import Table
from Cell import Cell
from CellType import DetailedDataType
from CellType import DataType
from bs4 import Tag

from heuristic_errors import TitleTypeError, DataTypeError, LayoutError
from heuristic_rules import (
    _check_data_type_compatibility,
    _check_if_cross_section,
    _count_merged_parents,
    _is_section_divider,
)


def vertical_check(table: Table) -> Table:
    """
    Полностью проверяет таблицу с заголовком сверху.

    Разбор идёт тремя стадиями, каждая из которых опирается на разметку,
    проставленную предыдущей:

    1. :func:`get_head`    -- находит границу блока заголовков и размечает их;
    2. :func:`get_data`    -- проверяет область данных и находит перерезы;
    3. :func:`get_sidebar` -- проверяет боковик, если строк больше двух.

    Args:
        table: таблица, ячейки которой будут размечены на месте

    Returns:
        Ту же таблицу с проставленными классами ячеек

    Raises:
        TitleTypeError: в заголовке оказался недопустимый тип данных
        DataTypeError: типы данных в столбце не согласуются
        LayoutError: нарушена геометрия таблицы
    """
    get_head(table)
    get_data(table)
    if len(table.table) > 2:
        get_sidebar(table)
    return table

def get_head(table: Table) -> Table:
    """
    Проверяет, что заголовки не зубчатые (заканчиваются на одной линии).
    Помечает все заголовки как CELL_TITLE, первую строку данных как CELL_DATA.

    Returns:
        Table с размеченными классами ячеек

    Raises:
        TitleTypeError: если заголовок содержит неправильный тип данных
        LayoutError: если структура нарушена или заголовки "зубчатые"
    """
    table_data = table.table

    if len(table_data) < 2:
        raise LayoutError("Таблица должна иметь минимум 2 строки (заголовок + данные)")

    # Начинаем с первой строки (родительские ячейки)
    old = []
    for cell in table_data[0]:
        if cell.type not in {DataType.STRING, DataType.NO_DATA, DataType.LINK}:
            raise TitleTypeError(f'Ячейка-заголовок: "{cell.content}" имеет неправильный тип {cell.type}')
        cell.classCell = CellType.ClassCell.CELL_TITLE
        old.append(cell)

    new = []

    # Итерируемся по оставшимся строкам
    for i in range(1, len(table_data)):
        # Разделитель секции подписывает идущую ниже группу строк данных
        # и не задаёт структуру столбцов, поэтому в сопоставлении
        # с родительскими ячейками не участвует и рядов родителей не расходует
        if _is_section_divider(table_data[i], old):
            table_data[i][0].classCell = CellType.ClassCell.CELL_TITLE
            continue

        # Уменьшаем rowspan у всех старых ячеек
        for cell in old:
            cell.rowspan -= 1

        j = 0  # Индекс дочерней ячейки в текущей строке
        s = 0  # Сумма длин (colspan) дочерних ячеек
        k = 0  # Индекс родительской ячейки

        while k < len(old):
            # Если родительская ячейка еще "активна" (rowspan > 0)
            if old[k].rowspan > 0:
                new.append(old[k])
                k += 1
                continue

            # Проверяем наличие дочерней ячейки
            if j >= len(table_data[i]):
                raise LayoutError(
                    f'Недостаточно ячеек в строке {i}: ожидалось покрытие ячейки "{old[k].content}"')

            # Сумма длин дочерних меньше родительской
            if (s + table_data[i][j].colspan) < old[k].colspan:
                s += table_data[i][j].colspan

                # Проверка, что заголовок это строка
                if table_data[i][j].type not in {DataType.GENUINE, DataType.STRING, DataType.LINK}:
                    raise TitleTypeError(
                        f'Ячейка-заголовок: "{table_data[i][j].content}" имеет неправильный тип "{table_data[i][j].type}"')

                table_data[i][j].classCell = CellType.ClassCell.CELL_TITLE
                new.append(table_data[i][j])
                j += 1
                continue

            # Сумма длин дочерних равна родительской
            if (s + table_data[i][j].colspan) == old[k].colspan:
                if s == 0:
                    # Один родитель = один потомок → это первая ячейка данных
                    # Значит, ВСЕ заголовки закончились на предыдущей строке

                    # Проверяем, что слева нет других ячеек (иначе "зубчатые" заголовки)
                    if j > 0:
                        raise LayoutError(
                            f'Заголовки "зубчатые": ячейка данных "{table_data[i][j].content}" '
                            f'находится справа от ячейки заголовка "{table_data[i][j - 1].content}"')

                    # Помечаем текущую ячейку как данные
                    table_data[i][j].classCell = CellType.ClassCell.CELL_DATA
                    j += 1
                    k += 1

                    # Теперь проверяем, что ВСЕ оставшиеся ячейки в строке тоже данные
                    # и соответствуют структуре (нет активных rowspan у заголовков)

                    while k < len(old):
                        # print(old[k].content, table_data[i][j].content, '<<<<')
                        # Проверяем, что родительская ячейка закончилась

                        if old[k].rowspan > 0:
                            raise LayoutError(
                                f'Заголовки "зубчатые": ячейка-заголовок "{old[k].content}" '
                                f'выступает за строку {i} (rowspan={old[k].rowspan})')
                        # if old[k].rowspan == 1:
                        #     k += 1
                        #     continue
                        # Проверяем наличие дочерней ячейки
                        if j >= len(table_data[i]):
                            raise LayoutError(
                                f'Недостаточно ячеек данных в строке {i}: '
                                f'ожидалось покрытие ячейки "{old[k].content}"')

                        # Проверяем соответствие colspan
                        if table_data[i][j].colspan != old[k].colspan:
                            raise LayoutError(
                                f'Заголовки "зубчатые": ячейка данных "{table_data[i][j].content}" '
                                f'(colspan={table_data[i][j].colspan}) не соответствует '
                                f'заголовку "{old[k].content}" (colspan={old[k].colspan})')

                        # Помечаем как данные
                        table_data[i][j].classCell = CellType.ClassCell.CELL_DATA
                        k += 1
                        j += 1

                    # Проверяем, что обработали все ячейки корректно
                    if not ((j == len(table_data[i])) and (k == len(old))):
                        raise LayoutError(
                            f'Несоответствие структуры в строке {i}: '
                            f'обработано {j} из {len(table_data[i])} ячеек')

                    # Все проверки пройдены - таблица валидна, заголовки размечены
                    return table

                else:
                    # Один родитель = несколько потомков (и этот последний)
                    # Это всё ещё заголовки
                    if table_data[i][j].type not in {DataType.GENUINE, DataType.STRING, DataType.LINK}:
                        raise TitleTypeError(
                            f'Ячейка-заголовок: "{table_data[i][j].content}" '
                            f'имеет неправильный тип "{table_data[i][j].type}"')

                    s = 0  # Сбрасываем счетчик
                    table_data[i][j].classCell = CellType.ClassCell.CELL_TITLE
                    new.append(table_data[i][j])
                    j += 1
                    k += 1
                    continue

            # Несоответствие структуры (сумма > родительской)
            raise LayoutError(
                f'Ячейка "{table_data[i][j].content}" (colspan={table_data[i][j].colspan}) '
                f'выходит за границы родительской ячейки "{old[k].content}" (colspan={old[k].colspan})')

        # Проверяем, что обработали все ячейки в строке
        if not ((j == len(table_data[i])) and (k == len(old))):
            raise LayoutError(
                f'Несоответствие структуры в строке {i}: '
                f'обработано {j} из {len(table_data[i])} ячеек, {k} из {len(old)} родителей')

        # Переносим обработанные ячейки в "старые"
        old = [cell for cell in new]
        new = []

    # Если дошли до конца и не нашли строку данных
    raise LayoutError('В таблице нет ячеек данных - только заголовки')

def get_sidebar(table: Table) -> Table:
    """
    Проверяет, что боковики не зубчатые (заканчиваются на одной линии).
    Помечает все боковики как CELL_SIDEBAR, первый столбец данных как CELL_DATA.

    Returns:
        Table с размеченными классами ячеек

    Raises:
        TitleTypeError: если боковик содержит неправильный тип данных
        LayoutError: если структура нарушена или боковики "зубчатые"
    """
    table.reset_span()
    table.transpose
    table_data = table.table

    if len(table_data) < 2:
        raise LayoutError("Таблица должна иметь минимум 2 строки (боковик + данные)")

    # Начинаем с первой строки (родительские ячейки)
    old = []
    for cell in table_data[0]:
        # Пропускаем заголовки и результаты
        if cell.classCell in {CellType.ClassCell.CELL_TITLE, CellType.ClassCell.CELL_RESULT}:
            continue
        if cell.type not in {DataType.GENUINE, DataType.STRING, DataType.LINK}:
            raise TitleTypeError(f'Ячейка-боковик: "{cell.content}" имеет неправильный тип {cell.type}')
        cell.classCell = CellType.ClassCell.CELL_SIDEBAR
        old.append(cell)

    if len(old) == 0:
        raise LayoutError("В первой строке нет боковиков (все ячейки - заголовки или результаты)")

    new = []

    # Итерируемся по оставшимся строкам
    for i in range(1, len(table_data)):
        # Разделитель секции подписывает идущую ниже группу строк данных
        # и не задаёт структуру столбцов, поэтому в сопоставлении
        # с родительскими ячейками не участвует и рядов родителей не расходует
        if _is_section_divider(table_data[i], old):
            table_data[i][0].classCell = CellType.ClassCell.CELL_TITLE
            continue

        # Уменьшаем rowspan у всех старых ячеек
        for cell in old:
            cell.rowspan -= 1

        j = 0  # Индекс дочерней ячейки в текущей строке
        s = 0  # Сумма длин (colspan) дочерних ячеек
        k = 0  # Индекс родительской ячейки
        sidebar_count = 0  # Сколько боковиков обработано в текущей строке

        while k < len(old):
            # Пропускаем заголовки и результаты
            while j < len(table_data[i]) and table_data[i][j].classCell in {CellType.ClassCell.CELL_TITLE, CellType.ClassCell.CELL_RESULT}:
                j += 1

            # Если родительская ячейка еще "активна" (rowspan > 0)
            if old[k].rowspan > 0:
                new.append(old[k])
                k += 1
                continue

            # Проверяем наличие дочерней ячейки
            if j >= len(table_data[i]):
                raise LayoutError(
                    f'Недостаточно ячеек в строке {i}: ожидалось покрытие ячейки "{old[k].content}"')

            # Сумма длин дочерних меньше родительской
            if (s + table_data[i][j].colspan) < old[k].colspan:
                s += table_data[i][j].colspan
                # Проверка, что боковик это строка
                if table_data[i][j].type not in {DataType.GENUINE, DataType.STRING, DataType.LINK}:
                    raise TitleTypeError(
                        f'Ячейка-боковик: "{table_data[i][j].content}" имеет неправильный тип "{table_data[i][j].type}"')
                table_data[i][j].classCell = CellType.ClassCell.CELL_SIDEBAR
                new.append(table_data[i][j])
                sidebar_count += 1
                j += 1
                continue

            # Сумма длин дочерних равна родительской
            if (s + table_data[i][j].colspan) == old[k].colspan:
                if s == 0:
                    # Один родитель = один потомок → это первая ячейка данных
                    # Значит, ВСЕ боковики закончились на предыдущей строке

                    # Проверяем, что слева нет других боковиков (иначе "зубчатые" боковики)
                    if sidebar_count > 0:
                        raise LayoutError(
                            f'Боковики "зубчатые": ячейка данных "{table_data[i][j].content}" '
                            f'находится справа от ячейки боковика')

                    # Помечаем текущую ячейку как данные (только если она еще не помечена)
                    if table_data[i][j].classCell not in {CellType.ClassCell.CELL_DATA,
                                                           CellType.ClassCell.CELL_TITLE,
                                                           CellType.ClassCell.CELL_RESULT}:
                        table_data[i][j].classCell = CellType.ClassCell.CELL_DATA
                    j += 1
                    k += 1

                    # Теперь проверяем, что ВСЕ оставшиеся ячейки в строке тоже данные
                    # и соответствуют структуре (нет активных rowspan у боковиков)
                    while k < len(old):
                        # Пропускаем заголовки и результаты
                        while j < len(table_data[i]) and table_data[i][j].classCell in {CellType.ClassCell.CELL_TITLE, CellType.ClassCell.CELL_RESULT}:
                            j += 1

                        # Проверяем, что родительская ячейка закончилась
                        if old[k].rowspan > 1:
                            raise LayoutError(
                                f'Боковики "зубчатые": ячейка-боковик "{old[k].content}" '
                                f'выступает за строку {i} (rowspan={old[k].rowspan})')

                        if old[k].rowspan == 1:
                            k += 1
                            continue

                        # Проверяем наличие дочерней ячейки
                        if j >= len(table_data[i]):
                            raise LayoutError(
                                f'Недостаточно ячеек данных в строке {i}: '
                                f'ожидалось покрытие ячейки "{old[k].content}"')

                        # Проверяем соответствие colspan
                        if table_data[i][j].colspan != old[k].colspan:
                            raise LayoutError(
                                f'Боковики "зубчатые": ячейка данных "{table_data[i][j].content}" '
                                f'(colspan={table_data[i][j].colspan}) не соответствует '
                                f'боковику "{old[k].content}" (colspan={old[k].colspan})')

                        # Помечаем как данные (только если еще не помечена)
                        if table_data[i][j].classCell not in {CellType.ClassCell.CELL_DATA,
                                                               CellType.ClassCell.CELL_TITLE,
                                                               CellType.ClassCell.CELL_RESULT}:
                            table_data[i][j].classCell = CellType.ClassCell.CELL_DATA
                        k += 1
                        j += 1

                    # Все проверки пройдены - боковики размечены
                    # table_transpose.reset_span()
                    # table_transpose.print()
                    table.reset_span()
                    # table_transpose.print()
                    table.transpose
                    # result_table.print()


                    return table

                else:
                    # Один родитель = несколько потомков (и этот последний)
                    # Это всё ещё боковики
                    if table_data[i][j].type not in {DataType.GENUINE, DataType.STRING, DataType.LINK}:
                        raise TitleTypeError(
                            f'Ячейка-боковик: "{table_data[i][j].content}" '
                            f'имеет неправильный тип "{table_data[i][j].type}"')
                    s = 0  # Сбрасываем счетчик
                    table_data[i][j].classCell = CellType.ClassCell.CELL_SIDEBAR
                    new.append(table_data[i][j])
                    sidebar_count += 1
                    j += 1
                    k += 1
                    continue

            # Несоответствие структуры (сумма > родительской)
            raise LayoutError(
                f'Ячейка "{table_data[i][j].content}" (colspan={table_data[i][j].colspan}) '
                f'выходит за границы родительской ячейки "{old[k].content}" (colspan={old[k].colspan})')

        # Переносим обработанные ячейки в "старые"
        old = [cell for cell in new]
        new = []

    # Если дошли до конца и не нашли столбец данных
    raise LayoutError('В таблице нет ячеек данных - только боковики')

def get_data(table: Table) -> Table:
    """
    Проверяет корректность области данных после разметки заголовков.
    Запускается ПОСЛЕ get_hed, проверяет:
    - Каждая родительская ячейка имеет РОВНО одного потомка с тем же colspan
    - Типы данных в столбцах согласованы
    - Обрабатывает перерезы (итоговые строки)

    Returns:
        Table с размеченными ячейками данных (CELL_DATA) и результатов (CELL_RESULT)

    Raises:
        LayoutError: если структура некорректна
        DataTypeError: если типы данных в столбце несовместимы
    """
    table_data = table.table

    if len(table_data) < 2:
        raise LayoutError("Таблица должна иметь минимум 2 строки (заголовок + данные)")

    # Находим первую строку данных (помеченную get_hed)
    start = 0
    while start < len(table_data) and table_data[start][0].classCell == CellType.ClassCell.CELL_TITLE:
        start += 1

    if start >= len(table_data):
        raise LayoutError("В таблице нет строк с данными")

    # Начинаем с первой строки данных (родительские ячейки)
    old = [cell for cell in table_data[start]]

    # Итерируемся по оставшимся строкам данных
    for i in range(start + 1, len(table_data)):
        # Уменьшаем rowspan у всех старых ячеек
        for cell in old:
            cell.rowspan -= 1

        new = []
        j = 0  # Индекс дочерней ячейки в текущей строке
        k = 0  # Индекс родительской ячейки

        while k < len(old):


            # Если родительская ячейка еще "активна" (rowspan > 0)
            if old[k].rowspan > 0:
                new.append(old[k])
                k += 1
                continue

            # Проверяем наличие дочерней ячейки
            if j >= len(table_data[i]):
                raise LayoutError(
                    f'Недостаточно ячеек в строке {i}: '
                    f'ожидалась дочерняя ячейка для "{old[k].content}"')

            # Родительская ячейка может делиться на несколько потомков:
            # так устроен многоуровневый боковик, где, например, падеж "В."
            # разбивается на "одуш." и "неодуш.". Собираем потомков до тех пор,
            # пока их суммарная ширина не покроет родителя
            if table_data[i][j].colspan < old[k].colspan:
                covered = 0
                while j < len(table_data[i]) and covered < old[k].colspan:
                    child = table_data[i][j]

                    if covered + child.colspan > old[k].colspan:
                        raise LayoutError(
                            f'Несоответствие colspan в строке {i}: потомки ячейки '
                            f'"{old[k].content}" (colspan={old[k].colspan}) в сумме шире родителя')

                    _check_data_type_compatibility(old[k], child)
                    child.classCell = CellType.ClassCell.CELL_DATA
                    new.append(child)
                    covered += child.colspan
                    j += 1

                if covered != old[k].colspan:
                    raise LayoutError(
                        f'Несоответствие colspan в строке {i}: '
                        f'родительская ячейка "{old[k].content}" имеет colspan={old[k].colspan}, '
                        f'а потомки покрывают только {covered}.')

                k += 1
                continue

            # Проверка на перерез
            if table_data[i][j].colspan > old[k].colspan:
                # Сначала пробуем прочитать строку как перерез. Если по типам
                # данных она перерезом не является, проверяем другой случай:
                # несколько родительских ячеек под одним потомком -- так
                # многоуровневый боковик возвращается на один уровень
                try:
                    _check_if_cross_section(table_data[i])
                except DataTypeError:
                    # Объединение допускаем только в боковике: это первая ячейка
                    # строки, покрывающая крайние слева родительские ячейки
                    # и при этом не всю строку целиком -- строка во всю ширину
                    # это перерез, а не боковик
                    merged = 0
                    if k == 0 and j == 0:
                        merged = _count_merged_parents(old, k, table_data[i][j].colspan)
                        if merged >= len(old):
                            merged = 0
                    if not merged:
                        raise

                    child = table_data[i][j]
                    _check_data_type_compatibility(old[k], child)
                    child.classCell = CellType.ClassCell.CELL_DATA
                    new.append(child)
                    j += 1
                    k += merged
                    continue
                # if not is_cross:
                #     raise LayoutError(
                #         f'Несоответствие colspan в строке {i}: '
                #         f'родительская ячейка "{old[k].content}" имеет colspan={old[k].colspan}, '
                #         f'а дочерняя "{table_data[i][j].content}" имеет colspan={table_data[i][j].colspan}. '
                #         f'Строка не соответствует структуре переза.')

                # Проверяем, что перед перерезом были данные (CELL_DATA)
                has_data_before = any(cell.classCell == CellType.ClassCell.CELL_DATA
                                      for row in table_data[start:i]
                                      for cell in row)

                if not has_data_before:
                    raise LayoutError(
                        f'Перед перерезом в строке {i} должны быть ячейки с данными (CELL_DATA)')

                # Проверяем, что перерез на всю ширину таблицы
                total_colspan = sum(cell.colspan for cell in table_data[i])
                expected_width = sum(cell.colspan for cell in table_data[start])

                if total_colspan != expected_width:
                    raise LayoutError(
                        f'Перерез в строке {i} должен быть на всю ширину таблицы. '
                        f'Ожидается {expected_width}, получено {total_colspan}')

                # Помечаем все ячейки переза как CELL_RESULT
                for cell in table_data[i]:
                    cell.classCell = CellType.ClassCell.CELL_RESULT

                # Восстанавливаем rowspan для old (так как мы его уменьшили в начале цикла)
                for cell in old:
                    cell.rowspan = 1

                # old остается без изменений - следующая строка будет проверяться
                # относительно строки перед перерезом (как будто переза не было)
                new = []
                k = 0
                # if j == len(table_data):
                #     return table
                break  # Выходим из while, переходим к следующей строке

            # Проверяем согласованность типов данных
            _check_data_type_compatibility(old[k], table_data[i][j])

            # Помечаем как данные
            table_data[i][j].classCell = CellType.ClassCell.CELL_DATA
            if table_data[i][j].detailType != CellType.DetailedDataType.NO_DATA:
                new.append(table_data[i][j])
            else:
                old[k].rowspan += 1
                new.append(old[k])
            j += 1
            k += 1

        # Если был перерез, old не меняем, просто продолжаем
        if new == [] and k < len(old):
            continue

        # Проверяем, что обработали все ячейки корректно
        if j != len(table_data[i]):
            raise LayoutError(
                f'Лишние ячейки в строке {i}: обработано {j}, всего {len(table_data[i])}')

        if k != len(old):
            raise LayoutError(
                f'Не все родительские ячейки обработаны в строке {i}')

        # Переносим обработанные ячейки в "старые"
        old = [cell for cell in new]

    # Проверяем, что нет "висящих" ячеек с rowspan > 1
    for cell in old:
        if cell.rowspan != 1:
            raise LayoutError(
                f'Ячейка "{cell.content}" имеет rowspan={cell.rowspan}, '
                f'но таблица закончилась (выходит за пределы по вертикали)')

    return table

def get_genuine(table: Table) -> Table:
    """
    • Если таблица валидна – возвращает сам объект Table в нужной ориентации
      (top — без изменений, left — transpose)
    """
    pair = (len(table.table), len(table.table[0]))
    if (pair in {(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}) or (len(table.table) == 1) or (all(len(table.table[i]) == 1 for i in range(len(table.table)))):
        raise LayoutError(f"Таблица слишком малого размера {len(table.table)} на {len(table.table[0])}")
    if (len(table.table) == 2) and (len(table.table[0]) + len(table.table[1]) == 3):
        raise LayoutError(f"Таблица слишком малого размера {len(table.table)} на {len(table.table[0])}")
    # 1) top ───────────────────────────────────────────────────────────────
    try:
        table_ = table.copy
        vertical_check(table_)
        return table_
    except (TitleTypeError, DataTypeError, LayoutError) as first_err:
        saved_err = first_err  # запоминаем, понадобится если всё рухнет
        pass
    # 2) left ──────────────────────────────────────────────────────────────
    try:
        table_ = table.copy
        table_.transpose
        vertical_check(table_)
        return table_           # заголовок слева
    except (TitleTypeError, DataTypeError, LayoutError) :
        pass
    raise saved_err

def is_genuine(table: Table) -> bool:
        """
        Проверяет, является ли таблица подлинной (валидной в любом направлении)

        Returns:
            True, если таблица валидна хотя бы в одном направлении
        """
        try:
            get_genuine(table)
            return True
        except (TitleTypeError, DataTypeError, LayoutError):
            return False


# Пример использования:
if __name__ == "__main__":
    from bs4 import BeautifulSoup

    html = """
    <table border="1" style="border-collapse: collapse; width: 100%;">
  <thead>
    <tr>
      <th rowspan="2">Год</th>
      <th colspan="3">Среднемесячные показатели</th>
    </tr>
    <tr>
      <th><a></a>Разность, см</th>
      <th>Абсолютные отметки, м</th>
      <th>Месяц</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="2">2001</td>
      <td rowspan="2">86</td>
      <td>max 456.92</td>
      <td>сентябрь 2001</td>
    </tr>
    <tr>
      <td>min 456.05</td>
      <td>апрель 2001</td>
    </tr>
    <tr>
      <td rowspan="2">2002</td>
      <td rowspan="2">64</td>
      <td>max 456.73</td>
      <td>август 2002</td>
    </tr>
    <tr>
      <td>min 456.09</td>
      <td>май 2002</td>
    </tr>
    <tr>
      <td rowspan="2">2003</td>
      <td rowspan="2">65</td>
      <td>max 456.69</td>
      <td>октябрь 2003</td>
    </tr>
    <tr>
      <td>min 456.04</td>
      <td>май 2003</td>
    </tr>
    <tr>
      <td rowspan="2">2004</td>
      <td rowspan="2">78</td>
      <td>max 456.90</td>
      <td>октябрь 2004</td>
    </tr>
    <tr>
      <td>min 456.12</td>
      <td>апрель 2004</td>
    </tr>
  </tbody>
</table>
    """

    soup = BeautifulSoup(html, 'html.parser')
    table_tag = soup.find('table')

    # Создаем объект Table
    table = Table(table_tag)

    try:
        good_table = get_genuine(table)
    except (TitleTypeError, DataTypeError, LayoutError) as err:
        print(f"⚠️  Таблица некорректна: {err}")

    # Проверяем валидность
    is_valid = is_genuine(table)
    print(f"Таблица валидна: {is_valid}")