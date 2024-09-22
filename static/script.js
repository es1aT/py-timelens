document.addEventListener("DOMContentLoaded", function () {
  const ctx = document.getElementById('profileChart').getContext('2d');

  // グラフのデータを受け取る
  const labels = profileData.labels;
  const codes = profileData.codes;
  const hitsData = profileData.hits;
  const timesData = profileData.times;

  // データセットを作成
  const datasets = [{
    label: '実行回数',
    data: hitsData,
    backgroundColor: hitsData.map((_, i) => {
      const codeLine = codes[i];
      if (codeLine.includes('input(') || codeLine.includes('print(') || codeLine.includes('import ')) {
        return 'rgba(192, 192, 192, 0.2)';
      } else {
        return 'rgba(75, 192, 192, 0.2)';
      }
    }),
    borderColor: hitsData.map((_, i) => {
      const codeLine = codes[i];
      if (codeLine.includes('input(') || codeLine.includes('print(') || codeLine.includes('import ')) {
        return 'rgba(192, 192, 192, 1)';
      } else {
        return 'rgba(75, 192, 192, 1)';
      }
    }),
    borderDash: hitsData.map((_, i) => {
      const codeLine = codes[i];
      if (codeLine.includes('input(') || codeLine.includes('print(') || codeLine.includes('import ')) {
        return [5, 5];
      } else {
        return [];
      }
    }),
    borderWidth: 1
  },
  {
    label: '総実行時間 (ns)',
    data: timesData,
    backgroundColor: timesData.map((_, i) => {
      const codeLine = codes[i];
      if (codeLine.includes('input(') || codeLine.includes('print(') || codeLine.includes('import ')) {
        return 'rgba(255, 192, 192, 0.2)';
      } else {
        return 'rgba(255, 99, 132, 0.2)';
      }
    }),
    borderColor: timesData.map((_, i) => {
      const codeLine = codes[i];
      if (codeLine.includes('input(') || codeLine.includes('print(') || codeLine.includes('import ')) {
        return 'rgba(255, 192, 192, 1)';
      } else {
        return 'rgba(255, 99, 132, 1)';
      }
    }),
    borderDash: timesData.map((_, i) => {
      const codeLine = codes[i];
      if (codeLine.includes('input(') || codeLine.includes('print(') || codeLine.includes('import ')) {
        return [5, 5];
      } else {
        return [];
      }
    }),
    borderWidth: 1
  }];

  // グラフの初期設定
  let currentDatasetIndex = 0;  // 初期表示は実行回数
  const profileChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [datasets[currentDatasetIndex]],
    },
    options: {
      scales: {
        y: {
          beginAtZero: true
        }
      },
      onClick: function(event, elements) {
        if (elements.length > 0) {
          const index = elements[0].index;
          const label = labels[index];

          // クリックされた行番号に対応する要素にスクロール
          const elementId = `line-${label}`;
          const targetElement = document.getElementById(elementId);

          if (targetElement) {
            targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: function(tooltipItem) {
              const hits = hitsData[tooltipItem.dataIndex];
              const time = timesData[tooltipItem.dataIndex];
              const code = codes[tooltipItem.dataIndex].trim();
              if (currentDatasetIndex === 0) {
                return `実行回数: ${hits}, コード: ${code}`;
              } else {
                return `総実行時間 (ns): ${time}, コード: ${code}`;
              }
            }
          }
        }
      }
    }
  });

  // ラジオボタンの選択状態によってデータセットを変更する
  const radioButtons = document.querySelectorAll('input[name="graph-option"]');
  radioButtons.forEach(function(button) {
    button.addEventListener('change', function() {
      if (this.value === 'hits') {
        currentDatasetIndex = 0;
      } else {
        currentDatasetIndex = 1;
      }
      profileChart.data.datasets = [datasets[currentDatasetIndex]];
      profileChart.update();
    });
  });

  // タブキーによるインデントを有効にする
  const codeInput = document.getElementById("code-input");
  if (codeInput) {
    codeInput.addEventListener("keydown", function (e) {
      if (e.key === "Tab") {
        e.preventDefault();
        let start = this.selectionStart;
        let end = this.selectionEnd;
        const indent = "  ";
        this.value =
          this.value.substring(0, start) +
          indent +
          this.value.substring(end);
        this.selectionStart = this.selectionEnd = start + indent.length;
      }
    });
  }
});
