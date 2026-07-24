<template>
  <div
    ref="stageRef"
    class="annotation-stage"
    :class="{ 'annotation-stage--editable': editable }"
    :style="stageStyle"
  >
    <el-button class="annotation-zoom" circle title="放大查看原图" aria-label="放大查看原图" @click="previewVisible = true">
      <el-icon><zoom-in /></el-icon>
    </el-button>
    <canvas ref="canvasRef" :aria-label="alt"></canvas>
  </div>
  <el-image-viewer
    v-if="previewVisible"
    :url-list="[src]"
    hide-on-click-modal
    @close="previewVisible = false"
  />
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
const stageStyle = ref({})
let canvas = null
let image = null
let renderVersion = 0
let isSyncing = false

function toCanvasBox(box) {
  // Unmarked boxes are legacy data stored in the old 0-1000 coordinate space.
  const usesSourcePixels = box.coordinate_space === 'source_pixel'
  const scaleX = usesSourcePixels ? 1 : canvas.width / 1000
  const scaleY = usesSourcePixels ? 1 : canvas.height / 1000
  const left = Number(box.x) * scaleX
  const top = Number(box.y) * scaleY
  const width = Number(box.width) * scaleX
  const height = Number(box.height) * scaleY
  const boundedLeft = Math.max(0, Math.min(left, canvas.width - 1))
  const boundedTop = Math.max(0, Math.min(top, canvas.height - 1))
  return {
    left: boundedLeft,
    top: boundedTop,
    width: Math.max(1, Math.min(width, canvas.width - boundedLeft)),
    height: Math.max(1, Math.min(height, canvas.height - boundedTop)),
  }
}

function createRect(box, index) {
  const position = toCanvasBox(box)
  const strokeWidth = Math.max(3, Math.min(canvas.width, canvas.height) * 0.004)
  return new Rect({
    ...position,
    fill: 'rgba(229, 72, 77, 0.08)',
    stroke: '#e5484d',
    strokeWidth,
    strokeDashArray: [strokeWidth * 3, strokeWidth * 1.6],
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
    const coordinates = [box?.x, box?.y, box?.width, box?.height].map(Number)
    if (coordinates.every(Number.isFinite) && coordinates[2] > 0 && coordinates[3] > 0) {
      canvas.add(createRect(box, index))
    }
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
      x: Number(item.left.toFixed(2)),
      y: Number(item.top.toFixed(2)),
      width: Number(item.getScaledWidth().toFixed(2)),
      height: Number(item.getScaledHeight().toFixed(2)),
      coordinate_space: 'source_pixel',
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

function openPreviewFromCanvas(event) {
  if (event.target && event.target !== image) return
  previewVisible.value = true
}

async function initializeCanvas() {
  if (!canvasRef.value || !stageRef.value || !props.src) return
  const version = ++renderVersion
  if (canvas) canvas.dispose()
  canvas = new Canvas(canvasRef.value, {
    selection: props.editable,
    preserveObjectStacking: true,
    backgroundColor: '#ffffff',
    defaultCursor: 'zoom-in',
    hoverCursor: props.editable ? 'move' : 'zoom-in',
  })
  canvas.on('mouse:up', openPreviewFromCanvas)
  canvas.on('object:moving', keepObjectInsideCanvas)
  canvas.on('object:scaling', keepObjectInsideCanvas)
  canvas.on('object:modified', emitBoxes)

  try {
    const loadedImage = await FabricImage.fromURL(props.src, { crossOrigin: 'anonymous' })
    if (version !== renderVersion || !canvas) return
    image = loadedImage
    stageStyle.value = {
      '--annotation-image-width': `${image.width}px`,
      '--annotation-image-ratio': `${image.width} / ${image.height}`,
    }
    // Browser coordinate = source pixel * rendered size / natural size. Fabric applies the inverse
    // mapping to pointer events because both canvas layers share this responsive CSS size.
    canvas.setDimensions({ width: image.width, height: image.height })
    image.set({ left: 0, top: 0, selectable: false, evented: false, scaleX: 1, scaleY: 1 })
    canvas.add(image)
    renderBoxes()
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
})

watch(() => props.src, initializeCanvas)
watch(() => props.boxes, renderBoxes, { deep: true })
watch(() => props.editable, initializeCanvas)

onBeforeUnmount(() => {
  canvas?.dispose()
})
</script>

<style scoped>
.annotation-stage {
  position: relative;
  width: min(100%, var(--annotation-image-width, 100%));
  aspect-ratio: var(--annotation-image-ratio, auto);
  overflow: visible;
  background: #f7faf9;
  border: 1px solid #dbe7e2;
  border-radius: 6px;
  margin-inline: auto;
}

.annotation-stage :deep(.canvas-container) {
  width: 100% !important;
  height: 100% !important;
}

.annotation-stage :deep(.lower-canvas),
.annotation-stage :deep(.upper-canvas) {
  width: 100% !important;
  height: 100% !important;
}

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
