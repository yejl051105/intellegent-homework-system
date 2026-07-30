// 坐标换算工具：错误标注框在「原图像素坐标」和「画布显示坐标」之间的互转。
//
// 全项目约定（与后端一致）：标注数据只存原图像素坐标
// （coordinate_space = "source_pixel"，以原图左上角为原点）。
// 画布尺寸随窗口变化，展示前用 convertImageBoxToCanvasBox 缩放到画布，
// 教师拖动编辑后用 convertCanvasBoxToImageBox 换算回像素坐标再提交。

function finiteNumber(value, fallback = 0) {
  const number = Number(value)
  return Number.isFinite(number) ? number : fallback
}

// 从标注对象中取出规范化的 bbox（兼容 bbox 嵌套和平铺两种结构）
export function getImageBox(annotation) {
  const box = annotation?.bbox || annotation || {}
  return {
    x: finiteNumber(box.x),
    y: finiteNumber(box.y),
    width: Math.max(0, finiteNumber(box.width)),
    height: Math.max(0, finiteNumber(box.height)),
  }
}

// 计算原图 → 画布的横纵缩放比（尺寸兜底为 1，避免除零）
function getScale(imageSize, canvasSize) {
  // 即使当前图片等比显示，也保留 x/y 两套比例，后续若容器策略变化不需要改调用方。
  const imageWidth = Math.max(1, finiteNumber(imageSize?.width))
  const imageHeight = Math.max(1, finiteNumber(imageSize?.height))
  const canvasWidth = Math.max(1, finiteNumber(canvasSize?.width))
  const canvasHeight = Math.max(1, finiteNumber(canvasSize?.height))
  return {
    x: canvasWidth / imageWidth,
    y: canvasHeight / imageHeight,
    imageWidth,
    imageHeight,
    canvasWidth,
    canvasHeight,
  }
}

// 原图像素坐标 → 画布坐标（fabric 的 left/top/width/height），越界时收缩到画布内
export function convertImageBoxToCanvasBox(bbox, imageSize, canvasSize) {
  const source = getImageBox(bbox)
  const scale = getScale(imageSize, canvasSize)
  // 先限制 left/top，再按剩余空间限制宽高，保证换算后的框不会跑出可见图片区域。
  const left = Math.max(0, Math.min(source.x * scale.x, scale.canvasWidth))
  const top = Math.max(0, Math.min(source.y * scale.y, scale.canvasHeight))
  return {
    left,
    top,
    width: Math.max(1, Math.min(source.width * scale.x, scale.canvasWidth - left)),
    height: Math.max(1, Math.min(source.height * scale.y, scale.canvasHeight - top)),
  }
}

// 画布坐标 → 原图像素坐标，保留两位小数并夹紧到图片范围内（提交给后端用）
export function convertCanvasBoxToImageBox(box, imageSize, canvasSize) {
  const canvasBox = getImageBox({
    x: box?.left ?? box?.x,
    y: box?.top ?? box?.y,
    width: box?.width,
    height: box?.height,
  })
  const scale = getScale(imageSize, canvasSize)
  const x = Math.max(0, Math.min(canvasBox.x / scale.x, scale.imageWidth))
  const y = Math.max(0, Math.min(canvasBox.y / scale.y, scale.imageHeight))
  return {
    x: Math.round(x * 100) / 100,
    y: Math.round(y * 100) / 100,
    width: Math.round(Math.max(1, Math.min(canvasBox.width / scale.x, scale.imageWidth - x)) * 100) / 100,
    height: Math.round(Math.max(1, Math.min(canvasBox.height / scale.y, scale.imageHeight - y)) * 100) / 100,
  }
}
