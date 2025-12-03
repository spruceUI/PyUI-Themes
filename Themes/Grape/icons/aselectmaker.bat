@echo off
setlocal EnableDelayedExpansion

:: Get the parent directory for config access
pushd ..

:: Use findstr to extract font from config.json
for /f "tokens=2 delims=:," %%a in ('findstr "\"font\":" config.json') do (
    set "fontfile=%%~a"
    :: Remove quotes and whitespace
    set "fontfile=!fontfile:"=!"
    set "fontfile=!fontfile: =!"
)

:: Hardcode the font color
set "fontcolor=#f7f5fb"

:: Get the absolute path to the parent directory and escape backslashes
set "parentdir=%CD%"
set "parentdir=%parentdir:\=/%"

:: Return to icons directory
popd

:: Create generated directory if it doesn't exist
if not exist "generated" mkdir "generated"

echo Font file: "!parentdir!/!fontfile!"
echo Font color: "!fontcolor!"

:: Process each PNG file
for %%f in (*.png) do (
    :: Get filename without extension and convert to uppercase
    set "name=%%~nf"
    set "name=!name: =!"
    for %%i in ("!name!") do set "name=%%~ni"
    call :ToUpper name

    echo Processing: %%f with font: "!parentdir!/!fontfile!"
    
    :: Use ImageMagick to add text
    magick "%%f" ^
        -gravity south ^
        -background none ^
        -splice 0x20 ^
        -font "!parentdir!/!fontfile!" ^
        -pointsize 17 ^
        -fill "!fontcolor!" ^
        -stroke "!fontcolor!" ^
        -strokewidth 0.2 ^
        -gravity south ^
        -annotate +0+2 "!name!" ^
        "generated\%%~nf.png"
)

echo Processing complete!
pause
goto :eof

:ToUpper
set %1=!%1:a=A!
set %1=!%1:b=B!
set %1=!%1:c=C!
set %1=!%1:d=D!
set %1=!%1:e=E!
set %1=!%1:f=F!
set %1=!%1:g=G!
set %1=!%1:h=H!
set %1=!%1:i=I!
set %1=!%1:j=J!
set %1=!%1:k=K!
set %1=!%1:l=L!
set %1=!%1:m=M!
set %1=!%1:n=N!
set %1=!%1:o=O!
set %1=!%1:p=P!
set %1=!%1:q=Q!
set %1=!%1:r=R!
set %1=!%1:s=S!
set %1=!%1:t=T!
set %1=!%1:u=U!
set %1=!%1:v=V!
set %1=!%1:w=W!
set %1=!%1:x=X!
set %1=!%1:y=Y!
set %1=!%1:z=Z!
goto :eof