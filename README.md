# FactuLink

## Conector de Pedidos Multi-Empresa para Factusol (ACCDB)

### Descripción General

`FactuLink` es un sistema de automatización diseñado para integrar y sincronizar los flujos de pedidos entre tres compañías que operan con Factusol.  El objetivo principal es automatizar el proceso por el cual 2 subempresas, al realizar una venta de productos que pertenecen al inventario de la empresa matriz, generen automáticamente un pedido de compra a esta. Esto asegura una gestión de stock y una trazabilidad contable coherente sin intervención manual.

### Problema a Resolver

Actualmente, cuando Duofic o OfiFactory venden un producto del inventario de Oficit, deben generar manualmente un pedido de compra a Oficit. Este proceso es propenso a errores, consume tiempo y puede generar desincronizaciones de stock.

### Solución Propuesta

`FactuLink` implementa una arquitectura basada en **Listeners**, un **Controller** con cola de mensajes y un **Worker** dedicado.

* **Listeners (1 por subempresa):** Servicios independientes que monitorizan las bases de datos `.accdb` de las subempresas. Detectan la creación de nuevos pedidos de cliente y envían estos eventos al Controller.
* **Controller:** Un servicio central que recibe los eventos de los Listeners. Gestiona una cola de pedidos a proveedor, normaliza los datos y asegura que los pedidos se procesen de forma ordenada y sin conflictos de concurrencia.
* **Worker:** Un componente que toma los pedidos de la cola del Controller y los inserta directamente en la base de datos `.accdb` de la empresa matriz como nuevos pedidos a proveedor. Esto simula la operación manual pero de forma automatizada y segura.

### Tecnologías Utilizadas

* **Lenguaje de Programación:** Python
* **Conexión a Bases de Datos:** `pyodbc` (para `.accdb` de Access)
* **Gestión de Colas/Estado:** `sqlite3` (base de datos embebida)
* **Concurrencia:** `threading` (para ejecutar componentes en paralelo)
* **Programación de Tareas:** `schedule` o `APScheduler` (para los Listeners)

### Beneficios

* **Automatización completa:** Elimina la necesidad de introducir pedidos manualmente entre empresas.
* **Consistencia de datos:** Asegura que el inventario de la empresa matriz se actualice correctamente con cada venta de una subempresa.
* **Reducción de errores:** Minimiza fallos humanos en la gestión de pedidos.
* **Trazabilidad:** Mantiene un registro claro de todas las operaciones.
* **Robustez:** Diseño con gestión de concurrencia y reintentos para entornos de bases de datos Access.

---