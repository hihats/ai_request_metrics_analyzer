#!/usr/bin/env python3
import json
import os
import pandas as pd
from pathlib import Path
import sys
import argparse
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, timedelta


def get_github_token():
    """Get GitHub token from environment variable or gh CLI."""
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_ACCESS_TOKEN')
    if token:
        return token
    # Fallback: try gh CLI
    try:
        result = subprocess.run(
            ['gh', 'auth', 'token'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("エラー: GitHubトークンが見つかりません。GH_TOKEN環境変数を設定するか、gh auth loginを実行してください。")
        sys.exit(1)


def fetch_from_api(org, report_type, day=None):
    """Fetch metrics from the new Copilot Usage Metrics API."""
    token = get_github_token()
    base_url = 'https://api.github.com'

    if report_type == '28-day':
        url = f'{base_url}/orgs/{org}/copilot/metrics/reports/organization-28-day/latest'
    else:
        if not day:
            day = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        url = f'{base_url}/orgs/{org}/copilot/metrics/reports/organization-1-day?day={day}'

    print(f"APIからメトリクスを取得中: {url}")

    req = urllib.request.Request(url, headers={
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {token}',
        'X-GitHub-Api-Version': '2022-11-28'
    })

    try:
        resp = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        print(f"エラー: API呼び出しに失敗しました (HTTP {e.code}): {body}")
        sys.exit(1)

    api_response = json.loads(resp.read().decode('utf-8'))
    download_links = api_response.get('download_links', [])
    if not download_links:
        print("エラー: ダウンロードリンクが取得できませんでした。")
        sys.exit(1)

    print("レポートデータをダウンロード中...")
    report_data = urllib.request.urlopen(download_links[0]).read().decode('utf-8')
    return parse_ndjson_or_json(report_data)


def fetch_date_range(org, start_date, end_date):
    """Fetch metrics for a date range using the 1-day API endpoint.

    Loops through each day from start_date to end_date, calling the 1-day
    endpoint individually. Individual day failures are skipped gracefully.
    """
    token = get_github_token()
    base_url = 'https://api.github.com'
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    total_days = (end - start).days + 1
    all_days = []

    print(f"{start_date} 〜 {end_date} ({total_days}日分) のメトリクスを取得中...")

    for i in range(total_days):
        target_date = start + timedelta(days=i)
        day_str = target_date.strftime('%Y-%m-%d')
        url = f'{base_url}/orgs/{org}/copilot/metrics/reports/organization-1-day?day={day_str}'

        req = urllib.request.Request(url, headers={
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {token}',
            'X-GitHub-Api-Version': '2022-11-28'
        })

        try:
            resp = urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            print(f"  {day_str}: スキップ (HTTP {e.code})")
            continue

        api_response = json.loads(resp.read().decode('utf-8'))
        download_links = api_response.get('download_links', [])
        if not download_links:
            print(f"  {day_str}: スキップ (ダウンロードリンクなし)")
            continue

        report_data = urllib.request.urlopen(download_links[0]).read().decode('utf-8')
        day_data = parse_ndjson_or_json(report_data)
        day_records = normalize_new_api_data(day_data)
        all_days.extend(day_records)
        print(f"  {day_str}: 取得完了 ({len(day_records)}件)")

    if not all_days:
        print("エラー: 取得できたデータがありません。")
        sys.exit(1)

    return all_days


def parse_ndjson_or_json(text):
    """Parse NDJSON (newline-delimited JSON) or regular JSON.

    Note on the new Copilot Usage Metrics API (2026-02 GA) NDJSON adoption:
    The API returns download_links (signed URLs) to pre-generated NDJSON files,
    not an inline NDJSON HTTP response (application/x-ndjson with chunked
    transfer encoding). This means the streaming benefits of NDJSON — where
    server sends and client processes records incrementally — are not utilized.
    The actual benefit is limited to client-side memory efficiency when parsing
    large files line-by-line instead of loading entire JSON into memory.
    See: https://docs.github.com/en/rest/copilot/copilot-usage-metrics
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # NDJSON: each line is a separate JSON object
        records = []
        for line in text.strip().split('\n'):
            line = line.strip()
            if line:
                records.append(json.loads(line))
        if len(records) == 1:
            return records[0]
        return records


def detect_format(data):
    """Detect whether data is legacy or new API format."""
    if isinstance(data, list):
        sample = data[0] if data else {}
    else:
        sample = data
    # New API format has totals_by_ide or day_totals
    if 'totals_by_ide' in sample or 'day_totals' in sample:
        return 'new'
    return 'legacy'


def normalize_new_api_data(raw_data):
    """Convert new API report data into a list of per-day records."""
    if isinstance(raw_data, list):
        # NDJSON parsed as list: could be list of day records or list of 28-day reports
        all_days = []
        for item in raw_data:
            if 'day_totals' in item:
                all_days.extend(item['day_totals'])
            else:
                all_days.append(item)
        return all_days
    if 'day_totals' in raw_data:
        return raw_data['day_totals']
    # 1-day report is a single record
    return [raw_data]


def load_metrics_data(file_path):
    """Load the GitHub Copilot metrics data from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
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


def calculate_acceptance_rate_new(metrics_data):
    """Calculate the acceptance rate from new API format data."""
    results = []

    for day_data in metrics_data:
        date = day_data.get('day', 'Unknown')

        total_suggestions = day_data.get('code_generation_activity_count', 0)
        total_acceptances = day_data.get('code_acceptance_activity_count', 0)

        # Editor stats from totals_by_ide
        editor_stats = {}
        for ide_data in day_data.get('totals_by_ide', []):
            ide_name = ide_data.get('ide', 'unknown')
            editor_stats[ide_name] = {
                'suggestions': ide_data.get('code_generation_activity_count', 0),
                'acceptances': ide_data.get('code_acceptance_activity_count', 0),
                'rate': 0
            }

        # Language stats from totals_by_language_feature (code_completion only)
        language_stats = {}
        for lf_data in day_data.get('totals_by_language_feature', []):
            lang_name = lf_data.get('language', 'unknown')
            suggestions = lf_data.get('code_generation_activity_count', 0)
            acceptances = lf_data.get('code_acceptance_activity_count', 0)

            if lang_name not in language_stats:
                language_stats[lang_name] = {
                    'suggestions': 0,
                    'acceptances': 0,
                    'rate': 0
                }
            language_stats[lang_name]['suggestions'] += suggestions
            language_stats[lang_name]['acceptances'] += acceptances

        # Calculate rates
        for stats in editor_stats.values():
            if stats['suggestions'] > 0:
                stats['rate'] = (stats['acceptances'] / stats['suggestions']) * 100

        for stats in language_stats.values():
            if stats['suggestions'] > 0:
                stats['rate'] = (stats['acceptances'] / stats['suggestions']) * 100

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


def calculate_acceptance_rate_legacy(metrics_data):
    """Calculate the acceptance rate from legacy API format data."""
    results = []

    for day_data in metrics_data:
        date = day_data.get('date', 'Unknown')

        total_suggestions = 0
        total_acceptances = 0
        language_stats = {}
        editor_stats = {}

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

                    total_suggestions += suggestions
                    total_acceptances += acceptances

                    editor_stats[editor_name]['suggestions'] += suggestions
                    editor_stats[editor_name]['acceptances'] += acceptances

                    if lang_name not in language_stats:
                        language_stats[lang_name] = {
                            'suggestions': 0,
                            'acceptances': 0,
                            'rate': 0
                        }
                    language_stats[lang_name]['suggestions'] += suggestions
                    language_stats[lang_name]['acceptances'] += acceptances

        for stats in editor_stats.values():
            if stats['suggestions'] > 0:
                stats['rate'] = (stats['acceptances'] / stats['suggestions']) * 100

        for stats in language_stats.values():
            if stats['suggestions'] > 0:
                stats['rate'] = (stats['acceptances'] / stats['suggestions']) * 100

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
    results = sorted(results, key=lambda x: x['date'])
    print("\n組織のGitHub Copilot Acceptance Rate:")
    print("=" * 60)

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

    total_suggestions = sum(day['total_suggestions'] for day in results)
    total_acceptances = sum(day['total_acceptances'] for day in results)
    overall_rate = 0
    if total_suggestions > 0:
        overall_rate = (total_acceptances / total_suggestions) * 100

    print(f"\n全体の統計:")
    print(f"  全体の採用率: {overall_rate:.2f}%")
    print(f"  全体の提案数: {total_suggestions}")
    print(f"  全体の採用数: {total_acceptances}")

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
    parser = argparse.ArgumentParser(
        description='GitHub Copilotのメトリクスデータから組織のAcceptance Rateを抽出します。')
    parser.add_argument('file_path', nargs='?', default=None,
                        help='メトリクスデータのJSONファイルパス (デフォルト: /app/copilot_metrics.json)')
    parser.add_argument('--api', action='store_true',
                        help='GitHub APIから直接メトリクスを取得する')
    parser.add_argument('--org', default='crowdworksjp',
                        help='GitHub Organization名 (デフォルト: crowdworksjp)')
    parser.add_argument('--report-type', choices=['1-day', '28-day'], default='28-day',
                        help='レポートタイプ (デフォルト: 28-day)')
    parser.add_argument('--day', default=None,
                        help='1-dayレポートの日付 (YYYY-MM-DD形式)')
    parser.add_argument('--start-date', default=None,
                        help='取得開始日 (YYYY-MM-DD形式)')
    parser.add_argument('--end-date', default=None,
                        help='取得終了日 (YYYY-MM-DD形式、省略時: 2日前)')
    parser.add_argument('--days', type=int, default=None,
                        help='取得日数 (--end-dateからN日前を--start-dateとする簡易指定)')
    parser.add_argument('--output', default=None,
                        help='レポートデータの保存先ファイルパス')

    args = parser.parse_args()

    # --start-date / --days が指定されていれば --api を暗黙的に有効化
    use_date_range = args.start_date or args.days
    if use_date_range:
        args.api = True

    if args.api and use_date_range:
        # 期間指定: end_date を確定（省略時は2日前、APIの反映ラグを考慮）
        if args.end_date:
            end_date = args.end_date
        else:
            end_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')

        # start_date を確定（--start-date 優先、なければ --days から算出）
        if args.start_date:
            start_date = args.start_date
        else:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            start_date = (end_dt - timedelta(days=args.days - 1)).strftime('%Y-%m-%d')

        metrics_data = fetch_date_range(args.org, start_date, end_date)
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(metrics_data, f, ensure_ascii=False, indent=2)
            print(f"レポートデータを保存しました: {args.output}")
        results = calculate_acceptance_rate_new(metrics_data)
    elif args.api:
        raw_data = fetch_from_api(args.org, args.report_type, args.day)
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(raw_data, f, ensure_ascii=False, indent=2)
            print(f"レポートデータを保存しました: {args.output}")
        metrics_data = normalize_new_api_data(raw_data)
        results = calculate_acceptance_rate_new(metrics_data)
    else:
        if args.file_path:
            file_path = args.file_path
        else:
            file_path = Path.home() / 'Downloads' / 'copilot_metrics.json'

        print(f"メトリクスデータを読み込み中: {file_path}")
        metrics_data = load_metrics_data(file_path)

        if not metrics_data:
            print("エラー: メトリクスデータが空です。")
            sys.exit(1)

        fmt = detect_format(metrics_data)
        if fmt == 'new':
            all_days = []
            for item in metrics_data:
                all_days.extend(normalize_new_api_data(item))
            results = calculate_acceptance_rate_new(all_days)
        else:
            results = calculate_acceptance_rate_legacy(metrics_data)

    print_results(results)


if __name__ == "__main__":
    main()
