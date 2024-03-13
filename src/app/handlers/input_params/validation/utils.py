import copy

from app.utils.type_conversions import wrap_in_list


def merge_schemas(schema1, schema2, rule_merger=lambda n, r1, r2: r2):
    '''
    Мерджит две схемы

    Args:
        schema1 (dict): первая схема
        schema2 (dict): вторая схема
        rule_merger (function): функция, которая определяет, как мерджить каждое правило;
        по умолчанию правило из первой схемы заменяется правилом из второй

    Returns:
        dict: новая схема
    '''

    schema = copy.deepcopy(schema1)
    for field, ruleset2 in schema2.items():
        schema[field] = ruleset = schema.get(field, {})
        ruleset.update({
            rulename: rule_merger(rulename, ruleset.get(rulename), rule2)
            for rulename, rule2 in ruleset2.items()
        })
    return schema


def make_array_rule_merger(rulename):
    '''
    Фабрика функций-предикатов для `merge_schemas`.
    Создает функцию, которая отличается от дефолтной тем, что объединяет в общий массив
    правила с заданным названием

    Args:
        rulename (str): название правила

    Returns:
        function: каррированная функция
    '''

    def rule_merger(current_rulename, rule1, rule2):
        '''
        Функция-предикат для `merge_schemas`

        Args:
            current_rulename (str): название правила
            rule1 (*): правило из первой схемы
            rule2 (*): правило из второй схемы

        Returns:
            *|list: объединенный массив правил из обеих схем, если название правила
            соответствует заданному; правило из второй схемы в остальных случаях
        '''

        if current_rulename == rulename:
            return [*wrap_in_list(rule1), *wrap_in_list(rule2)]

        return rule2

    return rule_merger


extend_coercers = make_array_rule_merger('coerce')
