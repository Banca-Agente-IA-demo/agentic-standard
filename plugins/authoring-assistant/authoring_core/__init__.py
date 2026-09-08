"""Núcleo del asistente de autoría.

**Se llama `authoring_core` y no como el plugin a propósito.** Son dos cosas distintas: el plugin es
lo que se instala, y esto es la lógica que sus scripts importan. Y el nombre tiene que ser único en
la sesión: los scripts importan por `sys.path`, así que dos plugins instalados a la vez con un
paquete del mismo nombre se pisarían.

Vive en la raíz del plugin y no se instala: los clientes clonan la carpeta entera del plugin, y cada
script de entrada añade esta raíz a `sys.path` antes de importar. Por eso el paquete usa **sólo la
biblioteca estándar**: el autor no ejecuta `pip` para tener el asistente, y la única instalación que
ocurre alguna vez es la del validador del estándar, en un entorno privado y al primer uso.

Las capas siguen la regla de dependencia de G5: `domain` no importa nada del proyecto fuera de sí
mismo, `application` orquesta el dominio, `ports` declara lo único que tiene más de una
implementación, y `adapters` habla con el exterior.
"""
