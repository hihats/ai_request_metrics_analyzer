#!/usr/bin/env python3
"""
Cursor Admin API 設定ファイル

環境変数やファイルからAPIキーや設定を読み込む
"""

import os
from pathlib import Path
from typing import Dict, Optional
import json


class CursorConfig:
    """Cursor Admin API 設定クラス"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        設定を初期化
        
        Args:
            config_file: 設定ファイルのパス（未指定時は ~/.cursor-config.json を使用）
        """
        self.config_file = config_file or str(Path.home() / '.cursor-config.json')
        self._config = self._load_config()
    
    def _load_config(self) -> Dict:
        """設定ファイルを読み込み"""
        config = {}
        
        # 設定ファイルから読み込み
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        return config
    
    def get_api_key(self) -> Optional[str]:
        """
        APIキーを取得
        
        優先順位:
        1. 環境変数 CURSOR_API_KEY
        2. 設定ファイルの api_key
        
        Returns:
            APIキー
        """
        return os.getenv('CURSOR_API_KEY') or self._config.get('api_key')
    
    def get_base_url(self) -> str:
        """
        ベースURLを取得
        
        Returns:
            ベースURL
        """
        return os.getenv('CURSOR_BASE_URL') or self._config.get('base_url', 'https://api.cursor.com')
    
    def get_default_days(self) -> int:
        """
        デフォルト取得日数を取得
        
        Returns:
            デフォルト日数
        """
        return int(os.getenv('CURSOR_DEFAULT_DAYS', 
                           self._config.get('default_days', 7)))
    
    def get_output_format(self) -> str:
        """
        デフォルト出力形式を取得
        
        Returns:
            出力形式（json, csv, console）
        """
        return os.getenv('CURSOR_OUTPUT_FORMAT') or self._config.get('output_format', 'console')
    
    def save_config(self, api_key: Optional[str] = None, 
                   base_url: Optional[str] = None,
                   default_days: Optional[int] = None,
                   output_format: Optional[str] = None):
        """
        設定をファイルに保存
        
        Args:
            api_key: APIキー
            base_url: ベースURL
            default_days: デフォルト日数
            output_format: 出力形式
        """
        config = self._config.copy()
        
        if api_key:
            config['api_key'] = api_key
        if base_url:
            config['base_url'] = base_url
        if default_days:
            config['default_days'] = default_days
        if output_format:
            config['output_format'] = output_format
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self._config = config
        except IOError as e:
            raise RuntimeError(f"設定ファイルの保存に失敗しました: {e}")
    
    def create_sample_config(self):
        """
        サンプル設定ファイルを作成
        """
        sample_config = {
            "api_key": "your-cursor-admin-api-key-here",
            "base_url": "https://api.cursor.com",
            "default_days": 7,
            "output_format": "console"
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f, ensure_ascii=False, indent=2)
            print(f"サンプル設定ファイルを作成しました: {self.config_file}")
            print("APIキーを設定してください。")
        except IOError as e:
            raise RuntimeError(f"設定ファイルの作成に失敗しました: {e}")


def setup_config():
    """設定セットアップ用のインタラクティブ関数"""
    config = CursorConfig()
    
    print("Cursor Admin API 設定セットアップ")
    print("=" * 40)
    
    # APIキー入力
    api_key = input("Cursor Admin API キーを入力してください: ").strip()
    if not api_key:
        print("APIキーは必須です。")
        return
    
    # ベースURL入力（オプション）
    base_url = input("ベースURL (デフォルト: https://api.cursor.com): ").strip()
    if not base_url:
        base_url = "https://api.cursor.com"
    
    # デフォルト日数入力（オプション）
    try:
        default_days_input = input("デフォルト取得日数 (デフォルト: 7): ").strip()
        default_days = int(default_days_input) if default_days_input else 7
    except ValueError:
        default_days = 7
    
    # 出力形式入力（オプション）
    output_format = input("出力形式 [console/json/csv] (デフォルト: console): ").strip()
    if output_format not in ['console', 'json', 'csv']:
        output_format = 'console'
    
    # 設定保存
    try:
        config.save_config(
            api_key=api_key,
            base_url=base_url,
            default_days=default_days,
            output_format=output_format
        )
        print(f"\n✅ 設定を保存しました: {config.config_file}")
        print("これで extract_cursor_metrics.py を実行できます。")
    except Exception as e:
        print(f"❌ 設定の保存に失敗しました: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Cursor Admin API 設定管理')
    parser.add_argument('--setup', action='store_true', help='インタラクティブ設定')
    parser.add_argument('--sample', action='store_true', help='サンプル設定ファイル作成')
    parser.add_argument('--show', action='store_true', help='現在の設定を表示')
    
    args = parser.parse_args()
    
    if args.setup:
        setup_config()
    elif args.sample:
        config = CursorConfig()
        config.create_sample_config()
    elif args.show:
        config = CursorConfig()
        print(f"設定ファイル: {config.config_file}")
        print(f"APIキー: {'設定済み' if config.get_api_key() else '未設定'}")
        print(f"ベースURL: {config.get_base_url()}")
        print(f"デフォルト日数: {config.get_default_days()}")
        print(f"出力形式: {config.get_output_format()}")
    else:
        print("使用方法: python config.py [--setup|--sample|--show]")