// firestorm-pr-180s 瀏覽器版面與基礎健康檢查（game-build-pipeline S3）。
//
// 用法：
//   1. 於倉庫根目錄啟動本機伺服器：python3 -m http.server 8781 --bind 127.0.0.1
//   2. 在瀏覽器開啟 http://127.0.0.1:8781/index.html（或 samples/ 樣張）
//   3. 將本檔貼入 DevTools Console 執行（或由瀏覽器代理透過 JS 工具執行）。
//   4. 任何 FAIL 都不得交付。
//
// 以兩個隱藏 iframe 同時檢查桌面 (1360x900) 與手機 (390x844)：
// - 無 uncaught runtime error
// - 無橫向捲軸 (scrollWidth <= clientWidth + 1)
// - 若頁面含遊戲元件（按鈕、textarea、canvas），檢查均未超出視窗寬度且可視大小正常
(async () => {
  const SIZES = [[1360, 900], [390, 844]];
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const lines = [];
  let fails = 0, warns = 0;
  const out = (ok, size, msg) => { if (!ok) fails++; lines.push((ok ? 'PASS ' : 'FAIL ') + size + '  ' + msg); };
  const warn = (size, msg) => { warns++; lines.push('WARN ' + size + '  ' + msg); };

  for (const [w, h] of SIZES) {
    const size = w + 'x' + h;
    const f = document.createElement('iframe');
    f.style.cssText = 'position:fixed;left:-10000px;top:0;border:0;width:' + w + 'px;height:' + h + 'px';
    f.src = location.href.split('#')[0];
    const runtimeErrors = [];
    document.body.appendChild(f);
    await new Promise(r => {
      f.onload = r;
    });
    f.contentWindow.addEventListener('error', e => runtimeErrors.push(e.message || 'error'));
    await wait(1200);

    const d = f.contentDocument, W = f.contentWindow;
    out(runtimeErrors.length === 0, size, 'Runtime error 數 ' + runtimeErrors.length + (runtimeErrors.length ? '：' + runtimeErrors.join(' / ') : ''));

    const overflowX = d.documentElement.scrollWidth - d.documentElement.clientWidth;
    out(overflowX <= 1, size, '橫向溢出 ' + overflowX + 'px (scrollWidth=' + d.documentElement.scrollWidth + ', clientWidth=' + d.documentElement.clientWidth + ')');

    const canvases = [...d.querySelectorAll('canvas')];
    const brokenCanvases = canvases.filter(c => {
      const r = c.getBoundingClientRect();
      return W.getComputedStyle(c).display !== 'none' && (r.right > w + 1 || r.left < -1);
    });
    out(brokenCanvases.length === 0, size, 'Canvas 視窗邊界檢查（可見 ' + canvases.length + ' 個，超出 ' + brokenCanvases.length + ' 個）');

    const interactive = [...d.querySelectorAll('button, input, textarea')].filter(el => {
      const st = W.getComputedStyle(el);
      return st.display !== 'none' && st.visibility !== 'hidden';
    });
    if (interactive.length === 0) {
      warn(size, '未偵測到可見互動元件（按鈕或輸入框）');
    } else {
      const clipped = interactive.filter(el => {
        const r = el.getBoundingClientRect();
        return r.width > 0 && (r.right > w + 1 || r.left < -1);
      });
      out(clipped.length === 0, size, '互動元件未超出螢幕寬度（檢查 ' + interactive.length + ' 個，超出 ' + clipped.length + ' 個）');
    }

    f.remove();
  }

  lines.push('--- Summary: FAIL ' + fails + ', WARN ' + warns);
  console.log(lines.join('\n'));
  return lines.join('\n');
})();
