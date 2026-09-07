# Texto de entrada de `/speckit-specify`

Redactado el 2026-09-07 a partir de la guía de configuración de GitHub (§10, prueba de humo de la
organización) y del plan global (§3.7 y hito 0). Se guarda para que quede claro qué se pidió.

---

Prueba de humo de la organización de GitHub.

El equipo de plataforma necesita saber, en una sola ejecución y sin mirar pantallas, si la
organización de GitHub está configurada exactamente como el estándar exige antes de cerrar el hito 0 y
antes de cada demostración. Hoy eso son diez comandos manuales cuyo resultado se compara a ojo con lo
esperado, y la demo anterior falló precisamente porque el esquema exigía una propiedad de repositorio
que nadie había creado y nadie lo comprobó.

La comprobación recorre lo que la guía fija como obligatorio y falla si falta cualquier cosa:

- La organización existe, con el plan esperado y los ajustes de miembros (permiso base y quién puede
  crear repositorios) que dicta la guía para ese entorno.
- Existen los equipos que el estándar espera, con los nombres que fija el mapa de papeles a equipos.
- La GitHub App del ciclo de vida está instalada en la organización y cubre todos los repositorios.
- Cada uno de los repositorios de la plataforma y de dominio tiene los dos secretos de la App.
- Cada marketplace tiene sus dos variables, con el canal correcto en cada uno.
- Sólo los repositorios de dominio llevan el topic que usa el generador del índice; ningún repositorio
  de prueba lo lleva.
- Cada repositorio de dominio tiene los dos rulesets, y el que protege la rama principal exige
  exactamente los tres contextos requeridos del estándar, ni uno más ni uno menos, con el origen
  correcto.

El resultado es un informe legible que dice, por cada comprobación, si pasó o qué falta exactamente,
y un veredicto global: verde sólo si todo pasó. Sirve tanto para la organización de demostración
(plan gratuito, repositorios públicos) como para la de BCP (Enterprise, repositorios privados), donde
cambian el nombre de la organización, los nombres reales de los equipos y algunos valores esperados,
pero no las comprobaciones.
