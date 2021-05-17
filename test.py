import unittest
from .utils import merge_dicts, set_value_for_key, _lowercase_for_dict_keys
from .rough_config_parser import RoughConfigParser


class TestParser(unittest.TestCase):
    def setUp(self):
        pass

    def test_save_and_load(self):
        """ Сохраняем и читаем настройки, применяя шифрование отдельных полей """
        a0 = {
            'db_con': {
                'USER_fio': 'a0',
                'USER_PASS': 'a0',
                'hoSt': 'a0',
                'PORT': 0,
                'NAME_DB': 'a0'
            },
            'PATH': {
                'PATH_TO_COMMENT_FOR_SURVEY': '//SAMBA/share/OBRABOTKA/LungScreen/appData/config/lung_labeling/'
            },
            "print": {
                "test": {
                    "test": 1
                }
            },
            "pass": "qwerty12345"
        }
        cfg = RoughConfigParser(init_data=(a0,), hide_fields=["pass"])
        cfg.write_config_file('new.yml')
        cfg.read_config_file('new.yml')
        self.assertEqual(_lowercase_for_dict_keys(a0), cfg.as_dict())


class TestUtils(unittest.TestCase):
    a = {}
    a0 = {
        'db_con': {
            'USER_fio': 'a0',
            'USER_PASS': 'a0',
            'hoSt': 'a0',
            'PORT': 0,
            'NAME_DB': 'a0'
        },
        'PATH': {
            'PATH_TO_COMMENT_FOR_SURVEY': '//SAMBA/share/OBRABOTKA/LungScreen/appData/config/lung_labeling/'
        }
    }
    a1 = {
        'DB_CON': {
            'USER_NAME': 'a1',
            'USER_PASS': 'a1',
            'HOST': 'a1',
            'PORT': 3306,
            'NAME_DB': 'screening'
        },
        'path': {
            'PATH_TO_COMMENT_FOR_SURVEY': 'Что это ?/'
        }
    }
    a2 = {
        'db_con': {
            'user_name': 'a2',
            'user_pass': 'a2',
            'host': 'a2',
            'port1': 5555,
            'name_db': 'a2'
        },
        'path': {
            'path_to_comment_for_survey': '//config/lung_labeling/'
        }
    }

    def setUp(self):
        pass

    def test_merge_dicts(self):
        result = {
            'db_con': {
                'host': ['a2', 'a1', 'a0'],
                'name_db': ['a2', 'screening', 'a0'],
                'port': [3306, 0],
                'port1': 5555,
                'user_name': ['a2', 'a1'],
                'user_pass': ['a2', 'a1', 'a0'],
                'user_fio': 'a0'
            },
            'path': {
                'path_to_comment_for_survey': ['//config/lung_labeling/',
                                               'Что это ?/',
                                               '//SAMBA/share/OBRABOTKA/LungScreen/appData/config/lung_labeling/']
            }
        }
        self.assertEqual(result, merge_dicts((self.a2, self.a1, self.a0, self.a), only_new_value=False))

    def test_merge_dicts_only_new_value(self):
        result = {
            'db_con': {
                'host': 'a0',
                'name_db': 'a0',
                'port': 0,
                'port1': 5555,
                'user_name': 'a1',
                'user_pass': 'a0',
                'user_fio': 'a0'
            },
            'path': {
                'path_to_comment_for_survey': '//SAMBA/share/OBRABOTKA/LungScreen/appData/config/lung_labeling/'
            }
        }
        self.assertEqual(result, merge_dicts((self.a2, self.a1, self.a0, self.a), only_new_value=True))

    def test_merge_empty_dicts(self):
        result = {}
        self.assertEqual(result, merge_dicts(({}, {}, {}, {})))

    def test_set_value_for_key(self):
        """
        Пытаемся заменить значение для всех ключей.
        При иерархической структуре, при встречающихся ключах будут заменены все значения
        """
        in_dict = {
            "new_key": {
                "new_k1": 5,
                "new_b": {
                    "new_k": 5
                },
                "new_с": {
                    "new_k": 5
                },
                "new_k": 5
            }
        }
        out_dict = {
            "new_key": {
                "new_k1": 5,
                "new_b": {
                    "new_k": 1
                },
                "new_с": {
                    "new_k": 1
                },
                "new_k": 1
            }
        }
        self.assertEqual((out_dict, True), set_value_for_key(in_dict, "new_k", 1))

    def test_set_value_for_key_only_first(self):
        """ Пытаемся заменить значение только для первого встретившегося ключа """
        in_dict = {
            "new_key": {
                "new_k1": 5,
                "new_b": {
                    "new_k": 5
                },
                "new_с": {
                    "new_k": 5
                },
                "new_k": 5
            }
        }
        out_dict = {
            "new_key": {
                "new_k1": 5,
                "new_b": {
                    "new_k": 5
                },
                "new_с": {
                    "new_k": 5
                },
                "new_k": 1
            }
        }
        self.assertEqual((out_dict, True), set_value_for_key(in_dict, "new_k", 1, only_first=True))

    def test_set_value_for_key_not_found(self):
        """ Пытаемся заменить значение для ключа, отсутствующего в словаре """
        res = []
        in_dict = {
            "new_key": {
                "new_k1": 5,
                "new_b": {
                    "new_k": 5
                },
                "new_с": {
                    "new_k": 5
                },
                "new_k": 5
            }
        }
        out_dict = in_dict
        res.append((out_dict, False) == set_value_for_key(in_dict, "new_key_no", 1, only_first=True))
        res.append((out_dict, False) == set_value_for_key(in_dict, "new_key_no", 1))
        self.assertEqual([True, True], res)


if __name__ == "__main__":
    unittest.main()
