import asyncio
from datetime import datetime
import json
import logging
import logging.handlers
import queue
import os.path
import traceback

from app.database import models
from app import constants
from app.utils import config


LOGGER_NAME = 'app'


class Logger(logging.Logger):
    '''
    Дополняет `LogRecord`, гарантируя наличие полей, к которым обращаются хэндлеры;
    дополнительные поля организованы так, чтобы из `LogRecord` было удобно создавать
    модель `LogEntry` (значения `extra`, чьи ключи соответствуют полям `LogEntry`,
    записываются в поля `LogRecord`, оставшееся содержимое `extra` записывается
    в поле `_context` как есть)
    '''

    _extra_attrs = {'opid', 'partnership_id', 'initiator_opid', '_context'}

    def makeRecord(
        self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None
    ):
        # дефолтное поведение для библиотечных модулей
        # (т.к. переопределять класс логгера приходится глобально)
        if name.split('.')[0] != LOGGER_NAME:
            return super().makeRecord(name, level, fn, lno, msg, args, exc_info, func, extra, sinfo)

        record = logging.LogRecord(name, level, fn, lno, msg, args, exc_info, func, sinfo)
        extra = extra or {}
        record.__dict__.update({key: extra.pop(key, None) for key in self._extra_attrs})
        record.__dict__['_context'] = extra
        return record


class LoggerAdapter(logging.LoggerAdapter):
    '''
    TODO: начиная с Python 3.13 класс не нужен,
    можно использовать стандартный LoggerAdapter с аргументом `merge_extra=True`
    '''

    def process(self, msg, kwargs):
        return (
            msg,
            {
                **kwargs,
                'extra': {
                    **(self.extra or {}),
                    **kwargs.get('extra', {}),
                },
            }
        )


class QueuedWriter():
    '''
    Класс для неблокирующей записи логов в базу; по назначению похож на
    `logging.handlers.QueueListener`, но в отличие от него,
    использует асинхронную очередь в главном треде и сам управляет записью логов
    '''

    def __init__(self, queue, db_sessionmaker, num_workers=1):
        '''
        Args:
            queue (asyncio.Queue): очередь, в которую кладет `LogRecord`ы
                непосредственный хэндлер логгера
            db_sessionmaker (qlalchemy.ext.asyncio.AsyncSession): фабрика DB-сессий
            num_workers (int): количество воркеров для обработки задач из очереди
            fallback_logger (logging.Logger): логгер, который будет использован
                при невозможности записать лог в базу
        '''

        self.queue = queue
        self._db_sessionmaker = db_sessionmaker
        self._num_workers = num_workers
        self._tasks = set()

    async def start(self):
        for idx in range(self._num_workers):
            task = asyncio.create_task(self._worker(idx=idx))
            self._tasks.add(task)

    async def stop(self):
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def _worker(self, **kwargs):
        async with self._db_sessionmaker() as session:
            while True:
                record = await self.queue.get()
                try:
                    async with session.begin():
                        entry = self._make_entry(record)
                        session.add(entry)
                except Exception as error:
                    print('!' * 50)
                    print('Ошибка при записи лога в базу')
                    traceback.print_exception(error)
                finally:
                    self.queue.task_done()

    @staticmethod
    def _make_entry(record):
        return models.LogEntry(
            level=record.levelname,
            opid=record.opid,
            # используется `partnership_id` в явном виде вместо relationship-а `partnership`,
            # т.к. запрос модели `Partnership` и логирование происходят в разных asyncio тасках,
            # каждый из которых создает свою sqlAlchemy-сессию,
            # а в sqlAlchemy нельзя использовать один и тот же объект в контексте разных сессий
            partnership_id=record.partnership_id,
            initiator_opid=record.initiator_opid,
            logged_at=datetime.fromtimestamp(record.created, constants.APP_TIMEZONE),
            data={'message': record.getMessage(), 'context': record._context},
        )


class LoggingService():
    '''
    Управляет записью логов в терминал и базу данных
    '''

    def __init__(self, db_sessionmaker, num_workers=3):
        '''
        Args:
            db_sessionmaker (qlalchemy.ext.asyncio.AsyncSession): фабрика DB-сессий
            num_workers (int): количество воркеров для записи логов в базу
        '''

        logging.setLoggerClass(Logger)

        logger = self.logger = logging.getLogger(LOGGER_NAME)
        logger.setLevel(logging.INFO)

        self._init_stream_logging(logger)

        self._init_db_logging(logger, db_sessionmaker, num_workers)

    def _init_stream_logging(self, logger):
        que = queue.SimpleQueue()
        que_handler = logging.handlers.QueueHandler(que)
        logger.addHandler(que_handler)
        formatter = logging.Formatter(
            (
                "[{asctime}] [{levelname:<8}] [{pathname}:{lineno}]: {message}"
                "\nданные операции: opid={opid}, "
                "partnership_id={partnership_id}, "
                "initiator_opid={initiator_opid}"
                "\nпрочие данные: {_context}\n"
            ),
            '%Y-%m-%d %H:%M:%S %Z',
            style='{'
        )
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(config.get('LOGS_DIR'), 'app.log'),
            when='midnight',
            utc=True
        )
        file_handler.setFormatter(formatter)
        self._stream_listener = logging.handlers.QueueListener(que, stream_handler, file_handler)

    def _init_db_logging(self, logger, db_sessionmaker, num_workers):
        que = asyncio.Queue()
        logger.addHandler(logging.handlers.QueueHandler(que))
        self._db_writer = QueuedWriter(que, db_sessionmaker, num_workers)

    async def start(self):
        await self._db_writer.start()
        self._stream_listener.start()

    async def stop(self):
        await self._db_writer.stop()
        await self._db_writer.queue.join()

        self._stream_listener.stop()


class JSONEncoder(json.JSONEncoder):
    '''
    Расширяет дефолтный JSONEncoder,
    чтобы большинство видов данных можно было записывать в базу в читаемом виде
    '''

    def default(self, obj):
        if isinstance(obj, Exception):
            return obj.__dict__

        try:
            return super().default(obj)
        except TypeError:
            return str(obj)
