<template>
  <div class="dashboard-panel pattern-card pattern-card--amber">
    <div class="metrics-grid">
      <MetricCard title="Pending approvals" :value="pending.length" caption="Need your decision" variant="warning" />
      <MetricCard title="Approved" :value="approved.length" caption="Last 30 days" variant="success" />
      <MetricCard title="Awaiting booking" :value="hrDeskQueue.length" caption="HR approved" variant="info" />
      <MetricCard title="Rejected" :value="rejectedByYou.length" caption="Need rework" variant="danger" />
      <MetricCard title="Total requests" :value="allIndents.length" caption="Team travel" />
    </div>

  <section class="manager-section pattern-card pattern-card--emerald">
      <header>
        <div>
          <h2>Pending approvals</h2>
          <p>Review employee justification and approve or reject.</p>
        </div>
        <button class="ghost-btn" @click="fetchAll">Refresh</button>
      </header>

      <TravelList :items="pending" :loading="loading">
        <template #actions="{ item }">
          <div class="approval-actions">
            <button class="ghost-btn" @click="updateStatus(item.indent_id, 'reject')">Reject</button>
            <button class="primary-btn" @click="updateStatus(item.indent_id, 'approve')">Approve</button>
          </div>
        </template>
      </TravelList>
    </section>

  <section class="manager-section pattern-card pattern-card--lavender">
      <h2>Recently approved</h2>
      <TravelList :items="approved.slice(0, 5)" :loading="loading">
        <template #empty>
          <p>No approvals yet. Actions appear here after you approve a request.</p>
        </template>
      </TravelList>
    </section>

    <section class="manager-section pattern-card pattern-card--sky">
      <header>
        <div>
          <h2>Awaiting booking</h2>
          <p>HR has approved these tickets but bookings are still pending.</p>
        </div>
        <button class="ghost-btn" @click="fetchAll">Refresh</button>
      </header>
      <TravelList :items="hrDeskQueue" :loading="loading">
        <template #empty>
          <p>No HR-approved items waiting for booking.</p>
        </template>
      </TravelList>
    </section>

    <section class="manager-section pattern-card pattern-card--rose">
      <h2>Rejected by you</h2>
      <TravelList :items="rejectedByYou" :loading="loading">
        <template #empty>
          <p>Rejected indents will show up here for traceability.</p>
        </template>
      </TravelList>
    </section>
  </div>
</template>

<script>
import MetricCard from '../../components/MetricCard.vue'
import TravelList from '../../components/TravelList.vue'
import api from '../../services/api'

export default {
  name: 'ManagerDashboard',
  components: {
    MetricCard,
    TravelList,
  },
  data() {
    return {
      pending: [],
      approved: [],
      allIndents: [],
      loading: false,
    }
  },
  computed: {
    hrDeskQueue() {
      return this.allIndents.filter((item) => {
        const workflow = this.workflowStatus(item)
        return workflow === 'hr_approved'
      })
    },
    rejectedByYou() {
      return this.allIndents.filter((item) => this.statusCode(item) === 'rejected_manager')
    },
  },
  methods: {
    statusCode(item) {
      return String(item?.status_code || item?.is_approved || item?.status || '').trim().toLowerCase()
    },
    workflowStatus(item) {
      return this.statusCode(item)
    },
    async fetchAll() {
      this.loading = true
      try {
        const [pendingRes, approvedRes, allRes] = await Promise.all([
          api.get('/manager/pending'),
          api.get('/manager/approved'),
          api.get('/manager/indents'),
        ])
        this.pending = pendingRes.data || []
        this.approved = approvedRes.data || []
        this.allIndents = allRes.data || []
      } catch (error) {
        console.error('Failed to load manager data', error)
      } finally {
        this.loading = false
      }
    },
    async updateStatus(indentId, action) {
      try {
        if (action === 'approve') {
          await api.post(`/manager/approve/${indentId}`)
        } else {
          await api.post(`/manager/reject/${indentId}`)
        }
        await this.fetchAll()
      } catch (error) {
        console.error('Unable to update status', error)
      }
    },
  },
  mounted() {
    this.fetchAll()
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

.manager-section {
  margin-top: 2rem;
  padding: 1.5rem;
  border-radius: 1.4rem;
}

.manager-section header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.manager-section h2 {
  margin-bottom: 0.25rem;
}

.ghost-btn {
  border: 1px solid var(--slate-200);
  border-radius: 0.8rem;
  padding: 0.6rem 1rem;
  background: white;
  cursor: pointer;
  font-weight: 600;
}

.approval-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.pattern-card--sky {
  background: linear-gradient(135deg, #ecfeff 0%, #e0f2fe 100%);
}

.pattern-card--rose {
  background: linear-gradient(135deg, #ffe4e6 0%, #ffe9f0 100%);
}
</style>
