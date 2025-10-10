document.addEventListener('DOMContentLoaded', () => {
  const themeToggleButton = document.getElementById('theme-toggle-button');
  const modeIcon = document.getElementById('mode-icon');
  const darkModeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

  // ライトモードを設定
  const setLightMode = () => {
    document.documentElement.setAttribute('theme', 'light');
    if (modeIcon) {
      modeIcon.textContent = 'dark_mode';
    }
    localStorage.setItem('theme', 'light');
  };

  // ダークモードを設定
  const setDarkMode = () => {
    document.documentElement.setAttribute('theme', 'dark');
    if (modeIcon) {
      modeIcon.textContent = 'light_mode';
    }
    localStorage.setItem('theme', 'dark');
  };

  // モードを切り替え
  const toggleMode = () => {
    document.body.classList.add('enable-transitions');

    if (document.documentElement.getAttribute('theme') === 'dark') {
      setLightMode();
    } else {
      setDarkMode();
    }
  };

  // ページ読み込み時のテーマ適用
  const loadTheme = () => {
    const savedTheme = localStorage.getItem('theme');
    // ユーザーの保存設定があればそれを優先
    if (savedTheme === 'dark') {
      setDarkMode();
    } else if (savedTheme === 'light') {
      setLightMode();
    } else {
      // 保存設定がなければ、システムのテーマ設定に従う
      if (darkModeMediaQuery.matches) {
        setDarkMode();
      } else {
        setLightMode();
      }
    }
  };

  // システムのテーマ変更を検知した場合の処理
  const handleSystemThemeChange = (event) => {
    if (event.matches) {
      setDarkMode();
    } else {
      setLightMode();
    }
  };

  // イベントリスナーを設定
  if (themeToggleButton) {
    themeToggleButton.addEventListener('click', toggleMode);
  }
  darkModeMediaQuery.addEventListener('change', handleSystemThemeChange);

  // 初期読み込み
  loadTheme();
});