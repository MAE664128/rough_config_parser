# Код написан в образовательных целях и использования для личных нужд.

"""
Грубый набросок парсера конфигурационного файла
Служит для создания объектов, с доступом к атрибутам как по ключам, так и через точку.

Инициализация значение по умолчанию происходит путем:
    -   передачи их в конструктор в виде словаря (dict) или картежа (Tuple[dict,...]
        с последующим их объединением в один словарь
    -   передачи пути к yml файлу

Особенности:
    -   Объединение словарей
    -   Доступ к атрибутам как через ключ, так и через "точку"
    -   Добавление новых атрибутов
    -   Чтение и запись значений в yml файл
    -   Кодирование и декодирование значений при записи и чтении файла


Пример:
    rcp = RoughConfigParser(init_data={"key1": "val0", "deep_data": {"deep_key1": "val1", "deep_key2": "val2"}})
    rcp.deep_data.deep_key1
    >> val1
    rcp['deep_data']['deep_key1']
    >> val1
"""

import base64
from os.path import isfile as os_isfile
from typing import Tuple, Union, Callable, Optional, List

import yaml
from yaml.scanner import ScannerError

from .utils import merge_dicts, set_value_for_key

SECRET_KEY = "vNoVP7turjKWUtRWAjyFBXVU4AQY-7hlkagOQFixXEI="


def coder_string(native_string: str) -> str:
    """
    Шифрует строку.
    Цель сокрыть истинное значение строки при сохранении ее в файл.
    Требование к безопасности упущены.
    """
    global SECRET_KEY
    key = SECRET_KEY
    encoded_chars = []
    for i in range(len(native_string)):
        key_c = key[i % len(key)]
        encoded_c = chr(ord(native_string[i]) + ord(key_c) % 256)
        encoded_chars.append(encoded_c)
    encoded_string = "".join(encoded_chars)
    return base64.urlsafe_b64encode(encoded_string.encode()).decode("utf-8")


def decoder_string(coded_string: str) -> str:
    """
    Дешифрует строку.
    Цель получить истинное значение строки при чтении зашифрованной строки из файла.
    Требование к безопасности упущены.
    """
    global SECRET_KEY
    key = SECRET_KEY
    encoded_chars = []
    coded_string = base64.urlsafe_b64decode(coded_string).decode()
    for i in range(len(coded_string)):
        key_c = key[i % len(key)]
        encoded_c = chr(ord(coded_string[i]) - ord(key_c) % 256)
        encoded_chars.append(encoded_c)
    encoded_string = "".join(encoded_chars)
    return encoded_string


class OBJ:
    """
    Объект инициируемый из dict с доступом атрибутом,
    как через значение ключа, так и через точку
    """

    def __init__(self, dictionary: dict):
        def _traverse(key, element):
            if isinstance(element, dict):
                return key, OBJ(element)
            else:
                return key, element

        tmp_obj = dict(_traverse(k, v) for k, v in dictionary.items())
        self.__dict__.update(tmp_obj)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __getattr__(self, attr):
        return self[attr]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def as_dict(self):
        result = {}
        d = self.__dict__
        for key, value in d.items():
            if isinstance(value, OBJ):
                result[key] = value.as_dict()
            else:
                result[key] = value
        return result


class RoughConfigParser:
    """
    Класс реализующий инструменты для работы с настройками

    :attributes:

    config_file_path: str
    Путь к файлу с настройками

    hide_fields: List[str] = []
    Список полей (ключей) для которых нужно зашифровывать значение при хранении в файле

    config_file_path_for_update: Optional[List[str]]
    Список путей к файлу для чтения из них пак ключ - значение, при обновлении

    fn_coder_string: Callable[[str],str]
    Функция используемая для шифрования строки
    default coder_string function

    fn_decoder_string: Callable[[str],str]
    Функция используемая для дешифрования строки
    default decoder_string function

    """

    def __init__(self,
                 config_file_path_for_init: Optional[str] = None,
                 init_data: Union[Tuple[dict, ...], dict] = ({},),
                 hide_fields: Optional[list] = None,
                 config_file_path_for_update: Optional[List[str]] = None,
                 fn_coder_string: Callable[[str], str] = None,
                 fn_decoder_string: Callable[[str], str] = None):

        self.hide_fields: list = []
        self.__coder_string = coder_string
        self.__decoder_string = decoder_string
        self.data = OBJ({})
        self.config_file_path_for_update: List[str] = []
        if config_file_path_for_update is not None:
            self.config_file_path_for_update = config_file_path_for_update

        if config_file_path_for_init is not None:
            # Читаем из указанного файла настройки и инициируем экземпляр значениями хранящимися в файле
            self.read_config_file(config_file_path=config_file_path_for_init)
        if isinstance(init_data, dict):
            init_data = (self.as_dict(), init_data)
        elif isinstance(init_data, tuple):
            init_data = (self.as_dict(),) + init_data
        self.__validation_init_data(init_data)
        self.data = OBJ(merge_dicts(init_data))
        self.set_hide_fields(hide_fields)
        self.set_fn_coder_string(fn_coder_string)
        self.set_fn_decoder_string(fn_decoder_string)

    @staticmethod
    def __validation_init_data(dictionaries: Union[Tuple[dict, ...], dict]):
        """ Проверка правильности типа данных переданных в dictionaries """
        if not isinstance(dictionaries, tuple) and not isinstance(dictionaries, dict):
            raise TypeError
        if isinstance(dictionaries, tuple):
            for el in dictionaries:
                if not isinstance(el, dict):
                    raise TypeError

    def set_hide_fields(self, hide_fields: Optional[list] = None):
        """ Устанавливает список полей (ключей), для которых необходимо скрывать значение при записи в файл """
        self.hide_fields = hide_fields if hide_fields is not None else []

    def set_config_file_path_for_update(self, config_file_path_for_update: Optional[List[str]] = None):
        """ Устанавливает список полей (ключей), для которых необходимо скрывать значение при записи в файл """
        if config_file_path_for_update is not None:
            self.config_file_path_for_update = config_file_path_for_update

    def set_fn_coder_string(self, fn_coder_string: Callable[[str], str] = None):
        """ Изменяет функцию кодирования скрытых строк """
        self.__coder_string = fn_coder_string if callable(fn_coder_string) else coder_string

    def set_fn_decoder_string(self, fn_decoder_string: Callable[[str], str] = None):
        """ Изменяет функцию декодирования скрытых строк """
        self.__decoder_string = fn_decoder_string if callable(fn_decoder_string) else decoder_string

    def add_new_config_params(self, dictionaries: dict):
        """ Добавляет новые параметры из dictionaries """
        old_dictionaries = self.as_dict()
        self.__validation_init_data(dictionaries)
        self.data = OBJ(merge_dicts((old_dictionaries, dictionaries)))

    def add_config_file_path_for_update(self, config_file_path: str):
        """ Добавляет путь к файлу из которого необходимо прочитать пару ключ - значение при обновлении """
        self.config_file_path_for_update.append(config_file_path)

    def replace_config(self, dictionaries: Union[Tuple[dict, ...], dict] = ({},)):
        """ Очищает старые и создает новые атрибуту из dictionaries """
        self.__validation_init_data(dictionaries)
        self.data = OBJ(merge_dicts(dictionaries))

    def read_config_file(self, config_file_path: str, only_read=False, overwrite=True) -> dict:
        """
        Выполняет чтение настроек из файла и возвращает их в случаи успеха.
        Если файла с настройками нет, то создается новый файл с параметрами по умолчанию.
        Если overwrite = True, то все прочитанные настройки обновляют (заменяют) текущие значения экземпляра.
        Если overwrite = False, то все прочитанные настройки объединяются с текущими значениями экземпляра.
        Если only_read = True, то значения будут только прочитаны, но обновление значений экземпляра не произойдет.
        """

        if not os_isfile(config_file_path):
            # Если файл с настройками отсутствует, то создаем файл с дефолтными настройками
            self.write_config_file(config_file_path)
        else:
            with open(config_file_path, "r") as yml_file:
                try:
                    cfg_dict = yaml.load(yml_file, Loader=yaml.CLoader)
                except ScannerError:
                    return {}
                else:
                    if isinstance(cfg_dict, dict):
                        for key in self.hide_fields:
                            cfg_dict, _ = set_value_for_key(cfg_dict, key, self.__decoder_string)
                        pass
                    if not only_read:
                        if overwrite:
                            self.replace_config(cfg_dict)
                        else:
                            self.add_new_config_params(cfg_dict)
                    else:
                        if cfg_dict is not None:
                            return dict(cfg_dict)
                        else:
                            return {}
        return self.as_dict()

    def write_config_file(self, config_file_path: str):
        """ Запись настроек в файл """
        data = self.as_dict()
        for key in self.hide_fields:
            data, _ = set_value_for_key(data, key, self.__coder_string)

        with open(config_file_path, "w") as yml_file:
            yaml.dump(data, yml_file, default_flow_style=False)

    def r_update(self):
        """ Выполняет чтение значений из файлов в списке config_file_path_for_update """
        for file_path in self.config_file_path_for_update:
            if os_isfile(file_path):
                self.read_config_file(config_file_path=file_path, overwrite=True)

    def as_dict(self) -> dict:
        """ Вернуть объект как словарь """
        result = {}
        d = self.data.__dict__
        for key, value in d.items():
            if isinstance(value, OBJ):
                result[key] = value.as_dict()
            else:
                result[key] = value
        return result

    def __getitem__(self, key):
        return self.data.__dict__[key]

    def __getattr__(self, attr):
        return self.data[attr]

    def __setitem__(self, key, value):
        self.data[key] = value
