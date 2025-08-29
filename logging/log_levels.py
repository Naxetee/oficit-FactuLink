import logging
from enum import IntEnum

class LogLevel(IntEnum):
    """
    Niveles de log personalizados.
    """
    TRACE = 5      # más fino que DEBUG
    DEBUG = logging.DEBUG         # 10
    INFO = logging.INFO           # 20
    WARNING = logging.WARNING     # 30
    ERROR = logging.ERROR         # 40
    CRITICAL = logging.CRITICAL   # 50

# Registrar el nivel TRACE en logging (solo una vez)
if not hasattr(logging, "TRACE"):
    logging.addLevelName(LogLevel.TRACE, "TRACE")
    def trace(self, msg, *args, **kwargs):
        if self.isEnabledFor(LogLevel.TRACE):
            self._log(LogLevel.TRACE, msg, args, **kwargs)
    logging.Logger.trace = trace

NAME_TO_LEVEL = {
    "TRACE": LogLevel.TRACE,
    "DEBUG": LogLevel.DEBUG,
    "INFO": LogLevel.INFO,
    "WARN": LogLevel.WARNING,
    "WARNING": LogLevel.WARNING,
    "ERROR": LogLevel.ERROR,
    "CRITICAL": LogLevel.CRITICAL,
    "FATAL": LogLevel.CRITICAL,
}

def parse_level(level_str: str | int | LogLevel, default: LogLevel = LogLevel.INFO) -> LogLevel:
    """
    Convierte una cadena o entero a un nivel de log LogLevel.
    Args:
        level_str (str | int | LogLevel): Nivel de log como cadena, entero o LogLevel.
        default (LogLevel): Nivel por defecto si la conversión falla.
    Returns:
        LogLevel: Nivel de log correspondiente.
    """
    if isinstance(level_str, LogLevel):
        return level_str
    if isinstance(level_str, int):
        try:
            return LogLevel(level_str)
        except ValueError:
            return default
    if isinstance(level_str, str):
        return NAME_TO_LEVEL.get(level_str.strip().upper(), default)
    return default