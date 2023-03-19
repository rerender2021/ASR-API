pyinstaller --noconfirm --clean .\config\main.spec

Xcopy /Y /E /I .\venv\Lib\site-packages\vosk .\dist\ASR-API\vosk /EXCLUDE:.\exclude.txt
Xcopy /Y /E /I .\venv\Lib\site-packages\numpy\distutils .\dist\ASR-API\numpy\distutils /EXCLUDE:.\exclude.txt
Xcopy /Y /E /I .\model .\dist\ASR-API\model 

copy /Y ".\script\run.bat" ".\dist\ASR-API\run.bat"

