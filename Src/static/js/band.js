document.addEventListener('DOMContentLoaded', () => {
  const tooltip = document.getElementById('tooltip');
  // スケジュールデータを持つ<td>要素を選択するようにセレクタを修正
  // .time-labelクラスを持つ<td>要素（時間ラベル）は除外します
  const scheduleCells = document.querySelectorAll('.schedule-table tbody td:not(.time-label)');

  if (!tooltip) {
    console.error("エラー: ID 'tooltip' を持つツールチップ要素が見つかりませんでした。HTMLを確認してください。");
    return;
  }

  scheduleCells.forEach(cell => {
    // data-members属性があるセルのみにイベントを付与
    if (cell.dataset.members) {
      // マウスがセルに乗った時の処理
      cell.addEventListener('mouseover', (event) => {
        const count = cell.dataset.count;
        const members = cell.dataset.members;

        if (count > 0 && members) {
          tooltip.innerHTML = `<strong>${count}人参加可能:</strong><br>${members.replace(/,/g, '<br>')}`;
          // CSSクラスを追加してツールチップを表示
          tooltip.classList.add('is-visible');
          // 位置を即座に更新
          tooltip.style.left = `${event.pageX + 10}px`;
          tooltip.style.top = `${event.pageY + 10}px`;
        }
      });

      // マウスがセル上を移動する時の処理
      cell.addEventListener('mousemove', (event) => {
        // ツールチップがカーソルの少し右下に表示されるように調整
        if (tooltip.classList.contains('is-visible')) { // 表示中の場合のみ位置を更新
          tooltip.style.left = `${event.pageX + 10}px`;
          tooltip.style.top = `${event.pageY + 10}px`;
        }
      });

      // マウスがセルから離れた時の処理
      cell.addEventListener('mouseout', () => {
        // CSSクラスを削除してツールチップを非表示
        tooltip.classList.remove('is-visible');
      });

      // タップイベント（モバイル対応）
      cell.addEventListener('touchstart', (event) => {
        // デフォルトのタッチ動作（スクロールなど）を防止
        event.preventDefault();

        const count = cell.dataset.count;
        const members = cell.dataset.members;

        // 他のツールチップが表示されていたら非表示にする
        document.querySelectorAll('.schedule-tooltip.is-visible').forEach(t => t.classList.remove('is-visible'));

        if (count > 0 && members) {
          tooltip.innerHTML = `<strong>${count}人参加可能:</strong><br>${members.replace(/,/g, '<br>')}`;
          tooltip.classList.add('is-visible');

          // タップされたセルの下にツールチップを表示
          const rect = cell.getBoundingClientRect();
          tooltip.style.left = `${rect.left + window.scrollX + rect.width / 2 - tooltip.offsetWidth / 2}px`; // セルの中央に寄せる
          tooltip.style.top = `${rect.top + window.scrollY + rect.height + 5}px`; // セルのすぐ下に表示
        } else {
          tooltip.classList.remove('is-visible');
        }
      });
    }
  });

  // ツールチップ以外の場所をタップしたときにツールチップを非表示にするグローバルリスナー
  document.addEventListener('touchstart', (event) => {
    // イベントターゲットがスケジュールセルでもツールチップでもない場合
    if (!event.target.closest('.schedule-table tbody td') && !event.target.closest('.schedule-tooltip')) {
      tooltip.classList.remove('is-visible');
    }
  });

  // ツールチップの表示位置が画面外にならないように調整するリスナー (オプション)
  window.addEventListener('scroll', () => {
    if (tooltip.classList.contains('is-visible')) {
    }
  });
});