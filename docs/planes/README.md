# Planes de prueba

Tres planes redactados siguiendo **ISO/IEC/IEEE 29119**, que es la norma vigente.

Conviene ser preciso con la relación entre ambas normas, porque es una pregunta previsible en
una defensa: **ISO/IEC/IEEE 29119-3 reemplazó formalmente a IEEE 829 en 2013**. No están
vigentes en paralelo. Se cita 829 como antecedente por dos razones: su estructura documental
—identificador, alcance, elementos a probar, criterios de aprobación y suspensión, entregables
y riesgos— se conserva casi íntegra en 29119-3, y sigue siendo la referencia que se enseña.

De 29119 viene además lo que 829 no tenía: el proceso que produce el documento y las técnicas
de diseño de casos —partición de equivalencia, valores límite, prueba de contrato— que aparecen
en el plan de integración.

| Plan | Identificador | Estado |
|------|---------------|--------|
| [Maestro](PLAN_PRUEBAS.md) | PPM-SNED-01 | Vigente |
| [Integración](PLAN_INTEGRACION.md) | PPI-SNED-01 | 5 de 5 integraciones cubiertas |
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
pytest                          # las 61 pruebas
pytest tests/unitarias          # solo unitarias
pytest -m paridad               # solo paridad: no necesita base ni artefactos
pytest -m "not requiere_bd"     # omitir lo que exige PostgreSQL
```
