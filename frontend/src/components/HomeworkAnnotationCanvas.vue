<template>
  <div ref="stageRef" class="annotation-stage" :class="{ 'annotation-stage--editable': editable }">
    <el-button class="annotation-zoom" circle title="放大查看原图" aria-label="放大查看原图" @click="previewVisible = true">
      <el-icon><zoom-in /></el-icon>
    </el-button>
    <canvas ref="canvasRef" :aria-label="alt"></canvas>
  </div>
  <el-image-viewer v-if="previewVisible" :url-list="[src]" @close="previewVisible = false" />
</template>

<script setup>
import { Canvas, FabricImage, Rect } from 'fabric'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  src: { type: String, required: true },
  boxes: { type: Array, default: () => [] },
  editable: { type: Boolean, default: false },
  alt: { type: String, default: '作业错误标注图' },
})

const emit = defineEmits(['update:boxes'])
const stageRef = ref(null)
const canvasRef = ref(null)
const previewVisible = ref(false)
let canvas = null
let image = null
let resizeObserver = null
let renderVersion = 0
let isSyncing = false
let observedWidth = 0

function toCanvasBox(box) {
  return {
    left: (Number(box.x) / 1000) * canvas.width,
    top: (Number(box.y) / 1000) * canvas.height,
    width: (Number(box.width) / 1000) * canvas.width,
    height: (Number(box.height) / 1000) * canvas.height,
  }
}

function createRect(box, index) {
  const position = toCanvasBox(box)
  return new Rect({
    ...position,
    fill: 'rgba(229, 72, 77, 0.08)',
    stroke: '#e5484d',
    strokeWidth: 3,
    strokeDashArray: [9, 5],
    strokeUniform: true,
    selectable: props.editable,
    evented: props.editable,
    hasControls: props.editable,
    lockRotation: true,
    transparentCorners: false,
    cornerColor: '#e5484d',
    cornerStrokeColor: '#ffffff',
    borderColor: '#e5484d',
    objectCaching: false,
    annotationId: index,
    annotationText: box.text || '',
    annotationReason: box.reason || '错误答案',
  })
}

function renderBoxes() {
  if (!canvas || !image) return
  isSyncing = true
  canvas.getObjects().filter((item) => item !== image).forEach((item) => canvas.remove(item))
  props.boxes.forEach((box, index) => {
    if (box && Number(box.width) > 0 && Number(box.height) > 0) canvas.add(createRect(box, index))
  })
  image.sendToBack()
  canvas.renderAll()
  isSyncing = false
}

function emitBoxes() {
  if (!canvas || isSyncing || !props.editable) return
  const boxes = canvas.getObjects()
    .filter((item) => item !== image && item.type === 'rect')
    .map((item) => ({
      x: Number(((item.left / canvas.width) * 1000).toFixed(2)),
      y: Number(((item.top / canvas.height) * 1000).toFixed(2)),
      width: Number(((item.getScaledWidth() / canvas.width) * 1000).toFixed(2)),
      height: Number(((item.getScaledHeight() / canvas.height) * 1000).toFixed(2)),
      text: item.annotationText || '',
      reason: item.annotationReason || '错误答案',
    }))
  emit('update:boxes', boxes)
}

function keepObjectInsideCanvas(event) {
  const target = event.target
  if (!target || target === image || !canvas) return
  if (target.getScaledWidth() > canvas.width) target.scaleX = canvas.width / target.width
  if (target.getScaledHeight() > canvas.height) target.scaleY = canvas.height / target.height
  target.left = Math.max(0, Math.min(target.left, canvas.width - target.getScaledWidth()))
  target.top = Math.max(0, Math.min(target.top, canvas.height - target.getScaledHeight()))
  target.setCoords()
}

function fitCanvasToContainer() {
  if (!canvas || !image || !stageRef.value || !image.width || !image.height) return
  const displayWidth = Math.min(image.width, stageRef.value.clientWidth || image.width)
  const displayHeight = displayWidth * (image.height / image.width)
  canvas.setDimensions(
    { width: `${displayWidth}px`, height: `${displayHeight}px` },
    { cssOnly: true },
  )
}

async function initializeCanvas() {
  if (!canvasRef.value || !stageRef.value || !props.src) return
  const version = ++renderVersion
  if (canvas) canvas.dispose()
  canvas = new Canvas(canvasRef.value, {
    selection: props.editable,
    preserveObjectStacking: true,
    backgroundColor: '#ffffff',
  })
  canvas.on('object:moving', keepObjectInsideCanvas)
  canvas.on('object:scaling', keepObjectInsideCanvas)
  canvas.on('object:modified', emitBoxes)

  try {
    const loadedImage = await FabricImage.fromURL(props.src, { crossOrigin: 'anonymous' })
    if (version !== renderVersion || !canvas) return
    image = loadedImage
    stageRef.value.style.maxWidth = `${image.width}px`
    canvas.setDimensions({ width: image.width, height: image.height }, { backstoreOnly: true })
    image.set({ left: 0, top: 0, selectable: false, evented: false, scaleX: 1, scaleY: 1 })
    canvas.add(image)
    renderBoxes()
    fitCanvasToContainer()
  } catch {
    // The surrounding page owns image loading errors; avoid leaving a broken Fabric instance behind.
    canvas?.dispose()
    canvas = null
    image = null
  }
}

onMounted(async () => {
  await nextTick()
  await initializeCanvas()
  resizeObserver = new ResizeObserver(([entry]) => {
    const width = Math.round(entry.contentRect.width)
    if (width && Math.abs(width - observedWidth) > 1) {
      observedWidth = width
      fitCanvasToContainer()
    }
  })
  if (stageRef.value) resizeObserver.observe(stageRef.value)
})

watch(() => props.src, initializeCanvas)
watch(() => props.boxes, renderBoxes, { deep: true })
watch(() => props.editable, initializeCanvas)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  canvas?.dispose()
})
</script>

<style scoped>
.annotation-stage {
  position: relative;
  width: 100%;
  overflow: hidden;
  background: #f7faf9;
  border: 1px solid #dbe7e2;
  border-radius: 6px;
}

.annotation-stage--editable :deep(.upper-canvas) { cursor: move; }
.annotation-stage :deep(.canvas-container) { margin: 0 auto; }
.annotation-zoom.el-button {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 2;
  width: 34px;
  min-height: 34px;
  padding: 0;
  color: #164f4d;
  background: rgba(255, 255, 255, .92);
  border-color: #dbe7e2;
  box-shadow: 0 3px 12px rgba(20, 67, 65, .16);
}
</style>
