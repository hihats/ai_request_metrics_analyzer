# AI Code Editor メトリクス分析ツール

GitHub CopilotとCursor Admin APIのメトリクスデータを分析し、AI コード補完の採用率や使用統計を取得・分析するためのPythonツール集です。

## 📋 概要

このプロジェクトには以下のツールが含まれています：

1. **GitHub Copilot メトリクス分析** - GitHub Copilotの使用データから採用率を計算
2. **Cursor Admin API メトリクス取得** - Cursor Admin APIからチーム使用統計を取得
3. **設定管理** - API認証情報とツール設定の管理

## 🚀 クイックスタート

### 前提条件

- Python 3.8以上
- pip（Pythonパッケージマネージャー）
- Docker（オプション）

### インストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd copilot

# 依存関係をインストール
pip install -r requirements.txt
```

## 🛠️ ツール詳細

### 1. GitHub Copilot メトリクス分析

GitHub Copilotの使用メトリクスJSONファイルを解析し、採用率統計を生成します。

#### 使用方法

```bash
# デフォルトファイル（~/Downloads/copilot_metrics.json）を使用
python extract_copilot_acceptance_rate.py

# 特定のファイルを指定
python extract_copilot_acceptance_rate.py path/to/copilot_metrics.json

# ヘルプを表示
python extract_copilot_acceptance_rate.py --help
```

#### 出力内容

- 📊 **全体統計**: 総採用率、提案数、採用数
- 🗓️ **日別統計**: 日付ごとの詳細な採用率データ
- 💻 **言語別統計**: プログラミング言語ごとの採用率
- 🖥️ **エディタ別統計**: 使用エディタごとの採用率

### 2. Cursor Admin API メトリクス取得

Cursor Admin APIを使用してチームの使用メトリクス、支出データ、メンバー情報を取得します。

#### 設定

```bash
# 環境変数でAPIキーを設定
export CURSOR_API_KEY=your-api-key-here

# または設定ファイルを作成
python config.py --setup
```

#### 使用方法

```bash
# 過去7日間のメトリクスを取得
python extract_cursor_metrics.py

# 特定の期間を指定
python extract_cursor_metrics.py --start-date 2024-01-01 --end-date 2024-01-31

# 結果をJSONファイルに出力
python extract_cursor_metrics.py --output cursor_metrics_$(date +%Y%m%d).json

# 支出データも含めて取得
python extract_cursor_metrics.py --include-spending

# 取得日数を指定
python extract_cursor_metrics.py --days 30
```

#### 出力内容

- 👥 **チーム情報**: メンバー数と詳細
- 📈 **使用統計**: コード行数、AI提案採用率
- 👤 **ユーザー別統計**: 個人ごとの詳細な使用データ
- 📁 **拡張子別統計**: ファイル形式ごとの使用パターン
- 💰 **支出データ**: チーム使用料金（オプション）

### 3. 設定管理

API認証情報やツール設定を管理します。

```bash
# インタラクティブ設定
python config.py --setup

# サンプル設定ファイル作成
python config.py --sample

# 現在の設定を表示
python config.py --show
```

## 🐳 Docker使用

### イメージのビルド

```bash
docker build -t ai-metrics-analyzer .
```

### 実行

```bash
# GitHub Copilotメトリクス分析
docker run -v /path/to/data:/app ai-metrics-analyzer extract_copilot_acceptance_rate.py copilot_metrics.json

# Cursor メトリクス取得（環境変数でAPIキー指定）
source .envrc && docker run -e CURSOR_API_KEY=$CURSOR_API_KEY -v $(pwd):/app metrics_analyzer extract_cursor_metrics.py --days 30 --output outputs/cursor_metrics_$(date +%Y%m%d).json
```

## 📁 プロジェクト構造

```
copilot/
├── extract_copilot_acceptance_rate.py  # GitHub Copilot分析メイン
├── extract_cursor_metrics.py           # Cursor Admin API取得メイン
├── config.py                          # 設定管理
├── requirements.txt                   # Python依存関係
├── Dockerfile                         # Docker設定
├── .gitignore                        # Git除外設定
├── outputs/                          # 出力ファイル格納
└── README.md                         # このファイル
```

## 📊 データ形式

### GitHub Copilot メトリクス

期待されるJSON構造：
```json
[
  {
    "date": "2024-01-01",
    "copilot_ide_code_completions": {
      "editors": [
        {
          "name": "vscode",
          "models": [
            {
              "languages": [
                {
                  "name": "python",
                  "total_code_suggestions": 100,
                  "total_code_acceptances": 75
                }
              ]
            }
          ]
        }
      ]
    }
  }
]
```

### Cursor Admin API

APIから自動取得される形式：
- 日次使用データ（行数、AI提案、リクエストタイプ等）
- チームメンバー情報
- 支出データ（オプション）

## 🔧 設定オプション

### 環境変数

- `CURSOR_API_KEY`: Cursor Admin API キー
- `CURSOR_BASE_URL`: APIベースURL（デフォルト: https://api.cursor.com）
- `CURSOR_DEFAULT_DAYS`: デフォルト取得日数（デフォルト: 7）
- `CURSOR_OUTPUT_FORMAT`: 出力形式（console/json/csv）

### 設定ファイル

`~/.cursor-config.json` に設定を保存可能：
```json
{
  "api_key": "your-cursor-admin-api-key-here",
  "base_url": "https://api.cursor.com",
  "default_days": 7,
  "output_format": "console"
}
```

## 📋 要件

### Python依存関係

- `pandas>=2.0.3` - データ分析とテーブル表示
- `requests>=2.31.0` - HTTP APIリクエスト
- `matplotlib>=3.7.2` - グラフ作成（将来の機能用）
- `numpy>=1.24.3` - 数値計算

## 🚨 注意事項

- **APIキーの管理**: APIキーは環境変数または設定ファイルで安全に管理してください
- **データプライバシー**: メトリクスデータには個人情報が含まれる場合があります
- **API制限**: Cursor Admin APIには90日間の取得制限があります
- **出力言語**: ユーザー向け出力は日本語で表示されます

## 🤝 貢献

プロジェクトへの貢献を歓迎します：

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📄 ライセンス

このプロジェクトのライセンス情報については、LICENSEファイルを参照してください。

## 🔗 参考資料

- [GitHub Copilot API Documentation](https://docs.github.com/en/copilot)
- [Cursor Admin API Documentation](https://docs.cursor.com/en/account/teams/admin-api)
- [Docker Documentation](https://docs.docker.com/)

## 📞 サポート

問題や質問がある場合は、GitHubのIssuesページで報告してください。
