"""
Раскраска таблиц HTML-страницы так, как их видит программа.

Утилита для экспериментов: на вход -- страница, на выходе -- та же страница,
в которой подлинные таблицы обведены зелёной рамкой, а их ячейки окрашены
по классам: заголовок, боковик, данные, итог. Неподлинные таблицы обводятся
красным пунктиром, причина отказа видна во всплывающей подсказке таблицы.

Решение принимается так же, как во всём конвейере: сначала эвристика,
и если она таблицу пропустила, -- модель.

Запуск:
    python tools/highlight_tables.py page.html page_highlighted.html
"""

import argparse
import copy
import os
import sys
import warnings

# Модули программы лежат на уровень выше каталога tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from bs4 import BeautifulSoup

from config import MODEL_PATH
from CellType import ClassCell
from Heuristic import get_genuine, LayoutError, TitleTypeError, DataTypeError
from MLverification import MLVerification, get_parameters_from_table
from Table import Table

COLORS = {
    ClassCell.CELL_TITLE: 'background:#add8e6;color:#000',
    ClassCell.CELL_SIDEBAR: 'background:#90ee90;color:#000',
    ClassCell.CELL_DATA: 'background:#2b2b2b;color:#fff',
    ClassCell.CELL_RESULT: 'background:#ffef66;color:#000',
}
GENUINE_STYLE = 'outline:3px solid #2e7d32'
REJECTED_STYLE = 'outline:2px dashed #d32f2f'

# Временный атрибут: по нему размеченная копия ячейки находит исходный тег
MARK = 'data-cell-id'


def add_style(tag, style):
    """Дописывает стиль к уже имеющемуся атрибуту style тега."""
    tag['style'] = (tag.get('style', '') + ';' + style).strip(';')


def highlight(soup, model):
    """
    Размечает все таблицы документа на месте.

    Эвристика работает с копиями ячеек и может разобрать таблицу после
    поворота, поэтому исходные ячейки заранее нумеруются атрибутом MARK.
    Копии наследуют номер, и класс возвращается к исходной ячейке при любой
    ориентации разбора.

    Args:
        soup: разобранный документ
        model: загруженная модель MLVerification

    Returns:
        Пару (число таблиц, число подлинных)
    """
    cells = {}
    for number, tag in enumerate(soup.find_all(['td', 'th'])):
        tag[MARK] = str(number)
        cells[str(number)] = tag

    tables = soup.find_all('table')
    genuine = 0
    for table_tag in tables:
        # Разбирается копия: Table правит дерево, а страница должна остаться прежней
        table = Table(copy.copy(table_tag))
        try:
            marked = get_genuine(table)
        except (LayoutError, TitleTypeError, DataTypeError) as err:
            add_style(table_tag, REJECTED_STYLE)
            table_tag['title'] = f'неподлинная: {err}'
            continue

        features = pd.DataFrame([get_parameters_from_table(table)])
        if model.wrapper.predict(features)[0] != 'genuine':
            add_style(table_tag, REJECTED_STYLE)
            table_tag['title'] = 'неподлинная: эвристика пропустила, модель отклонила'
            continue

        genuine += 1
        add_style(table_tag, GENUINE_STYLE)
        table_tag['title'] = 'подлинная'
        for row in marked.table:
            for cell in row:
                original = cells.get(cell.data.get(MARK))
                if original is not None and cell.classCell in COLORS:
                    add_style(original, COLORS[cell.classCell])

    for tag in cells.values():
        del tag[MARK]

    return len(tables), genuine


def main():
    parser = argparse.ArgumentParser(
        description="Раскрашивает таблицы HTML-страницы по решению программы")
    parser.add_argument("source", help="исходная HTML-страница")
    parser.add_argument("target", help="куда сохранить раскрашенную страницу")
    args = parser.parse_args()

    with open(args.source, encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Модель сохранена под зафиксированные версии библиотек и при загрузке
    # предупреждает о них; на результат это не влияет
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        model = MLVerification(MODEL_PATH)
        total, genuine = highlight(soup, model)

    with open(args.target, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    print(f"Таблиц: {total}, подлинных: {genuine}. Результат: {args.target}")


if __name__ == '__main__':
    main()
