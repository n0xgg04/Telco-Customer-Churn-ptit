<script setup>
defineProps({
  table: { type: Object, required: true },
  best: { type: Array, default: () => [] },
})
</script>

<template>
  <div class="table-wrap" tabindex="0" role="region" :aria-label="table.label">
    <table>
      <thead>
        <tr><th v-for="label in table.header" :key="label" scope="col">{{ label }}</th></tr>
      </thead>
      <tbody>
        <tr v-for="([label, ...values], rowIndex) in table.rows" :key="rowIndex">
          <th scope="row">{{ label }}<slot name="row-note" :row-index="rowIndex" /></th>
          <td v-for="(value, column) in values" :key="column" :class="{ best: best[column] === parseFloat(value.replace(',', '.')) }">
            <slot name="value" :value="value">{{ value }}</slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
