@echo off

cd /d "%~dp0\webforge-ai-desktop"

echo.
echo [1/3] Generator
python -m pytest tests/test_generator_smoke.py -v

echo.
echo [2/3] Pipeline
python -m pytest tests/test_pipeline_smoke.py -v

echo.
echo [3/3] FastAPI Routes
python -m pytest tests/test_routes_font_generator.py -v

echo.
echo ==========================
echo ALL TESTS FINISHED
echo ==========================

pause