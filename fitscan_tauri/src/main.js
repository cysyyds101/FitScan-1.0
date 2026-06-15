// ----- 窗口控制 -----
const { appWindow } = window.__TAURI__.window;
document.getElementById('close').addEventListener('click', () => appWindow.close());
document.getElementById('minimize').addEventListener('click', () => appWindow.minimize());

// ----- 本地尺码规则 -----
async function loadSizeRules() {
  const { readTextFile, BaseDirectory } = window.__TAURI__.fs;
  try {
    const txt = await readTextFile('size_rules.json', { dir: BaseDirectory.Resource });
    return JSON.parse(txt);
  } catch (e) { return null; }
}

// ----- 像素 → 厘米 换算（使用 A4 参考物） -----
function pixelToCm(pixels, refPixels) {
  const cmPerPixel = 21.0 / refPixels; // A4 宽 21 cm
  return pixels * cmPerPixel;
}

// ----- TensorFlow.js 模型推理 -----
let model = null;

async function loadModel() {
  if (!model) {
    const tf = await import('@tensorflow/tfjs');
    // 加载现有的 TensorFlow.js 模型（从 movenet_model 目录）
    // 注意：这里使用 file:// URL 加载本地模型
    const modelPath = '../movenet_model/model.json';
    model = await tf.loadGraphModel(modelPath);
  }
  return model;
}

async function runModel(imageBitmap) {
  const tf = await import('@tensorflow/tfjs');
  const model = await loadModel();
  
  // 将图片转换为 tensor
  const canvas = document.createElement('canvas');
  canvas.width = 192;
  canvas.height = 192;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(imageBitmap, 0, 0, 192, 192);
  
  // 获取图像数据并归一化
  const imgData = ctx.getImageData(0, 0, 192, 192);
  const data = new Float32Array(192 * 192 * 3);
  for (let i = 0; i < 192 * 192; i++) {
    data[i * 3] = imgData.data[i * 4] / 255;
    data[i * 3 + 1] = imgData.data[i * 4 + 1] / 255;
    data[i * 3 + 2] = imgData.data[i * 4 + 2] / 255;
  }
  
  // 创建 tensor [1, 192, 192, 3]
  const tensor = tf.tensor4d(data, [1, 192, 192, 3]);
  
  // 运行推理
  const result = model.predict(tensor);
  const output = await result.data();
  
  // 释放 tensor
  tensor.dispose();
  result.dispose();
  
  // 解析关键点（假设输出格式为 [1, 17, 3] -> y, x, score）
  const keypoints = [];
  for (let i = 0; i < 17; i++) {
    keypoints.push({
      y: output[i * 3],
      x: output[i * 3 + 1],
      score: output[i * 3 + 2]
    });
  }
  return keypoints;
}

// ----- 身高估算 -----
function estimateHeight(kp, refPixels) {
  const nose = kp[0];
  const leftAnkle = kp[15];
  const rightAnkle = kp[16];
  const ankleY = (leftAnkle.y + rightAnkle.y) / 2;
  const pixelDist = Math.abs(ankleY - nose.y) * 192; // 归一化乘以实际尺寸
  return pixelToCm(pixelDist, refPixels);
}

// ----- 尺码映射 -----
function mapSize(heightCm, rules) {
  if (!rules) return '未知';
  for (const r of rules) if (heightCm >= r.min && heightCm <= r.max) return r.size;
  return '未知';
}

// ----- 摄像头初始化 -----
async function initCamera() {
  const video = document.getElementById('video');
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
  } catch (e) { console.error('摄像头获取失败', e); }
}
initCamera();

// ----- 处理图片（摄像头抓帧或本地上传） -----
async function handleImage(bitmap) {
  const status = document.getElementById('status');
  status.textContent = '加载模型...';
  const keypoints = await runModel(bitmap);
  status.textContent = '计算中...';
  const refPixels = 100; // 需要根据实际图片校准，可在 UI 中提供调节
  const heightCm = estimateHeight(keypoints, refPixels);
  const rules = await loadSizeRules();
  const size = mapSize(heightCm, rules);
  const result = { height: heightCm.toFixed(1) + ' cm', size };
  // 保存到 localStorage（后续结果页读取）
  localStorage.setItem('latestResult', JSON.stringify(result));
  // 跳转结果页
  window.location.href = 'result.html';
}

// ----- 按钮事件 -----
document.getElementById('processBtn').addEventListener('click', async () => {
  const fileInput = document.getElementById('fileInput');
  if (fileInput.files.length > 0) {
    // 本地图片上传
    const img = await createImageBitmap(fileInput.files[0]);
    await handleImage(img);
  } else {
    // 摄像头抓帧
    const video = document.getElementById('video');
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const bitmap = await createImageBitmap(canvas);
    await handleImage(bitmap);
  }
});