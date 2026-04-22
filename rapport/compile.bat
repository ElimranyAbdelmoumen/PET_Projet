@echo off
echo ============================================
echo  Compilation LaTeX via Docker
echo ============================================

set DIR=%~dp0

docker run --rm ^
  -v "%DIR%:/workspace" ^
  texlive/texlive:latest ^
  bash -c "cd /workspace && pdflatex -interaction=nonstopmode rapport.tex && pdflatex -interaction=nonstopmode rapport.tex"

if %errorlevel% == 0 (
    echo.
    echo  PDF genere : rapport\rapport.pdf
) else (
    echo.
    echo  ERREUR : verifiez les logs ci-dessus.
)

pause
