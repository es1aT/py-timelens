from flask import Flask, render_template, request
import subprocess
import tempfile
import os
import time
import psutil  # psutilをインポート
import threading

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    # 初期値の設定
    output = ''
    error = ''
    code = ''
    stdin_input = ''
    exec_time = 0.0  # 実行時間をミリ秒で保持
    memory_usage = 0  # メモリ使用量をKBで保持
    status = ''  # 実行ステータス

    if request.method == 'POST':
        code = request.form['code']
        stdin_input = request.form.get('stdin', '')

        # 改行コードを統一
        stdin_input = stdin_input.replace('\r\n', '\n').replace('\r', '\n')

        temp_file_name = ''
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(code)
                temp_file_name = temp_file.name

            # 実行開始時間を記録
            start_time = time.time()

            # サブプロセスを非同期で実行
            process = subprocess.Popen(
                ['python', temp_file_name],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True  # Python 3.7以降
                # Python 3.6以前の場合は、universal_newlines=True を使用
                # universal_newlines=True
            )

            # プロセスのPIDを取得してpsutilで監視
            try:
                p = psutil.Process(process.pid)
            except psutil.NoSuchProcess:
                p = None

            max_memory = 0  # 最大メモリ使用量を記録

            def monitor_memory():
                nonlocal max_memory
                try:
                    while process.poll() is None:
                        if p:
                            try:
                                mem = p.memory_info().rss / 1024  # メモリ使用量（KB）
                                if mem > max_memory:
                                    max_memory = mem
                            except psutil.NoSuchProcess:
                                break
                        time.sleep(0.1)  # 監視間隔を0.1秒に設定
                except Exception as e:
                    pass

            # メモリ監視を別スレッドで開始
            monitor_thread = threading.Thread(target=monitor_memory)
            monitor_thread.start()

            try:
                stdout, stderr = process.communicate(input=stdin_input, timeout=10)
                monitor_thread.join()
                memory_usage = max_memory
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                monitor_thread.join()
                memory_usage = max_memory
                raise subprocess.TimeoutExpired(process.args, 10)

            exec_time = (time.time() - start_time) * 1000  # 実行時間をミリ秒に変換

            output = stdout
            error = stderr

            # ステータスの判定
            if process.returncode == 0:
                status = '成功'
            else:
                status = '失敗'

        except subprocess.TimeoutExpired:
            output = ''
            error = '実行がタイムアウトしました'
            status = '時間超過'
            exec_time = 10000  # タイムアウト時間をミリ秒として設定

        except Exception as e:
            output = ''
            error = f'エラーが発生しました: {e}'
            status = '失敗'

        finally:
            if temp_file_name and os.path.exists(temp_file_name):
                os.remove(temp_file_name)

        # 結果をテンプレートに渡す
        return render_template(
            'index.html',
            output=output,
            error=error,
            code=code,
            stdin_input=stdin_input,
            exec_time=round(exec_time, 2),  # ミリ秒で小数点以下2桁まで
            memory_usage=round(memory_usage, 2),
            status=status
        )

    # GETリクエスト時にも全ての変数をテンプレートに渡す
    return render_template(
        'index.html',
        output=output,
        error=error,
        code=code,
        stdin_input=stdin_input,
        exec_time=exec_time,          # 0.0
        memory_usage=memory_usage,    # 0
        status=status                 # 空文字
    )

if __name__ == '__main__':
    app.run(debug=True)
