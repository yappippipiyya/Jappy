document.addEventListener('DOMContentLoaded', () => {
  const bandSelector = document.getElementById('band-selector');
  const saveStatus = document.getElementById('save-status');
  let isDirty = false; // スケジュールに変更があったかどうかのフラグ

  // 新規追加: 日付ヘッダーと時間ラベルの要素を取得
  const dateHeaders = document.querySelectorAll('.date-header');
  const timeLabels = document.querySelectorAll('.time-label');
  const allCheckboxes = document.querySelectorAll('.schedule-checkbox'); // 全てのチェックボックス

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

  // 5秒ごとに変更をチェックして自動保存
  setInterval(async () => {
    if (!isDirty) return; // 変更がなければ何もしない

    saveStatus.textContent = '保存中...';
    const scheduleData = collectScheduleData();
    const bandId = bandSelector.value;

    try {
      const response = await fetch('/schedule-manage/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          band_id: bandId,
          schedule: scheduleData
        }),
      });

      if (response.ok) {
        isDirty = false; // 保存成功したらフラグを戻す
        saveStatus.textContent = '保存済み';
      } else {
        saveStatus.textContent = '保存に失敗しました';
      }
    } catch (error) {
      console.error('Error saving schedule:', error);
      saveStatus.textContent = 'エラーが発生しました';
    }
  }, 5000);

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

          // デフォルトスケジュールに該当データがあり、それが1(可能)ならチェック
          const shouldBeChecked = defaultSchedule[date] && defaultSchedule[date][hour] === 1;
          if (checkbox.checked !== shouldBeChecked) {
             checkbox.checked = shouldBeChecked;
             isDirty = true; // 変更があったのでフラグを立てる
             saveStatus.textContent = '変更あり';
          }
        });

        alert('デフォルトのスケジュールを適用しました。変更は数秒後に自動保存されます。');

      } catch (error) {
        console.error('Error applying default schedule:', error);
        alert('デフォルトのスケジュールの適用に失敗しました。');
      }
    });
  }

  // --- 新規追加: 縦軸・横軸タップでの一括チェック/解除機能 ---

  // 列（日付）ヘッダーのクリックイベント
  dateHeaders.forEach(header => {
    header.addEventListener('click', (event) => {
      const targetDate = header.dataset.date;
      // 該当する列のチェックボックスをフィルタリング
      const columnCheckboxes = Array.from(allCheckboxes).filter(cb => cb.dataset.date === targetDate);

      // 現在の列のチェック状態を確認
      const allChecked = columnCheckboxes.every(cb => cb.checked);
      // 全てチェック済みなら解除、そうでなければ全てチェックする状態を決定
      const targetCheckedState = !allChecked;

      let changedCount = 0;
      columnCheckboxes.forEach(cb => {
        if (cb.checked !== targetCheckedState) {
          cb.checked = targetCheckedState;
          changedCount++;
        }
      });

      if (changedCount > 0) {
        isDirty = true;
        saveStatus.textContent = '変更あり';
      }

      // 列をハイライトする処理
      columnCheckboxes.forEach(cb => {
        // チェックボックスの親セルにハイライトクラスを追加
        cb.closest('.schedule-cell').classList.add('cell-highlight');
      });
      // 300ミリ秒後にハイライトを解除
      setTimeout(() => {
        columnCheckboxes.forEach(cb => {
          cb.closest('.schedule-cell').classList.remove('cell-highlight');
        });
      }, 300);
    });
  });

  // 行（時間）ラベルのクリックイベント
  timeLabels.forEach(label => {
    label.addEventListener('click', (event) => {
      const targetHour = label.dataset.hour;
      // 該当する行のチェックボックスをフィルタリング
      const rowCheckboxes = Array.from(allCheckboxes).filter(cb => cb.dataset.hour === targetHour);

      // 現在の行のチェック状態を確認
      const allChecked = rowCheckboxes.every(cb => cb.checked);
      // 全てチェック済みなら解除、そうでなければ全てチェックする状態を決定
      const targetCheckedState = !allChecked;

      let changedCount = 0;
      rowCheckboxes.forEach(cb => {
        if (cb.checked !== targetCheckedState) {
          cb.checked = targetCheckedState;
          changedCount++;
        }
      });

      if (changedCount > 0) {
        isDirty = true;
        saveStatus.textContent = '変更あり';
      }

      // 行をハイライトする処理
      rowCheckboxes.forEach(cb => {
        // チェックボックスの親セルにハイライトクラスを追加
        cb.closest('.schedule-cell').classList.add('cell-highlight');
      });
      // 300ミリ秒後にハイライトを解除
      setTimeout(() => {
        rowCheckboxes.forEach(cb => {
          cb.closest('.schedule-cell').classList.remove('cell-highlight');
        });
      }, 300);
    });
  });
});