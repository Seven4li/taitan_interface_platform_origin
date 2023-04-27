import logging
from logging import handlers
from backend.config import LOG_LEVEL, BASE_DIR


# 定义日志收集的方法
def init_logging(logger_name=None, stream=None):
    # 初始化日志器
    logger = logging.getLogger(logger_name)
    # 设置日志等级
    logger.setLevel(LOG_LEVEL)
    # 初始化处理器
    sh = logging.StreamHandler(stream=stream)  # 控制台处理器
    fh = logging.handlers.TimedRotatingFileHandler(filename=BASE_DIR + "/backend/logs/lagou.log",
                                                   when='h',
                                                   interval=24,
                                                   backupCount=7,
                                                   encoding="utf-8")
    # 初始化格式化器
    fmt = "[%(asctime)s %(levelname)s %(threadName)s %(filename)s %(funcName)s %(lineno)d] [%(thread)d] [%(message)s]"
    formmater = logging.Formatter(fmt)
    # 设置格式化器
    sh.setFormatter(formmater)
    fh.setFormatter(formmater)
    # 设置处理器
    logger.addHandler(sh)
    logger.addHandler(fh)

    return logger
