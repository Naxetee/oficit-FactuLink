import logging
import logging.handlers
from logging import LoggerAdapter
import os
from pathlib import Path
import sys
import json
from queue import Queue
from .log_levels import LogLevel, parse_level

_LOG_QUEUE = Queue()
_LISTENER = None

def setup_logging_from_file(config_path: Path):
    """
    Configura el sistema de logging a partir de un archivo JSON.
    Args:
        config_path (Path): Ruta al archivo de configuración JSON.
    """
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        cfg = {}
    _setup_logging(
        log_dir=cfg.get("log_dir"),
        log_file=cfg.get("log_file"),
        level=cfg.get("level"),
        json=cfg.get("json", False),
        when=cfg.get("when"),
        backup_count=int(cfg.get("backup_count")),
    )

def _setup_logging(
    log_dir: str,
    log_file: str,
    level: LogLevel,
    json: bool,
    when: str,
    backup_count: int
):
    """
    Configura el sistema de logging.
    Args:
        log_dir (str): Directorio donde se guardarán los logs.
        log_file (str): Nombre del archivo de log.
        level (LogLevel): Nivel de log.
        json (bool): Si es True, el log se formateará en JSON.
        when (str): Intervalo para rotar los logs.
        backup_count (int): Número de archivos de log antiguos a conservar.
    """
    # Crear el directorio de logs si no existe
    os.makedirs(log_dir, exist_ok=True)
    logfile_path = os.path.join(log_dir, log_file)

    # Obtenemos el nivel de log
    log_level = getattr(logging, str(level), LogLevel.TRACE)

    # Configuramos el formateo del log
    if json:
        fmt = '{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","thread":"%(threadName)s","msg":"%(message)s","business":"%(business)s","component":"%(component)s"}'
        datefmt = "%Y-%m-%dT%H:%M:%S"
    else:
        fmt = "[%(asctime)s] %(levelname)s %(component)s(%(business)s) - %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"

    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    # Configuramos el handler de archivo
    file_handler = logging.handlers.TimedRotatingFileHandler(
        logfile_path, when=when, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    # Configuramos el handler de consola
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # Configuramos el logger root
    root = logging.getLogger()
    root.setLevel(log_level)
    for h in list(root.handlers):
        root.removeHandler(h)
    queue_handler = logging.handlers.QueueHandler(_LOG_QUEUE)
    root.addHandler(queue_handler)

    global _LISTENER
    if _LISTENER:
        _LISTENER.stop()
    _LISTENER = logging.handlers.QueueListener(_LOG_QUEUE, file_handler, console_handler, respect_handler_level=True)
    _LISTENER.start()

def get_logger(component: str, business: str = None) -> logging.LoggerAdapter:
    """
    Obtiene un logger configurado para un componente y negocio específicos.
    Args:
        component (str): Nombre del componente (ej. "Listener", "Controller").
        business (str, optional): Nombre del negocio. Defaults to None.
    Returns:
        logging.LoggerAdapter: Logger adaptado con información adicional.
    """
    base_logger = logging.getLogger(component)
    return logging.LoggerAdapter(base_logger, extra={"component": component, "business": business or ""})

def shutdown_logging():
    """
    Detiene el listener de logging y cierra los handlers.
    """
    global _LISTENER
    if _LISTENER:
        _LISTENER.stop()
        _LISTENER = None
    logging.shutdown()