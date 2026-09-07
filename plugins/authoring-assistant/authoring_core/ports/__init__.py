"""El único puerto del asistente: el proveedor de releases.

Sólo hay puerto donde hay polimorfismo real. Git, el sistema de archivos y las plantillas tienen una
implementación única y no lo llevan, porque una interfaz con un solo implementador es indirección sin
beneficio (G5).
"""
