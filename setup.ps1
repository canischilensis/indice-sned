<#
    indice-sned — bootstrap para Windows (PowerShell)

    Uso:  .\setup.ps1

    Si PowerShell bloquea la ejecucion ("la ejecucion de scripts esta deshabilitada"),
    habilitala una sola vez para tu usuario:
        Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
    o solo para esta ventana:
        Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#>

$ErrorActionPreference = "Stop"
Write-Host "== indice-sned :: preparacion del entorno ==" -ForegroundColor Cyan

# --- 1. Verificar Python ---
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python no esta en el PATH. Instala Python 3.11 o 3.12 desde python.org y reintenta."
}
Write-Host "Python detectado: $(python --version)"

# --- 2. Entorno virtual: reutiliza el que exista (env o .venv) ---
$VENV = $null
foreach ($candidato in @("env", ".venv", "venv")) {
    if (Test-Path "$candidato\Scripts\python.exe") { $VENV = $candidato; break }
}
if ($VENV) {
    Write-Host "Entorno virtual existente detectado: $VENV\  (se reutiliza)" -ForegroundColor Yellow
} else {
    $VENV = "env"
    Write-Host "Creando entorno virtual $VENV\ ..."
    python -m venv $VENV
}
$PY = ".\$VENV\Scripts\python.exe"

# --- 3. Dependencias ---
Write-Host "Instalando dependencias (puede tardar varios minutos)..."
& $PY -m pip install --upgrade pip
& $PY -m pip install -r requirements-dev.txt

# --- 4. Kernel de Jupyter ligado al entorno ---
Write-Host "Registrando kernel de Jupyter 'indice-sned' ..."
& $PY -m ipykernel install --user --name indice-sned --display-name "indice-sned"

# --- 5. Archivo de configuracion ---
#  OJO: 'env\' es el ENTORNO VIRTUAL (carpeta). '.env' es el archivo de CONFIGURACION.
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Se creo .env desde .env.example. Revisa JWT_SECRET_KEY y POSTGRES_PASSWORD." -ForegroundColor Yellow
}

# --- 6. Frontend (opcional) ---
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "Instalando dependencias del cuanto 4 (React)..."
    Push-Location quanta\q4_cliente
    npm install
    Pop-Location
} else {
    Write-Host "npm no encontrado: omito el frontend. Instala Node 20+ si lo necesitas." -ForegroundColor Yellow
}

# --- 7. Compuerta de arquitectura ---
Write-Host "Verificando fronteras de cuantos..."
& $PY scripts\verificar_arquitectura.py

Write-Host ""
Write-Host "== Entorno listo ==" -ForegroundColor Green
Write-Host "Activar:      .\$VENV\Scripts\Activate.ps1"
Write-Host "Levantar API: python -m uvicorn q3_servicio.main:app --reload --app-dir quanta --port 8000"
Write-Host "Levantar web: cd quanta\q4_cliente ; npm run dev"
