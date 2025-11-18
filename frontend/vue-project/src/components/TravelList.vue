<template>
  <div class="travel-list">
    <div v-if="!items.length && !loading" class="travel-list__empty">
      <slot name="empty">No records yet.</slot>
    </div>

    <div v-else>
      <article
        v-for="item in items"
        :key="item.indent_id"
        :class="['travel-card', cardAccent(item.status)]"
      >
        <div class="travel-card__header">
          <div>
            <p class="travel-card__title">{{ item.purpose_of_booking || item.purpose || 'Travel Request' }}</p>
            <p class="travel-card__subtitle">
              {{ formatCity(item.from_city, item.to_city) }}
            </p>
          </div>
          <span class="travel-card__badge" :class="statusClass(item.status)">{{ formatStatus(item.status) }}</span>
        </div>
        <div class="travel-card__meta">
          <div>
            <small>Indent ID</small>
            <p>{{ item.indent_id }}</p>
          </div>
          <div>
            <small>Travel Dates</small>
            <p>{{ formatDates(item.travel_start_date, item.travel_end_date) }}</p>
          </div>
          <div>
            <small>Type</small>
            <p>{{ (item.travel_type || 'domestic').toUpperCase() }}</p>
          </div>
          <slot name="actions" :item="item"></slot>
        </div>
      </article>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TravelList',
  props: {
    items: {
      type: Array,
      default: () => [],
    },
    loading: {
      type: Boolean,
      default: false,
    },
  },
  methods: {
    formatStatus(value) {
      if (!value) return 'Pending'
      const normalized = String(value).toLowerCase()
      if (normalized.includes('draft')) return 'Draft'
      if (normalized.includes('rejected') || normalized.includes('reject')) return 'Rejected'
      if (normalized.includes('approved by manager') || normalized.includes('accept') || normalized.includes('approve')) return 'Approved by manager'
      if (normalized.includes('pending')) return 'Pending'
      if (normalized.includes('completed') || normalized.includes('booked') || normalized.includes('hr_approved')) return 'Completed'
      // fallback: return given label nicely
      const s = String(value)
      return s.charAt(0).toUpperCase() + s.slice(1)
    },
    statusClass(value) {
      const normalized = String(value || '').toLowerCase()
      if (normalized.includes('draft')) return 'travel-card__badge--info'
      if (normalized.includes('reject')) return 'travel-card__badge--danger'
      if (normalized.includes('approved') || normalized.includes('accept')) return 'travel-card__badge--success'
      if (normalized.includes('pending')) return 'travel-card__badge--warning'
      if (normalized.includes('completed') || normalized.includes('booked')) return 'travel-card__badge--success'
      return 'travel-card__badge--info'
    },
    cardAccent(value) {
      const normalized = String(value || '').toLowerCase()
      if (normalized.includes('draft')) return 'travel-card--info'
      if (normalized.includes('reject')) return 'travel-card--danger'
      if (normalized.includes('approved') || normalized.includes('accept')) return 'travel-card--success'
      if (normalized.includes('pending')) return 'travel-card--warning'
      if (normalized.includes('complete') || normalized.includes('booked')) return 'travel-card--success'
      return 'travel-card--info'
    },
    formatDates(start, end) {
      if (!start && !end) return 'TBD'
      if (!end || start === end) return start || end
      return `${start} → ${end}`
    },
    formatCity(from, to) {
      if (!from && !to) return 'Route TBD'
      return `${from || 'Origin'} → ${to || 'Destination'}`
    },
  },
}
</script>

<style scoped>
.travel-card {
  position: relative;
  background: linear-gradient(135deg, #ffffff, #f8fbff);
  border-radius: 1rem;
  padding: 1rem 1.25rem;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
  margin-bottom: 0.85rem;
  border-left: 6px solid rgba(59, 130, 246, 0.3);
  background-image:
    radial-gradient(circle at 5% 0%, rgba(59, 130, 246, 0.18), transparent 45%),
    radial-gradient(circle at 90% 10%, rgba(236, 72, 153, 0.12), transparent 40%),
    linear-gradient(135deg, #ffffff, #f8fbff);
}

.travel-card--success {
  border-left-color: var(--success-500);
}

.travel-card--warning {
  border-left-color: var(--warning-500);
}

.travel-card--danger {
  border-left-color: var(--danger-500);
}

.travel-card--info {
  border-left-color: var(--primary-500);
}

.travel-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.travel-card__title {
  margin: 0;
  font-weight: 600;
  font-size: 1.05rem;
}

.travel-card__subtitle {
  margin: 0.15rem 0 0;
  color: var(--slate-500);
}

.travel-card__badge {
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 600;
}

.travel-card__badge--success {
  background: var(--success-100);
  color: var(--success-500);
}

.travel-card__badge--warning {
  background: var(--warning-100);
  color: var(--warning-500);
}

.travel-card__badge--danger {
  background: var(--danger-100);
  color: var(--danger-500);
}

.travel-card__badge--info {
  background: var(--primary-50);
  color: var(--primary-600);
}

.travel-card__meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
  font-size: 0.9rem;
}

.travel-card__meta small {
  display: block;
  color: var(--slate-500);
  margin-bottom: 0.25rem;
}

.travel-card__meta p {
  margin: 0;
  font-weight: 600;
}

.travel-list__empty {
  padding: 2rem;
  text-align: center;
  border: 1px dashed var(--slate-200);
  border-radius: 1rem;
  background: white;
  color: var(--slate-500);
}
</style>
