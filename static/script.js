document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('codeForm');
  const loadingOverlay = document.getElementById('loadingOverlay');

  if (form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault(); // フォームのデフォルト動作を防ぐ

      // ローディングオーバーレイを表示
      if (loadingOverlay) {
        loadingOverlay.style.display = 'flex';
      }

      // ボタンを無効化
      const button = document.getElementById('executeButton');
      if (button) {
        button.disabled = true;
        button.textContent = '実行中...';
      }

      // フォームデータを取得
      const formData = new FormData(form);

      // サーバーに非同期リクエストを送信
      fetch('/', {
        method: 'POST',
        body: formData
      })
      .then(response => response.text())
      .then(html => {
        // サーバーからの HTML をパース
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');

        // 新しい出力結果とエラーメッセージを取得
        const newOutputElement = doc.querySelector('.output-section pre');
        const newErrorElement = doc.querySelector('.error-section pre');

        const newOutput = newOutputElement ? newOutputElement.innerHTML : '';
        const newError = newErrorElement ? newErrorElement.innerHTML : '';

        // 実行情報を取得
        const newStatusElement = doc.querySelector('.execution-info table tr:nth-child(1) td:nth-child(2)');
        const newExecTimeElement = doc.querySelector('.execution-info table tr:nth-child(2) td:nth-child(2)');
        const newMemoryUsageElement = doc.querySelector('.execution-info table tr:nth-child(3) td:nth-child(2)');

        const newStatus = newStatusElement ? newStatusElement.innerHTML : '';
        const newExecTime = newExecTimeElement ? newExecTimeElement.innerHTML : '';
        const newMemoryUsage = newMemoryUsageElement ? newMemoryUsageElement.innerHTML : '';

        // 既存のページに反映
        const outputPre = document.querySelector('.output-section pre');
        const errorPre = document.querySelector('.error-section pre');
        const executionInfoDiv = document.querySelector('.execution-info');

        if (outputPre) {
          outputPre.innerHTML = newOutput;
        }

        if (errorPre) {
          errorPre.innerHTML = newError;
        }

        if (executionInfoDiv) {
          executionInfoDiv.innerHTML = `
            <table>
              <tr>
                <td class="label-cell">ステータス</td>
                <td class="value-cell">${newStatus}</td>
              </tr>
              <tr>
                <td class="label-cell">実行時間</td>
                <td class="value-cell">${newExecTime}</td>
              </tr>
              <tr>
                <td class="label-cell">メモリ</td>
                <td class="value-cell">${newMemoryUsage}</td>
              </tr>
            </table>
          `;
        }
      })
      .catch(error => {
        console.error('Error:', error);
        // エラーメッセージを標準エラー表示エリアに表示
        const errorSection = document.querySelector('.error-section pre');
        if (errorSection) {
          errorSection.innerHTML = `実行中にエラーが発生しました: ${error}`;
        }
      })
      .finally(() => {
        // ローディングオーバーレイを非表示
        if (loadingOverlay) {
          loadingOverlay.style.display = 'none';
        }

        // ボタンを再度有効化
        if (button) {
          button.disabled = false;
          button.textContent = '実行';
        }
      });
    });
  }

  // Tabキーでインデントを挿入する機能
  const codeInput = document.getElementById('code-input');
  if (codeInput) {
    codeInput.addEventListener('keydown', function(e) {
      if (e.key === 'Tab') {
        e.preventDefault();  // デフォルトのタブ動作を防ぐ

        let start = this.selectionStart;
        let end = this.selectionEnd;

        const indent = '  '; // スペース2つ
        this.value = this.value.substring(0, start) + indent + this.value.substring(end);

        this.selectionStart = this.selectionEnd = start + indent.length;
      }
    });
  }
});
