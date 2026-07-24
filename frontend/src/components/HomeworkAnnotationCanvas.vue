<template>
  <div
    class="annotation-stage"
    :class="{ 'annotation-stage--editable': editable }"
    :style="stageStyle"
  >
    <div ref="stageRef" class="annotation-viewport">
      <img
        ref="imageRef"
        class="annotation-image"
        :src="src"
        :alt="alt"
        @load="handleImageLoad"
        @error="handleImageError"
      />
      <canvas ref="canvasRef" class="annotation-canvas" :aria-label="`${alt}批注覆盖层`"></canvas>
      <div
        v-if="editable && deductionEditor.visible"
        class="annotation-deduction-editor"
        :style="deductionEditor.style"
        @mousedown.stop
        @click.stop
      >
        <span aria-hidden="true">-</span>
        <input
          type="text"
          inputmode="numeric"
          autocomplete="off"
          maxlength="3"
          :value="deductionEditor.value"
          aria-label="当前错误扣分"
          @input="handleDeductionInput"
          @change="commitDeduction"
          @keydown.enter="commitDeduction"
        />
      </div>
      <div v-if="imageLoadError" class="annotation-image-error" role="status">
        <el-icon><picture /></el-icon>
        <span>作业图片加载失败</span>
      </div>
    </div>
    <el-button class="annotation-zoom" circle title="放大查看原图" aria-label="放大查看原图" @click="previewVisible = true">
      <el-icon><zoom-in /></el-icon>
    </el-button>
  </div>
  <el-image-viewer
    v-if="previewVisible"
    :url-list="[src]"
    hide-on-click-modal
    @close="previewVisible = false"
  />
</template>

<script setup>
import { Canvas, Rect, Text } from 'fabric'
import { nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { convertCanvasBoxToImageBox, convertImageBoxToCanvasBox } from '../utils/coordinate'

const props = defineProps({
  src: { type: String, required: true },
  boxes: { type: Array, default: () => [] },
  editable: { type: Boolean, default: false },
  alt: { type: String, default: '作业错误标注图' },
})

const emit = defineEmits(['update:boxes'])
const stageRef = ref(null)
const imageRef = ref(null)
const canvasRef = ref(null)
const previewVisible = ref(false)
const imageLoadError = ref(false)
const stageStyle = ref({})
const deductionEditor = reactive({
  visible: false,
  value: '',
  style: { left: '0px', top: '0px' },
})
let canvas = null
let resizeObserver = null
let imageSize = { width: 0, height: 0 }
let canvasSize = { width: 0, height: 0 }
let isSyncing = false
let isEmitting = false
let labelByRect = new WeakMap()
let selectedRect = null

function normalizeDeduction(value) {
  const deduction = Number(value)
  return Number.isInteger(deduction) && deduction >= 1 && deduction <= 100 ? deduction : null
}

function createRect(annotation, index) {
  const position = convertImageBoxToCanvasBox(annotation, imageSize, canvasSize)
  const strokeWidth = Math.max(2, Math.min(canvasSize.width, canvasSize.height) * 0.004)
  return new Rect({
    ...position,
    originX: 'left',
    originY: 'top',
    centeredScaling: false,
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
    annotationId: annotation.ocr_id ?? annotation.id ?? index + 1,
    annotationText: annotation.text || '',
    annotationReason: annotation.reason || '错误答案',
    annotationDeduction: normalizeDeduction(annotation.deduction),
  })
}

function positionDeductionLabel(rect) {
  const label = labelByRect.get(rect)
  if (!label) return
  const gap = 7
  const labelWidth = label.getScaledWidth()
  const labelHeight = label.getScaledHeight()
  const rectWidth = rect.getScaledWidth()
  let left = rect.left + rectWidth + gap
  let top = rect.top

  if (left + labelWidth > canvasSize.width) {
    left = rect.left + rectWidth - labelWidth
    top = rect.top - labelHeight - gap
  }
  if (top < 0) top = rect.top + gap

  label.set({
    left: Math.max(0, Math.min(left, canvasSize.width - labelWidth)),
    top: Math.max(0, Math.min(top, canvasSize.height - labelHeight)),
  })
  label.setCoords()
}

function createDeductionLabel(rect) {
  if (rect.annotationDeduction === null) return null
  const label = new Text(`- ${rect.annotationDeduction}`, {
    originX: 'left',
    originY: 'top',
    fontFamily: 'Arial, sans-serif',
    fontSize: 16,
    fontWeight: '700',
    fill: '#c9343b',
    backgroundColor: 'rgba(255, 255, 255, 0.94)',
    selectable: false,
    evented: false,
    objectCaching: false,
  })
  labelByRect.set(rect, label)
  positionDeductionLabel(rect)
  return label
}

function positionDeductionEditor(rect) {
  if (!rect || !deductionEditor.visible) return
  const editorWidth = 86
  const editorHeight = 32
  const gap = 7
  const rectWidth = rect.getScaledWidth()
  let left = rect.left + rectWidth + gap
  let top = rect.top

  if (left + editorWidth > canvasSize.width) {
    left = rect.left + rectWidth - editorWidth
    top = rect.top - editorHeight - gap
  }
  if (top < 0) top = rect.top + gap

  deductionEditor.style = {
    left: `${Math.max(0, Math.min(left, canvasSize.width - editorWidth))}px`,
    top: `${Math.max(0, Math.min(top, canvasSize.height - editorHeight))}px`,
  }
}

function showDeductionEditor(rect) {
  if (!props.editable || !rect) return
  selectedRect = rect
  const label = labelByRect.get(rect)
  if (label) label.visible = false
  deductionEditor.value = rect.annotationDeduction ?? ''
  deductionEditor.visible = true
  positionDeductionEditor(rect)
  canvas?.requestRenderAll()
}

function hideDeductionEditor() {
  const label = selectedRect && labelByRect.get(selectedRect)
  if (label) label.visible = true
  selectedRect = null
  deductionEditor.visible = false
  canvas?.requestRenderAll()
}

function syncDeductionLabel(rect) {
  if (!canvas) return
  let label = labelByRect.get(rect)
  if (rect.annotationDeduction === null) {
    if (label) canvas.remove(label)
    labelByRect.delete(rect)
    return
  }
  if (!label) {
    label = createDeductionLabel(rect)
    if (label) canvas.add(label)
  } else {
    label.set('text', `- ${rect.annotationDeduction}`)
  }
  if (label) {
    label.visible = selectedRect !== rect
    positionDeductionLabel(rect)
  }
}

function handleDeductionInput(event) {
  const value = event.target.value.replace(/\D/g, '').slice(0, 3)
  event.target.value = value
  deductionEditor.value = value
}

function commitDeduction() {
  if (!selectedRect) return
  const rawValue = deductionEditor.value
  if (rawValue === '') {
    selectedRect.annotationDeduction = null
  } else {
    const deduction = normalizeDeduction(rawValue)
    if (deduction === null) {
      deductionEditor.value = selectedRect.annotationDeduction ?? ''
      return
    }
    selectedRect.annotationDeduction = deduction
    deductionEditor.value = deduction
  }
  syncDeductionLabel(selectedRect)
  positionDeductionEditor(selectedRect)
  canvas?.requestRenderAll()
  emitBoxes()
}

function renderBoxes() {
  if (!canvas || !imageSize.width || !canvasSize.width) return
  isSyncing = true
  canvas.getObjects().forEach((item) => canvas.remove(item))
  labelByRect = new WeakMap()
  selectedRect = null
  deductionEditor.visible = false
  props.boxes.forEach((annotation, index) => {
    const box = annotation?.bbox || annotation
    const coordinates = [box?.x, box?.y, box?.width, box?.height].map(Number)
    if (coordinates.every(Number.isFinite) && coordinates[2] > 0 && coordinates[3] > 0) {
      const rect = createRect(annotation, index)
      canvas.add(rect)
      const label = createDeductionLabel(rect)
      if (label) canvas.add(label)
    }
  })
  canvas.renderAll()
  isSyncing = false
}

function emitBoxes() {
  if (!canvas || isSyncing || !props.editable) return
  const boxes = canvas.getObjects()
    .filter((item) => item.type === 'rect')
    .map((item) => {
      const annotation = {
        ocr_id: item.annotationId,
        bbox: convertCanvasBoxToImageBox(
          {
            x: item.left,
            y: item.top,
            width: item.getScaledWidth(),
            height: item.getScaledHeight(),
          },
          imageSize,
          canvasSize,
        ),
        coordinate_space: 'source_pixel',
        text: item.annotationText || '',
        reason: item.annotationReason || '错误答案',
      }
      if (item.annotationDeduction !== null) annotation.deduction = item.annotationDeduction
      return annotation
    })
  isEmitting = true
  emit('update:boxes', boxes)
  nextTick(() => {
    isEmitting = false
  })
}

function keepObjectInsideCanvas(event) {
  const target = event.target
  if (!target || !canvas) return
  if (target.getScaledWidth() > canvasSize.width) target.scaleX = canvasSize.width / target.width
  if (target.getScaledHeight() > canvasSize.height) target.scaleY = canvasSize.height / target.height
  target.left = Math.max(0, Math.min(target.left, canvasSize.width - target.getScaledWidth()))
  target.top = Math.max(0, Math.min(target.top, canvasSize.height - target.getScaledHeight()))
  target.setCoords()
  positionDeductionLabel(target)
  positionDeductionEditor(target)
  canvas.requestRenderAll()
}

function handleObjectModified(event) {
  if (event.target) positionDeductionLabel(event.target)
  if (event.target) positionDeductionEditor(event.target)
  emitBoxes()
}

function handleSelectionCreated(event) {
  showDeductionEditor(event.selected?.[0] || event.target)
}

function handleSelectionUpdated(event) {
  showDeductionEditor(event.selected?.[0] || event.target)
}

function handleSelectionCleared() {
  hideDeductionEditor()
}

function openPreviewFromCanvas(event) {
  if (event.target) return
  previewVisible.value = true
}

function syncCanvasDimensions() {
  if (!canvas || !stageRef.value || !imageRef.value || !imageSize.width) return
  const imageRect = imageRef.value.getBoundingClientRect()
  const viewportRect = stageRef.value.getBoundingClientRect()
  const width = Math.max(1, imageRect.width)
  const height = Math.max(1, imageRect.height)
  const wrapper = canvas.wrapperEl

  canvasSize = { width, height }
  canvas.setDimensions({ width, height })
  if (wrapper) {
    wrapper.style.left = `${imageRect.left - viewportRect.left}px`
    wrapper.style.top = `${imageRect.top - viewportRect.top}px`
    wrapper.style.width = `${width}px`
    wrapper.style.height = `${height}px`
  }
  renderBoxes()
}

function createCanvas() {
  if (!canvasRef.value || canvas) return
  canvas = new Canvas(canvasRef.value, {
    selection: props.editable,
    preserveObjectStacking: true,
    backgroundColor: 'transparent',
    defaultCursor: 'zoom-in',
    hoverCursor: props.editable ? 'move' : 'zoom-in',
  })
  canvas.lowerCanvasEl.style.pointerEvents = 'none'
  canvas.upperCanvasEl.style.pointerEvents = 'auto'
  canvas.on('mouse:up', openPreviewFromCanvas)
  canvas.on('object:moving', keepObjectInsideCanvas)
  canvas.on('object:scaling', keepObjectInsideCanvas)
  canvas.on('object:modified', handleObjectModified)
  canvas.on('selection:created', handleSelectionCreated)
  canvas.on('selection:updated', handleSelectionUpdated)
  canvas.on('selection:cleared', handleSelectionCleared)
}

async function handleImageLoad() {
  if (!imageRef.value?.naturalWidth || !imageRef.value?.naturalHeight) return
  imageLoadError.value = false
  imageSize = {
    width: imageRef.value.naturalWidth,
    height: imageRef.value.naturalHeight,
  }
  stageStyle.value = {
    '--annotation-image-width': `${imageSize.width}px`,
    '--annotation-image-ratio': `${imageSize.width} / ${imageSize.height}`,
  }
  await nextTick()
  createCanvas()
  syncCanvasDimensions()
  if (!resizeObserver && stageRef.value && typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(syncCanvasDimensions)
    resizeObserver.observe(stageRef.value)
  }
}

function handleImageError() {
  imageLoadError.value = true
  canvas?.clear()
}

function resetCanvas() {
  resizeObserver?.disconnect()
  resizeObserver = null
  canvas?.dispose()
  canvas = null
  labelByRect = new WeakMap()
  selectedRect = null
  deductionEditor.visible = false
  imageSize = { width: 0, height: 0 }
  canvasSize = { width: 0, height: 0 }
  stageStyle.value = {}
}

async function refreshImage() {
  resetCanvas()
  imageLoadError.value = false
  await nextTick()
  if (imageRef.value?.complete) await handleImageLoad()
}

onMounted(refreshImage)
watch(() => props.src, refreshImage)
watch(() => props.boxes, () => {
  if (!isEmitting) renderBoxes()
}, { deep: true })
watch(() => props.editable, () => {
  if (canvas) {
    canvas.selection = props.editable
    if (!props.editable) hideDeductionEditor()
    renderBoxes()
  }
})

onBeforeUnmount(resetCanvas)
</script>

<style scoped>
.annotation-stage {
  position: relative;
  width: 100%;
  overflow: visible;
  background: #f7faf9;
  border: 1px solid #dbe7e2;
  border-radius: 6px;
}

.annotation-viewport {
  position: relative;
  width: min(100%, var(--annotation-image-width, 100%));
  aspect-ratio: var(--annotation-image-ratio, auto);
  margin-inline: auto;
  overflow: hidden;
  background: #ffffff;
}

.annotation-image,
.annotation-canvas {
  position: absolute;
  inset: 0;
  display: block;
  width: 100%;
  height: 100%;
}

.annotation-image {
  z-index: 0;
  object-fit: contain;
}

.annotation-canvas {
  z-index: 0;
  pointer-events: none;
}

.annotation-deduction-editor {
  position: absolute;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  box-sizing: border-box;
  width: 86px;
  height: 32px;
  padding: 2px 5px;
  color: #c9343b;
  font-size: 15px;
  font-weight: 700;
  background: rgba(255, 255, 255, .97);
  border: 1px solid #e5484d;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(35, 58, 55, .18);
}

.annotation-deduction-editor input {
  box-sizing: border-box;
  width: 52px;
  height: 25px;
  padding: 0 3px;
  color: #324946;
  font: inherit;
  text-align: center;
  background: #ffffff;
  border: 0;
  outline: 0;
}


.annotation-viewport :deep(.canvas-container) {
  position: absolute !important;
  inset: 0;
  z-index: 1;
  pointer-events: auto;
  width: auto !important;
  height: auto !important;
}

.annotation-viewport :deep(.lower-canvas) {
  z-index: 0 !important;
  pointer-events: none !important;
}

.annotation-viewport :deep(.upper-canvas) {
  width: 100% !important;
  height: 100% !important;
  z-index: 1 !important;
  pointer-events: auto !important;
  touch-action: none;
}

.annotation-image-error {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: grid;
  gap: 7px;
  place-content: center;
  color: #82918e;
  font-size: 13px;
  background: #ffffff;
}

.annotation-image-error .el-icon {
  margin: 0 auto;
  font-size: 28px;
}

.annotation-zoom.el-button {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 3;
  width: 34px;
  min-height: 34px;
  padding: 0;
  color: #164f4d;
  background: rgba(255, 255, 255, .92);
  border-color: #dbe7e2;
  box-shadow: 0 3px 12px rgba(20, 67, 65, .16);
}
</style>
