import cerberus

from .utils import merge_schemas, extend_coercers
from .custom_rules import multi_to_single


class Validator(cerberus.Validator):
    '''
    Подкласс для валидации входных параметров в виде мультидикта,
    добавляющий валидацию однозначности каждого параметра и нормализацию к виду обычного словаря
    '''

    @staticmethod
    def _prepare_schema(schema):
        '''
        Преобразует схему таким образом, чтобы вызов `normalized` приводил
        документ-мультидикт к обычному словарю, если у каждого его ключа единственное значение

        Args:
            schema (dict): схема, правила которой предполагают работу с обычными словарями

        Returns:
            dict: схема с дополнительными правилами нормализации
        '''

        if schema is None:
            return None

        normalizer_schema = {field: {'coerce': multi_to_single} for field in schema}
        return merge_schemas(normalizer_schema, schema, extend_coercers)

    @staticmethod
    def _prepare_document(document):
        '''
        Args:
            document (multidict.MultiDict): валидируемый/нормализуемый документ

        Returns:
            dict: представление документа в виде словаря,
            где каждому ключу сопоставлен список его значений
        '''

        # если передан обычный словарь (не должно происходить при нормальном использовании)
        if not hasattr(document, 'getall'):
            return document

        return {field: document.getall(field) for field in document}

    def __init__(self, schema=None, **kwargs):
        super().__init__(schema=self._prepare_schema(schema), **kwargs)

    def validate(self, document, schema=None, **kwargs):
        return super().validate(
            self._prepare_document(document),
            schema=self._prepare_schema(schema),
            **kwargs
        )

    def normalized(self, document, schema=None, **kwargs):
        return super().normalized(
            self._prepare_document(document),
            schema=self._prepare_schema(schema),
            **kwargs
        )

    @property
    def is_document_valid(self):
        return len(self.errors) == 0
