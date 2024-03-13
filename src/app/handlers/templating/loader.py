import os

import aiofiles
import aiofiles.os
import genshi.template

from .rendering import Template


class TemplateLoader():
    def __init__(self, search_path):
        '''
        Args:
            search_path (str): путь к корневой папке, где лежат шаблоны
        '''

        self.search_path = search_path

    async def load(self, filepath):
        '''
        Загружает шаблон из файловой системы

        Args:
            filepath (str): путь к шаблону относительно `self.search_path`

        Returns:
            Template: шаблон, созданный из загруженного файла

        Raises:
            genshi.template.TemplateNotFound: если файл не найден
        '''

        fullpath = os.path.join(self.search_path, filepath)
        if not await aiofiles.os.path.exists(fullpath):
            raise genshi.template.TemplateNotFound(filepath, self.search_path)

        async with aiofiles.open(fullpath, encoding='UTF-8') as template_file:
            return Template(await template_file.read())
