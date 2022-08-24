cd tools\emulator\bin
call em-cli.bat launch -n M-6.5-x86
timeout /t 30 /nobreak
cd ..
cd ..
sdb.exe forward tcp:2727 tcp:2323
echo "sdb forward tcp 2727 -> 2323"
sdb.exe forward tcp:2323 tcp:2727
echo "sdb forward tcp:2323 -> 2727"
sdb.exe root on