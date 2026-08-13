<script setup lang="ts">
import type { DiagramAnnotation } from '~/types/academy'

defineProps<{
  annotations: DiagramAnnotation[]
}>()
</script>

<template>
  <g>
    <g v-for="(item, idx) in annotations" :key="`ann-${idx}`">
      <!-- Dimension ticks -->
      <line
        :x1="item.from.x"
        :y1="item.from.y - 1.1"
        :x2="item.from.x"
        :y2="item.from.y + 1.1"
        stroke="#fde68a"
        stroke-width="0.28"
        opacity="0.9"
      />
      <line
        :x1="item.to.x"
        :y1="item.to.y - 1.1"
        :x2="item.to.x"
        :y2="item.to.y + 1.1"
        stroke="#fde68a"
        stroke-width="0.28"
        opacity="0.9"
      />
      <line
        :x1="item.from.x"
        :y1="item.from.y"
        :x2="item.to.x"
        :y2="item.to.y"
        stroke="#fde68a"
        stroke-width="0.32"
        stroke-dasharray="0.9 0.7"
        opacity="0.95"
      />
      <!-- Leader toward label -->
      <line
        :x1="(item.from.x + item.to.x) / 2"
        :y1="(item.from.y + item.to.y) / 2"
        :x2="item.label_at.x + 1.2"
        :y2="item.label_at.y"
        stroke="#fde68a"
        stroke-width="0.22"
        opacity="0.7"
      />
      <text
        :x="item.label_at.x"
        :y="item.label_at.y"
        text-anchor="end"
        dominant-baseline="middle"
        font-size="2.1"
        font-weight="700"
        fill="#fde68a"
        fill-opacity="0.95"
      >
        {{ item.label }}
      </text>
    </g>
  </g>
</template>
