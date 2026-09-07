---
name: <<NAME>>
description: <<DESCRIPTION>>
metadata:
  tags: <<TAGS>>
---

# <<TITLE>>

<!--
  DÓNDE VA: `skills/<<NAME>>/SKILL.md`. El directorio TIENE que llamarse igual que `name`: es la única
  regla de identidad que la especificación impone, y si no coinciden el cliente no encuentra el skill,
  sin error, simplemente no aparece.

  EL FRONTMATTER SÓLO LLEVA LO QUE EL CLIENTE LEE más el mapa `metadata:` de catálogo. Nada de gobierno:
  ni id, ni owner, ni version, ni status, ni clasificación. Todo eso vive en el GOVERNANCE.json y en el
  plugin.json de la unidad, y el validador FALLA si reaparece aquí («vive en GOVERNANCE.json»).

  `metadata:` ES OPCIONAL y es texto a texto, como lo define la especificación Agent Skills. Sirve para
  que Port filtre. Claves admitidas: `tags` (lista separada por comas), `platform_source`,
  `platform_source_version`, `platform_target`, `platform_target_version`, `technologies`. Nombre y
  versión de plataforma van en claves separadas para poder filtrar por versión. Ejemplo completo:

      metadata:
        tags: migracion, cnf, atlas, validacion
        platform_source: Atlas
        platform_source_version: "2.6"
        platform_target: CNF
        platform_target_version: "3.0"
        technologies: Quarkus 3.x, Maven

  Si no hay nada que declarar, borra el bloque `metadata:` entero en vez de dejarlo vacío.

  LA `description` ES EL CAMPO MÁS IMPORTANTE del archivo y el que más se descuida. Es lo que el modelo
  lee para decidir si usa este skill, y lo único que se carga en CADA petición. Tiene que decir DOS cosas:
      QUÉ hace          «Revisa una consulta JQL y señala los filtros que faltan...»
      CUÁNDO usarlo     «...Úsalo cuando alguien escriba o pegue una consulta JQL.»
  En TERCERA PERSONA. Nada de «Puedo ayudarte a...»: la descripción se inyecta en el prompt del sistema y
  mezclar el punto de vista degrada la selección. Máximo 1024 caracteres.

  EL CUERPO SE CARGA SÓLO CUANDO EL SKILL SE USA, así que puede ser largo, pero cada línea compite con la
  conversación. Por debajo de 500 líneas; si necesitas más, parte el contenido en `references/` y
  referéncialo desde aquí.

  SU SUITE DE EVALS es obligatoria y vive en `evals/<<NAME>>/promptfooconfig.yaml` de la unidad (o en
  `evals/promptfooconfig.yaml` si la unidad es individual). El caso negativo de un skill comprueba que
  NO SE ACTIVE ante una consulta que comparte vocabulario pero necesita otra cosa.

  BORRA ESTE COMENTARIO al rellenar la plantilla.
-->

## Cuándo usar esto

<<WHEN>>

## Qué comprobar

<<PROCEDURE>>

## Qué devolver

<<OUTPUT>>
