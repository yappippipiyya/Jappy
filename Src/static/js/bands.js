document.addEventListener('DOMContentLoaded', () => {
  // --- 1. バンドカードクリックによるページ遷移処理 ---
  const bandCards = document.querySelectorAll('.band-card');

  bandCards.forEach(card => {
    card.addEventListener('click', (event) => {
      // クリックされたのがコピーボタン等のアクションエリアでなければ遷移
      if (!event.target.closest('.band-actions')) {
        const token = card.dataset.token;
        if (token) {
          window.location.href = `/band?token=${token}`;
        }
      }
    });
  });


  // --- 2. 既存のコピーボタンの処理 ---
  const copyButtons = document.querySelectorAll('.copy-btn');

  copyButtons.forEach(button => {
    button.addEventListener('click', (event) => {
      // クリックされたボタンに関連する要素を取得
      const bandActions = event.target.closest('.band-actions');
      if (!bandActions) return;

      const urlInput = bandActions.querySelector('input[type="text"]');
      const feedbackElement = bandActions.querySelector('.copy-feedback');

      if (!urlInput || !feedbackElement) return;

      const urlToCopy = urlInput.value;

      // クリップボードにコピー
      navigator.clipboard.writeText(urlToCopy).then(() => {
        // 成功時のフィードバック
        feedbackElement.textContent = 'コピーしました！';
        feedbackElement.style.opacity = '1';

        // 2秒後にフィードバックを非表示にする
        setTimeout(() => {
          feedbackElement.style.opacity = '0';
        }, 2000);
      }).catch(err => {
        // 失敗時のフィードバック
        console.error('URLのコピーに失敗しました: ', err);
        feedbackElement.textContent = 'コピーに失敗しました';
        feedbackElement.style.color = '#fff';
        feedbackElement.style.backgroundColor = '#e74c3c'; // エラー色
        feedbackElement.style.opacity = '1';

        setTimeout(() => {
          feedbackElement.style.opacity = '0';
           // 少し待ってから元のスタイルに戻す
          setTimeout(() => {
            feedbackElement.style.color = '#fff';
            feedbackElement.style.backgroundColor = '#2c3e50';
          }, 300);
        }, 2000);
      });
    });
  });
});