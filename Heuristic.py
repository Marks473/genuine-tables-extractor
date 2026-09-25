"""
Эвристический разбор структуры HTML-таблицы.

Проверка строится на одном свойстве таблицы данных: её строки образуют
правильное разбиение. Каждая следующая строка либо повторяет разбиение
предыдущей, либо дробит её ячейки, но никогда не пересекает их границы.

Разбор ведёт :func:`vertical_check`, последовательно вызывая три стадии:
:func:`get_head` находит границу блока заголовков, :func:`get_data` проверяет
область данных, :func:`get_sidebar` -- боковик. Каждая опирается на разметку,
проставленную предыдущей.

Точка входа для внешнего кода -- :func:`get_genuine` и :func:`is_genuine`.
"""

import CellType
from CellType import DataType
from Table import Table

from heuristic_errors import TitleTypeError, DataTypeError, LayoutError
from heuristic_rules import (
    check_data_type_compatibility,
    check_cross_section,
    count_merged_parents,
    is_section_divider,
)

ClassCell = CellType.ClassCell
DetailedDataType = CellType.DetailedDataType

# Типы, допустимые в самой верхней строке заголовков
FIRST_TITLE_TYPES = {DataType.STRING, DataType.NO_DATA, DataType.LINK}

# Типы, допустимые в заголовках и боковиках ниже первой строки
HEADER_TYPES = {DataType.GENUINE, DataType.STRING, DataType.LINK}

# Классы, проставленные предыдущими стадиями: разбор боковика их пропускает
PRECLASSIFIED = {ClassCell.CELL_TITLE, ClassCell.CELL_RESULT}

# Классы, которые разбор боковика не перезаписывает
KEEP_CLASS = {ClassCell.CELL_DATA, ClassCell.CELL_TITLE, ClassCell.CELL_RESULT}


def _require_type(cell, allowed: set, role: str) -> None:
    """
    Проверяет, что тип данных ячейки допустим для её роли.

    Args:
        cell: проверяемая ячейка
        allowed: множество допустимых типов данных
        role: название роли в сообщении об ошибке, например "заголовок"

    Raises:
        TitleTypeError: тип ячейки не входит в допустимые
    """
    if cell.type not in allowed:
        raise TitleTypeError(
            f'Ячейка-{role}: "{cell.content}" имеет неправильный тип {cell.type}')


def _open_block(row: list, allowed: set, role_class, role: str, skip: set) -> list:
    """
    Размечает верхнюю строку блока и возвращает её ячейки как родительские.

    Args:
        row: первая строка блока
        allowed: допустимые типы данных
        role_class: класс, который присваивается ячейкам
        role: название роли в сообщениях об ошибках
        skip: классы ячеек, которые в блок не входят

    Returns:
        Список размеченных ячеек

    Raises:
        TitleTypeError: в строке встретился недопустимый тип данных
    """
    parents = []
    for cell in row:
        if cell.classCell in skip:
            continue
        _require_type(cell, allowed, role)
        cell.classCell = role_class
        parents.append(cell)

    return parents


def _next_child(row: list, position: int, skip: set) -> int:
    """Возвращает позицию следующей ячейки строки, пропуская уже размеченные."""
    while position < len(row) and row[position].classCell in skip:
        position += 1

    return position


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


def _mark_block(rows: list, allowed: set, role_class, role: str, skip: set,
                close, strict: bool, dead_end: str, split_data: bool = False) -> None:
    """
    Общий обход блока заголовков или боковика.

    Заголовки сверху и боковик слева проверяются одним правилом: каждая
    следующая строка блока должна точно разбивать ячейки предыдущей. Боковик
    разбирается на транспонированной таблице и потому обходится тем же кодом;
    различаются только роль ячеек и способ завершения блока.

    Ячейки предыдущего уровня выступают родителями, ячейки текущей строки --
    потомками. Потомки набираются, пока их суммарная ширина не совпадёт
    с шириной родителя. Единственный потомок у единственного родителя в начале
    строки означает, что блок кончился и началась область данных.

    Args:
        rows: строки таблицы, для боковика -- транспонированной
        allowed: допустимые типы данных в верхней строке блока
        role_class: класс, который присваивается ячейкам блока
        role: название роли в сообщениях об ошибках
        skip: классы ячеек, которые обход пропускает
        close: функция разметки первой строки данных
        strict: требовать, чтобы строка целиком покрывала родителей
        dead_end: сообщение, если строка данных так и не нашлась
        split_data: допускать, что в первой строке данных одни родители
            дробятся на несколько ячеек, а другие продолжаются одной. Так
            устроен боковик, за которым идёт столбец данных с объединениями:
            номер типа спряжения "1" делится на окончания "-ать", "-ять",
            "-еть", а номер "3" продолжается одним окончанием "-нуть".
            Действует только для одноуровневого блока, см. :func:`_close_sidebar`

    Raises:
        TitleTypeError: в блоке встретился недопустимый тип данных
        LayoutError: нарушена структура либо блок "зубчатый"
    """
    if len(rows) < 2:
        raise LayoutError(f"Таблица должна иметь минимум 2 строки ({role} + данные)")

    parents = _open_block(rows[0], allowed, role_class, role, skip)

    if not parents:
        raise LayoutError(
            f"В первой строке нет ячеек роли <<{role}>>: "
            f"все они размечены предыдущей стадией")

    for index in range(1, len(rows)):
        row = rows[index]

        # Разделитель секции подписывает идущую ниже группу строк данных
        # и не задаёт структуру столбцов, поэтому в сопоставлении
        # с родительскими ячейками не участвует и рядов родителей не расходует
        if is_section_divider(row, parents):
            row[0].classCell = ClassCell.CELL_TITLE
            continue

        for parent in parents:
            parent.rowspan -= 1

        marked = []       # ячейки блока в этой строке: родители для следующей
        child_index = 0   # позиция в текущей строке
        parent_index = 0  # позиция в списке родителей
        covered = 0       # ширина, уже покрытая потомками текущего родителя
        consumed = []     # потомки этой строки, уже отнесённые к блоку

        while parent_index < len(parents):
            child_index = _next_child(row, child_index, skip)
            parent = parents[parent_index]

            # Родитель растянут на эту строку, потомков для него здесь нет
            if parent.rowspan > 0:
                marked.append(parent)
                parent_index += 1
                continue

            if child_index >= len(row):
                raise LayoutError(
                    f'Недостаточно ячеек в строке {index}: '
                    f'ожидалось покрытие ячейки "{parent.content}"')

            child = row[child_index]
            width = covered + child.colspan

            if width > parent.colspan:
                raise LayoutError(
                    f'Ячейка "{child.content}" (colspan={child.colspan}) выходит за границы '
                    f'родительской ячейки "{parent.content}" (colspan={parent.colspan})')

            # Ширина сошлась, и потомок был первым и единственным:
            # блок кончился, эта строка -- первая строка данных
            if width == parent.colspan and covered == 0:
                if consumed and not (split_data and index == 1):
                    raise LayoutError(
                        f'Блок роли <<{role}>> зубчатый: ячейка данных '
                        f'"{child.content}" находится правее ячейки блока')

                # Блок кончился уровнем выше: ячейки, дробившие родителей
                # в этой строке, -- тоже данные, а не продолжение блока
                for cell in consumed:
                    cell.classCell = ClassCell.CELL_DATA

                close(row, index, parents, parent_index, child_index)
                return

            _require_type(child, HEADER_TYPES, role)
            child.classCell = role_class
            marked.append(child)
            consumed.append(child)
            child_index += 1

            # Родитель покрыт целиком -- переходим к следующему
            if width == parent.colspan:
                covered = 0
                parent_index += 1
            else:
                covered = width

        if strict and (child_index != len(row) or parent_index != len(parents)):
            raise LayoutError(
                f'Несоответствие структуры в строке {index}: обработано {child_index} '
                f'из {len(row)} ячеек, {parent_index} из {len(parents)} родителей')

        parents = marked

    raise LayoutError(dead_end)


def get_head(table: Table) -> Table:
    """
    Размечает блок заголовков и находит первую строку данных.

    Заголовки не должны быть "зубчатыми", то есть обязаны заканчиваться
    на одной линии. Ячейки блока получают класс ``CELL_TITLE``, ячейки
    первой строки данных -- ``CELL_DATA``.

    Args:
        table: таблица, размечается на месте

    Returns:
        Ту же таблицу с размеченными заголовками

    Raises:
        TitleTypeError: заголовок содержит недопустимый тип данных
        LayoutError: нарушена структура либо заголовки "зубчатые"
    """
    _mark_block(table.table, FIRST_TITLE_TYPES, ClassCell.CELL_TITLE, "заголовок",
                skip=set(), close=_close_head, strict=True,
                dead_end="В таблице нет ячеек данных - только заголовки")

    return table


def _close_head(row: list, index: int, parents: list,
                parent_index: int, child_index: int) -> None:
    """
    Размечает первую строку данных, завершая разбор заголовков.

    Первая ячейка строки уже опознана как данные вызывающим кодом. Здесь
    проверяется, что и остальные ячейки строки соответствуют родителям:
    ни один заголовок не растянут на эту строку, а ширины совпадают.

    Args:
        row: первая строка данных
        index: номер строки, нужен для сообщений об ошибках
        parents: ячейки последнего уровня заголовков
        parent_index: позиция родителя, с которого продолжается проверка
        child_index: позиция ячейки данных, которая уже опознана

    Raises:
        LayoutError: заголовки "зубчатые" либо строка не покрывает родителей
    """
    row[child_index].classCell = ClassCell.CELL_DATA
    child_index += 1
    parent_index += 1

    while parent_index < len(parents):
        parent = parents[parent_index]

        if parent.rowspan > 0:
            raise LayoutError(
                f'Заголовки "зубчатые": ячейка-заголовок "{parent.content}" '
                f'выступает за строку {index} (rowspan={parent.rowspan})')

        if child_index >= len(row):
            raise LayoutError(
                f'Недостаточно ячеек данных в строке {index}: '
                f'ожидалось покрытие ячейки "{parent.content}"')

        child = row[child_index]
        if child.colspan != parent.colspan:
            raise LayoutError(
                f'Заголовки "зубчатые": ячейка данных "{child.content}" '
                f'(colspan={child.colspan}) не соответствует '
                f'заголовку "{parent.content}" (colspan={parent.colspan})')

        child.classCell = ClassCell.CELL_DATA
        parent_index += 1
        child_index += 1

    if child_index != len(row) or parent_index != len(parents):
        raise LayoutError(
            f'Несоответствие структуры в строке {index}: '
            f'обработано {child_index} из {len(row)} ячеек')


def get_sidebar(table: Table) -> Table:
    """
    Размечает боковик -- заголовки строк.

    Работает на транспонированной таблице: боковик при повороте становится
    заголовком, и к нему применяется тот же разбор, что и к заголовкам.
    Ячейки боковика получают класс ``CELL_SIDEBAR``, первый столбец данных --
    ``CELL_DATA``. Ячейки, размеченные предыдущими стадиями, пропускаются.

    Args:
        table: таблица, размечается на месте

    Returns:
        Ту же таблицу в исходной ориентации с размеченным боковиком

    Raises:
        TitleTypeError: боковик содержит недопустимый тип данных
        LayoutError: нарушена структура либо боковики "зубчатые"
    """
    table.reset_span()
    table.transpose

    _mark_block(table.table, HEADER_TYPES, ClassCell.CELL_SIDEBAR, "боковик",
                skip=PRECLASSIFIED, close=_close_sidebar, strict=False,
                dead_end="В таблице нет ячеек данных - только боковики",
                split_data=True)

    table.reset_span()
    table.transpose

    return table


def _close_sidebar(row: list, index: int, parents: list,
                   parent_index: int, child_index: int) -> None:
    """
    Размечает первый столбец данных, завершая разбор боковика.

    В отличие от :func:`_close_head`, уже размеченные классы не перезаписываются,
    а родитель с ``rowspan == 1`` пропускается: боковик мог закончиться раньше
    остальных столбцов.

    Если боковик одноуровневый, родитель может покрываться несколькими
    ячейками данных общей ширины: такой боковик группирует строки, и группы
    разной высоты для него обычны. В многоуровневом боковике нижний уровень
    для того и нужен, чтобы дробить строки, поэтому он обязан соответствовать
    строкам данных один к одному.

    Args:
        row: первый столбец данных, в транспонированном виде -- строка
        index: номер строки для сообщений об ошибках
        parents: ячейки последнего уровня боковика
        parent_index: позиция родителя, с которого продолжается проверка
        child_index: позиция ячейки данных, которая уже опознана

    Raises:
        LayoutError: боковики "зубчатые" либо ширины не совпадают
    """
    if row[child_index].classCell not in KEEP_CLASS:
        row[child_index].classCell = ClassCell.CELL_DATA
    child_index += 1
    parent_index += 1

    while parent_index < len(parents):
        child_index = _next_child(row, child_index, PRECLASSIFIED)
        parent = parents[parent_index]

        if parent.rowspan > 1:
            raise LayoutError(
                f'Боковики "зубчатые": ячейка-боковик "{parent.content}" '
                f'выступает за строку {index} (rowspan={parent.rowspan})')

        # Боковик закончился на предыдущей строке, потомка для него здесь нет
        if parent.rowspan == 1:
            parent_index += 1
            continue

        # Одноуровневый боковик данные могут дробить, как в get_data,
        # но не выходить за его границы
        covered = 0
        while covered < parent.colspan:
            child_index = _next_child(row, child_index, PRECLASSIFIED)
            if child_index >= len(row):
                raise LayoutError(
                    f'Недостаточно ячеек данных в строке {index}: '
                    f'ожидалось покрытие ячейки "{parent.content}"')

            child = row[child_index]
            covered += child.colspan
            if covered > parent.colspan or (covered < parent.colspan and index > 1):
                raise LayoutError(
                    f'Боковики "зубчатые": ячейка данных "{child.content}" '
                    f'(colspan={child.colspan}) не соответствует '
                    f'боковику "{parent.content}" (colspan={parent.colspan})')

            if child.classCell not in KEEP_CLASS:
                child.classCell = ClassCell.CELL_DATA
            child_index += 1

        parent_index += 1



def get_data(table: Table) -> Table:
    """
    Проверяет область данных после разметки заголовков.

    Требование строже, чем к заголовкам: у родительской ячейки должен быть
    ровно один потомок той же ширины. Из этого правила есть два исключения --
    перерез (итоговая строка во всю ширину) и объединение ячеек боковика.

    Args:
        table: таблица, размечается на месте

    Returns:
        Ту же таблицу с размеченными данными (``CELL_DATA``)
        и итоговыми строками (``CELL_RESULT``)

    Raises:
        LayoutError: нарушена структура области данных
        DataTypeError: типы данных в столбце несовместимы
    """
    rows = table.table

    if len(rows) < 2:
        raise LayoutError("Таблица должна иметь минимум 2 строки (заголовок + данные)")

    # Первую строку данных уже нашла стадия разбора заголовков
    start = 0
    while start < len(rows) and rows[start][0].classCell == ClassCell.CELL_TITLE:
        start += 1

    if start >= len(rows):
        raise LayoutError("В таблице нет строк с данными")

    width = sum(cell.colspan for cell in rows[start])
    parents = list(rows[start])

    for index in range(start + 1, len(rows)):
        row = rows[index]

        for parent in parents:
            parent.rowspan -= 1

        marked = []
        child_index = 0
        parent_index = 0

        while parent_index < len(parents):
            parent = parents[parent_index]

            # Родитель растянут на эту строку, потомка для него здесь нет
            if parent.rowspan > 0:
                marked.append(parent)
                parent_index += 1
                continue

            if child_index >= len(row):
                raise LayoutError(
                    f'Недостаточно ячеек в строке {index}: '
                    f'ожидалась дочерняя ячейка для "{parent.content}"')

            child = row[child_index]

            if child.colspan < parent.colspan:
                child_index = _split_parent(row, index, parent, child_index, marked)
                parent_index += 1
                continue

            if child.colspan > parent.colspan:
                merged = _merge_parents(row, parents, parent_index, child_index, marked)
                if merged:
                    child_index += 1
                    parent_index += merged
                    continue

                _mark_cross_section(rows, row, index, start, parents, width)
                marked = []
                break

            check_data_type_compatibility(parent, child)
            child.classCell = ClassCell.CELL_DATA

            # Пустая ячейка не заменяет родителя: столбец продолжает
            # сверяться с последним содержательным значением. Родитель
            # перенимает высоту пустой ячейки, иначе её rowspan теряется
            if child.detailType != DetailedDataType.NO_DATA:
                marked.append(child)
            else:
                parent.rowspan += child.rowspan
                marked.append(parent)

            child_index += 1
            parent_index += 1

        # После переза структура столбцов не меняется
        if not marked and parent_index < len(parents):
            continue

        if child_index != len(row):
            raise LayoutError(
                f'Лишние ячейки в строке {index}: обработано {child_index}, всего {len(row)}')

        if parent_index != len(parents):
            raise LayoutError(f'Не все родительские ячейки обработаны в строке {index}')

        parents = marked

    for cell in parents:
        if cell.rowspan != 1:
            raise LayoutError(
                f'Ячейка "{cell.content}" имеет rowspan={cell.rowspan}, '
                f'но таблица закончилась (выходит за пределы по вертикали)')

    return table


def _split_parent(row: list, index: int, parent, child_index: int, marked: list) -> int:
    """
    Разбирает случай, когда родительская ячейка делится на нескольких потомков.

    Так устроен многоуровневый боковик: падеж "В." разбивается на "одуш."
    и "неодуш.". Потомки набираются, пока их суммарная ширина не покроет
    родителя.

    Args:
        row: текущая строка
        index: номер строки для сообщений об ошибках
        parent: родительская ячейка
        child_index: позиция первого потомка
        marked: список, куда складываются размеченные ячейки

    Returns:
        Позицию в строке после последнего потомка

    Raises:
        LayoutError: потомки шире родителя либо не покрывают его целиком
        DataTypeError: тип данных потомка несовместим с родителем
    """
    covered = 0
    while child_index < len(row) and covered < parent.colspan:
        child = row[child_index]

        if covered + child.colspan > parent.colspan:
            raise LayoutError(
                f'Несоответствие colspan в строке {index}: потомки ячейки '
                f'"{parent.content}" (colspan={parent.colspan}) в сумме шире родителя')

        check_data_type_compatibility(parent, child)
        child.classCell = ClassCell.CELL_DATA
        marked.append(child)
        covered += child.colspan
        child_index += 1

    if covered != parent.colspan:
        raise LayoutError(
            f'Несоответствие colspan в строке {index}: родительская ячейка '
            f'"{parent.content}" имеет colspan={parent.colspan}, '
            f'а потомки покрывают только {covered}.')

    return child_index


def _merge_parents(row: list, parents: list, parent_index: int,
                   child_index: int, marked: list) -> int:
    """
    Разбирает случай, когда один потомок покрывает нескольких родителей.

    Так многоуровневый боковик возвращается на один уровень: строки "В."
    и "неодуш." вместе занимают ту же ширину, что одна ячейка "Тв." ниже.
    Сначала строка проверяется как перерез, и только если по типам данных
    перерезом она не является, рассматривается объединение.

    Объединение допускается лишь в боковике: это первая ячейка строки,
    покрывающая крайних слева родителей, но не всю строку целиком --
    строка во всю ширину является перерезом.

    Args:
        row: текущая строка
        parents: родительские ячейки
        parent_index: позиция текущего родителя
        child_index: позиция потомка
        marked: список, куда складываются размеченные ячейки

    Returns:
        Число покрытых родителей либо 0, если это не объединение

    Raises:
        DataTypeError: строка не является ни перерезом, ни объединением
    """
    try:
        check_cross_section(row)
    except DataTypeError:
        merged = 0
        if parent_index == 0 and child_index == 0:
            merged = count_merged_parents(parents, parent_index, row[child_index].colspan)
            if merged >= len(parents):
                merged = 0
        if not merged:
            raise

        child = row[child_index]
        check_data_type_compatibility(parents[parent_index], child)
        child.classCell = ClassCell.CELL_DATA
        marked.append(child)

        return merged

    return 0


def _mark_cross_section(rows: list, row: list, index: int, start: int,
                        parents: list, width: int) -> None:
    """
    Размечает перерез -- итоговую строку во всю ширину таблицы.

    Структура столбцов при этом не меняется: следующая строка сверяется
    с той, что была до переза, как будто переза не было.

    Args:
        rows: все строки таблицы
        row: строка переза
        index: номер строки
        start: номер первой строки данных
        parents: родительские ячейки, их rowspan восстанавливается
        width: ширина таблицы

    Raises:
        LayoutError: выше переза нет данных либо он не во всю ширину
    """
    has_data = any(cell.classCell == ClassCell.CELL_DATA
                   for earlier in rows[start:index]
                   for cell in earlier)
    if not has_data:
        raise LayoutError(
            f'Перед перерезом в строке {index} должны быть ячейки с данными (CELL_DATA)')

    total = sum(cell.colspan for cell in row)
    if total != width:
        raise LayoutError(
            f'Перерез в строке {index} должен быть на всю ширину таблицы. '
            f'Ожидается {width}, получено {total}')

    for cell in row:
        cell.classCell = ClassCell.CELL_RESULT

    # rowspan был уменьшен в начале строки, а перерез его не расходует
    for parent in parents:
        parent.rowspan = 1


def get_genuine(table: Table) -> Table:
    """
    Проверяет, является ли таблица подлинной, в обеих ориентациях.

    Сначала таблица разбирается как имеющая заголовок сверху. Если разбор
    не удался, она транспонируется и проверяется как имеющая заголовок слева.
    Возбуждается ошибка первой попытки: она обычно содержательнее.

    Args:
        table: проверяемая таблица

    Returns:
        Размеченную таблицу в той ориентации, в которой разбор удался

    Raises:
        TitleTypeError: в заголовке недопустимый тип данных
        DataTypeError: типы данных в столбце не согласуются
        LayoutError: нарушена геометрия таблицы
    """
    height = len(table.table)
    widths = [len(row) for row in table.table]

    too_small = (
        (height, widths[0]) in {(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}
        or height == 1
        or all(size == 1 for size in widths)
        or (height == 2 and widths[0] + widths[1] == 3)
    )
    if too_small:
        raise LayoutError(f"Таблица слишком малого размера {height} на {widths[0]}")

    # Заголовок сверху
    try:
        top = table.copy
        vertical_check(top)
        return top
    except (TitleTypeError, DataTypeError, LayoutError) as first_error:
        saved = first_error

    # Заголовок слева
    try:
        left = table.copy
        left.transpose
        vertical_check(left)
        return left
    except (TitleTypeError, DataTypeError, LayoutError):
        pass

    raise saved


def is_genuine(table: Table) -> bool:
    """
    Проверяет подлинность таблицы, не возбуждая исключений.

    Args:
        table: проверяемая таблица

    Returns:
        True, если таблица разобралась хотя бы в одной ориентации
    """
    try:
        get_genuine(table)
        return True
    except (TitleTypeError, DataTypeError, LayoutError):
        return False
