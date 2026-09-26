# Выделение подлинных таблиц из HTML

Программа определяет, является ли HTML-таблица *подлинной*, то есть содержит ли
она структурированные данные, а не служит средством вёрстки страницы.

Решение принимается в два этапа:

1. **Эвристика** разбирает геометрию таблицы -- заголовки, боковик, область
   данных -- и отбраковывает всё, что не укладывается в структуру таблицы данных.
2. **Модель машинного обучения** классифицирует то, что эвристику прошло,
   опираясь на доли типов данных в ячейках.

Эвристика работает жёстким фильтром: таблица, не прошедшая проверку структуры,
сразу получает метку `no genuine`, и модель к ней не применяется.

## Установка

Версии библиотек зафиксированы: под ними обучена модель `trained_model.pkl`.
С более новыми `numpy` и `pandas` сохранённая модель не загружается.

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Быстрый старт

```python
from bs4 import BeautifulSoup

from Heuristic import get_genuine, LayoutError, TitleTypeError, DataTypeError
from Table import Table

html = "<table><tr><th>Товар</th><th>Цена</th></tr>" \
       "<tr><td>Яблоко</td><td>100</td></tr>" \
       "<tr><td>Молоко</td><td>80</td></tr></table>"

soup = BeautifulSoup(html, "html.parser")
table = Table(soup.find("table"))

try:
    get_genuine(table)
    print("таблица подлинная")
except (LayoutError, TitleTypeError, DataTypeError) as err:
    print("таблица отбракована:", err)
```

Классификация с участием модели:

```python
from MLverification import MLVerification

verifier = MLVerification()
print(verifier.predict(table))      # genuine или no genuine
```

## Состав

| Файл | Назначение |
| --- | --- |
| `Cell.py` | Обёртка над ячейкой `<td>` или `<th>`: объединения, содержимое, теги, тип |
| `CellType.py` | Определение типа данных ячейки по её содержимому и набору тегов |
| `Table.py` | Таблица как список строк: копирование, поворот, выгрузка в Excel |
| `Heuristic.py` | Стадии разбора структуры и общая проверка подлинности |
| `heuristic_rules.py` | Частные правила проверки, которыми пользуются стадии разбора |
| `heuristic_errors.py` | Исключения разбора: по типу ошибки видно, какая проверка не прошла |
| `comparisonML.py` | Извлечение признаков, обёртка модели, сравнение шести классификаторов |
| `MLverification.py` | Обучение и сохранение модели, классификация готовой моделью |
| `config.py` | Пути и общие настройки |
| `TableGrid.py` | Сетка покрытия: какая ячейка накрывает каждую клетку таблицы |
| `TableStructure.py` | Объектная модель подлинной таблицы: заголовки, атрибуты, данные, итоги и связи между ними |
| `TableExporter.py` | Выгрузка объектной модели в JSON и Excel |
| `PageAnalyzer.py` | Разбор одной таблицы страницы для расширения браузера |
| `tools/` | Снятие и сверка контрольных срезов, раскраска таблиц на странице, сервер для расширения браузера |

Данные:

| Файл | Содержимое |
| --- | --- |
| `verified_dataset.json` | 1000 таблиц с ручной разметкой: 46 подлинных, 954 неподлинных |
| `trained_model.pkl` | Обученный случайный лес вместе с кодировщиком меток |
| `table_for_test.html` | 79 таблиц, на которых работают тесты; состав и источники -- в [docs/dataset.md](docs/dataset.md) |

## Тесты

```
python -m pytest -q
```

Ожидается 209 пройденных тестов и 2 ожидаемых отказа (`xfailed`):
они описывают известные слабости эвристики, см. `test_heuristic.py`.

Файл `test_program.py` тестов не содержит: это интерактивный аудит набора данных, который открывает в браузере отчёт по
каждому расхождению между разметкой и решением эвристики. Запускается отдельно:

```
python test_program.py
```

## Как программа видит страницу

Чтобы посмотреть решение программы глазами, раскрасьте таблицы любой
сохранённой HTML-страницы:

```
python tools/highlight_tables.py page.html page_highlighted.html
```

Результат -- та же страница, в которой:

| Вид | Значение |
| --- | --- |
| Зелёная сплошная рамка | подлинная таблица |
| Красная пунктирная рамка | неподлинная; причина -- во всплывающей подсказке таблицы |
| Голубая ячейка | заголовок |
| Зелёная ячейка | боковик |
| Чёрная ячейка | данные |
| Жёлтая ячейка | итоговая строка (перерез) |

Ячейки окрашиваются только у подлинных таблиц. Если таблицы на сайте
достраиваются скриптами, на вход нужна страница, сохранённая из браузера
после загрузки, а не её исходный код.

То же самое прямо в браузере, без сохранения страницы, делает расширение
Chrome "Подлинные таблицы"
([genuine-tables-browser-extension](https://github.com/Marks473/genuine-tables-browser-extension)).
Ему нужен запущенный сервер программы:

```
python tools/table_server.py
```

Сервер слушает только адрес `http://127.0.0.1:8765` этого компьютера.

## Объектная модель таблицы

Размеченную эвристикой таблицу удобно исследовать как набор связанных
объектов: каждая ячейка знает свою роль, заголовки над собой, атрибуты
слева, а итог -- ячейки, которые он агрегирует.

```python
from bs4 import BeautifulSoup

from Table import Table
from TableStructure import StructureTable, ResultCell

soup = BeautifulSoup(open('table_for_test.html', encoding='utf-8'), 'html.parser')
structure = StructureTable.from_table(Table(soup.find_all('table')[5]))

cell = structure.cell_at(10, 4)          # "91" в строке "Итого по 2-ой бригаде"
print(isinstance(cell, ResultCell))      # True
print(cell.aggregated)                   # [DataCell('15', ...), DataCell('26', ...), DataCell('50', ...)]
print(cell.header_path)                  # [TitleCell('Отработано, ч', ...), TitleCell('Всего', ...)]
```

| Класс | Роль | Главные поля |
| --- | --- | --- |
| `TitleCell` | заголовок | `parent`, `children`, `data_cells`, `data_types` |
| `SidebarCell` | атрибут (боковик) | `parent`, `children`, `header_path`, `sidebar_path` |
| `DataCell` | данные | `header_path`, `sidebar_path`, `value` |
| `ResultCell` | итоговая строка | `is_label`, `aggregated`, `value` |

Координаты `row`, `col` и `cell_at` -- как таблица стоит на странице, даже
если эвристика разбирала её повёрнутой. Правила построения путей и
агрегации описаны в документации расширения,
[docs/architecture.md](https://github.com/Marks473/genuine-tables-browser-extension/blob/main/docs/architecture.md).

Выгрузка:

```python
from TableExporter import TableExporter

exporter = TableExporter(structure)
exporter.to_dict()                 # словарь для json.dump
exporter.to_xlsx(colored=False)    # байты файла .xlsx без заливки
```

## Проверка неизменности результатов

После любой правки кода результаты классификации нужно сверить с эталоном --
иначе незаметная регрессия в разборе таблицы меняет качество модели. Порядок
описан в [docs/regression.md](docs/regression.md).

## Документация

* [docs/algorithm.md](docs/algorithm.md) -- как устроена эвристика;
* [docs/dataset.md](docs/dataset.md) -- формат набора данных и признаки модели;
* [docs/regression.md](docs/regression.md) -- сверка результатов классификации.
