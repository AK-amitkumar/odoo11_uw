@title �����Ʊ���ϵͳ��������
@color 0A

@echo off
@echo =====================================
@echo.
@echo        �����Ʊ���ϵͳ��������
@echo               ver 1.3.4
@echo.
@echo.
@echo  ��������Ϊ�˷����״�ʹ�ø�����߿���
@echo  ���쿴��Ч����д�������Ǳ�ʾ�����Ʊ�
@echo  �Ĺ��ܽ����ڴˡ�
@echo.
@echo.
@echo  !!!!!  ����ϸ�Ķ���!!!!!
@echo  �������Ʊ���ϵͳ��Ҫʹ��˵��.txt��
@echo  ��
@echo  �������Ʊ���ϵͳ���ʹ���ֲ�.txt��
@echo  �����ļ�����ѧϰ��ϸ��ʹ�÷�ʽ��
@echo.
@echo -------------------------------------
@echo.
@echo   ���ߣ��������������
@echo   QQ��  360026606
@echo   ΢�ţ�360026606
@echo.
@echo.
@echo.
@echo ���������ʼ����...
@pause > NUL

start notepad.exe �����Ʊ���ϵͳ��Ҫʹ��˵��.txt

start notepad.exe �����Ʊ���ϵͳ���ʹ���ֲ�.txt

cd cfprint

start cfprint.exe
start iexplore.exe %CD%\printtest.html

cd ..