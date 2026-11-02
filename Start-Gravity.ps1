$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$taskDeps = Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) 'work/m4-deps'
if (Test-Path -LiteralPath '.venv/Scripts/python.exe') {
    & '.venv/Scripts/python.exe' m4_serve.py streamlit_app.py 8507
} else {
    if (Test-Path -LiteralPath $taskDeps) { $env:PYTHONPATH = $taskDeps + ';' + $env:PYTHONPATH }
    python m4_serve.py streamlit_app.py 8507
}
