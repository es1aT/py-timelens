# app.py
import io
import sys
import os
import importlib.util
import traceback  # 追加
from flask import Flask, render_template, request
from line_profiler import LineProfiler
import time
import re

app = Flask(__name__)

def parse_profile_output(profile_output):
    lines = profile_output.strip().split('\n')
    parsed_data = []

    for i, line in enumerate(lines):
        if i < 9:  # 最初の9行を無視する
            continue

        # まず空行はスキップ
        if not line.strip():
            continue

        try:
            # 各列の範囲を固定して取得
            hits = line[10:22].strip() or '-'  # 実行回数 (列の開始位置: 10, 終了位置: 22)
            time = line[22:29].strip() or '-'  # 実行時間 (列の開始位置: 22, 終了位置: 36)
            per_hit = line[38:47].strip() or '-'  # 1回あたりの実行時間 (列の開始位置: 36, 終了位置: 50)
            code = line[53:] or '-'  # コード部分 (列の開始位置: 60以降)
            parsed_data.append({
                'hits': hits,
                'time': time,
                'per_hit': per_hit,
                'code': code
            })
        except Exception as e:
            print(f"パースエラー: {e}, line: {line}")  # どの行でエラーが発生しているか出力
            continue

    return parsed_data

# プロファイリング機能を実行する関数
def run_profiled_code(code, stdin_input):
    result = ""
    output = ""  # outputを空文字で初期化
    error = ""  # errorを空文字で初期化
    temp_filename = "torima.py"

    # ユーザーの入力したコードを一時ファイルに保存
    with open(temp_filename, 'w', encoding='utf-8') as f:
        f.write(f"def user_function():\n{indent_code(code)}\n")

    # 標準入力をキャプチャ
    old_stdin = sys.stdin
    sys.stdin = io.StringIO(stdin_input)  # 標準入力に指定された値をセット

    # 標準出力と標準エラーをキャプチャ
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    old_stderr = sys.stderr
    sys.stderr = io.StringIO()

    # プロファイラーをセットアップ
    profiler = LineProfiler()

    try:
        # モジュールとして一時ファイルをインポート
        spec = importlib.util.spec_from_file_location("torima", temp_filename)
        temp_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(temp_module)

        profiler.add_function(temp_module.user_function)

        # プロファイリングと関数実行
        profiler.enable_by_count()
        temp_module.user_function()  # 関数として実行
        profiler.disable_by_count()

        # 標準出力とエラーの結果を取得
        output = sys.stdout.getvalue()
        error = sys.stderr.getvalue()

        # プロファイリング結果を取得
        if not error:  # エラーがなければプロファイリング結果を追加
            profile_output = io.StringIO()
            profiler.print_stats(stream=profile_output)
            result += profile_output.getvalue()

    except Exception as e:
        # エラーが発生した場合、トレースバックのメッセージを取得
        tb = traceback.format_exc()

        # 最初に "File" が出てきた位置を取得
        start_idx = tb.find("File")
        # "^^^^^^^^^^^^^^^^^^^^^^^^^^^" が出てきた位置を取得
        end_idx = tb.find("^^^^^^^^^^^^^^^^^^^^^^^^^^^")

        # start_idx と end_idx が有効な場合、その部分を削除
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            tb = tb[:start_idx] + tb[end_idx + len("^^^^^^^^^^^^^^^^^^^^^^^^^^^"):]

        # エラーメッセージを取得
        error = tb

    finally:
        # 標準入力と標準出力、標準エラーを元に戻す
        sys.stdin = old_stdin
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        # 一時ファイルを削除
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    return result, output, error

# ユーザーのコードをインデントする関数
def indent_code(code):
    return '\n'.join(['    ' + line for line in code.splitlines()])

@app.route('/', methods=['GET', 'POST'])
def index():
    output = ''
    error = ''
    code = ''
    stdin_input = ''
    exec_time = 0.0
    memory_usage = 0
    status = ''
    profiled_output = []

    if request.method == 'POST':
        code = request.form['code']
        stdin_input = request.form.get('stdin', '')

        try:
            start_time = time.time()
            profiled_output_raw, output, error = run_profiled_code(code, stdin_input)
            exec_time = (time.time() - start_time) * 1000
            profiled_output = parse_profile_output(profiled_output_raw)

            # プロファイル結果に行番号を追加
            for i, line in enumerate(profiled_output):
                line['line_no'] = i + 1  # 1から始まる行番号
            print(profiled_output)
            status = '成功' if not error else '失敗'

        except Exception as e:
            error = f'{e}'
            status = '失敗'

        return render_template(
            'index.html',
            output=output,
            error=error,
            code=code,
            stdin_input=stdin_input,
            exec_time=round(exec_time, 2),
            memory_usage=round(memory_usage, 2),
            status=status,
            profiled_output=profiled_output  # 辞書形式のプロファイルデータ
        )

    return render_template(
        'index.html',
        output=output,
        error=error,
        code=code,
        stdin_input=stdin_input,
        exec_time=exec_time,
        memory_usage=memory_usage,
        status=status,
        profiled_output=profiled_output
    )

if __name__ == '__main__':
    app.run(debug=True)
