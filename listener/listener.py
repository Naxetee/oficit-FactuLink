import pyodbc
from pathlib import Path
import queue
import time
from log_utils import get_logger

class Listener:
    def __init__(self, business_name: str, accdb_path: Path, controller_queue: 'queue.Queue'):
        """
        Inicializa el listener para una base de datos Access específica.
        Args:
            business_name (str): Nombre del negocio (ej. "OFICIT").
            accdb_path (Path): Ruta al archivo .accdb de la base de datos.
            controller_queue (queue.Queue): Cola para comunicar con el controlador.
        """
        self.business_name = business_name
        self.accdb_path = accdb_path
        self.controller_queue = controller_queue
        self.last_id = None
        self.log = get_logger("Listener", business_name)

    def connect(self) -> pyodbc.Connection:
        """
        Conecta a la base de datos Access.
        Returns:
            conn (pyodbc.Connection): Objeto de conexión a la base de datos.
        """
        try:  
            conn =  pyodbc.connect(
                rf'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.accdb_path};'
            )
        except Exception as e:
            self.log.error(f"Error conectando a {self.accdb_path}: {e}")
            return None
        return conn

    def run(self):
        self.log.info("Listener iniciado")
        self._initialize_last_id()
        while True:
            try:
                new_orders = self._get_new_orders()
                if new_orders:
                    self.log.info(f"Nuevos pedidos encontrados: {len(new_orders)}")
                    for order in new_orders:
                        self._process_new_order(order)
                        self.last_id = f"{order[1]}"
                else:
                    self.log.debug("No hay nuevos pedidos.")
            except Exception as e:
                self.log.exception(f"Error en Listener: {e}")
            time.sleep(10)

    def _initialize_last_id(self):
        """
        Inicializa el último ID conocido desde la base de datos.
        """
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT TOP 1 CODPCL FROM F_PCL ORDER BY CODPCL DESC")
            row = cursor.fetchone()
            if row:
                self.last_id = f"{row[0]}"
                self.log.debug(f"Último ID inicializado a {self.last_id}")
            else:
                self.last_id = "1"
                self.log.debug("No hay pedidos en la base de datos. Último ID inicializado a 0")

    def _get_new_orders(self) -> list[tuple]:
        """
        Obtiene los nuevos pedidos desde la base de datos.
        Returns:
            new_orders (list[tuple]): Lista de tuplas con los nuevos pedidos.
        """
        try:
            query = "SELECT TIPPCL, CODPCL, CNOPCL FROM F_PCL"
            if self.last_id is not None:
                query += f" WHERE CODPCL > {self.last_id}"
            query += " ORDER BY CODPCL ASC"

            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                return rows
        except Exception as e:
            self.log.error(f"Error obteniendo nuevos pedidos: {e}")
            return None

    def _process_new_order(self, order: tuple):
        """
        Procesa un nuevo pedido y lo envía al controlador.
        Args:
            order (tuple): Tupla con los datos del pedido (TIPPCL, CODPCL, CNOPCL).
        """
        try:
            order_type, order_id, nom_cliente = order[:3]
            self.log.info(f"Procesando pedido ID={order_type}-{order_id:06d}, Cliente={nom_cliente}")
            event = {
                "empresa": self.business_name,
                "id": f"{order_type}-{order_id:06d}",
                "nombre_cliente": nom_cliente,
                "timestamp": time.time()
            }
            self.controller_queue.put(event)
            self.log.debug(f"Pedido {order[1]} enviado al controlador.")
        except Exception as e:
            self.log.error(f"Error procesando el pedido {order[1]}: {e}")
    
        