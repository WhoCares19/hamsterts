@echo off
rem Change directory to the PARENT of the 'Arrows' package
cd /d "C:\Users\VvV\Desktop\python code\Random Generator Map\Randomizer test"

:run
echo Starting app...
rem Run main_window.py as a module within the 'Arrows' package
"C:\Users\VvV\AppData\Local\Programs\Python\Python312\python.exe" main.py

:loop
set /p action=Type "restart" to run again, "clear" to clear screen, or "exit" to quit: 

if /i "%action%"=="restart" goto run
if /i "%action%"=="cls" (
    cls
    goto loop
)
if /i "%action%"=="exit" exit

goto loop