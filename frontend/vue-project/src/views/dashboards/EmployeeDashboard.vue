<template>
  <div class="dashboard-grid">
    <section class="dashboard-panel">
      <header class="panel-header">
        <p class="panel-eyebrow">Employee workspace</p>
        <h2>Raise a travel indent</h2>
        <p>
          Trip requests route to your manager first and then HR/travel desk. Save drafts when you're waiting on
          confirmations.
        </p>
      </header>

      <form class="indent-form" @submit.prevent="submitIndent" ref="indentForm">
        <label>
          Purpose of travel
          <textarea
            v-model="form.purpose_of_booking"
            rows="3"
            required
            placeholder="Client review meet in Pune to finalize Q4 rollouts"
          ></textarea>
        </label>

        <div class="form-grid form-grid--aligned">
          <label>
            Travel type
            <select v-model="form.travel_type" @change="onTravelTypeChange">
              <option value="domestic">Domestic</option>
              <option value="international">International</option>
            </select>
          </label>
          <div class="field-hint field-hint--subtle">
            {{
              isInternational
                ? 'International requests trigger compliance and visa checks.'
                : 'Domestic requests only need city details.'
            }}
          </div>
        </div>

        <p class="field-hint">
          {{
            isInternational
              ? 'International trips need both city and country details for visa and ticketing.'
              : 'Domestic trips auto-fill India as the country.'
          }}
        </p>

        <div class="form-grid">
          <label>
            Travel start date
            <input v-model="form.travel_start_date" type="date" :min="today" @change="normalizeDates" required />
          </label>
          <label>
            Travel end date
            <input
              v-model="form.travel_end_date"
              type="date"
              :min="form.travel_start_date || today"
              @change="normalizeDates"
              required
            />
          </label>
        </div>

        <div class="form-grid">
          <label>
            From city
            <input v-model="form.from_city" required placeholder="Indore" />
          </label>
          <label>
            To city
            <input v-model="form.to_city" required placeholder="Pune" />
          </label>
        </div>

        <div class="form-grid" v-if="isInternational">
          <label>
            From country
            <input v-model="form.from_country" required placeholder="India" />
          </label>
          <label>
            To country
            <input v-model="form.to_country" required placeholder="Germany" />
          </label>
        </div>
        <div class="field-hint" v-else>
          Countries stay locked to India for domestic trips. Change only if you are travelling from a different base
          location.
        </div>

        <div class="button-row">
          <button class="primary-btn" type="submit" :disabled="submitLoading">
            {{ submitLoading ? 'Submitting…' : 'Submit travel request' }}
          </button>
          <button class="ghost-btn" type="button" @click="saveDraft" :disabled="submitLoading">Save draft</button>
        </div>

        <p v-if="formMessage" class="form-message">{{ formMessage }}</p>
      </form>
    </section>

    <section class="dashboard-stack">
      <div class="metrics-grid">
        <MetricCard title="Manager review" :value="openCount" caption="Waiting for manager" />
        <MetricCard title="With HR / Travel" variant="success" :value="approvedCount" caption="Cleared by manager" />
        <MetricCard title="Drafts" variant="info" :value="draftCount" caption="Parked for later" />
        <MetricCard title="Rejected" variant="danger" :value="rejectedCount" caption="Needs revision" />
      </div>

      <div class="dashboard-panel">
        <FrequentRoutes
          :routes="bookmarkedRoutes"
          :loading="bookmarkLoading"
          :saving="bookmarkSaving"
          :deleting-id="bookmarkDeletingId"
          :add-success-key="bookmarkSuccessKey"
          :prefill-route="currentRoutePrefill"
          @create="handleBookmarkCreate"
          @select="useBookmarkRoute"
          @delete="handleBookmarkDelete"
        />
        <p v-if="bookmarkError" class="form-error">{{ bookmarkError }}</p>
      </div>

      <div class="role-lane-grid">
        <div class="dashboard-panel">
          <h2>Manager lane</h2>
          <p class="panel-caption">Items waiting for people leaders to approve.</p>
          <TravelList :items="managerLaneTickets" :loading="loading">
            <template #empty>
              <p>Nothing pending with your manager right now.</p>
            </template>
          </TravelList>
        </div>

        <div class="dashboard-panel">
          <h2>HR & travel desk</h2>
          <p class="panel-caption">Requests that cleared manager review now sit with HR/travel.</p>
          <TravelList :items="hrLaneTickets" :loading="loading">
            <template #empty>
              <p>Once your manager approves you'll see requests here.</p>
            </template>
          </TravelList>
        </div>
      </div>

      <div class="dashboard-panel">
        <h2>Drafts</h2>
        <p class="panel-caption">Resume a saved draft to finish submission.</p>
        <TravelList :items="draftTickets" :loading="loading">
          <template #actions="{ item }">
            <button type="button" class="ghost-btn ghost-btn--inline" @click="resumeDraft(item)">Resume draft</button>
          </template>
          <template #empty>
            <p>No drafts yet. Use the Save draft button to capture partial details.</p>
          </template>
        </TravelList>
      </div>

      <div class="dashboard-panel">
        <h2>History</h2>
        <p class="panel-caption">Completed, booked, or rejected requests stay here for reference.</p>
        <TravelList :items="historyTickets" :loading="loading">
          <template #empty>
            <p>No historical requests yet.</p>
          </template>
        </TravelList>
      </div>

      <div class="assistant-card">
        <div>
          <h2>Travel policy assistant</h2>
          <p>Ask about entitlements, grade-wise limits, or approval workflows.</p>
        </div>
        <div class="chip-row">
          <button
            v-for="suggestion in policySuggestions"
            :key="suggestion"
            type="button"
            class="suggestion-chip"
            @click="sendSuggestion(suggestion)"
          >
            {{ suggestion }}
          </button>
        </div>
        <button class="primary-btn" type="button" @click="openPolicyChat()">Chat with policy bot</button>
      </div>
    </section>
  </div>

  <transition name="chat-slide">
    <section v-if="policyChatOpen" class="chat-drawer">
      <header>
        <div>
          <p class="chat-label">Policy knowledge base</p>
          <h3>Answers grounded in the latest travel policy</h3>
        </div>
        <button class="ghost-btn" type="button" @click="closePolicyChat">Close</button>
      </header>

      <div class="chat-body">
        <div v-if="!policyMessages.length && !policyLoading" class="chat-empty">
          <p>Ask about allowances, reimbursement docs, eligibility, or approvals.</p>
          <div class="chip-row">
            <button
              v-for="suggestion in policySuggestions"
              :key="`empty-${suggestion}`"
              type="button"
              class="suggestion-chip"
              @click="sendSuggestion(suggestion)"
            >
              {{ suggestion }}
            </button>
          </div>
        </div>

        <div class="chat-scroll" ref="policyChatScrollRef">
          <article
            v-for="(message, index) in policyMessages"
            :key="index"
            :class="['chat-bubble', `chat-bubble--${message.role}`]"
          >
            <header class="chat-bubble__header" v-if="message.role === 'assistant'">
              <span class="assistant-tag">Policy bot</span>
              <time v-if="message.created_at">{{ formatTimestamp(message.created_at) }}</time>
            </header>

            <div class="chat-bubble__content" v-html="renderMessage(message.content)"></div>

            <details v-if="message.sources?.length" class="chat-sources" open>
              <summary>Sources ({{ message.sources.length }})</summary>
              <ol>
                <li v-for="(source, idx) in message.sources" :key="idx">
                  <strong>Source {{ idx + 1 }}:</strong>
                  <span v-html="renderSource(source.text)"></span>
                </li>
              </ol>
            </details>
          </article>

          <div v-if="policyLoading" class="chat-loading">Consulting policies…</div>
        </div>
      </div>

      <form class="chat-input" @submit.prevent="sendPolicyMessage()">
        <input
          v-model="policyInput"
          type="text"
          placeholder="e.g., What is the hotel limit for Grade E4 in Mumbai?"
          :disabled="policyLoading"
        />
        <button class="primary-btn" type="submit" :disabled="policyLoading || !policyInput.trim()">
          Ask
        </button>
      </form>

      <p v-if="policyError" class="chat-error">{{ policyError }}</p>
    </section>
  </transition>
</template>

<script>
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import MetricCard from '../../components/MetricCard.vue'
import TravelList from '../../components/TravelList.vue'
import FrequentRoutes from '../../components/FrequentRoutes.vue'
import api from '../../services/api'

const MANAGER_QUEUE_STATUSES = new Set(['pending', 'manager_pending', 'pending_manager', 'submitted', ''])
const HR_QUEUE_STATUSES = new Set(['accepted_manager', 'accpeted_manager', 'manager_approved', 'hr_approved'])
const HISTORY_STATUSES = new Set([
  'completed_hr',
  'completed',
  'booked',
  'rejected_manager',
  'rejected_hr',
  'rejected',
  'declined',
])

export default {
  name: 'EmployeeDashboard',
  components: {
    MetricCard,
    TravelList,
    FrequentRoutes,
  },
  data() {
    const today = new Date().toISOString().slice(0, 10)
    return {
      today,
      tickets: [],
      loading: false,
      submitLoading: false,
      formMessage: '',
      bookmarkedRoutes: [],
      bookmarkLoading: false,
      bookmarkSaving: false,
      bookmarkDeletingId: null,
      bookmarkSuccessKey: 0,
      bookmarkError: '',
      form: {
        purpose_of_booking: '',
        travel_type: 'domestic',
        travel_start_date: today,
        travel_end_date: today,
        from_city: '',
        from_country: 'India',
        to_city: '',
        to_country: 'India',
        indent_id: null,
      },
      policyChatOpen: false,
      policyMessages: [],
      policyInput: '',
      policySessionId: null,
      policyLoading: false,
      policyError: '',
      policySuggestions: [
        'How many days of daily allowance can I claim?',
        'Do I need extra approvals for international travel?',
      ],
    }
  },
  computed: {
    currentRoutePrefill() {
      return {
        from_city: this.form.from_city,
        to_city: this.form.to_city,
        from_country: this.form.from_country,
        to_country: this.form.to_country,
      }
    },
    isInternational() {
      return (this.form.travel_type || '').toLowerCase() === 'international'
    },
    draftTickets() {
      return this.tickets.filter((ticket) => this.getStatusCode(ticket) === 'draft')
    },
    historyTickets() {
      return this.tickets.filter((ticket) => HISTORY_STATUSES.has(this.getStatusCode(ticket)))
    },
    managerLaneTickets() {
      return this.tickets.filter((ticket) => {
        const code = this.getStatusCode(ticket)
        if (code === 'draft') return false
        if (HISTORY_STATUSES.has(code)) return false
        return MANAGER_QUEUE_STATUSES.has(code)
      })
    },
    hrLaneTickets() {
      return this.tickets.filter((ticket) => {
        const code = this.getStatusCode(ticket)
        if (code === 'draft') return false
        if (HISTORY_STATUSES.has(code)) return false
        return HR_QUEUE_STATUSES.has(code)
      })
    },
    openCount() {
      return this.managerLaneTickets.length
    },
    approvedCount() {
      return this.hrLaneTickets.length
    },
    draftCount() {
      return this.draftTickets.length
    },
    rejectedCount() {
      return this.historyTickets.filter((ticket) => this.getStatusCode(ticket).includes('reject')).length
    },
  },
  methods: {
    async fetchBookmarks() {
      this.bookmarkLoading = true
      try {
        const { data } = await api.get('/employee/frequent-routes')
        const normalized = Array.isArray(data?.items) ? data.items : []
        this.bookmarkedRoutes = normalized
        this.bookmarkError = ''
      } catch (error) {
        console.error('Failed to load frequent routes', error)
        this.bookmarkError = 'Unable to load frequent routes'
      } finally {
        this.bookmarkLoading = false
      }
    },
    async handleBookmarkCreate(payload) {
      if (this.bookmarkSaving) return
      this.bookmarkError = ''
      this.bookmarkSaving = true
      try {
        await api.post('/employee/frequent-routes', {
          from_city: payload.from_city,
          to_city: payload.to_city,
          from_country: payload.from_country,
          to_country: payload.to_country,
          label: payload.label,
        })
        this.bookmarkSuccessKey += 1
        await this.fetchBookmarks()
      } catch (error) {
        console.error('Bookmark save failed', error)
        this.bookmarkError = error?.response?.data?.detail || 'Unable to save bookmark'
      } finally {
        this.bookmarkSaving = false
      }
    },
    async handleBookmarkDelete(bookmarkId) {
      if (!bookmarkId) return
      this.bookmarkError = ''
      this.bookmarkDeletingId = bookmarkId
      try {
        await api.delete(`/employee/frequent-routes/${bookmarkId}`)
        await this.fetchBookmarks()
      } catch (error) {
        console.error('Bookmark delete failed', error)
        this.bookmarkError = error?.response?.data?.detail || 'Unable to delete bookmark'
      } finally {
        this.bookmarkDeletingId = null
      }
    },
    async useBookmarkRoute(route) {
      if (!route) return
      this.form.from_city = route.from_city || ''
      this.form.to_city = route.to_city || ''
      this.form.from_country = route.from_country || (this.isInternational ? '' : 'India')
      this.form.to_country = route.to_country || (this.isInternational ? '' : 'India')
      this.form.travel_type = this.detectTravelTypeFromRoute(route)
      this.onTravelTypeChange()
      try {
        await api.post(`/employee/frequent-routes/${route.bookmark_id}/use`)
        await this.fetchBookmarks()
      } catch (error) {
        console.warn('Bookmark usage tracking failed', error)
      }
      this.formMessage = 'Route prefilled from your bookmarks.'
      this.$nextTick(() => {
        if (this.$refs.indentForm) {
          this.$refs.indentForm.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      })
    },
    detectTravelTypeFromRoute(route) {
      const fromCountry = (route.from_country || '').trim().toLowerCase()
      const toCountry = (route.to_country || '').trim().toLowerCase()
      if (!fromCountry || !toCountry) return this.form.travel_type || 'domestic'
      return fromCountry === 'india' && toCountry === 'india' ? 'domestic' : 'international'
    },
    getStatusCode(ticket) {
      return (ticket?.status_code || ticket?.status || '').toString().trim().toLowerCase()
    },
    async fetchTickets() {
      this.loading = true
      try {
        const { data } = await api.get('/employee/my-indents')
        const normalized = Array.isArray(data) ? data : data?.items || data?.indents || data?.data || []
        this.tickets = Array.isArray(normalized) ? normalized : []
      } catch (error) {
        console.error('Failed to load tickets', error)
      } finally {
        this.loading = false
      }
    },
    prepareFormPayload() {
      const payload = { ...this.form }
      payload.travel_type = (payload.travel_type || 'domestic').toLowerCase()
      if (payload.travel_type !== 'international') {
        payload.from_country = payload.from_country || 'India'
        payload.to_country = payload.to_country || 'India'
      }
      if (!payload.indent_id) {
        delete payload.indent_id
      }
      return payload
    },
    async submitIndent() {
      this.formMessage = ''
      this.submitLoading = true
      try {
        const payload = this.prepareFormPayload()
        const { data } = await api.post('/employee/create-indent', payload)
        this.formMessage = data.message || 'Travel request submitted'
        this.resetForm(payload.travel_type)
        await this.fetchTickets()
      } catch (error) {
        this.formMessage = error?.response?.data?.detail || 'Unable to submit indent'
      } finally {
        this.submitLoading = false
      }
    },
    async saveDraft() {
      this.formMessage = ''
      this.submitLoading = true
      try {
        const payload = this.prepareFormPayload()
        const { data } = await api.post('/employee/save-draft', payload)
        this.formMessage = data.message || 'Draft saved'
        if (data?.indent_id) {
          this.form.indent_id = data.indent_id
        }
        // keep form values but refresh ticket list
        await this.fetchTickets()
      } catch (error) {
        this.formMessage = error?.response?.data?.detail || 'Unable to save draft'
      } finally {
        this.submitLoading = false
      }
    },
    onTravelTypeChange() {
      this.form.travel_type = (this.form.travel_type || 'domestic').toLowerCase()
      if (this.form.travel_type === 'international') {
        if (!this.form.to_country) this.form.to_country = ''
        if (!this.form.from_country) this.form.from_country = ''
      } else {
        this.form.to_country = 'India'
        this.form.from_country = 'India'
      }
      this.normalizeDates()
    },
    normalizeDates() {
      if (!this.form.travel_start_date || this.form.travel_start_date < this.today) {
        this.form.travel_start_date = this.today
      }
      if (!this.form.travel_end_date || this.form.travel_end_date < this.form.travel_start_date) {
        this.form.travel_end_date = this.form.travel_start_date
      }
    },
    resetForm(travelType = 'domestic') {
      const type = travelType || 'domestic'
      this.form = {
        purpose_of_booking: '',
        travel_type: type,
        travel_start_date: this.today,
        travel_end_date: this.today,
        from_city: '',
        from_country: type === 'international' ? '' : 'India',
        to_city: '',
        to_country: type === 'international' ? '' : 'India',
        indent_id: null,
      }
    },
    resumeDraft(draft) {
      if (!draft) return
      const travelType = (draft.travel_type || 'domestic').toLowerCase()
      this.form = {
        purpose_of_booking: draft.purpose_of_booking || draft.purpose || '',
        travel_type: travelType,
        travel_start_date: draft.travel_start_date || this.today,
        travel_end_date: draft.travel_end_date || draft.travel_start_date || this.today,
        from_city: draft.from_city || '',
        from_country:
          travelType === 'international' ? draft.from_country || '' : draft.from_country || 'India',
        to_city: draft.to_city || '',
        to_country:
          travelType === 'international' ? draft.to_country || '' : draft.to_country || 'India',
        indent_id: draft.indent_id,
      }
      this.normalizeDates()
      this.formMessage = 'Draft loaded. Review details and submit when ready.'
      this.$nextTick(() => {
        if (this.$refs.indentForm) {
          this.$refs.indentForm.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      })
    },
    openPolicyChat(prefill) {
      this.policyChatOpen = true
      this.policyMessages = []
      this.policyInput = ''
      this.policySessionId = null
      this.policyError = ''
      this.policyLoading = false
      this.$nextTick(() => {
        this.scrollPolicyChatToBottom()
        if (prefill) {
          this.sendPolicyMessage(prefill)
        }
      })
    },
    closePolicyChat() {
      this.policyChatOpen = false
      this.policyMessages = []
      this.policyInput = ''
      this.policySessionId = null
      this.policyError = ''
      this.policyLoading = false
    },
    sendSuggestion(suggestion) {
      if (!suggestion) return
      if (!this.policyChatOpen) {
        this.openPolicyChat(suggestion)
        return
      }
      this.sendPolicyMessage(suggestion)
    },
    async sendPolicyMessage(customMessage) {
      const message = (customMessage ?? this.policyInput).trim()
      if (!message) return

      this.policyError = ''
      this.policyLoading = true

      this.policyMessages.push({ role: 'user', content: message, created_at: new Date().toISOString() })
      if (!customMessage) {
        this.policyInput = ''
      }
      this.$nextTick(() => this.scrollPolicyChatToBottom())

      try {
        const payload = {
          session_id: this.policySessionId,
          message,
        }
        const { data } = await api.post('/employee/policy/chat', payload)
        this.policySessionId = data.session_id
        this.policyMessages.push({
          role: 'assistant',
          content: data.response,
          sources: data.sources,
          created_at: new Date().toISOString(),
        })
      } catch (error) {
        console.error('Policy chat failed', error)
        this.policyError = error?.response?.data?.detail || 'Unable to reach policy assistant'
      } finally {
        this.policyLoading = false
        this.$nextTick(() => this.scrollPolicyChatToBottom())
      }
    },
    scrollPolicyChatToBottom() {
      const el = this.$refs.policyChatScrollRef
      if (el) {
        el.scrollTop = el.scrollHeight
      }
    },
    renderMessage(content) {
      if (!content) return ''
      const html = marked.parse(content, { breaks: true })
      return DOMPurify.sanitize(html)
    },
    renderSource(content) {
      if (!content) return ''
      const html = marked.parseInline(content)
      return DOMPurify.sanitize(html)
    },
    formatTimestamp(isoString) {
      if (!isoString) return ''
      const date = new Date(isoString)
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    },
  },
  mounted() {
    this.fetchTickets()
    this.fetchBookmarks()
  },
}
</script>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 2rem;
}

.dashboard-panel {
  background: white;
  border-radius: 1.5rem;
  padding: 1.75rem;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.1);
}

.dashboard-panel h2 {
  margin: 0 0 0.25rem;
}

.dashboard-panel p {
  margin: 0 0 1.5rem;
  color: var(--slate-500);
}

.dashboard-stack {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.panel-header {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-bottom: 1rem;
}

.panel-eyebrow {
  margin: 0;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  color: var(--slate-500);
}

.panel-caption {
  margin: 0 0 1rem;
  color: var(--slate-500);
  font-size: 0.9rem;
}

.indent-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.9rem;
}

.form-grid--aligned {
  align-items: flex-end;
}

label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-weight: 600;
  color: var(--slate-600);
}

textarea,
select,
input {
  border-radius: 0.9rem;
  border: 1px solid var(--slate-200);
  padding: 0.75rem 1rem;
  font-family: inherit;
}

textarea {
  resize: vertical;
}

.field-hint {
  background: var(--slate-50);
  border-left: 3px solid rgba(59, 130, 246, 0.3);
  padding: 0.6rem 0.8rem;
  border-radius: 0.9rem;
  font-size: 0.9rem;
  color: var(--slate-600);
}

.field-hint--subtle {
  background: transparent;
  border: none;
  padding: 0;
  color: var(--slate-500);
  font-size: 0.85rem;
}

.form-message {
  background: var(--success-100);
  color: var(--success-500);
  padding: 0.75rem 1rem;
  border-radius: 0.9rem;
}

.form-error {
  color: var(--danger-500);
  margin: 0.5rem 0 0;
}

.button-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
}

.role-lane-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.assistant-card {
  background: linear-gradient(135deg, #eef2ff 0%, #f8fafc 100%);
  border-radius: 1.5rem;
  padding: 1.5rem;
  box-shadow: 0 15px 45px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.suggestion-chip {
  border-radius: 999px;
  border: 1px solid rgba(59, 130, 246, 0.3);
  padding: 0.35rem 0.95rem;
  background: white;
  cursor: pointer;
  color: var(--primary-600);
  font-weight: 600;
}

.ghost-btn {
  border: 1px solid var(--slate-200);
  border-radius: 0.8rem;
  padding: 0.4rem 0.8rem;
  background: white;
  cursor: pointer;
  font-weight: 600;
}

.ghost-btn--inline {
  padding: 0.35rem 0.75rem;
  font-size: 0.85rem;
}

.chat-drawer {
  position: fixed;
  bottom: 0;
  right: 0;
  width: min(520px, 100%);
  max-height: 92vh;
  background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%);
  border-top-left-radius: 1.5rem;
  box-shadow: 0 -15px 60px rgba(15, 23, 42, 0.25);
  padding: 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  border-left: 1px solid rgba(15, 23, 42, 0.08);
  border-top: 1px solid rgba(15, 23, 42, 0.08);
}

.chat-drawer header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.chat-label {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--slate-500);
  margin: 0;
}

.chat-meta {
  margin: 0;
  color: var(--slate-500);
}

.chat-body {
  flex: 1;
  min-height: 320px;
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 1.25rem;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  background: white;
}

.chat-scroll {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.chat-bubble {
  padding: 0.85rem 1rem;
  border-radius: 1.05rem;
  max-width: 92%;
  box-shadow: 0 15px 45px rgba(15, 23, 42, 0.08);
  border: 1px solid transparent;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.chat-bubble__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--slate-500);
}

.assistant-tag {
  background: rgba(59, 130, 246, 0.15);
  color: var(--primary-700);
  border-radius: 999px;
  padding: 0.1rem 0.6rem;
  font-weight: 700;
}

.chat-bubble__content {
  font-size: 0.95rem;
  line-height: 1.5;
  margin: 0;
  overflow-wrap: anywhere;
}

.chat-bubble__content :where(p, ul, ol, pre, code) {
  margin: 0.35rem 0;
}

.chat-bubble__content pre {
  background: rgba(15, 23, 42, 0.08);
  padding: 0.5rem 0.75rem;
  border-radius: 0.75rem;
  overflow-x: auto;
}

.chat-bubble__content code {
  background: rgba(15, 23, 42, 0.08);
  padding: 0.15rem 0.35rem;
  border-radius: 0.4rem;
}

.chat-bubble--user {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: white;
  align-self: flex-end;
  border-color: rgba(255, 255, 255, 0.3);
}

.chat-bubble--assistant {
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.06);
  align-self: flex-start;
}

.chat-sources {
  margin: 0.5rem 0 0;
  padding: 0.4rem 0.6rem;
  border-radius: 0.9rem;
  background: rgba(15, 23, 42, 0.04);
  border: 1px dashed rgba(15, 23, 42, 0.1);
  font-size: 0.82rem;
  color: var(--slate-600);
}

.chat-sources summary {
  cursor: pointer;
  font-weight: 600;
  margin-bottom: 0.3rem;
}

.chat-sources ol {
  margin: 0;
  padding-left: 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.chat-loading {
  text-align: center;
  color: var(--slate-500);
}

.chat-input {
  display: flex;
  gap: 0.75rem;
}

.chat-input input {
  flex: 1;
  border-radius: 999px;
  border: 1px solid rgba(59, 130, 246, 0.4);
  padding: 0.9rem 1.1rem;
  background: rgba(59, 130, 246, 0.04);
}

.chat-empty {
  text-align: center;
  margin-bottom: 1rem;
  color: var(--slate-500);
}

.chat-error {
  color: var(--danger-500);
  margin: 0;
}

.chat-slide-enter-active,
.chat-slide-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.chat-slide-enter-from,
.chat-slide-leave-to {
  transform: translateY(20px);
  opacity: 0;
}
</style>
