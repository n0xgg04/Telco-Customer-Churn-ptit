<script setup>
defineProps({
  points: { type: Array, required: true },
})
</script>

<template>
  <ul class="point-list">
    <li v-for="point in points" :key="point">
      <template v-for="(segment, index) in point.split('**')" :key="index">
        <strong v-if="index % 2">{{ segment }}</strong>
        <span v-else>{{ segment.replaceAll('`', '') }}</span>
      </template>
    </li>
  </ul>
</template>
