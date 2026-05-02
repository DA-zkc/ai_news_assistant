@echo off
cd /d C:\Users\ZHENG\ai_news_assistant

mkdir modules utils tests 2>nul

type nul > modules\__init__.py
type nul > modules\fetcher.py
type nul > modules\filter.py
type nul > modules\fact_opinion.py
type nul > modules\core_event.py
type nul > modules\merger.py
type nul > modules\output.py

type nul > utils\__init__.py
type nul > utils\api_clients.py
type nul > utils\scoring.py
type nul > utils\logger.py

type nul > tests\__init__.py

type nul > main.py
type nul > requirements.txt
type nul > .env
type nul > .gitignore

echo 目录结构创建完成！
pause