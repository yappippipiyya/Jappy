document.addEventListener('DOMContentLoaded', () => {
  // ツールチップ用の要素をbodyの末尾に作成
  const tooltip = document.createElement('div');
  tooltip.className = 'schedule-tooltip';
  document.body.appendChild(tooltip);

  // ツールチップを表示する関数
  const showTooltip = (event) => {
    const cell = event.target.closest('td');
    const members = cell.dataset.members;

    if (!members) return;

    // メンバー名をリスト表示に整形
    const membersArray = members.split(',');
    const listHtml = membersArray.map(name => `<li>${name}</li>`).join('');
    tooltip.innerHTML = `<ul>${listHtml}</ul>`;
    
    // ツールチップの位置を調整
    tooltip.style.left = `${event.pageX + 10}px`;
    tooltip.style.top = `${event.pageY + 10}px`;

    // 表示
    tooltip.classList.add('is-visible');
  };

  // ツールチップを非表示にする関数
  const hideTooltip = () => {
    tooltip.classList.remove('is-visible');
  };

  const scheduleCells = document.querySelectorAll('.schedule-table td[data-members]');

  scheduleCells.forEach(cell => {
    // PC向け: マウスが乗ったら表示、離れたら非表示
    cell.addEventListener('mouseenter', showTooltip);
    cell.addEventListener('mouseleave', hideTooltip);

    // スマホ向け: タップで表示/非表示を切り替え
    cell.addEventListener('click', (event) => {
      // 既に表示されている場合は非表示にする
      if (tooltip.classList.contains('is-visible')) {
        hideTooltip();
      } else {
        showTooltip(event);
      }
      event.stopPropagation(); // ボディのクリックイベントが発火しないようにする
    });
  });

  // ツールチップの外側をクリックしたら非表示にする
  document.body.addEventListener('click', () => {
    if (tooltip.classList.contains('is-visible')) {
      hideTooltip();
    }
  });
    // --- 削除確認の処理 ---
  const deleteForm = document.getElementById('delete-band-form');

  if (deleteForm) {
    deleteForm.addEventListener('submit', (event) => {
      // 確認ダイアログで「いいえ」が押されたらフォームの送信を中止
      if (!confirm('本当にこのバンドを削除しますか？\nこの操作は元に戻せません。')) {
        event.preventDefault();
      }
    });
  }
});

