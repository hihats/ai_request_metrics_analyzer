# Cursor Admin API Rules

## Cursor Admin API

Cursor Admin API specification として必ず以下のドキュメントを参照すること:
https://docs.cursor.com/en/account/teams/admin-api

### 主要なエンドポイント

- `/teams/members` - チームメンバー情報取得
- `/teams/daily-usage-data` - 日次使用データ取得
- `/teams/spend` - 支出データ取得

### 注意事項

- APIレスポンスの構造は公式ドキュメントに従うこと
- 日次データの取得は90日間の制限があります
- 認証にはAPIキーまたはBasic認証を使用
- レート制限に注意して実装すること

### データ構造

- チームメンバー: `{"teamMembers": [...]}`
- 日次データ: フィールド名は `totalLinesAdded`, `totalAccepts` 等を使用
- 日付は epoch milliseconds で提供される 