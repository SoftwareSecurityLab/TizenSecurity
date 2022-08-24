cd tools\ide\bin
call tizen.bat build-native -a x86 -c gcc -C Debug -- C:\Users\Hossein\Documents\Tizen-workspace\test001
call tizen.bat package -t tpk -- C:\Users\Hossein\Documents\Tizen-workspace\test001\Debug
call tizen.bat install -n org.example.test001-1.0.0-x86.tpk -- C:\Users\Hossein\Documents\Tizen-workspace\test001\Debug
cd ../../../