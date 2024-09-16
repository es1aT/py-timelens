# fu.pyの内容を関数化します
import io
import sys
import os
import importlib.util
from line_profiler import LineProfiler

def run_profiled_code(code, stdin_input):
    result = ""

    # 改行コードを統一
    stdin_input = stdin_input.replace('\r\n', '\n').replace('\r', '\n')

    # 複数の標準入力を処理できるようにリスト化
    stdin_values = stdin_input.split('\n')

    # ユーザーの入力したコードに input() の代わりに標準入力値を挿入
    modified_code = code
    for value in stdin_values:
        modified_code = modified_code.replace("input()", f'"{value}"', 1)

    # ユーザーの入力したコードを一時ファイルに保存
    temp_filename = "temp_user_code.py"
    with open(temp_filename, 'w', encoding='utf-8') as f:
        f.write(f"def user_function():\n{indent_code(modified_code)}\n")

    # 標準出力をキャプチャ
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    # プロファイラーをセットアップ
    profiler = LineProfiler()

    try:
        # モジュールとして一時ファイルをインポート
        spec = importlib.util.spec_from_file_location("temp_user_code", temp_filename)
        temp_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(temp_module)

        profiler.add_function(temp_module.user_function)

        # プロファイリングと関数実行
        profiler.enable_by_count()
        temp_module.user_function()  # 関数として実行
        profiler.disable_by_count()

        # プロファイリング結果を取得
        result = sys.stdout.getvalue()

        # プロファイリングの結果を表示
        profile_output = io.StringIO()
        profiler.print_stats(stream=profile_output)
        result += "\n" + profile_output.getvalue()

    except Exception as e:
        result = f"エラー: {str(e)}"

    finally:
        # 標準出力を元に戻す
        sys.stdout = old_stdout

        # 一時ファイルを削除
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    return result

def indent_code(code):
    """ ユーザーコードをインデントして関数として実行可能にする """
    return '\n'.join(['    ' + line for line in code.splitlines()])
