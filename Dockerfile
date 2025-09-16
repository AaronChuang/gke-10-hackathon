FROM python:3.11-slim

# 設定工作目錄
WORKDIR /workspace

# 複製依賴檔案並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製整個專案到容器中
COPY . .

# 設定 PYTHONPATH 讓 Python 能找到 app 模組
ENV PYTHONPATH=/workspace