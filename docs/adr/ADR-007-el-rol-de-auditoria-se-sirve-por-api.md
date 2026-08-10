# ADR-007 · El rol de auditoria se sirve por la API y no por la interfaz

- **Estado:** aceptada
- **Fecha:** agosto de 2026
- **Afecta a:** `quanta/q3_servicio/core/seguridad.py`, `quanta/q4_cliente/src/App.tsx`,
  `docs/manuales/MANUAL_USUARIO.md`

## Contexto

El sistema declara tres roles: sostenedor, directivo y auditor. Los tres existen
en el control de acceso del cuanto 3 y los tres estan verificados:
`test_auditor_ve_cualquier_rbd` comprueba que el auditor **alcanza cualquier
establecimiento**, sin la restriccion de jurisdiccion que CTRL-04 aplica a los
otros dos.

Al verificar la interfaz el 2026-08-10 aparecio una divergencia. El auditor entra
con normalidad, pero su lista de establecimientos asignados esta vacia —lo esta a
proposito: su alcance no es una lista, es todo— y la interfaz interpreta esa lista
vacia como ausencia de jurisdiccion. Le muestra el mensaje

> Su perfil no tiene establecimientos asignados. El control de acceso limita la
> consulta a los establecimientos bajo su jurisdiccion.

y le bloquea las cuatro ventanas.

**El mensaje es exactamente lo contrario de la verdad.** El auditor no tiene menos
alcance que los demas: tiene mas. Lo que no tiene es una lista, porque el selector
de la barra superior esta construido sobre una enumeracion de identificadores
autorizados y el conjunto del auditor no se enumera.

## Decision

**El rol de auditoria se sirve por la API del cuanto 3, no por la interfaz del
cuanto 4.** Se declara como decision de alcance y no como defecto pendiente.

Dos consecuencias operativas:

1. La interfaz **distingue el caso**. Un perfil sin establecimientos por falta de
   asignacion sigue viendo el mensaje actual. Un perfil de auditoria ve un mensaje
   propio que dice lo que ocurre: su rol consulta por la API, con las mismas rutas
   y el mismo token, y la interfaz no ofrece la enumeracion que su alcance
   requeriria.
2. El manual de usuario lo declara en el apartado de acceso, para que un auditor
   no lea la pantalla como una negativa de autorizacion.

## Por que no se sirve por interfaz

Servirlo no es agregar una pantalla: es cambiar el modelo de navegacion. El
selector enumera identificadores autorizados, y el conjunto del auditor son todos
los establecimientos del pais depurados. Necesitaria busqueda por identificador,
resultados paginados y una decision sobre que puede ver un auditor sin haber
elegido establecimiento —el tablero consolidado del sostenedor no tiene sentido
sobre 7.754 establecimientos—.

Eso es alcance nuevo, no un ajuste. A ocho dias de la entrega, la eleccion honesta
es declarar la frontera y no simularla.

## Consecuencias

**Positivas.** La interfaz deja de mentirle a un rol sobre su propio alcance. La
frontera entre lo que el servicio ofrece y lo que la interfaz consume queda
explicita, que es la misma frontera que el proyecto sostiene entre cuantos: el
cuanto 3 publica capacidades, el cuanto 4 consume las que necesita, y no toda
capacidad publicada tiene ventana.

**Negativas.** Un auditor sin conocimientos tecnicos no puede usar el sistema. Se
acepta: el rol existe para verificar el calculo, no para gestionar un
establecimiento, y quien verifica un calculo tiene los medios para consultar una
ruta HTTP documentada en `/docs`.

**Riesgo de lectura.** Puede leerse como una funcionalidad incompleta presentada
como decision. La diferencia esta en que la capacidad **existe y esta verificada**
en el servicio: lo que se decide es no construirle una interfaz, no dejarla sin
implementar.

## Alternativas descartadas

**Construir la busqueda por identificador.** Es la solucion correcta y queda
registrada como trabajo futuro. Se descarta por fecha, no por criterio.

**Asignarle al auditor una lista fija de establecimientos.** Haria funcionar la
interfaz al precio de recortar el alcance del rol en el servicio. Ajustar el
sistema para que calce con la pantalla es la direccion equivocada.

**Ocultar el rol.** Retirarlo del directorio haria desaparecer el sintoma y
tambien una capacidad verificada del control de acceso.
