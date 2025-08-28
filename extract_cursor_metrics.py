#!/usr/bin/env python3
"""
Cursor Admin API メトリクス取得スクリプト

Cursor Admin API (https://docs.cursor.com/account/teams/admin-api) を使用して
チームの使用メトリクス、支出データ、メンバー情報を取得します。
"""

import json
import requests
import pandas as pd
from pathlib import Path
import sys
import argparse
from datetime import datetime, timedelta
import os
import base64
from typing import Dict, List, Optional
import time


def format_date_from_timestamp(timestamp_value, default: str = 'N/A') -> str:
    """
    エポックタイムスタンプを日付文字列に変換
    
    Args:
        timestamp_value: エポックタイムスタンプ（ミリ秒または秒）
        default: 変換できない場合のデフォルト値
        
    Returns:
        YYYY-MM-DD形式の日付文字列
    """
    if isinstance(timestamp_value, (int, float)) and timestamp_value > 0:
        try:
            # エポックタイムスタンプ（ミリ秒）を日付に変換
            # 値が大きい場合はミリ秒、小さい場合は秒として処理
            if timestamp_value > 10**10:  # ミリ秒の場合
                date_obj = datetime.fromtimestamp(timestamp_value / 1000)
            else:  # 秒の場合
                date_obj = datetime.fromtimestamp(timestamp_value)
            return date_obj.strftime('%Y-%m-%d')
        except (ValueError, OSError):
            return str(timestamp_value)
    else:
        return str(timestamp_value) if timestamp_value != 'unknown' and timestamp_value else default


class CursorAdminClient:
    """Cursor Admin API クライアント"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.cursor.com"):
        """
        初期化
        
        Args:
            api_key: Cursor Admin API キー
            base_url: APIのベースURL
        """
        if not api_key:
            raise ValueError("API キーが必要です")
        
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        
        # Basic認証でAPIキーを設定
        encoded_key = base64.b64encode(f"{api_key}:".encode()).decode()
        self.session.headers.update({
            'Authorization': f'Basic {encoded_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'Cursor-Admin-Metrics-Client/1.0'
        })
    
    def _make_request(self, endpoint: str, method: str = 'GET', data: Dict = None) -> Dict:
        """
        API リクエストを実行
        
        Args:
            endpoint: APIエンドポイント
            method: HTTPメソッド
            data: リクエストボディ
            
        Returns:
            APIレスポンス
            
        Raises:
            requests.exceptions.RequestException: APIリクエストエラー
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"サポートされていないHTTPメソッド: {method}")
            
            response.raise_for_status()
            
            try:
                json_response = response.json()
                return json_response
            except json.JSONDecodeError as e:
                print(f"JSONパースエラー: {e}")
                print(f"レスポンス全文: {response.text}")
                raise
            
        except requests.exceptions.RequestException as e:
            print(f"APIリクエストエラー: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  ステータスコード: {e.response.status_code}")
                print(f"  エラーレスポンス: {e.response.text}")
                print(f"  レスポンスヘッダー: {dict(e.response.headers)}")
            raise
    
    def get_team_members(self) -> List[Dict]:
        """
        チームメンバー情報を取得
        
        Returns:
            チームメンバーのリスト（名前、メール、役割を含む）
        """
        try:
            response = self._make_request('teams/members')
            
            # メンバー情報の抽出
            members = self._extract_team_members_from_response(response)
            
            if members:
                print(f"✅ チームメンバー取得成功: {len(members)} 人")
            else:
                print(f"チームメンバー情報が見つかりませんでした")
            
            return members
            
        except Exception as e:
            print(f"メンバー取得エラー: {e}")
            return []
    
    def _extract_team_members_from_response(self, response) -> List[Dict]:
        """
        APIレスポンスからチームメンバー情報を抽出
        
        Args:
            response: APIレスポンス
            
        Returns:
            メンバー情報のリスト
        """
        if not response:
            print("⚠️ レスポンスが空です")
            return []
        
        # ドキュメント通りの形式を最初に試す
        if isinstance(response, dict):
            # Cursor Admin API の標準レスポンス形式
            if 'teamMembers' in response and isinstance(response['teamMembers'], list):
                return response['teamMembers']
            
            # その他のキーパターンを試す
            possible_keys = [
                'members',      # 一般的なキー名
                'data',         # データを含むキー
                'users',        # ユーザー情報
                'team_members', # アンダースコア形式
                'teamMember',   # 単数形
                'results',      # 結果を含むキー
                'items',        # アイテムリスト
                'people'        # 人のリスト
            ]
            
            for key in possible_keys:
                if key in response and isinstance(response[key], list):
                    return response[key]
            
            # ネストされた構造をチェック
            for key, value in response.items():
                if isinstance(value, dict):
                    nested_members = self._extract_team_members_from_response(value)
                    if nested_members:
                        return nested_members
            
            return []
            
        elif isinstance(response, list):
            # 直接配列の場合
            return response
            
        else:
            return []
    
    def get_daily_usage_data(self, start_date: datetime, end_date: datetime) -> Dict:
        """
        日次使用データを取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            日次使用データ（行数、AI提案、リクエストタイプ、モデル使用量等）
        """
        print(f"日次使用データを取得中...")
        print(f"期間: {start_date.strftime('%Y-%m-%d %H:%M:%S')} から {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # エポック時間（ミリ秒）に変換
        start_epoch = int(start_date.timestamp() * 1000)
        end_epoch = int(end_date.timestamp() * 1000)
        
        data = {
            'startDate': start_epoch,
            'endDate': end_epoch
        }
        
        # 90日制限のチェック
        days_diff = (end_date - start_date).days
        if days_diff > 90:
            print(f"警告: 期間が90日を超えています ({days_diff}日)。APIの制限により失敗する可能性があります。")
        
        try:
            response = self._make_request('teams/daily-usage-data', method='POST', data=data)
            return response
                
        except Exception as e:
            print(f"日次使用データ取得エラー: {e}")
            raise
    

    
    def get_spending_data(self, search_term: Optional[str] = None, 
                         sort_by: Optional[str] = None, 
                         page: int = 1, page_size: int = 100) -> Dict:
        """
        支出データを取得
        
        Args:
            search_term: 検索語句
            sort_by: ソート項目
            page: ページ番号
            page_size: ページサイズ
            
        Returns:
            チームメンバーの支出詳細
        """
        data = {
            'page': page,
            'pageSize': page_size
        }
        
        if search_term:
            data['search'] = search_term
        if sort_by:
            data['sortBy'] = sort_by
            
        return self._make_request('teams/spend', method='POST', data=data)


def calculate_cursor_metrics(usage_data: Dict, members_data: List[Dict]) -> Dict:
    """
    Cursorメトリクスを計算・集計
    
    Args:
        usage_data: 使用データ
        members_data: メンバーデータ
        
    Returns:
        計算されたメトリクス
    """

    
    metrics = {
        'team_info': {
            'member_count': len(members_data),
            'members': members_data
        },
        'usage_summary': {},
        'daily_breakdown': [],
        'extension_stats': {},
        'language_stats': {},
        'model_stats': {},
        'feature_stats': {}
    }
    
    # 日次データの処理
    daily_data_found = False
    daily_data_source = None
    
    # 複数のキーパターンを試す
    possible_daily_keys = ['dailyData', 'data', 'usage_data', 'daily_usage', 'results', 'items']
    
    for key in possible_daily_keys:
        if key in usage_data and usage_data[key]:
            daily_data_found = True
            daily_data_source = key
            break
    
    if daily_data_found:
        daily_data_list = usage_data[daily_data_source]
    else:
        daily_data_list = []
    
    if daily_data_list:
        total_lines_added = 0
        total_lines_deleted = 0
        total_ai_accepts = 0
        total_ai_rejects = 0
        
        for i, day_data in enumerate(daily_data_list):
            # API仕様に基づく正しいフィールド名を使用
            date_raw = day_data.get('date', 'unknown')
            date = format_date_from_timestamp(date_raw, 'unknown')
                
            lines_added = day_data.get('totalLinesAdded', 0)
            lines_deleted = day_data.get('totalLinesDeleted', 0)
            ai_accepts = day_data.get('totalAccepts', 0)
            ai_rejects = day_data.get('totalRejects', 0)
            
            # 追加のメトリクス
            applies = day_data.get('totalApplies', 0)
            tabs_shown = day_data.get('totalTabsShown', 0)
            tabs_accepted = day_data.get('totalTabsAccepted', 0)
            composer_requests = day_data.get('composerRequests', 0)
            chat_requests = day_data.get('chatRequests', 0)
            is_active = day_data.get('isActive', False)
            email = day_data.get('email', 'N/A')
            
            total_lines_added += lines_added
            total_lines_deleted += lines_deleted
            total_ai_accepts += ai_accepts
            total_ai_rejects += ai_rejects
            
            # 日次詳細
            daily_metrics = {
                'date': date,
                'is_active': is_active,
                'email': email,
                'lines_added': lines_added,
                'lines_deleted': lines_deleted,
                'ai_accepts': ai_accepts,
                'ai_rejects': ai_rejects,
                'applies': applies,
                'tabs_shown': tabs_shown,
                'tabs_accepted': tabs_accepted,
                'composer_requests': composer_requests,
                'chat_requests': chat_requests,
                'acceptance_rate': (ai_accepts / (ai_accepts + ai_rejects) * 100) if (ai_accepts + ai_rejects) > 0 else 0,
                'tab_acceptance_rate': (tabs_accepted / tabs_shown * 100) if tabs_shown > 0 else 0
            }
            
            # 追加フィールドの処理
            optional_fields = [
                'acceptedLinesAdded', 'acceptedLinesDeleted', 'agentRequests', 
                'cmdkUsages', 'subscriptionIncludedReqs', 'apiKeyReqs', 
                'usageBasedReqs', 'bugbotUsages', 'mostUsedModel',
                'applyMostUsedExtension', 'tabMostUsedExtension', 'clientVersion'
            ]
            
            for field in optional_fields:
                if field in day_data:
                    daily_metrics[field.lower()] = day_data[field]
            
            metrics['daily_breakdown'].append(daily_metrics)
        
        # 全体サマリー
        metrics['usage_summary'] = {
            'total_lines_added': total_lines_added,
            'total_lines_deleted': total_lines_deleted,
            'total_ai_accepts': total_ai_accepts,
            'total_ai_rejects': total_ai_rejects,
            'overall_acceptance_rate': (total_ai_accepts / (total_ai_accepts + total_ai_rejects) * 100) if (total_ai_accepts + total_ai_rejects) > 0 else 0
        }
        
        # ユーザー別統計（各ユーザーの全期間合計）
        user_aggregated = {}
        
        # 拡張子別統計の初期化
        extension_stats = {
            'apply_extensions': {},
            'tab_extensions': {},
            'combined_extensions': {}
        }
        
        for day in metrics['daily_breakdown']:
            email = day.get('email', 'N/A')
            if email not in user_aggregated:
                user_aggregated[email] = {
                    'email': email,
                    'lines_added': 0,
                    'lines_deleted': 0,
                    'ai_accepts': 0,
                    'ai_rejects': 0,
                    'applies': 0,
                    'tabs_shown': 0,
                    'tabs_accepted': 0,
                    'composer_requests': 0,
                    'chat_requests': 0,
                    'active_days': 0
                }
            
            user_aggregated[email]['lines_added'] += day.get('lines_added', 0)
            user_aggregated[email]['lines_deleted'] += day.get('lines_deleted', 0)
            user_aggregated[email]['ai_accepts'] += day.get('ai_accepts', 0)
            user_aggregated[email]['ai_rejects'] += day.get('ai_rejects', 0)
            user_aggregated[email]['applies'] += day.get('applies', 0)
            user_aggregated[email]['tabs_shown'] += day.get('tabs_shown', 0)
            user_aggregated[email]['tabs_accepted'] += day.get('tabs_accepted', 0)
            user_aggregated[email]['composer_requests'] += day.get('composer_requests', 0)
            user_aggregated[email]['chat_requests'] += day.get('chat_requests', 0)
            if day.get('is_active', False):
                user_aggregated[email]['active_days'] += 1
            
            # 拡張子別統計の集計
            apply_ext = day.get('applymostusedextension')
            tab_ext = day.get('tabmostusedextension')
            applies_count = day.get('applies', 0)
            tabs_accepted_count = day.get('tabs_accepted', 0)
            
            if apply_ext and applies_count > 0:
                if apply_ext not in extension_stats['apply_extensions']:
                    extension_stats['apply_extensions'][apply_ext] = 0
                extension_stats['apply_extensions'][apply_ext] += applies_count
                
                # 全体統計にも追加
                if apply_ext not in extension_stats['combined_extensions']:
                    extension_stats['combined_extensions'][apply_ext] = {'applies': 0, 'tabs': 0}
                extension_stats['combined_extensions'][apply_ext]['applies'] += applies_count
            
            if tab_ext and tabs_accepted_count > 0:
                if tab_ext not in extension_stats['tab_extensions']:
                    extension_stats['tab_extensions'][tab_ext] = 0
                extension_stats['tab_extensions'][tab_ext] += tabs_accepted_count
                
                # 全体統計にも追加
                if tab_ext not in extension_stats['combined_extensions']:
                    extension_stats['combined_extensions'][tab_ext] = {'applies': 0, 'tabs': 0}
                extension_stats['combined_extensions'][tab_ext]['tabs'] += tabs_accepted_count
        
        # 拡張子別統計を保存
        metrics['extension_stats'] = extension_stats
        
        # 採用率を計算
        for email, stats in user_aggregated.items():
            total_suggestions = stats['ai_accepts'] + stats['ai_rejects']
            stats['acceptance_rate'] = (stats['ai_accepts'] / total_suggestions * 100) if total_suggestions > 0 else 0
            stats['tab_acceptance_rate'] = (stats['tabs_accepted'] / stats['tabs_shown'] * 100) if stats['tabs_shown'] > 0 else 0
        
        metrics['user_aggregated'] = sorted(user_aggregated.values(), key=lambda x: x['lines_added'] + x['lines_deleted'], reverse=True)
        
    else:
        metrics['usage_summary'] = {
            'total_lines_added': 0,
            'total_lines_deleted': 0,
            'total_ai_accepts': 0,
            'total_ai_rejects': 0,
            'overall_acceptance_rate': 0,
            'no_data_reason': '日次データが見つかりませんでした'
        }
    
    return metrics


def print_cursor_results(results: Dict):
    """結果をフォーマットして表示"""
    print("\nCursor Admin API メトリクス:")
    print("=" * 60)
    
    # チーム情報
    team_info = results.get('team_info', {})
    member_count = team_info.get('member_count', 0)
    members = team_info.get('members', [])
    
    print(f"チームメンバー数: {member_count}")
    
    # メンバー情報が取得できなかった場合のみメッセージ表示
    if not members:
        print("  ⚠️ メンバー情報が取得できませんでした")
    
    # 使用サマリー
    usage = results.get('usage_summary', {})
    if usage:
        print(f"\n全体統計:")
        
        # データが空の場合の特別処理
        if 'no_data_reason' in usage:
            print(f"  ⚠️ データなし: {usage['no_data_reason']}")
            print(f"  考えられる原因:")
            print(f"    - 指定期間にチームの活動がない")
            print(f"    - APIキーの権限が不足している")
            print(f"    - エンドポイントまたはリクエスト形式が正しくない")
        else:
            # 通常の統計表示
            total_activity = usage.get('total_lines_added', 0) + usage.get('total_lines_deleted', 0)
            total_ai_interactions = usage.get('total_ai_accepts', 0) + usage.get('total_ai_rejects', 0)
            
            print(f"  追加行数: {usage.get('total_lines_added', 0):,}")
            print(f"  削除行数: {usage.get('total_lines_deleted', 0):,}")
            print(f"  AI提案採用数: {usage.get('total_ai_accepts', 0):,}")
            print(f"  AI提案拒否数: {usage.get('total_ai_rejects', 0):,}")
            print(f"  AI採用率: {usage.get('overall_acceptance_rate', 0):.2f}%")
            
            if total_activity == 0:
                print(f"  📊 活動レベル: なし（指定期間中にコードの変更がありませんでした）")
            elif total_ai_interactions == 0:
                print(f"  📊 AI使用: なし（AI機能が使用されていませんでした）")
    
    # ユーザー別統計
    user_aggregated = results.get('user_aggregated', [])
    if user_aggregated:
        print(f"\nユーザー別統計:")
        user_df_data = []
        for user in user_aggregated:
            if user['email'] != 'N/A':  # 有効なユーザーのみ表示
                user_df_data.append({
                    'ユーザー': user['email'],
                    '追加行数': user['lines_added'],
                    '削除行数': user['lines_deleted'],
                    'AI採用': user['ai_accepts'],
                    'AI拒否': user['ai_rejects'],
                    '採用率(%)': f"{user['acceptance_rate']:.1f}%",
                    'アクティブ日数': user['active_days']
                })
        
        if user_df_data:
            user_df = pd.DataFrame(user_df_data)
            print(user_df.to_string(index=False))

    # 拡張子別統計
    extension_stats = results.get('extension_stats', {})
    if extension_stats:
        print(f"\n拡張子別統計:")
        
        # Apply操作の拡張子統計
        apply_extensions = extension_stats.get('apply_extensions', {})
        if apply_extensions:
            print(f"\n  📝 Apply操作 (Cmd+K) 使用拡張子:")
            sorted_apply_extensions = sorted(apply_extensions.items(), key=lambda x: x[1], reverse=True)
            for ext, count in sorted_apply_extensions[:10]:  # 上位10件表示
                print(f"    {ext}: {count}回")
        
        # Tab補完の拡張子統計
        tab_extensions = extension_stats.get('tab_extensions', {})
        if tab_extensions:
            print(f"\n  ⭐ Tab補完 使用拡張子:")
            sorted_tab_extensions = sorted(tab_extensions.items(), key=lambda x: x[1], reverse=True)
            for ext, count in sorted_tab_extensions[:10]:  # 上位10件表示
                print(f"    {ext}: {count}回")
        
        # 全体統計（拡張子ごとの総使用数）
        combined_extensions = extension_stats.get('combined_extensions', {})
        if combined_extensions:
            print(f"\n  🎯 全体拡張子使用統計 (Apply + Tab):")
            # 全体使用数でソート
            sorted_combined = sorted(combined_extensions.items(), 
                                   key=lambda x: x[1]['applies'] + x[1]['tabs'], 
                                   reverse=True)
            
            combined_df_data = []
            for ext, stats in sorted_combined[:15]:  # 上位15件表示
                total_usage = stats['applies'] + stats['tabs']
                combined_df_data.append({
                    '拡張子': ext,
                    'Apply操作': stats['applies'],
                    'Tab補完': stats['tabs'],
                    '合計使用': total_usage
                })
            
            if combined_df_data:
                combined_df = pd.DataFrame(combined_df_data)
                print(combined_df.to_string(index=False))


def export_to_json(results: Dict, output_path: str):
    """結果をJSONファイルにエクスポート"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nメトリクスデータをエクスポートしました: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Cursor Admin API メトリクス取得ツール')
    parser.add_argument('--days', type=int, default=7, help='取得日数 (デフォルト: 7)')
    parser.add_argument('--start-date', help='開始日 (YYYY-MM-DD形式)')
    parser.add_argument('--end-date', help='終了日 (YYYY-MM-DD形式)')
    parser.add_argument('--output', '-o', help='出力JSONファイルパス')
    parser.add_argument('--include-spending', action='store_true', help='支出データも取得')
    
    args = parser.parse_args()
    
    # 日付範囲の設定
    if args.start_date and args.end_date:
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        except ValueError:
            print("エラー: 日付形式が正しくありません (YYYY-MM-DD)")
            sys.exit(1)
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
    
    # APIキーを環境変数から取得
    api_key = os.getenv('CURSOR_API_KEY')
    if not api_key:
        print("エラー: 環境変数 CURSOR_API_KEY が設定されていません")
        print("以下のコマンドで環境変数を設定してください:")
        print("export CURSOR_API_KEY=your-api-key-here")
        sys.exit(1)
    
    try:
        # クライアント初期化
        client = CursorAdminClient(api_key=api_key)
        
        print("Cursor Admin API からメトリクスを取得中...")
        print(f"期間: {start_date.strftime('%Y-%m-%d')} から {end_date.strftime('%Y-%m-%d')}")
        
        # チームメンバー取得
        members_data = client.get_team_members()
        
        if not members_data:
            print(f"⚠️ メンバー情報が取得できませんでした")
        
        # 使用データ取得
        usage_data = client.get_daily_usage_data(start_date, end_date)
        
        # 支出データ取得（オプション）
        spending_data = None
        if args.include_spending:
            spending_data = client.get_spending_data()
        
        # メトリクス計算
        results = calculate_cursor_metrics(usage_data, members_data)
        
        # 支出データを追加
        if spending_data:
            results['spending_data'] = spending_data
        
        # 結果表示
        print_cursor_results(results)
        
        # JSONエクスポート
        if args.output:
            export_to_json(results, args.output)
        
        print(f"\n✅ メトリクス取得完了")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()