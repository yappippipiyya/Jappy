document.addEventListener('DOMContentLoaded', () => {
  const bandSelector = document.getElementById('band-selector');

  // バンドセレクターが変更されたらページをリロード
  bandSelector.addEventListener('change', () => {
    const selectedBandId = bandSelector.value;
    window.location.href = `/band-practice?band_id=${selectedBandId}`;
  });

  // 編集モードかどうかを判定 (チェックボックスの存在で判定)
  const isEditMode = document.querySelector('.schedule-checkbox') !== null;

  if (isEditMode) {
    const saveStatus = document.getElementById('save-status');
    const allCheckboxes = document.querySelectorAll('.schedule-checkbox');
    const dateHeaders = document.querySelectorAll('.date-header');
    const timeLabels = document.querySelectorAll('.time-label');
    let isDirty = false;

    // チェックボックスが変更されたら、変更フラグを立てる
    allCheckboxes.forEach(checkbox => {
      checkbox.addEventListener('change', () => {
        isDirty = true;
        saveStatus.textContent = '変更あり';
      });
    });

    // 3秒ごとに変更をチェックして自動保存
    setInterval(async () => {
      if (!isDirty) return;

      saveStatus.textContent = '保存中...';
      const scheduleData = collectScheduleData();
      const bandId = parseInt(bandSelector.value, 10);

      try {
        const response = await fetch('/band-practice/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            band_id: bandId,
            schedule: scheduleData,
          }),
        });

        if (response.ok) {
          isDirty = false;
          saveStatus.textContent = '保存済み';
        } else {
          saveStatus.textContent = '保存に失敗しました';
        }
      } catch (error) {
        console.error('Error saving schedule:', error);
        saveStatus.textContent = 'エラーが発生しました';
      }
    }, 3000);

    // 現在のチェックボックスの状態からスケジュールデータを収集する関数
    function collectScheduleData() {
      const schedule = {};
      allCheckboxes.forEach(checkbox => {
        const date = checkbox.dataset.date;
        const hour = parseInt(checkbox.dataset.hour, 10);

        if (!schedule[date]) {
          schedule[date] = Array(24).fill(0);
        }
        schedule[date][hour] = checkbox.checked ? 1 : 0;
      });
      return schedule;
    }

    // 縦軸・横軸タップでの一括チェック/解除機能
    dateHeaders.forEach(header => {
        header.addEventListener('click', () => {
        const targetDate = header.dataset.date;
        const columnCheckboxes = Array.from(allCheckboxes).filter(cb => cb.dataset.date === targetDate);
        const targetCheckedState = !columnCheckboxes.every(cb => cb.checked);
        let changedCount = 0;
        columnCheckboxes.forEach(cb => {
            if (cb.checked !== targetCheckedState) {
              cb.checked = targetCheckedState;
              changedCount++;
            }
            cb.closest('.schedule-cell').classList.add('cell-highlight');
        });
        if (changedCount > 0) {
            isDirty = true;
            saveStatus.textContent = '変更あり';
        }
        setTimeout(() => {
            columnCheckboxes.forEach(cb => cb.closest('.schedule-cell').classList.remove('cell-highlight'));
        }, 300);
        });
    });

    timeLabels.forEach(label => {
        label.addEventListener('click', () => {
        const targetHour = label.dataset.hour;
        const rowCheckboxes = Array.from(allCheckboxes).filter(cb => cb.dataset.hour === targetHour);
        const targetCheckedState = !rowCheckboxes.every(cb => cb.checked);
        let changedCount = 0;
        rowCheckboxes.forEach(cb => {
            if (cb.checked !== targetCheckedState) {
              cb.checked = targetCheckedState;
              changedCount++;
            }
            cb.closest('.schedule-cell').classList.add('cell-highlight');
        });
        if (changedCount > 0) {
            isDirty = true;
            saveStatus.textContent = '変更あり';
        }
        setTimeout(() => {
            rowCheckboxes.forEach(cb => cb.closest('.schedule-cell').classList.remove('cell-highlight'));
        }, 300);
        });
    });
  }

  // --- 以下は共通のスクロール処理 ---
  const tableWrapper = document.querySelector('.table-wrapper');
  if (tableWrapper) {
    const scheduleTable = tableWrapper.querySelector('.schedule-table');

    const toggleScrollClass = () => {
      if (tableWrapper.scrollLeft > 0) {
        scheduleTable.classList.add('is-scrolled');
      } else {
        scheduleTable.classList.remove('is-scrolled');
      }
    };
    toggleScrollClass();
    tableWrapper.addEventListener('scroll', toggleScrollClass, { passive: true });
  }

  const scrollToToday = () => {
    const tableWrapper = document.querySelector('.table-wrapper');
    if (!tableWrapper) return;

    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const todayDateString = `${year}-${month}-${day}`;

    const todayHeader = document.querySelector(`.date-header[data-date="${todayDateString}"]`);
    const cornerCell = document.querySelector('.corner-cell');

    if (todayHeader && cornerCell) {
      const columnWidth = todayHeader.offsetWidth;
      const offsetFactor = 0.8;
      const offset = columnWidth * offsetFactor;
      const scrollPosition = todayHeader.offsetLeft;
      const fixedColumnWidth = cornerCell.offsetWidth;
      const correctScrollLeft = scrollPosition - fixedColumnWidth - offset;
      tableWrapper.scrollLeft = Math.max(0, correctScrollLeft);
    }
  };
  scrollToToday();
});