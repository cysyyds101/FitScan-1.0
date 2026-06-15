// ----- 窗口控制 -----
const { appWindow } = window.__TAURI__.window;
document.getElementById('close').addEventListener('click', () => appWindow.close());
document.getElementById('minimize').addEventListener('click', () => appWindow.minimize());

// ----- 读取并展示最新结果 -----
const resultEl = document.getElementById('result');
const latest = localStorage.getItem('latestResult');
if (latest) {
  const data = JSON.parse(latest);
  resultEl.textContent = `身高：${data.height}\n推荐尺码：${data.size}`;
} else {
  resultEl.textContent = '暂无结果';
}

// ----- 保存到历史记录 -----
document.getElementById('saveBtn').addEventListener('click', () => {
  const history = JSON.parse(localStorage.getItem('history') || '[]');
  history.unshift({ id: Date.now(), ...JSON.parse(latest) });
  localStorage.setItem('history', JSON.stringify(history));
  alert('已保存到本地历史记录');
});

// ----- 分享（复制到剪贴板）-----
document.getElementById('shareBtn').addEventListener('click', async () => {
  try {
    const { writeText } = await import('@tauri-apps/api/clipboard');
    await writeText(`身高：${JSON.parse(latest).height}，推荐尺码：${JSON.parse(latest).size}`);
    alert('已复制到剪贴板，可粘贴分享');
  } catch (e) {
    // 如果剪贴板 API 不可用，使用浏览器原生 API
    const text = `身高：${JSON.parse(latest).height}，推荐尺码：${JSON.parse(latest).size}`;
    navigator.clipboard.writeText(text).then(() => {
      alert('已复制到剪贴板，可粘贴分享');
    }).catch(err => {
      alert('复制失败，请手动复制结果');
    });
  }
});

// ----- 重新测量 -----
document.getElementById('retryBtn').addEventListener('click', () => {
  window.location.href = 'index.html';
});