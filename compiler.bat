@echo off
setlocal enabledelayedexpansion

:: Kullanıcıdan Python dosyası alınır
set /p pyfile=Python dosyasinin adini (ornek: program.py) girin: 

if not exist "!pyfile!" (
    echo Dosya bulunamadi!
    pause
    exit /b
)

:: Kullanıcıya Cython mi Nuitka mi sorulur
echo Hangi yontemi kullanmak istiyorsunuz?
echo 1 - Nuitka (Onerilir)
echo 2 - Cython
set /p method=Seciminizi girin (1 veya 2): 

:: Icon dosyasi alinir
set /p iconfile=Exe icin icon dosyasini girin (ornek: icon.ico): 

if not exist "!iconfile!" (
    echo Icon dosyasi bulunamadi!
    pause
    exit /b
)

if "!method!"=="1" (
    :: Nuitka ile derleme
    echo Nuitka ile derleniyor...
    nuitka --onefile --windows-icon-from-ico="!iconfile!" --windows-console-mode=disable --enable-plugin=tk-inter --msvc=latest --standalone "!pyfile!"
    echo Derleme tamamlandi.
) else if "!method!"=="2" (
    :: Cython ile derleme
    echo Cython ile derleniyor...
    
    :: Python dosyasini .c ye cevirmek
    cython --embed -o program.c "!pyfile!"

    :: C dosyasini derlemek
    gcc -o program.exe program.c -I"%PYTHONHOME%\include" -L"%PYTHONHOME%\libs" -lpython%PYTHON_VERSION% -mwindows -Wno-unused-result -Wno-format -Wno-implicit-function-declaration -O2 -s -Wno-unused-variable -Wno-int-conversion -Wno-return-type -Wno-incompatible-pointer-types

    :: Ikon eklemek icin ek bir resource script gerekebilir. Bu kisim basit tutuldu.
    echo Derleme tamamlandi. program.exe olusturuldu.
) else (
    echo Hatali secim yapildi!
    pause
    exit /b
)

pause
exit /b