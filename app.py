# app.py
import io
import sys
import os
import importlib.util
import traceback  # 追加
from flask import Flask, render_template, request
from line_profiler import LineProfiler
import time

app = Flask(__name__)

# プロファイリング結果を解析し、辞書形式に変換する関数
def parse_profile_output(profile_output):
    lines = profile_output.strip().split('\n')
    parsed_data = []

    # 最初の9行をスキップ
    for i, line in enumerate(lines):
        if i < 9:
            continue  # 最初の9行を無視する

        parts = line.split()

        # partsが空だったり要素が少なすぎる場合はスキップ
        if len(parts) == 0:
            continue

        # 実行回数や実行時間が存在しない行に '-' を追加
        if len(parts) < 6:
            parsed_data.append({
                'line_no': parts[0] if len(parts) > 0 else '-',
                'hits': '-',
                'time': '-',
                'per_hit': '-',
                'percentage': '-',
                'code': ' '.join(parts[1:]) if len(parts) > 1 else '-'  # parts[1]が存在しない場合も考慮
            })
        else:
            # 正常なデータ行の処理
            parsed_data.append({
                'line_no': parts[0],  # 行番号
                'hits': parts[1],     # 実行回数
                'time': parts[2],     # 実行時間
                'per_hit': parts[3],  # 1回あたりの実行時間
                'percentage': parts[4],  # 全体に対する割合
                'code': ' '.join(parts[5:])  # コード内容は残り全部を1行で表示
            })

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
