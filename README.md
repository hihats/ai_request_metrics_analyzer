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

GitHub Copilotの使用メトリクスを取得・解析し、採用率統計を生成します。
新しい Copilot Usage Metrics API（2026年2月GA）と、レガシーAPIで取得済みのローカルJSONファイルの両方に対応しています。

#### 使用方法

```bash
# GitHub APIから28日間レポートを取得・分析
python extract_copilot_acceptance_rate.py --api --report-type 28-day

# GitHub APIから特定日のレポートを取得・分析
python extract_copilot_acceptance_rate.py --api --report-type 1-day --day 2026-03-01

# レポートデータをファイルに保存しつつ分析
python extract_copilot_acceptance_rate.py --api --report-type 28-day --output outputs/report.json

# Organization名を指定
python extract_copilot_acceptance_rate.py --api --org your-org-name

# ローカルJSONファイルを指定（レガシー・新形式どちらも自動判別）
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
# GitHub Copilot: APIから28日間レポートを取得・分析
docker run --rm -e GH_TOKEN=$(gh auth token) -v $(pwd):/app ai-metrics-analyzer \
  extract_copilot_acceptance_rate.py --api --report-type 28-day --output outputs/copilot_metrics.json

# GitHub Copilot: ローカルJSONファイルを分析
docker run --rm -v $(pwd):/app ai-metrics-analyzer \
  extract_copilot_acceptance_rate.py path/to/copilot_metrics.json

# Cursor メトリクス取得（環境変数でAPIキー指定）
source .envrc && docker run --rm -e CURSOR_API_KEY=$CURSOR_API_KEY -v $(pwd):/app ai-metrics-analyzer \
  extract_cursor_metrics.py --days 30 --output outputs/cursor_metrics_$(date +%Y%m%d).json
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

新API（Copilot Usage Metrics API）と レガシーAPIの両形式を自動判別して処理します。

**新API形式**（`--api` で取得、またはローカルファイル）：
```json
{
  "day": "2026-03-01",
  "code_generation_activity_count": 110,
  "code_acceptance_activity_count": 10,
  "totals_by_ide": [
    {"ide": "vscode", "code_generation_activity_count": 78, "code_acceptance_activity_count": 6}
  ],
  "totals_by_language_feature": [
    {"language": "typescript", "feature": "code_completion", "code_generation_activity_count": 53, "code_acceptance_activity_count": 3}
  ]
}
```

**レガシーAPI形式**（既存のローカルJSONファイル）：
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
                {"name": "python", "total_code_suggestions": 100, "total_code_acceptances": 75}
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

- `GH_TOKEN` / `GITHUB_ACCESS_TOKEN`: GitHub APIトークン（Copilotメトリクス取得に必要、`admin:org` スコープ）
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

- [GitHub Copilot Usage Metrics API](https://docs.github.com/en/rest/copilot/copilot-usage-metrics)
- [Copilot Usage Metrics リファレンス](https://docs.github.com/en/copilot/reference/copilot-usage-metrics)
- [Cursor Admin API Documentation](https://docs.cursor.com/en/account/teams/admin-api)
- [Docker Documentation](https://docs.docker.com/)

## 📞 サポート

問題や質問がある場合は、GitHubのIssuesページで報告してください。
