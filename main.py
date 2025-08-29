import os
import threading
import time
from pathlib import Path
from dotenv import load_dotenv
from listener import Listener
from queue import Queue
from log_utils import setup_logging_from_file, get_logger, shutdown_logging, LoggerAdapter

def _initialize_logging() -> LoggerAdapter:
    """
    Inicializa el sistema de logging.
    Returns:
        logging.LoggerAdapter: Logger principal.
    """
    setup_logging_from_file(config_path="./log_utils/logger_config.json")
    log = get_logger("Main")
    return log

def _read_env_file() -> dict:
    """
    Lee y valida las variables del archivo .env.
    Returns:
        dict: Diccionario con las variables de entorno.
    Raises:
        FileNotFoundError: Si el archivo .env o algún archivo .accdb no existe.
    """
    # Cargar variables del archivo .env
    load_dotenv()

    env_dict = {}
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_dict[key.strip()] = value.strip()

    # Validar que DATA_PATH existe   
    if 'DATA_PATH' not in env_dict or not os.path.exists(env_dict['DATA_PATH']):
        raise FileNotFoundError(f"El path '{env_dict['DATA_PATH']}' no existe.")

    # Convertir BUSINESS_CODE a un diccionario
    env_dict['BUSINESS_CODE'] = {name: code for b in env_dict.get('BUSINESS_CODE', '').split(',') for name, code in [b.split(':')]}

    # Comprobar que existen los archivos .accdb para cada negocio
    for business_name, code in env_dict['BUSINESS_CODE'].items():
        accdb_path = os.path.join(env_dict['DATA_PATH'], f"{code}{env_dict['EXERCISE']}.accdb")
        if not os.path.exists(accdb_path):
            raise FileNotFoundError(f"El archivo '{accdb_path}' para el negocio '{business_name}' no existe.")
        env_dict[f"{business_name}_ACCDB_PATH"] = accdb_path

    # Convertir BUSINESS_SERIALS a un diccionario
    env_dict['BUSINESS_SERIALS'] = {name: serial for b in env_dict.get('BUSINESS_SERIALS', '').split(',') for name, serial in [b.split(':')]}
    
    return env_dict

def main():
    log = _initialize_logging()
    ENV_DICT = _read_env_file()
    log.info("="*32)
    log.info("Arrancando oficit-FactuLink")
    
    # Creamos una cola vacía para el controlador principal
    controller_queue = Queue()

    # Creamos los listeners para las subempresas
    listener_dict = {}
    threas_dict = {}
    for business_name in ENV_DICT['BUSINESS_CODE'].keys():
        if business_name != ENV_DICT['MAIN_BUSINESS']:
            listener = Listener(
                business_name=business_name,
                accdb_path=Path(ENV_DICT[f"{business_name}_ACCDB_PATH"]),
                controller_queue=controller_queue,
            )
            listener_dict[business_name] = listener

    # Iniciamos los listeners
    for lst in listener_dict.values():
        t = threading.Thread(target=lst.run, daemon=True)
        threas_dict[lst.business_name] = t
        t.start()

    # Mantener el hilo principal activo
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Cierre solicitado por usuario")
        log.info("="*32)
    finally:
        shutdown_logging()
        

if __name__ == "__main__":
    main()