<template>
  <div class="frequent-routes">
    <header class="frequent-routes__header">
      <div>
        <p class="frequent-routes__eyebrow">Bookmarks</p>
        <h2>Frequent routes</h2>
        <p class="frequent-routes__caption">
          Pin the city pairs you travel through the most and drop them into new indents with one click.
        </p>
      </div>
      <button v-if="prefillRoute" type="button" class="ghost-btn" @click="applyPrefill">
        Use form values
      </button>
    </header>

    <form class="frequent-routes__form" @submit.prevent="submitBookmark">
      <label>
        From city
        <input v-model="form.from_city" placeholder="Indore" required />
      </label>
      <label>
        To city
        <input v-model="form.to_city" placeholder="Pune" required />
      </label>
      <label>
        From country
        <input v-model="form.from_country" placeholder="India" />
      </label>
      <label>
        To country
        <input v-model="form.to_country" placeholder="India" />
      </label>
      <label class="frequent-routes__label-field">
        Label (optional)
        <input v-model="form.label" placeholder="Client visits" />
      </label>
      <div class="frequent-routes__form-action">
        <button class="primary-btn" type="submit" :disabled="saving || !isFormValid">
          {{ saving ? 'Saving…' : 'Save bookmark' }}
        </button>
      </div>
    </form>

    <p v-if="formError" class="frequent-routes__error">{{ formError }}</p>

    <div v-if="loading" class="frequent-routes__loading">Loading saved routes…</div>
    <div v-else-if="!routes.length" class="frequent-routes__empty">
      <p>No bookmarked routes yet.</p>
      <p class="frequent-routes__hint">Capture a route above to keep it ready for the next request.</p>
    </div>

    <div v-else class="frequent-routes__list">
      <article v-for="route in routes" :key="route.bookmark_id" class="frequent-routes__card">
        <div>
          <p class="frequent-routes__title">
            {{ route.from_city }} → {{ route.to_city }}
          </p>
          <p v-if="route.label" class="frequent-routes__label">{{ route.label }}</p>
          <small class="frequent-routes__meta">
            Used {{ route.times_used || 0 }} times
            <span v-if="route.last_used_at"> · Last used {{ formatTimestamp(route.last_used_at) }}</span>
          </small>
        </div>
        <div class="frequent-routes__actions">
          <button type="button" class="ghost-btn" @click="$emit('select', route)">
            Use route
          </button>
          <button
            type="button"
            class="ghost-btn ghost-btn--danger"
            :disabled="deletingId === route.bookmark_id || saving"
            @click="$emit('delete', route.bookmark_id)"
          >
            {{ deletingId === route.bookmark_id ? 'Removing…' : 'Remove' }}
          </button>
        </div>
      </article>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FrequentRoutes',
  props: {
    routes: {
      type: Array,
      default: () => [],
    },
    loading: {
      type: Boolean,
      default: false,
    },
    saving: {
      type: Boolean,
      default: false,
    },
    deletingId: {
      type: String,
      default: null,
    },
    addSuccessKey: {
      type: Number,
      default: 0,
    },
    prefillRoute: {
      type: Object,
      default: null,
    },
  },
  emits: ['create', 'select', 'delete'],
  data() {
    return {
      form: {
        from_city: '',
        to_city: '',
        from_country: 'India',
        to_country: 'India',
        label: '',
      },
      formError: '',
    }
  },
  computed: {
    isFormValid() {
      return Boolean(this.form.from_city.trim() && this.form.to_city.trim())
    },
  },
  watch: {
    addSuccessKey() {
      this.resetForm()
    },
  },
  methods: {
    submitBookmark() {
      if (!this.isFormValid) {
        this.formError = 'Both origin and destination are required.'
        return
      }
      this.formError = ''
      const payload = {
        from_city: this.form.from_city.trim(),
        to_city: this.form.to_city.trim(),
        from_country: this.form.from_country?.trim() || 'India',
        to_country: this.form.to_country?.trim() || 'India',
        label: this.form.label?.trim() || undefined,
      }
      this.$emit('create', payload)
    },
    resetForm() {
      this.form = {
        from_city: '',
        to_city: '',
        from_country: 'India',
        to_country: 'India',
        label: '',
      }
      this.formError = ''
    },
    applyPrefill() {
      if (!this.prefillRoute) return
      this.form.from_city = this.prefillRoute.from_city || ''
      this.form.to_city = this.prefillRoute.to_city || ''
      this.form.from_country = this.prefillRoute.from_country || 'India'
      this.form.to_country = this.prefillRoute.to_country || 'India'
    },
    formatTimestamp(value) {
      if (!value) return ''
      const date = new Date(value)
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
    },
  },
}
</script>

<style scoped>
.frequent-routes__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}

.frequent-routes__eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.7rem;
  color: var(--slate-500);
}

.frequent-routes__caption {
  margin: 0.2rem 0 0;
  color: var(--slate-500);
}

.frequent-routes__form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.frequent-routes__form label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-weight: 600;
  color: var(--slate-600);
}

.frequent-routes__form input {
  border-radius: 0.8rem;
  border: 1px solid var(--slate-200);
  padding: 0.55rem 0.75rem;
}

.frequent-routes__label-field {
  grid-column: span 2;
}

.frequent-routes__form-action {
  display: flex;
  align-items: flex-end;
}

.frequent-routes__error {
  color: var(--danger-500);
  margin: 0 0 0.75rem;
}

.frequent-routes__loading,
.frequent-routes__empty {
  padding: 1rem;
  border-radius: 1rem;
  background: var(--slate-50);
  color: var(--slate-500);
}

.frequent-routes__hint {
  margin: 0.25rem 0 0;
  font-size: 0.85rem;
}

.frequent-routes__list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.frequent-routes__card {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 1rem;
  padding: 0.9rem 1rem;
  background: linear-gradient(120deg, rgba(59, 130, 246, 0.05), rgba(99, 102, 241, 0.05));
}

.frequent-routes__title {
  margin: 0;
  font-weight: 600;
}

.frequent-routes__label {
  margin: 0.15rem 0;
  color: var(--primary-600);
  font-weight: 600;
}

.frequent-routes__meta {
  color: var(--slate-500);
}

.frequent-routes__actions {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.ghost-btn--danger {
  border-color: rgba(239, 68, 68, 0.4);
  color: var(--danger-500);
}

@media (max-width: 720px) {
  .frequent-routes__card {
    flex-direction: column;
  }
  .frequent-routes__actions {
    flex-direction: row;
    flex-wrap: wrap;
  }
}
</style>
