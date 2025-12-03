@echo off
setlocal enabledelayedexpansion

REM Define the color variables
set backgroundColor=#4f43ae
set foregroundColor=#877dcd
set highlightColor=#665cb2
set altColor=#2b1810
set whiteColor=#f7f5fb
set darkGrey=#1a1a1a
set mediumGrey=#4a4a4a

:colorChoice
echo Choose a color:
echo 1. Background Color (Deep Purple)
echo 2. Foreground Color (Light Purple)
echo 3. Highlight Color (Medium Purple)
echo 4. Alternative Color (Dark Brown)
echo 5. White
echo 6. Dark Grey
echo 7. Medium Grey
set /p colorChoice="Enter choice (1-7): "

if "%colorChoice%"=="1" (
    set targetColor=%backgroundColor%
) else if "%colorChoice%"=="2" (
    set targetColor=%foregroundColor%
) else if "%colorChoice%"=="3" (
    set targetColor=%highlightColor%
) else if "%colorChoice%"=="4" (
    set targetColor=%altColor%
) else if "%colorChoice%"=="5" (
    set targetColor=%whiteColor%
) else if "%colorChoice%"=="6" (
    set targetColor=%darkGrey%
) else if "%colorChoice%"=="7" (
    set targetColor=%mediumGrey%
) else (
    echo Invalid choice. Please try again.
    goto colorChoice
)

:methodChoice
echo.
echo Choose coloring method:
echo 1. Replace lime green only
echo 2. Recolor entire image
set /p method="Enter choice (1-2): "

REM Create a subfolder named "converted" if it doesn't exist
if not exist "converted" mkdir "converted"

REM Loop through all image files
for %%f in (*.png *.jpg *.jpeg *.bmp) do (
    echo Processing %%f ...
    
    if "%method%"=="1" (
        REM Replace lime green only
        magick convert "%%f" ^
            -fuzz 20%% ^
            -fill "!targetColor!" ^
            -opaque "#99a659" "converted\%%f"
    ) else if "%method%"=="2" (
        REM Colorize entire image
        magick convert "%%f" ^
            -fill "!targetColor!" ^
            -colorize 100 "converted\%%f"
    ) else (
        echo Invalid method choice. Exiting...
        goto :eof
    )
    
    echo Processed: converted\%%f
)

echo Done! Converted files are saved in the "converted" folder.
pause