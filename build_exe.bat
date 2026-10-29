@echo off
title Build ThanosCam Executable
echo ======================================================
echo       BUILDING STANDALONE THANOS-CAM.EXE
echo ======================================================
echo.
python -m PyInstaller --onefile --name "ThanosCam" --add-data "selfie_segmenter.tflite;." --add-data "hand_landmarker.task;." --collect-all mediapipe --collect-all pyvirtualcam main.py
echo.
if exist "dist\ThanosCam.exe" (
    echo ======================================================
    echo  BASARILI! Executable hazir: dist\ThanosCam.exe
    echo ======================================================
) else (
    echo Bir hata olustu.
)
pause
