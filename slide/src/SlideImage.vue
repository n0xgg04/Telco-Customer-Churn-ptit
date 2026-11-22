<script setup>
import { Icon } from '@iconify/vue'
import expandIcon from '@iconify-icons/lucide/expand'

defineProps({
  src: { type: String, required: true },
  alt: { type: String, required: true },
})
defineEmits(['zoom'])
</script>

<template>
  <button type="button" class="media-button" :aria-label="`Phóng to ảnh. ${alt}`" @click="$emit('zoom')">
    <img :src="src" :alt="alt">
    <span class="zoom-icon" aria-hidden="true"><Icon :icon="expandIcon" /></span>
  </button>
</template>
