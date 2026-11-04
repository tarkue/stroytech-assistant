#!/bin/zsh
# Local-only launch; keeps all installed packages inside this project.
set -eu
cd -- "${0:A:h}"
project_python="${STROYTECH_PYTHON:-python3}"
if ! command -v "$project_python" >/dev/null 2>&1; then
  print -u2 'Не найден Python 3. Установите Python 3.12–3.14 или задайте STROYTECH_PYTHON.'
  exit 1
fi
if ! "$project_python" -c 'import sys; assert (3,12) <= sys.version_info[:2] <= (3,14)' 2>/dev/null; then
  print -u2 'Требуется Python 3.12–3.14. Проверенная версия: 3.14.4.'
  exit 1
fi
if [[ ! -x .venv/bin/python ]]; then
  "$project_python" -m venv .venv
fi
if ! .venv/bin/python -c 'import sys; assert (3,12) <= sys.version_info[:2] <= (3,14)' 2>/dev/null; then
  print -u2 'Существующая .venv несовместима. Переименуйте ее и повторите запуск.'
  exit 1
fi
requirements_hash="$(.venv/bin/python -c 'import hashlib; print(hashlib.sha256(open("requirements.txt","rb").read()).hexdigest())')"
installed_hash=''
if [[ -f .venv/.requirements.sha256 ]]; then
  installed_hash="$(<.venv/.requirements.sha256)"
fi
if [[ "$requirements_hash" != "$installed_hash" ]] || ! .venv/bin/python -c 'import streamlit; assert streamlit.__version__ == "1.66.1"' 2>/dev/null; then
  print 'Установка зависимостей в .venv (при первом запуске нужен интернет)…'
  .venv/bin/python -m pip install --disable-pip-version-check -r requirements.txt
  print -r -- "$requirements_hash" > .venv/.requirements.sha256
fi
print 'СтройТех: http://127.0.0.1:8501 — для остановки нажмите Ctrl+C в этом окне.'
exec .venv/bin/python -m streamlit run app.py --server.address=127.0.0.1 --server.port=8501 --server.headless="${STROYTECH_HEADLESS:-false}" --browser.gatherUsageStats=false
