document.addEventListener('DOMContentLoaded', () => {
  const tooltip = document.getElementById('tooltip');
  const scheduleCells = document.querySelectorAll('.schedule-table tbody td:not(.time-label)');

  if (!tooltip) {
    console.error("エラー: ID 'tooltip' を持つツールチップ要素が見つかりませんでした。HTMLを確認してください。");
    return;
  }

  scheduleCells.forEach(cell => {
    if (cell.dataset.members) {
      cell.addEventListener('mouseover', (event) => {
        const count = cell.dataset.count;
        const members = cell.dataset.members;
        if (count > 0 && members) {
          tooltip.innerHTML = `<strong>${count}人参加可能:</strong><br>${members.replace(/,/g, '<br>')}`;
          tooltip.classList.add('is-visible');
          tooltip.style.left = `${event.pageX + 10}px`;
          tooltip.style.top = `${event.pageY + 10}px`;
        }
      });

      cell.addEventListener('mousemove', (event) => {
        if (tooltip.classList.contains('is-visible')) {
          tooltip.style.left = `${event.pageX + 10}px`;
          tooltip.style.top = `${event.pageY + 10}px`;
        }
      });

      cell.addEventListener('mouseout', () => {
        tooltip.classList.remove('is-visible');
      });

      cell.addEventListener('touchstart', (event) => {
        event.preventDefault();
        const count = cell.dataset.count;
        const members = cell.dataset.members;
        document.querySelectorAll('.schedule-tooltip.is-visible').forEach(t => t.classList.remove('is-visible'));
        if (count > 0 && members) {
          tooltip.innerHTML = `<strong>${count}人参加可能:</strong><br>${members.replace(/,/g, '<br>')}`;
          tooltip.classList.add('is-visible');
          const rect = cell.getBoundingClientRect();
          tooltip.style.left = `${rect.left + window.scrollX + rect.width / 2 - tooltip.offsetWidth / 2}px`;
          tooltip.style.top = `${rect.top + window.scrollY + rect.height + 5}px`;
        } else {
          tooltip.classList.remove('is-visible');
        }
      });
    }
  });

  document.addEventListener('touchstart', (event) => {
    if (!event.target.closest('.schedule-table tbody td') && !event.target.closest('.schedule-tooltip')) {
      tooltip.classList.remove('is-visible');
    }
  });

  window.addEventListener('scroll', () => {
    if (tooltip.classList.contains('is-visible')) {
    }
  });

  // --- スクロール検知機能を追加 ---
  const tableWrapper = document.querySelector('.table-wrapper');
  if (tableWrapper) {
    const scheduleTable = tableWrapper.querySelector('.schedule-table');

    const toggleScrollClass = () => {
      // scrollLeftが0より大きい（＝少しでも横にスクロールされている）場合
      if (tableWrapper.scrollLeft > 0) {
        scheduleTable.classList.add('is-scrolled');
      } else {
        scheduleTable.classList.remove('is-scrolled');
      }
    };

    toggleScrollClass();

    tableWrapper.addEventListener('scroll', toggleScrollClass, { passive: true });
  }
});