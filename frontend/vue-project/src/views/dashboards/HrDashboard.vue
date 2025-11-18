<template>
  <div class="dashboard-panel pattern-card pattern-card--violet">
    <div class="metrics-grid">
      <MetricCard title="Active tickets" :value="activeTickets" caption="Across all teams" />
      <MetricCard title="Awaiting HR" :value="awaitingHr" caption="Need status update" variant="warning" />
      <MetricCard title="Completed" :value="completed" caption="Marked done" variant="success" />
    </div>

    <section
      v-for="section in ticketSections"
      :key="section.key"
      class="hr-section"
      :class="section.pattern"
    >
      <header>
        <div>
          <h2>{{ section.title }}</h2>
          <p>{{ section.caption }}</p>
        </div>
        <button class="ghost-btn" @click="fetchTickets">Refresh</button>
      </header>

      <div class="table-wrapper pattern-card pattern-card--slate" v-if="section.tickets.length">
        <table>
          <thead>
            <tr>
              <th>Indent ID</th>
              <th>Employee</th>
              <th>Route</th>
              <th>Dates</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="ticket in section.tickets"
              :key="ticket.indent_id"
              :class="['ticket-row', statusRowClass(ticket)]"
            >
              <td>{{ ticket.indent_id }}</td>
              <td>
                <strong>{{ ticket.employee_name || ticket.employee_id }}</strong>
                <p class="muted">{{ ticket.department }}</p>
              </td>
              <td>{{ ticket.from_city }} → {{ ticket.to_city }}</td>
              <td>{{ ticket.travel_start_date }} → {{ ticket.travel_end_date }}</td>
              <td>
                <span class="status-pill" :class="statusClass(ticket)">
                  {{ statusLabel(ticket) }}
                </span>
              </td>
              <td>
                <div v-if="section.actions === 'manager'" class="action-hint">
                  Waiting on manager approval
                </div>
                <div v-else-if="section.actions === 'readonly'" class="action-hint">
                  Completed · HR already booked
                </div>
                <div v-else class="action-stack">
                  <button
                    v-if="section.actions === 'hr_approval'"
                    class="ghost-btn"
                    :disabled="!canApprove(ticket)"
                    @click="updateStatus(ticket.indent_id, 'hr_approved')"
                  >
                    Mark approved
                  </button>
                  <button
                    v-if="section.actions === 'booking'"
                    class="ghost-btn"
                    :disabled="!canBook(ticket)"
                    @click="updateStatus(ticket.indent_id, 'completed_hr')"
                  >
                    Mark booked
                  </button>
                  <button
                    v-if="section.actions === 'booking'"
                    class="primary-btn"
                    :disabled="!canChat(ticket)"
                    @click="openChat(ticket)"
                  >
                    Chat & book
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p v-else class="empty-state">{{ section.empty }}</p>
    </section>

    <transition name="chat-slide">
      <section v-if="chatOpen" class="chat-drawer">
        <header>
          <div>
            <p class="chat-label">AI booking assistant</p>
            <h3>
              {{ activeTicket?.employee_name || activeTicket?.employee_id }} ·
              {{ activeTicket?.from_city }} → {{ activeTicket?.to_city }}
            </h3>
            <p class="chat-meta">
              Travel: {{ activeTicket?.travel_start_date }} → {{ activeTicket?.travel_end_date }} ·
              Type: {{ activeTicket?.travel_type }} · ID: {{ activeTicket?.indent_id }}
            </p>
          </div>
          <button class="ghost-btn" @click="closeChat">Close</button>
        </header>

        <div class="chat-body">
          <div v-if="!chatMessages.length && !chatLoading" class="chat-empty">
            <p>Start the conversation to plan tickets for this employee.</p>
            <button class="primary-btn" @click="sendPrefill">Suggest itinerary</button>
          </div>

          <div class="chat-scroll" ref="chatScrollRef">
            <article v-for="(message, index) in chatMessages" :key="index" :class="['chat-bubble', `chat-bubble--${message.role}`]">
              <div class="chat-bubble__content" v-html="renderMessage(message.content)"></div>
              <ul v-if="message.tools?.length" class="chat-tools">
                <li v-for="tool in message.tools" :key="tool">🔧 {{ tool }}</li>
              </ul>
            </article>

            <div v-if="chatLoading" class="chat-loading">AI is thinking…</div>
          </div>
        </div>

        <form class="chat-input" @submit.prevent="sendChat()">
          <input
            v-model="chatInput"
            type="text"
            placeholder="Ask the assistant to book flights/hotels or share preferences"
            :disabled="chatLoading"
          />
          <button class="primary-btn" type="submit" :disabled="chatLoading || !chatInput.trim()">Send</button>
        </form>

        <p v-if="chatError" class="chat-error">{{ chatError }}</p>
      </section>
    </transition>
  </div>
</template>

<script>
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import MetricCard from '../../components/MetricCard.vue'
import api from '../../services/api'

const MANAGER_PENDING_STATUSES = new Set(['pending', 'manager_pending', 'pending_manager', 'submitted', ''])
const MANAGER_APPROVED_STATUSES = new Set(['accepted_manager', 'accpeted_manager', 'manager_approved'])
const HR_READY_STATUSES = new Set(['hr_approved'])
const COMPLETED_STATUSES = new Set(['completed_hr', 'booked'])

export default {
  name: 'HrDashboard',
  components: {
    MetricCard,
  },
  data() {
    return {
      tickets: [],
      chatOpen: false,
      activeTicket: null,
      chatMessages: [],
      chatInput: '',
      chatLoading: false,
      chatError: '',
      sessionId: null,
    }
  },
  computed: {
    managerQueue() {
      return this.tickets.filter((ticket) => this.isWaitingOnManager(ticket))
    },
    hrApprovalQueue() {
      return this.tickets.filter((ticket) => this.isAwaitingHrDecision(ticket))
    },
    bookingQueue() {
      return this.tickets.filter((ticket) => this.isReadyForBooking(ticket))
    },
    completedTickets() {
      return this.tickets.filter((ticket) => this.isCompleted(ticket))
    },
    ticketSections() {
      return [
        {
          key: 'manager',
          title: 'Waiting on managers',
          caption: 'HR access unlocks after a manager approves the request.',
          empty: 'Managers have cleared all employee submissions.',
          pattern: 'pattern-card pattern-card--slate',
          actions: 'manager',
          tickets: this.managerQueue,
        },
        {
          key: 'hr_decision',
          title: 'Need HR decision',
          caption: 'Managers approved these tickets. Review policy, then accept.',
          empty: 'No travel requests awaiting HR right now.',
          pattern: 'pattern-card pattern-card--violet',
          actions: 'hr_approval',
          tickets: this.hrApprovalQueue,
        },
        {
          key: 'booking',
          title: 'Ready to book',
          caption: 'You accepted these tickets. Use chat to complete bookings.',
          empty: 'Approve a ticket to unlock AI booking.',
          pattern: 'pattern-card pattern-card--sky',
          actions: 'booking',
          tickets: this.bookingQueue,
        },
        {
          key: 'completed',
          title: 'Booked / Completed',
          caption: 'Reference log for finished itineraries.',
          empty: 'No completed tickets yet.',
          pattern: 'pattern-card pattern-card--emerald',
          actions: 'readonly',
          tickets: this.completedTickets,
        },
      ]
    },
    activeTickets() {
      return this.managerQueue.length + this.hrApprovalQueue.length + this.bookingQueue.length
    },
    awaitingHr() {
      return this.hrApprovalQueue.length
    },
    completed() {
      return this.completedTickets.length
    },
  },
  methods: {
    async fetchTickets() {
      try {
        const { data } = await api.get('/hr-mcp/travel-indents')
        const tickets = Array.isArray(data) ? data : []
        this.tickets = tickets.map((ticket) => ({
          ...ticket,
          status_code: this.normalizeStatus(ticket),
        }))
      } catch (error) {
        console.error('Failed to load HR tickets', error)
      }
    },
    async updateStatus(indentId, status) {
      try {
        const normalizedStatus = this.normalizeStatusValue(status)
        await api.patch(`/hr-mcp/tickets/${indentId}/status`, { status: normalizedStatus })
        await this.fetchTickets()
      } catch (error) {
        console.error('Unable to update HR status', error)
      }
    },
    normalizeStatusValue(value) {
      const normalized = (value ?? '').toString().trim().toLowerCase()
      return normalized || 'pending'
    },
    normalizeStatus(ticket) {
      if (!ticket) return 'pending'
      const source = ticket.status_code ?? ticket.status ?? ticket.is_approved ?? ticket.isApproved ?? ''
      return this.normalizeStatusValue(source)
    },
    statusCode(ticket) {
      return this.normalizeStatus(ticket)
    },
    isWaitingOnManager(ticket) {
      const code = this.statusCode(ticket)
      return MANAGER_PENDING_STATUSES.has(code)
    },
    isAwaitingHrDecision(ticket) {
      const code = this.statusCode(ticket)
      return MANAGER_APPROVED_STATUSES.has(code)
    },
    isReadyForBooking(ticket) {
      const code = this.statusCode(ticket)
      return HR_READY_STATUSES.has(code)
    },
    isCompleted(ticket) {
      const code = this.statusCode(ticket)
      return COMPLETED_STATUSES.has(code)
    },
    statusLabel(ticket) {
      const code = this.statusCode(ticket)
      const labels = {
        pending: 'Pending manager',
        manager_pending: 'Pending manager',
        pending_manager: 'Pending manager',
        submitted: 'Submitted',
        accepted_manager: 'Approved by manager',
        accpeted_manager: 'Approved by manager',
        manager_approved: 'Approved by manager',
        hr_approved: 'Approved by HR',
        completed_hr: 'Booked by HR',
        booked: 'Booked',
      }
      if (labels[code]) return labels[code]
      return code ? code.replace(/_/g, ' ') : 'Pending manager'
    },
    statusClass(ticket) {
      const code = typeof ticket === 'string' ? this.normalizeStatusValue(ticket) : this.statusCode(ticket)
      if (COMPLETED_STATUSES.has(code)) return 'status-pill--success'
      if (code === 'hr_approved' || MANAGER_APPROVED_STATUSES.has(code)) return 'status-pill--info'
      if (MANAGER_PENDING_STATUSES.has(code)) return 'status-pill--warning'
      if (code.includes('reject')) return 'status-pill--danger'
      return 'status-pill--info'
    },
    statusRowClass(ticket) {
      const code = typeof ticket === 'string' ? this.normalizeStatusValue(ticket) : this.statusCode(ticket)
      if (COMPLETED_STATUSES.has(code)) return 'ticket-row--success'
      if (code === 'hr_approved') return 'ticket-row--info'
      if (MANAGER_APPROVED_STATUSES.has(code)) return 'ticket-row--info'
      if (MANAGER_PENDING_STATUSES.has(code)) return 'ticket-row--warning'
      if (code.includes('reject')) return 'ticket-row--danger'
      return 'ticket-row--info'
    },
    canApprove(ticket) {
      return this.isAwaitingHrDecision(ticket)
    },
    canBook(ticket) {
      return this.isReadyForBooking(ticket)
    },
    canChat(ticket) {
      return this.isReadyForBooking(ticket)
    },
    openChat(ticket) {
      if (!this.canChat(ticket)) return
      this.activeTicket = ticket
      this.chatOpen = true
      this.chatMessages = []
      this.chatInput = ''
      this.chatError = ''
      this.sessionId = null
      this.$nextTick(() => {
        this.scrollChatToBottom()
      })
    },
    closeChat() {
      this.chatOpen = false
      this.activeTicket = null
      this.chatMessages = []
      this.chatInput = ''
      this.chatError = ''
      this.sessionId = null
    },
    buildPrefillMessage() {
      if (!this.activeTicket) return ''
      const ticket = this.activeTicket
      return `Please help me book travel for ${ticket.employee_name || ticket.employee_id} from ${ticket.from_city} to ${ticket.to_city} between ${ticket.travel_start_date} and ${ticket.travel_end_date}. Travel type is ${ticket.travel_type}.`
    },
    async sendPrefill() {
      const message = this.buildPrefillMessage()
      if (message) {
        await this.sendChat(message)
      }
    },
    async sendChat(customMessage) {
      if (!this.activeTicket) return
      const message = (customMessage ?? this.chatInput).trim()
      if (!message) return

      this.chatError = ''
      this.chatLoading = true

      const userMessage = { role: 'user', content: message }
      this.chatMessages.push(userMessage)
      if (!customMessage) {
        this.chatInput = ''
      }
      this.scrollChatToBottom()

      try {
        const payload = {
          session_id: this.sessionId,
          indent_id: this.activeTicket.indent_id,
          message,
        }
        const { data } = await api.post('/hr-mcp/chat', payload)
        this.sessionId = data.session_id

        this.chatMessages.push({
          role: 'assistant',
          content: data.response,
          tools: data.tools_used,
        })

        if (data.booking_complete) {
          await this.updateStatus(this.activeTicket.indent_id, 'completed_hr')
          this.chatMessages.push({
            role: 'assistant',
            content: 'Booking completed. Ticket marked as completed_hr.',
          })
        }
      } catch (error) {
        console.error('Chat failed', error)
        this.chatError = error?.response?.data?.detail || 'Unable to reach booking assistant'
      } finally {
        this.chatLoading = false
        this.$nextTick(() => this.scrollChatToBottom())
      }
    },
    scrollChatToBottom() {
      const el = this.$refs.chatScrollRef
      if (el) {
        el.scrollTop = el.scrollHeight
      }
    },
    renderMessage(content) {
      if (!content) return ''
      const html = marked.parse(content, { breaks: true })
      return DOMPurify.sanitize(html)
    },
  },
  mounted() {
    this.fetchTickets()
  },
}
</script>

<style scoped>
.dashboard-panel {
  background: transparent;
  border-radius: 1.5rem;
  padding: 1.75rem;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.hr-section header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 90%;
  margin-left: auto;
  margin-right: auto;
}

.table-wrapper {
  overflow-x: auto;
  border-radius: 1.2rem;
  margin-top: 1.5rem;
  padding: 0.75rem;
}

table {
  width: 100%;
  border-collapse: collapse;
}

.ticket-row th,
.ticket-row td,
th,
td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid var(--slate-100);
}

th {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.muted {
  margin: 0;
  color: var(--slate-500);
  font-size: 0.85rem;
}

.status-pill {
  display: inline-flex;
  padding: 0.35rem 0.8rem;
  border-radius: 999px;
  font-weight: 600;
}

.status-pill--success {
  background: var(--success-100);
  color: var(--success-500);
}

.status-pill--warning {
  background: var(--warning-100);
  color: var(--warning-500);
}

.status-pill--danger {
  background: var(--danger-100);
  color: var(--danger-500);
}

.status-pill--info {
  background: var(--primary-50);
  color: var(--primary-600);
}

.ticket-row {
  transition: background 0.2s;
}

.ticket-row--warning {
  background: rgba(234, 179, 8, 0.08);
}

.ticket-row--success {
  background: rgba(16, 185, 129, 0.08);
}

.ticket-row--danger {
  background: rgba(239, 68, 68, 0.08);
}

.ticket-row--info {
  background: rgba(59, 130, 246, 0.05);
}

.action-stack {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.action-hint {
  color: var(--slate-500);
  font-size: 0.9rem;
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

.empty-state {
  padding: 2rem;
  text-align: center;
  color: var(--slate-500);
  border: 1px dashed var(--slate-200);
  border-radius: 1.2rem;
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

.chat-tools {
  margin: 0.5rem 0 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  list-style: none;
}

.chat-tools li {
  background: rgba(15, 23, 42, 0.06);
  border-radius: 999px;
  padding: 0.2rem 0.7rem;
  font-size: 0.8rem;
  color: var(--slate-600);
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
