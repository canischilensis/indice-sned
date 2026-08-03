# Planes de prueba

Tres planes, redactados siguiendo **IEEE 829** e **ISO/IEC/IEEE 29119** en conjunto y no como
alternativas: IEEE 829 fija la estructura del documento —identificador, alcance, elementos a
probar, criterios de aprobación y suspensión, entregables y riesgos—; ISO 29119 fija el proceso
que lo produce —estrategia, gestión y diseño de casos por técnica—.

Declararlas juntas evita la pregunta obvia en una defensa: por qué se eligió una y se descartó
la otra.

| Plan | Identificador | Estado |
|------|---------------|--------|
| [Integración](PLAN_INTEGRACION.md) | PPI-SNED-01 | 4 de 5 integraciones cubiertas |
| [Aceptación](PLAN_ACEPTACION.md) | PPA-SNED-01 | Escenarios redactados, sin implementar |
| [Compatibilidad de navegadores](PLAN_COMPATIBILIDAD.md) | PPC-SNED-01 | Sin implementar |

## Estructura de las pruebas

Híbrida: **por tipo en el primer nivel, por cuanto adentro**. Refleja la nomenclatura que exige
la tesis y conserva la trazabilidad al cuanto.

```
tests/
├── unitarias/
│   ├── compartido/   Specification: el mecanismo componible
│   ├── q1/           reglas de cuarentena y esqueleto de ingesta
│   ├── q2/           contrato del índice, Decorator, Builder, Proxy, Factory
│   └── q3/           Repository con adaptadores y reglas de alerta
├── integracion/
│   ├── q1/           pipeline de calidad extremo a extremo
│   └── q3/           API y control de acceso
├── aceptacion/       Gherkin, pendiente
├── compatibilidad/   Playwright, pendiente
├── arquitectura/     fronteras de cuantos ejecutables
└── paridad/          los dos adaptadores del mismo puerto
```

## Ejecutar

```bash
pytest                          # las 57
pytest tests/unitarias          # solo unitarias
pytest -m paridad               # solo paridad: no necesita base ni artefactos
pytest -m "not requiere_bd"     # omitir lo que exige PostgreSQL
```
