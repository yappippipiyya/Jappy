document.addEventListener('DOMContentLoaded', () => {
  const bandSelector = document.getElementById('band-selector');
  const saveStatus = document.getElementById('save-status');
  const commentInput = document.getElementById('comment-input'); // 備考欄の要素を取得
  let isDirty = false; // スケジュールや備考欄に変更があったかどうかのフラグ

  const dateHeaders = document.querySelectorAll('.date-header');
  const timeLabels = document.querySelectorAll('.time-label');
  const allCheckboxes = document.querySelectorAll('.schedule-checkbox');

  // バンドセレクターが変更されたらページをリロード
  bandSelector.addEventListener('change', () => {
    const selectedBandId = bandSelector.value;
    window.location.href = `/schedule-manage?band_id=${selectedBandId}`;
  });

  // チェックボックスが変更されたら、変更フラグを立てる
  allCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', () => {
      isDirty = true;
      saveStatus.textContent = '変更あり';
    });
  });

  // 備考欄が変更されたら、変更フラグを立てる
  if (commentInput) {
    commentInput.addEventListener('input', () => {
      isDirty = true;
      saveStatus.textContent = '変更あり';
    });
  }

  // 3秒ごとに変更をチェックして自動保存
  setInterval(async () => {
    if (!isDirty) return;

    saveStatus.textContent = '保存中...';
    const scheduleData = collectScheduleData();
    const bandId = bandSelector.value;
    // 備考欄が存在する場合のみ、その値を取得
    const comment = commentInput ? commentInput.value : '';

    try {
      const response = await fetch('/schedule-manage/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          band_id: bandId,
          schedule: scheduleData,
          comment: comment,
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
        // 表示されている時間帯に関わらず、常に24時間分の配列を確保
        schedule[date] = Array(24).fill(0);
      }
      schedule[date][hour] = checkbox.checked ? 1 : 0;
    });
    return schedule;
  }

  // 「デフォルトを適用」ボタンの処理
  const applyDefaultBtn = document.getElementById('apply-default-btn');
  if (applyDefaultBtn) {
    applyDefaultBtn.addEventListener('click', async () => {
      if (!confirm('現在のチェック状態が、デフォルトのスケジュールで上書きされます。よろしいですか？')) {
        return;
      }
      try {
        const response = await fetch('/schedule-manage/default-schedule');
        if (!response.ok) throw new Error('Failed to fetch default schedule');
        const defaultSchedule = await response.json();
        allCheckboxes.forEach(checkbox => {
          const date = checkbox.dataset.date;
          const hour = parseInt(checkbox.dataset.hour, 10);
          const shouldBeChecked = defaultSchedule[date] && defaultSchedule[date][hour] === 1;
          if (checkbox.checked !== shouldBeChecked) {
            checkbox.checked = shouldBeChecked;
            isDirty = true; // 変更があったことをマーク
          }
        });
        if (isDirty) {
          saveStatus.textContent = '変更あり'; // 変更があった場合のみ表示を更新
        }
      } catch (error) {
        console.error('Error applying default schedule:', error);
        alert('デフォルトのスケジュールの適用に失敗しました。');
      }
    });
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