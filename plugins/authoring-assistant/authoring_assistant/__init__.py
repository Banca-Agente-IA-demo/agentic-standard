"""Núcleo del asistente de autoría.

Vive en la raíz del plugin y no se instala: los clientes clonan la carpeta entera del plugin, y cada
script de entrada añade esta raíz a `sys.path` antes de importar. Por eso el paquete usa **sólo la
biblioteca estándar**: el autor no ejecuta `pip` para tener el asistente, y la única instalación que
ocurre alguna vez es la del validador del estándar, en un entorno privado y al primer uso.

Las capas siguen la regla de dependencia de G5: `domain` no importa nada del proyecto fuera de sí
mismo, `application` orquesta el dominio, `ports` declara lo único que tiene más de una
implementación, y `adapters` habla con el exterior.
"""
