from typing import Tuple, Union, Callable, Any


def extend_dictionary(extend_dict: dict, key: str, value, only_new_value=True) -> dict:
    if key in extend_dict:
        if isinstance(extend_dict[key], list):
            extend_dict[key].append(value)
        elif isinstance(extend_dict[key], dict):
            if isinstance(value, dict):
                extend_dict[key] = merge_dicts((extend_dict[key], value), only_new_value=only_new_value)
        else:
            if extend_dict[key] != value:
                if only_new_value:
                    extend_dict[key] = value
                else:
                    extend_dict[key] = [extend_dict[key], value]
    else:
        extend_dict[key] = value
    return extend_dict


def merge_dicts(dict_args: Union[Tuple[dict, ...], dict], only_new_value=True) -> dict:
    """
    Объединяет словари, сохраняя все уникальные ключи.
    По умолчанию, при совпадении ключей в результирующем словаре будет записано значение из последнего словаря.
    Если вы ходите сохранить все значения как список, то установите only_new_value = False

    param:
    only_new_value -
    """
    result: dict = {}
    if isinstance(dict_args, dict):
        return _lowercase_for_dict_keys(dict_args)
    for dictionary in dict_args:
        dictionary = _lowercase_for_dict_keys(dictionary)
        if isinstance(dictionary, dict):
            for key, value in dictionary.items():
                result = extend_dictionary(result, key, value, only_new_value=only_new_value)
    return result


def _lowercase_for_dict_keys(any_keys_dict: dict):
    """ вернуть словарь с ключами в верхнем регистре """
    upper_dict = {}
    for k, v in any_keys_dict.items():
        if isinstance(v, dict):
            v = _lowercase_for_dict_keys(v)
        upper_dict[k.lower()] = v
    return upper_dict


def set_value_for_key(dct: dict, key: str,
                      val:Union[Callable[[str], str], Any],
                      only_first: bool = False) -> Tuple[dict, bool]:
    """
    Заменяет первое найденное значение (по уровням) с заданным ключом

    val Может содержать функцию, которая выполняет изменение над строкой.

    """
    successful = False
    if key in dct:
        dct[key] = val(dct[key]) if callable(val) else val
        successful = True
        if only_first:
            return dct, successful
    for k in dct:
        if isinstance(dct[k], dict):
            res, successful = set_value_for_key(dct[k], key, val, only_first)
            if successful:
                dct[k] = res
                if only_first:
                    return dct, successful
    return dct, successful
