@echo off

SET /a repeats=1
SET text=I'm called

:loop
IF NOT "%1"=="" (
    IF "%1"=="-r" (
		SET /a repeats=%2
		ECHO repeats = %2
        SHIFT
    )
    IF "%1"=="-t" (
		SET text=%2
		ECHO text = %2
        SHIFT
    )
	IF "%1"=="--clear" (
		ECHO "Clearing the file..."
        break>%HOMEPATH%\simple.txt
    )
    SHIFT
    GOTO :loop
)

SET /p DUMMY=Press enter to start writing to the file

for /l %%X in (1,1,%repeats%) do (
  ECHO %text% >> %HOMEPATH%\simple.txt
)

ECHO File content:
ECHO.
TYPE %HOMEPATH%\simple.txt