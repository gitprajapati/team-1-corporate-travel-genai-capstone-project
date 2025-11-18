<template>
  <div class="metric-card" :class="variantClass">
    <div class="metric-card__header">
      <p class="metric-card__title">{{ title }}</p>
      <slot name="icon"></slot>
    </div>
    <p class="metric-card__value">{{ value }}</p>
    <p v-if="caption" class="metric-card__caption">{{ caption }}</p>
  </div>
</template>

<script>
export default {
  name: 'MetricCard',
  props: {
    title: {
      type: String,
      required: true,
    },
    value: {
      type: [String, Number],
      required: true,
    },
    caption: {
      type: String,
      default: '',
    },
    variant: {
      type: String,
      default: 'default',
    },
  },
  computed: {
    variantClass() {
      return `metric-card--${this.variant}`
    },
  },
}
</script>

<style scoped>
.metric-card {
  background: white;
  border-radius: 1rem;
  padding: 1.25rem;
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.metric-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--slate-500);
  font-size: 0.9rem;
}

.metric-card__title {
  margin: 0;
  font-weight: 600;
}

.metric-card__value {
  font-size: 2rem;
  margin: 0;
  font-weight: 700;
  color: var(--slate-900);
}

.metric-card__caption {
  margin: 0;
  font-size: 0.9rem;
  color: var(--slate-500);
}

.metric-card--success {
  border-color: rgba(16, 185, 129, 0.4);
}

.metric-card--warning {
  border-color: rgba(234, 179, 8, 0.4);
}

.metric-card--danger {
  border-color: rgba(239, 68, 68, 0.4);
}
</style>
