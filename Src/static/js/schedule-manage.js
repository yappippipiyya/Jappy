document.addEventListener('DOMContentLoaded', () => {
  const bandSelector = document.getElementById('band-selector');
  const saveStatus = document.getElementById('save-status');
  let isDirty = false; // スケジュールに変更があったかどうかのフラグ

  // バンドセレクターが変更されたらページをリロード
  bandSelector.addEventListener('change', () => {
    const selectedBandId = bandSelector.value;
    window.location.href = `/schedule-manage?band_id=${selectedBandId}`;
  });

  // チェックボックスが変更されたら、変更フラグを立てる
  document.querySelectorAll('.schedule-checkbox').forEach(checkbox => {
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
    document.querySelectorAll('.schedule-checkbox').forEach(checkbox => {
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

        document.querySelectorAll('.schedule-checkbox').forEach(checkbox => {
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
});