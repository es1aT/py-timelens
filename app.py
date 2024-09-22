import io
import sys
import os
import importlib.util
import traceback
from flask import Flask, render_template, request
from line_profiler import LineProfiler
import tracemalloc  # 追加

app = Flask(__name__)

def parse_profile_output(profile_output):
    lines = profile_output.strip().split('\n')
    parsed_data = []

    for i, line in enumerate(lines):
        if i < 9 or not line.strip():
            continue

        try:
            parsed_data.append({
                'hits': line[6:20].strip() or '-',
                'time': line[18:29].strip() or '-',
                'per_hit': line[38:47].strip() or '-',
                'code': line[53:] or '-'
            })
        except Exception as e:
            print(f"パースエラー: {e}, line: {line}")

    return parsed_data

def handle_io_capture(stdin_input):
    old_stdin, old_stdout, old_stderr = sys.stdin, sys.stdout, sys.stderr
    sys.stdin = io.StringIO(stdin_input)
    sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
    return old_stdin, old_stdout, old_stderr

def reset_io_capture(old_stdin, old_stdout, old_stderr):
    sys.stdin, sys.stdout, sys.stderr = old_stdin, old_stdout, old_stderr

def run_profiled_code(code, stdin_input):
    result, output, error = "", "", ""
    temp_filename = "judge.py"
    profiler = LineProfiler()

    with open(temp_filename, 'w', encoding='utf-8') as f:
        f.write(f"def user_function():\n{indent_code(code)}\n")

    old_stdin, old_stdout, old_stderr = handle_io_capture(stdin_input)

    try:
        tracemalloc.start()  # メモリ計測開始

        spec = importlib.util.spec_from_file_location("judge", temp_filename)
        temp_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(temp_module)

        profiler.add_function(temp_module.user_function)
        profiler.enable_by_count()
        temp_module.user_function()
        profiler.disable_by_count()

        output = sys.stdout.getvalue()
        error = sys.stderr.getvalue()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        memory_usage = peak / 1024  # KBに変換

        if not error:
            profile_output = io.StringIO()
            profiler.print_stats(stream=profile_output)
            result = profile_output.getvalue()

    except Exception:
        error = traceback.format_exc()
        memory_usage = 0
    finally:
        reset_io_capture(old_stdin, old_stdout, old_stderr)
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    return result, output, error, memory_usage

def indent_code(code):
    return '\n'.join(['    ' + line for line in code.splitlines()])

@app.route('/', methods=['GET', 'POST'])
def index():
    output, error, code, stdin_input = '', '', '', ''
    exec_time = 0.0
    status, profiled_output = '', []
    memory_usage = 0.0

    if request.method == 'POST':
        code = request.form['code']
        stdin_input = request.form.get('stdin', '')

        try:
            profiled_output_raw, output, error, memory_usage = run_profiled_code(code, stdin_input)
            profiled_output = parse_profile_output(profiled_output_raw)

            total_exec_time = 0.0

            for i, line in enumerate(profiled_output):
                line['line_no'] = i + 1
                line['hits'] = int(line['hits']) if line['hits'] != '-' else 0
                line['time'] = float(line['time']) if line['time'] != '-' else 0.0
                line['per_hit'] = float(line['per_hit']) if line['per_hit'] != '-' else 0.0
                total_exec_time += line['time']

            exec_time = total_exec_time / 1000000  # nsをmsに変換

            status = '成功' if not error else '失敗'
        except Exception as e:
            error = str(e)
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
        profiled_output=profiled_output
    )

if __name__ == '__main__':
    app.run(debug=True)
