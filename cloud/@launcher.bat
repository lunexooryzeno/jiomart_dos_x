@echo off
title Python Script Launcher

REM ---- Update Python path if required ----
REM Example: set PYTHON=C:\Python311\python.exe
set PYTHON=python

REM ---- Script Paths Autonomous Agent----
set SCRIPT1=cloud_autonomous_agent.py --idx 1
set SCRIPT2=cloud_autonomous_agent.py --idx 2
set SCRIPT3=cloud_autonomous_agent.py --idx 3
set SCRIPT4=cloud_autonomous_agent.py --idx 4
set SCRIPT5=cloud_autonomous_agent.py --idx 5
set SCRIPT6=cloud_autonomous_agent.py --idx 6
set SCRIPT7=cloud_autonomous_agent.py --idx 7
set SCRIPT8=cloud_autonomous_agent.py --idx 8
set SCRIPT9=cloud_autonomous_agent.py --idx 9
set SCRIPT10=cloud_autonomous_agent.py --idx 10

REM ---- Script Paths Mitm Agent----
set SCRIPT11=mitm_agent.py --idx 1
set SCRIPT12=mitm_agent.py --idx 2
set SCRIPT13=mitm_agent.py --idx 3
set SCRIPT14=mitm_agent.py --idx 4
set SCRIPT15=mitm_agent.py --idx 5
set SCRIPT16=mitm_agent.py --idx 6
set SCRIPT17=mitm_agent.py --idx 7
set SCRIPT18=mitm_agent.py --idx 8
set SCRIPT19=mitm_agent.py --idx 9
set SCRIPT20=mitm_agent.py --idx 10

REM ---- Script Paths Set Addresses Agent----
set SCRIPT21=cloud_set_addresses.py

REM ---- Launch each script in a new CMD window ----
start "Script 1" cmd /k "%PYTHON% %SCRIPT1%"
start "Script 2" cmd /k "%PYTHON% %SCRIPT2%"
start "Script 3" cmd /k "%PYTHON% %SCRIPT3%"
start "Script 4" cmd /k "%PYTHON% %SCRIPT4%"
start "Script 5" cmd /k "%PYTHON% %SCRIPT5%"
start "Script 6" cmd /k "%PYTHON% %SCRIPT6%"
start "Script 7" cmd /k "%PYTHON% %SCRIPT7%"
start "Script 8" cmd /k "%PYTHON% %SCRIPT8%"
start "Script 9" cmd /k "%PYTHON% %SCRIPT9%"
start "Script 10" cmd /k "%PYTHON% %SCRIPT10%"


start "Script 11" cmd /k "%PYTHON% %SCRIPT11%"
start "Script 12" cmd /k "%PYTHON% %SCRIPT12%"
start "Script 13" cmd /k "%PYTHON% %SCRIPT13%"
start "Script 14" cmd /k "%PYTHON% %SCRIPT14%"
start "Script 15" cmd /k "%PYTHON% %SCRIPT15%"
start "Script 16" cmd /k "%PYTHON% %SCRIPT16%"
start "Script 17" cmd /k "%PYTHON% %SCRIPT17%"
start "Script 18" cmd /k "%PYTHON% %SCRIPT18%"
start "Script 19" cmd /k "%PYTHON% %SCRIPT19%"
start "Script 20" cmd /k "%PYTHON% %SCRIPT20%"

start "Script 21" cmd /k "%PYTHON% %SCRIPT21%"




exit
