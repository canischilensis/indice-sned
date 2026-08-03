# Plan de pruebas de aceptación

**Identificador:** PPA-SNED-01 · **Versión:** 1.0 · **Sistema:** Ecosistema predictivo del Índice SNED

> Estructura documental según **IEEE 829**. Proceso y diseño de casos según **ISO/IEC/IEEE 29119**.

---

## 1. Introducción

Verificar que el sistema hace lo que las historias de usuario declaran. El proyecto **excluye
explícitamente los estudios de satisfacción de usuarios**, de modo que la aceptación se formula
como verificación funcional y no como medición de usabilidad. El validador es el profesor guía.

## 2. Enfoque

Los criterios se redactan en **Gherkin** —Dado, Cuando, Entonces— porque el mismo texto sirve
en el documento de tesis y como prueba ejecutable con `pytest-bdd`. Cada historia del Product
Backlog se traduce en uno o más escenarios.

## 3. Escenarios positivos

```gherkin
Escenario: Consultar el índice estimado del establecimiento
  Dado un directivo autenticado con jurisdicción sobre el RBD 9
  Cuando solicita la predicción de su establecimiento
  Entonces recibe el índice estimado y el aporte de los seis factores
  Y cada factor indica si está acotado por información no pública

Escenario: Entender por qué se obtuvo ese resultado
  Dado un directivo consultando el factor Efectividad
  Cuando solicita la explicación
  Entonces recibe la contribución de cada variable ordenada por magnitud
  Y la suma de contribuciones más el valor base reproduce la predicción

Escenario: Simular el efecto de mover una variable
  Dado un directivo en el simulador
  Cuando modifica el puntaje SIMCE de matemática de 4° básico
  Entonces recibe la curva de sensibilidad del índice
  Y la respuesta advierte que comunica dirección, no promesa de retorno
```

## 4. Escenarios negativos

Los seis son obligatorios: es donde se cae la mayoría de las defensas.

```gherkin
Escenario: El control de acceso bloquea un RBD ajeno
  Dado un director con jurisdicción solo sobre el RBD 8451
  Cuando solicita la predicción del RBD 9012
  Entonces el sistema responde 403 y no revela dato alguno

Escenario: RBD inexistente
  Cuando se solicita la predicción de un RBD que no existe
  Entonces el sistema responde 404 con un mensaje comprensible

Escenario: Artefacto ausente
  Dado que el registro de modelos no tiene el artefacto
  Entonces el sistema responde 503 e indica cómo restaurarlo

Escenario: Variable no simulable
  Cuando se solicita simular una variable que no alimenta ningún factor
  Entonces el sistema responde 422 y nombra la variable

Escenario: Valor fuera de rango
  Cuando se solicita simular un SIMCE de 900 puntos
  Entonces el sistema responde 422 declarando el rango válido

Escenario: Sesión expirada
  Dado un token vencido
  Entonces el sistema responde 401 sin ejecutar la consulta
```

## 5. El principio ético como requisito verificable

```gherkin
Escenario: La IA asiste, el directivo decide
  Cuando se solicita cualquier predicción
  Entonces la respuesta incluye la advertencia de decisión humana

Escenario: La frontera de información es visible
  Cuando se consultan los factores del índice
  Entonces los cinco acotados por información no pública están marcados
  Y se declara la restricción que los limita
```

Esto convierte la premisa ética del proyecto en algo comprobable, no en una declaración.

## 6. Criterios de aprobación

Cobertura funcional **≥ 90 %** de las historias del Product Backlog. Los seis escenarios
negativos y los dos éticos son obligatorios: su fallo bloquea la aceptación sin importar la
cobertura alcanzada.

## 7. Alcance de la automatización

Contra la API para la lógica de negocio. Contra la interfaz solo para los tres flujos de las
ventanas: automatizar toda la interfaz es caro y frágil, y su cobertura corresponde al plan de
compatibilidad.

## 8. Entregables

`tests/aceptacion/` con los `.feature` y sus pasos · reporte HTML de `pytest` archivado por
Sprint como acta de aceptación.

## 9. Estado actual

**No implementado.** La estructura de carpetas existe y los escenarios están redactados; falta
traducirlos a `.feature` ejecutables e instalar `pytest-bdd`. El número exacto de historias del
Product Backlog está por confirmar, y de él depende el cálculo de cobertura del 90 %.
