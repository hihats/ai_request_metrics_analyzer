FROM python:3.9-slim
ENV LANG=ja_JP.UTF-8
ENV LC_ALL=ja_JP.UTF-8
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    wget \
    unzip \
    git \
    curl \
    file \
    sudo \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを設定
WORKDIR /app


# ボリュームを定義
VOLUME ["/app"]

# 必要なファイルをコピー
COPY requirements.txt .

# Pythonの依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# Pythonスクリプトをコピー
COPY *.py .

# デフォルトコマンド（エントリーポイントを上書き可能にする）
ENTRYPOINT ["python"]
CMD ["extract_acceptance_rate.py", "--help"]
