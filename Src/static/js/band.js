document.addEventListener('DOMContentLoaded', () => {
  const tooltip = document.getElementById('tooltip');
  const scheduleCells = document.querySelectorAll('.schedule-cell');

  scheduleCells.forEach(cell => {
    // マウスがセルに乗った時の処理
    cell.addEventListener('mouseover', (event) => {
      const count = cell.dataset.count;
      const members = cell.dataset.members;

      if (count > 0 && members) {
        tooltip.innerHTML = `<strong>${count}人参加可能:</strong><br>${members.replace(/,/g, '<br>')}`;
        tooltip.style.display = 'block';
      }
    });

    // マウスがセル上を移動する時の処理
    cell.addEventListener('mousemove', (event) => {
      // ツールチップがカーソルの少し右下に表示されるように調整
      tooltip.style.left = `${event.pageX + 10}px`;
      tooltip.style.top = `${event.pageY + 10}px`;
    });

    // マウスがセルから離れた時の処理
    cell.addEventListener('mouseout', () => {
      tooltip.style.display = 'none';
    });
  });
});