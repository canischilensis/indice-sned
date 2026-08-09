# Manual de instalación

Identificador del documento: **MI-SNED-01**

Procedimiento para levantar el sistema completo desde cero en una máquina limpia: base de datos,
servicio e interfaz. Está escrito para Windows con PowerShell, que es el entorno verificado, con
las equivalencias para Linux y macOS al final.

Cada paso incluye **cómo saber que salió bien**. Un paso sin verificación es un paso que se
descubre roto tres pasos más tarde.

---

## 1. Requisitos previos

| Componente | Versión | Verificar con |
|-----------|---------|---------------|
| Python | 3.11 o 3.12 | `python --version` |
| PostgreSQL | 16 | `psql --version` |
| Node.js | 18 o superior | `node --version` |
| Git | cualquiera reciente | `git --version` |

**Advertencia sobre versiones:** los artefactos de modelo se serializaron con **scikit-learn
1.6.1**, mientras que `requirements.txt` fija **1.5.2** para el entorno de servicio. Al cargarlos
verá `InconsistentVersionWarning`: el sistema funciona, pero es una desalineación real y está
declarada como deuda. No actualice las versiones sin reentrenar.

---

## 2. Instalar PostgreSQL

```powershell
winget install PostgreSQL.PostgreSQL.16
```

Durante la instalación se pide una contraseña para el superusuario `postgres`. **Anótela**: se
usa en el paso siguiente y no hay forma cómoda de recuperarla.

Cierre PowerShell y ábralo de nuevo para que la variable de entorno `PATH` incluya las
herramientas de PostgreSQL.

**Verificación:**

```powershell
psql --version
```

Debe imprimir `psql (PostgreSQL) 16.x`. Si dice que el comando no existe, la ventana de PowerShell
es anterior a la instalación: ciérrela y abra otra.

---

## 3. Clonar el repositorio y preparar el entorno de Python

```powershell
git clone <url-del-repositorio> indice-sned
cd indice-sned

python -m venv env
.\env\Scripts\Activate.ps1
pip install -r requirements.txt
```

Si PowerShell bloquea la activación del entorno con un error de directiva de ejecución:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

y vuelva a intentar. Es una autorización por usuario, no un cambio de seguridad del sistema.

**No confundir dos nombres parecidos:** `env\` es el entorno virtual de Python; `.env` es el
archivo de configuración. Son cosas distintas.

**Verificación:** el prompt debe mostrar el prefijo `(env)`.

---

## 4. Crear la base de datos y el usuario de aplicación

```powershell
psql -U postgres
```

Introduzca la contraseña del superusuario. Ya dentro de `psql`:

```sql
CREATE USER sned WITH PASSWORD 'ELIJA-UNA-CLAVE';
CREATE DATABASE indice_sned OWNER sned;
\q
```

**Verificación:**

```powershell
psql -U sned -d indice_sned -c "SELECT current_database();"
```

Debe responder `indice_sned`.

---

## 5. Configurar el archivo de entorno

```powershell
Copy-Item .env.example .env
```

Edite `.env` y confirme estas dos líneas:

```
DATABASE_URL=postgresql+psycopg://sned:ELIJA-UNA-CLAVE@localhost:5432/indice_sned
REPOSITORIO_DATOS=postgres
```

> **La clave la elige usted.** Reemplace `ELIJA-UNA-CLAVE` por un valor propio, el mismo en los
> dos lugares. Este repositorio es publico: no escriba credenciales reales en la documentacion ni
> en ningun archivo versionado. La unica copia de la clave vive en su `.env`, que esta ignorado.

El controlador es `psycopg` sin sufijo de versión: corresponde a la tercera generación del
adaptador, que es la que instala el archivo de requisitos.

**Verificación:**

```powershell
Get-Content .env | Select-String DATABASE_URL
```

---

## 6. Crear el esquema

```powershell
python scripts\inicializar_bd.py
```

El script ejecuta en orden: los cuatro espacios de nombres, las 16 tablas de catálogo con sus
semillas, las 6 entidades débiles, las 8 tablas de registro de modelos, las 8 de operación, y
finalmente las vistas.

Entre las tablas y las vistas **valida** que el catálogo de ponderaciones en archivo coincida con
la tabla. Si divergen, aborta con un mensaje explícito. En ese caso el que se corrige es el
archivo: el DDL es la fuente de verdad.

**Verificación:** el script termina con `Base de datos inicializada.`

```powershell
psql -U sned -d indice_sned -c "SELECT count(*) FROM information_schema.tables WHERE table_schema IN ('core','hechos','ml','app');"
```

Debe responder **38**.

---

## 7. Cargar los datos

Requiere que el directorio `data/processed/` contenga los archivos columnares. No se versionan por
tamaño: obténgalos del respaldo del proyecto o regenérelos con la ingesta.

```powershell
python scripts\cargar_bd.py
```

La carga es idempotente: copia a tabla temporal e inserta resolviendo conflictos sobre la llave.
Reejecutarla sobre una base ya poblada no duplica filas ni falla.

**Verificación:** el script imprime el conteo por tabla. El total debe rondar las 838.000 filas.

---

## 8. Verificar que el cálculo del índice es correcto

Este es el paso que confirma que la carga fue fiel al origen. Si falla, no siga adelante.

```powershell
psql -U sned -d indice_sned
```

```sql
SELECT max(abs(v.indicer_calculado - r.indicer)) AS discrepancia_maxima,
       avg(abs(v.indicer_calculado - r.indicer)) AS discrepancia_media,
       count(*)                                  AS filas_comparadas
FROM   hechos.v_indicer_reconstruido v
JOIN   hechos.sned_resultado r USING (rbd, periodo_id)
WHERE  v.n_factores = 6;
```

**Resultado esperado:**

| Métrica | Valor |
|---------|-------|
| Discrepancia máxima | ≈ 0,0006 |
| Discrepancia media | ≈ 0,00025 |
| Filas comparadas | ≈ 44.679 |

Una discrepancia mayor que 0,001 indica un problema de precisión en la carga.

---

## 9. Levantar el servicio

Terminal 1, con el entorno activo:

```powershell
cd C:\ruta\a\indice-sned
.\env\Scripts\Activate.ps1
$env:REPOSITORIO_DATOS = "postgres"
uvicorn q3_servicio.main:app --reload --app-dir quanta --port 8000
```

**El parámetro `--app-dir quanta` es obligatorio.** Los cuantos son paquetes hermanos bajo esa
carpeta y se importan por su nombre corto. Sin ese parámetro el arranque falla con
`ModuleNotFoundError: No module named 'q3_servicio'`.

**Verificación:** abra `http://127.0.0.1:8000/docs`. Debe listar las rutas de autenticación,
establecimientos, predicción, explicabilidad y salud.

Y la comprobación de composición:

```
http://127.0.0.1:8000/api/v1/salud/composicion
```

Debe informar una cobertura cercana a 0,814. Si informa 0,0, el servicio no está leyendo la base:
revise `REPOSITORIO_DATOS` y la cadena de conexión.

---

## 10. Levantar la interfaz

Terminal 2:

```powershell
cd C:\ruta\a\indice-sned\quanta\q4_cliente
npm install
npm run dev
```

Si al instalar aparece un aviso de que un paquete tiene guiones de instalación no aprobados:

```powershell
npm approve-scripts esbuild
npm rebuild esbuild
```

**Verificación:** la consola muestra `Local: http://localhost:5173/`. Abra esa dirección.

---

## 11. Entrar al sistema

| Usuario | Clave | Rol | Alcance |
|---------|-------|-----|---------|
| `sostenedor.demo` | `demo` | Sostenedor | Tres establecimientos |
| `directora.demo` | `demo` | Directivo | Un establecimiento |
| `auditor.demo` | `demo` | Auditor | Todos, sin restricción de jurisdicción |

**Nota sobre el perfil de auditoría:** puede consultar cualquier establecimiento por su
identificador, pero su lista de jurisdicción está vacía, de modo que el selector de la barra
aparece sin opciones. Para recorrer la interfaz use el perfil de sostenedor.

Si aparece el mensaje `RBD … sin registros en la base analítica`, el identificador configurado en
el directorio de demostración no está en el conjunto depurado. Es el comportamiento correcto del
sistema; corrija el identificador en `quanta/q3_servicio/core/seguridad.py` por uno presente en
la base.

---

## 12. Ejecutar la suite de pruebas

```powershell
pytest                          # la suite completa
pytest -m paridad               # solo paridad: no necesita base ni artefactos
pytest -m "not requiere_bd"     # omitir lo que exige PostgreSQL
pytest tests\unitarias          # solo unitarias
```

**Verificación:** `pytest -m paridad` debe informar cero divergencias.

---

## 13. Modo sin base de datos

El sistema conserva el adaptador de archivos columnares. Para operar sin PostgreSQL:

```powershell
$env:REPOSITORIO_DATOS = "parquet"
uvicorn q3_servicio.main:app --reload --app-dir quanta --port 8000
```

Requiere `data/processed/` y `models/registry/`. Sirve para demostrar el sistema sin
infraestructura y como modo de contingencia si la base no está disponible.

---

## 14. Equivalencias en Linux y macOS

| Paso | Windows | Linux / macOS |
|------|---------|---------------|
| Activar el entorno | `.\env\Scripts\Activate.ps1` | `source env/bin/activate` |
| Copiar la configuración | `Copy-Item .env.example .env` | `cp .env.example .env` |
| Fijar la variable | `$env:REPOSITORIO_DATOS = "postgres"` | `export REPOSITORIO_DATOS=postgres` |
| Separador de rutas | `scripts\cargar_bd.py` | `scripts/cargar_bd.py` |

El resto es idéntico.

---

## 15. Problemas frecuentes

| Síntoma | Causa | Solución |
|---------|-------|----------|
| `No module named 'q3_servicio'` | Falta `--app-dir quanta` | Use el comando del paso 9 |
| `node` o `npm` no se reconocen tras instalar | La ventana es anterior a la instalación | Cierre y abra PowerShell |
| `Activate.ps1 no se puede cargar` | Directiva de ejecución | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` |
| `password authentication failed` | Contraseña del superusuario | Es la que fijó al instalar PostgreSQL |
| `no se pudo determinar el tipo del parámetro` | Consulta con parámetro nulo sin conversión de tipo | Ya corregido en el adaptador; si reaparece, falta una conversión explícita |
| Cobertura 0,0 en la comprobación de composición | El servicio no lee la base | Revise `REPOSITORIO_DATOS` y la cadena de conexión |
| `Model type not yet supported` al pedir explicación | El explicador recibió el envoltorio de carga diferida | Ya corregido: la construcción del explicador materializa el artefacto |
| La primera predicción tarda mucho | Carga diferida de artefactos | Es el comportamiento diseñado; las siguientes son rápidas |
