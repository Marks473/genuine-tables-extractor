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


class test_fangraphs(unittest.TestCase):
    """Таблицы FanGraphs: меню, сетки ссылок и блоки-анонсы -- вёрстка, остальное -- данные"""
    @classmethod
    def setUpClass(cls):
        html_path = "table_for_test.html"
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
        cls.tables = soup.find_all("table", recursive=True)
        cls.verifier = MLVerification()

    def _assert_verdict(self, indexes, expected):
        for index in indexes:
            with self.subTest(table=index):
                table = Table(self.tables[index]).copy
                verdict = self.verifier.predict(table)
                self.assertEqual(verdict, expected,
                                 f'Таблица с индексом {index}: ожидалось "{expected}", '
                                 f'конвейер вернул "{verdict}"')

    def test_28_menu_frames(self):
        """Обёртки меню сайта, в которые вложены таблицы"""
        self._assert_verdict([27, 30], 'no genuine')

    def test_38_link_grids(self):
        """Меню и сетки ссылок на команды"""
        self._assert_verdict(range(37, 43), 'no genuine')

    def test_29_games(self):
        """Списки матчей в меню сайта"""
        self._assert_verdict([28, 29], 'no genuine')

    def test_32_standings(self):
        """Турнирные таблицы дивизионов без шапки"""
        self._assert_verdict(range(31, 37), 'genuine')

    def test_44_war_rating(self):
        """Рейтинги WAR на главной: блоки-анонсы полного рейтинга"""
        self._assert_verdict(range(43, 47), 'no genuine')

    def test_48_key_value(self):
        """Карточки «ключ -- значение»: итоги карьеры и данные драфта"""
        self._assert_verdict([47, 48], 'genuine')

    def test_50_injury_report(self):
        """Отчёт о травмах, по таблице на команду"""
        self._assert_verdict(range(49, 79), 'genuine')


if __name__ == '__main__':
    unittest.main(verbosity=2)
