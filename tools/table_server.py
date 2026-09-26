"""
Локальный сервер для расширения браузера.

Браузер выполняет только JavaScript, а эвристика и модель написаны на Python.
Поэтому расширение не разбирает таблицы само, а отправляет их HTML этому
серверу и получает готовый ответ: какие таблицы подлинные, какая ячейка
к какой области относится и что показывать при наведении.

Сервер слушает только адрес 127.0.0.1 -- этот же компьютер -- и снаружи
недоступен. Модуль http.server из стандартной библиотеки для открытой сети
не предназначен, а здесь она и не нужна.

Два обращения, оба методом POST с телом в JSON:

* ``/analyze``     -- разобрать таблицы страницы, ответ в JSON;
* ``/export/xlsx`` -- собрать файл Excel из одной или нескольких таблиц,
  каждая на своём листе; ответ -- сам файл.

Запуск:
    python tools/table_server.py [--port 8765]
"""

import argparse
import json
import os
import sys
import warnings
from http.server import BaseHTTPRequestHandler, HTTPServer

# Модули программы лежат на уровень выше каталога tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup

from config import MODEL_PATH
from MLverification import MLVerification
from PageAnalyzer import HEURISTIC_ERRORS, PageAnalyzer
from Table import Table
from TableExporter import tables_to_xlsx
from TableStructure import StructureTable

HOST = '127.0.0.1'
DEFAULT_PORT = 8765
XLSX_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


class AnalysisHandler(BaseHTTPRequestHandler):
    """
    Обработчик одного запроса.

    Сервер создаёт объект этого класса на каждый запрос и вызывает метод по
    имени запроса: для POST -- :meth:`do_POST`. Анализатор с загруженной
    моделью общий для всех запросов и задаётся при запуске сервера.
    """

    analyzer: PageAnalyzer = None

    def do_POST(self):
        """Читает тело запроса и передаёт его обработчику по пути запроса."""
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length).decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            self._send_json(400, {'error': 'тело запроса должно быть в формате JSON'})
            return

        if self.path == '/analyze':
            self._analyze(body)
        elif self.path == '/export/xlsx':
            self._export_xlsx(body)
        else:
            self._send_json(404, {'error': f'неизвестный путь {self.path}'})

    def _analyze(self, body: dict):
        """
        Разбирает все таблицы страницы.

        Ошибка разбора одной таблицы не должна лишать страницу ответа по
        остальным, поэтому она записывается как причина отказа этой таблицы.
        """
        page = {'url': body.get('page_url', ''), 'title': body.get('page_title', '')}
        answers = []
        for table in body.get('tables', []):
            source = dict(page, index=table.get('id'))
            try:
                answer = self.analyzer.analyze(table.get('html', ''), source)
            except Exception as err:
                answer = {'genuine': False,
                          'reason': f'ошибка программы: {type(err).__name__}: {err}'}
            answers.append(dict(answer, id=table.get('id')))

        self._send_json(200, {'tables': answers})

    def _export_xlsx(self, body: dict):
        """
        Собирает файл Excel и отправляет его как есть.

        Каждая таблица попадает на свой лист, лист назван номером таблицы на
        странице, считая с единицы: "Таблица_6" -- шестая таблица страницы.
        """
        structures, names = [], []
        for table in body.get('tables', []):
            tag = BeautifulSoup(table.get('html', ''), 'html.parser').find('table')
            if tag is None:
                self._send_json(400, {'error': 'в переданном коде нет таблицы'})
                return
            try:
                structures.append(StructureTable.from_table(Table(tag)))
            except HEURISTIC_ERRORS as err:
                self._send_json(422, {'error': str(err)})
                return
            names.append(f"Таблица_{int(table.get('id', len(names))) + 1}")

        if not structures:
            self._send_json(400, {'error': 'не передано ни одной таблицы'})
            return

        content = tables_to_xlsx(structures, names, colored=bool(body.get('colored', True)))
        self.send_response(200)
        self.send_header('Content-Type', XLSX_TYPE)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, code: int, payload: dict):
        """Отправляет ответ в JSON с кодом состояния code."""
        content = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)


class LocalServer(HTTPServer):
    """
    HTTP-сервер, который не делит порт с другими процессами.

    HTTPServer разрешает повторное использование адреса. В Windows это
    значит, что второй экземпляр сервера займёт тот же порт без ошибки,
    а отвечать будет первый -- со старым кодом. Здесь повторный запуск
    завершается понятной ошибкой.
    """

    allow_reuse_address = False


def main():
    parser = argparse.ArgumentParser(
        description="Локальный сервер, который разбирает таблицы для расширения браузера")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"порт, по умолчанию {DEFAULT_PORT}")
    args = parser.parse_args()

    # Модель сохранена под зафиксированные версии библиотек и при загрузке
    # предупреждает о них; на результат это не влияет
    warnings.simplefilter('ignore')
    AnalysisHandler.analyzer = PageAnalyzer(MLVerification(MODEL_PATH))

    try:
        server = LocalServer((HOST, args.port), AnalysisHandler)
    except OSError:
        sys.exit(f"Порт {args.port} уже занят: сервер, вероятно, уже запущен. "
                 f"Остановите его или укажите другой порт через --port")
    print(f"Сервер запущен: http://{HOST}:{args.port}. Остановка -- Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
