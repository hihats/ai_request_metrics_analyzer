#!/usr/bin/env python3
import json
import pandas as pd
from pathlib import Path
import sys
import argparse
from datetime import datetime

def load_metrics_data(file_path):
    """Load the GitHub Copilot metrics data from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            # Handle both array and single object formats
            if isinstance(data, dict):
                return [data]
            return data
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"エラー: 無効なJSON形式です: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"エラー: ファイル読み込み中に問題が発生しました: {str(e)}")
        sys.exit(1)

def calculate_acceptance_rate(metrics_data):
    """Calculate the acceptance rate from the metrics data."""
    results = []
    
    for day_data in metrics_data:
        date = day_data.get('date', 'Unknown')
        
        # Initialize counters for the day
        total_suggestions = 0
        total_acceptances = 0
        language_stats = {}
        editor_stats = {}
        
        # Process IDE code completions
        ide_completions = day_data.get('copilot_ide_code_completions', {})
        for editor in ide_completions.get('editors', []):
            editor_name = editor.get('name', 'unknown')
            editor_stats[editor_name] = {
                'suggestions': 0,
                'acceptances': 0,
                'rate': 0
            }
            
            for model in editor.get('models', []):
                for language in model.get('languages', []):
                    lang_name = language.get('name', 'unknown')
                    suggestions = language.get('total_code_suggestions', 0)
                    acceptances = language.get('total_code_acceptances', 0)
                    
                    # Update total counters
                    total_suggestions += suggestions
                    total_acceptances += acceptances
                    
                    # Update editor stats
                    editor_stats[editor_name]['suggestions'] += suggestions
                    editor_stats[editor_name]['acceptances'] += acceptances
                    
                    # Update or initialize language stats
                    if lang_name not in language_stats:
                        language_stats[lang_name] = {
                            'suggestions': 0,
                            'acceptances': 0,
                            'rate': 0
                        }
                    language_stats[lang_name]['suggestions'] += suggestions
                    language_stats[lang_name]['acceptances'] += acceptances
        
        # Calculate rates for editors and languages
        for editor in editor_stats:
            if editor_stats[editor]['suggestions'] > 0:
                editor_stats[editor]['rate'] = (editor_stats[editor]['acceptances'] / 
                                               editor_stats[editor]['suggestions']) * 100
                
        for lang in language_stats:
            if language_stats[lang]['suggestions'] > 0:
                language_stats[lang]['rate'] = (language_stats[lang]['acceptances'] / 
                                               language_stats[lang]['suggestions']) * 100
        
        # Calculate overall acceptance rate for the day
        acceptance_rate = 0
        if total_suggestions > 0:
            acceptance_rate = (total_acceptances / total_suggestions) * 100
        
        results.append({
            'date': date,
            'total_suggestions': total_suggestions,
            'total_acceptances': total_acceptances,
            'acceptance_rate': acceptance_rate,
            'language_stats': language_stats,
            'editor_stats': editor_stats
        })
    
    return results

def format_date(date_str):
    """Format date string to a more readable format if possible."""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%Y年%m月%d日")
    except:
        return date_str

def print_results(results):
    """Print the results in a formatted way."""
    print("\n組織のGitHub Copilot Acceptance Rate:")
    print("=" * 60)
    
    # Create a DataFrame for the main results
    main_data = []
    for day in results:
        main_data.append({
            '日付': format_date(day['date']),
            '提案数': day['total_suggestions'],
            '採用数': day['total_acceptances'],
            '採用率 (%)': f"{day['acceptance_rate']:.2f}%"
        })
    
    main_df = pd.DataFrame(main_data)
    print(main_df.to_string(index=False))
    print("=" * 60)
    
    # Calculate overall stats
    total_suggestions = sum(day['total_suggestions'] for day in results)
    total_acceptances = sum(day['total_acceptances'] for day in results)
    overall_rate = 0
    if total_suggestions > 0:
        overall_rate = (total_acceptances / total_suggestions) * 100
    
    print(f"\n全体の統計:")
    print(f"  全体の採用率: {overall_rate:.2f}%")
    print(f"  全体の提案数: {total_suggestions}")
    print(f"  全体の採用数: {total_acceptances}")
    
    # Print language breakdown if available
    all_languages = {}
    for day in results:
        for lang, stats in day.get('language_stats', {}).items():
            if lang not in all_languages:
                all_languages[lang] = {'suggestions': 0, 'acceptances': 0}
            all_languages[lang]['suggestions'] += stats['suggestions']
            all_languages[lang]['acceptances'] += stats['acceptances']
    
    if all_languages:
        print("\n言語別の統計:")
        lang_data = []
        for lang, stats in all_languages.items():
            rate = 0
            if stats['suggestions'] > 0:
                rate = (stats['acceptances'] / stats['suggestions']) * 100
            lang_data.append({
                '言語': lang,
                '提案数': stats['suggestions'],
                '採用数': stats['acceptances'],
                '採用率 (%)': f"{rate:.2f}%"
            })
        
        lang_df = pd.DataFrame(lang_data)
        lang_df = lang_df.sort_values(by='提案数', ascending=False)
        print(lang_df.to_string(index=False))
    
    # Print editor breakdown if available
    all_editors = {}
    for day in results:
        for editor, stats in day.get('editor_stats', {}).items():
            if editor not in all_editors:
                all_editors[editor] = {'suggestions': 0, 'acceptances': 0}
            all_editors[editor]['suggestions'] += stats['suggestions']
            all_editors[editor]['acceptances'] += stats['acceptances']
    
    if all_editors:
        print("\nエディタ別の統計:")
        editor_data = []
        for editor, stats in all_editors.items():
            rate = 0
            if stats['suggestions'] > 0:
                rate = (stats['acceptances'] / stats['suggestions']) * 100
            editor_data.append({
                'エディタ': editor,
                '提案数': stats['suggestions'],
                '採用数': stats['acceptances'],
                '採用率 (%)': f"{rate:.2f}%"
            })
        
        editor_df = pd.DataFrame(editor_data)
        editor_df = editor_df.sort_values(by='提案数', ascending=False)
        print(editor_df.to_string(index=False))

def main():
    parser = argparse.ArgumentParser(description='GitHub Copilotのメトリクスデータから組織のAcceptance Rateを抽出します。')
    parser.add_argument('file_path', nargs='?', default=None, 
                        help='メトリクスデータのJSONファイルパス (デフォルト: /app/copilot_metrics.json)')
    
    args = parser.parse_args()
    
    if args.file_path:
        file_path = args.file_path
    else:
        file_path = Path.home() / 'Downloads' / 'copilot_metrics.json'
    
    print(f"メトリクスデータを読み込み中: {file_path}")
    metrics_data = load_metrics_data(file_path)
    
    if not metrics_data:
        print("エラー: メトリクスデータが空です。")
        sys.exit(1)
    
    results = calculate_acceptance_rate(metrics_data)
    print_results(results)

if __name__ == "__main__":
    main()
