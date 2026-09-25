"""
Комплексные тесты всего конвейера: эвристика + модель.

В отличие от test_heuristic.py, здесь проверяется итоговый ответ
MLVerification.predict -- то, что получит внешний код, -- а не разметка
отдельных ячеек. Модель загружается из trained_model.pkl один раз на класс.
"""

import unittest

from bs4 import BeautifulSoup

from MLverification import MLVerification
from Table import Table


class test_wiktionary_main_page(unittest.TestCase):
    """Таблицы заглавной страницы Викисловаря: вёрстка, все неподлинные"""
    @classmethod
    def setUpClass(cls):
        html_path = "table_for_test.html"
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
        cls.tables = soup.find_all("table", recursive=True)
        cls.verifier = MLVerification()

    def _assert_not_genuine(self, index):
        table = Table(self.tables[index]).copy
        verdict = self.verifier.predict(table)
        self.assertEqual(verdict, 'no genuine',
                         f'Таблица с индексом {index} -- вёрстка, а конвейер вернул "{verdict}"')

    def test_21_layout_frame(self):
        """Таблица-каркас, в которую вложены все блоки страницы"""
        self._assert_not_genuine(20)

    def test_22_welcome(self):
        """Вложенный блок «Русский Викисловарь»"""
        self._assert_not_genuine(21)

    def test_23_about(self):
        """Вложенный блок «О Викисловаре»"""
        self._assert_not_genuine(22)

    def test_24_categories(self):
        """Вложенный блок «Категории»"""
        self._assert_not_genuine(23)

    def test_25_appendices(self):
        """Вложенный блок «Приложения»"""
        self._assert_not_genuine(24)

    def test_26_indexes(self):
        """Вложенный блок «Индексы»"""
        self._assert_not_genuine(25)

    def test_27_sister_projects(self):
        """Родственные проекты Викимедиа"""
        self._assert_not_genuine(26)


if __name__ == '__main__':
    unittest.main(verbosity=2)
