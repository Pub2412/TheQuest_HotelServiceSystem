@echo off
cd /d "%~dp0"

rem Add the standard Android SDK tools for this launcher process.
if not defined ANDROID_SDK_ROOT if defined ANDROID_HOME set "ANDROID_SDK_ROOT=%ANDROID_HOME%"
if not defined ANDROID_SDK_ROOT if exist "%LOCALAPPDATA%\Android\Sdk" set "ANDROID_SDK_ROOT=%LOCALAPPDATA%\Android\Sdk"
if defined ANDROID_SDK_ROOT if exist "%ANDROID_SDK_ROOT%\platform-tools" set "PATH=%ANDROID_SDK_ROOT%\platform-tools;%PATH%"
if defined ANDROID_SDK_ROOT if exist "%ANDROID_SDK_ROOT%\cmdline-tools\latest\bin" set "PATH=%ANDROID_SDK_ROOT%\cmdline-tools\latest\bin;%PATH%"

rem Add Gradle from GRADLE_HOME or the common C:\Gradle installation folder.
if defined GRADLE_HOME if exist "%GRADLE_HOME%\bin" set "PATH=%GRADLE_HOME%\bin;%PATH%"
for /d %%G in ("C:\Gradle\gradle-*") do if exist "%%~G\bin\gradle.bat" set "PATH=%%~G\bin;%PATH%"

where adb >nul 2>&1
if errorlevel 1 echo WARNING: adb was not found. Install Android SDK Platform-Tools.
where gradle >nul 2>&1
if errorlevel 1 echo WARNING: gradle was not found. Install Gradle or set GRADLE_HOME.

python android_launcher.py
