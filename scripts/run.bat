@ECHO OFF
setlocal
set PYTHONPATH=%cd%
python pyuiw/__main__.py -ni -nb f:/light_git/MAvatar/pose_editor/ui/window.ui
endlocal
