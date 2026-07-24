function finiteNumber(value, fallback = 0) {
  const number = Number(value)
  return Number.isFinite(number) ? number : fallback
}

export function getImageBox(annotation) {
  const box = annotation?.bbox || annotation || {}
  return {
    x: finiteNumber(box.x),
    y: finiteNumber(box.y),
    width: Math.max(0, finiteNumber(box.width)),
    height: Math.max(0, finiteNumber(box.height)),
  }
}

function getScale(imageSize, canvasSize) {
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

export function convertImageBoxToCanvasBox(bbox, imageSize, canvasSize) {
  const source = getImageBox(bbox)
  const scale = getScale(imageSize, canvasSize)
  const left = Math.max(0, Math.min(source.x * scale.x, scale.canvasWidth))
  const top = Math.max(0, Math.min(source.y * scale.y, scale.canvasHeight))
  return {
    left,
    top,
    width: Math.max(1, Math.min(source.width * scale.x, scale.canvasWidth - left)),
    height: Math.max(1, Math.min(source.height * scale.y, scale.canvasHeight - top)),
  }
}

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
