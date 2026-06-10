<template>
  <div class="glass-card flex-col gap-md" style="width: 100%;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
      <h3 style="font-size: 1.1rem; font-weight: 600;">Detection History</h3>
      <span style="font-size: 0.85rem; color: var(--text-sub);">Showing up to 30 recent strikes</span>
    </div>

    <div class="table-container">
      <table class="history-table">
        <thead>
          <tr>
            <th>Date & Time</th>
            <th>Distance</th>
            <th>Intensity</th>
            <th>Danger Level</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="strikes.length === 0">
            <td colspan="4" style="text-align: center; color: var(--text-muted); padding: 40px;">
              No lightning strikes detected yet. Scanning the atmosphere...
            </td>
          </tr>
          <tr v-for="strike in strikes" :key="strike.id" class="table-row">
            <td style="font-family: var(--font-mono); font-size: 0.9rem;">
              {{ formatDateTime(strike.timestamp) }}
            </td>
            <td style="font-weight: 600;">
              {{ strike.distance }} km
            </td>
            <td style="font-family: var(--font-mono); font-size: 0.9rem; color: var(--text-sub);">
              {{ strike.intensity }}
            </td>
            <td>
              <span class="danger-badge" :class="getDangerClass(strike.distance)">
                {{ getDangerText(strike.distance) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';

interface Strike {
  id: number;
  timestamp: string;
  distance: number;
  intensity: number;
}

export default defineComponent({
  name: 'StrikeHistory',
  props: {
    strikes: {
      type: Array as PropType<Strike[]>,
      required: true
    }
  },
  setup() {
    const formatDateTime = (isoString: string) => {
      const date = new Date(isoString);
      const yyyy = date.getFullYear();
      const mm = String(date.getMonth() + 1).padStart(2, '0');
      const dd = String(date.getDate()).padStart(2, '0');
      const hh = String(date.getHours()).padStart(2, '0');
      const min = String(date.getMinutes()).padStart(2, '0');
      const ss = String(date.getSeconds()).padStart(2, '0');
      
      return `${yyyy}-${mm}-${dd} ${hh}:${min}:${ss}`;
    };

    const getDangerClass = (distance: number) => {
      if (distance < 10) return 'severe';
      if (distance < 25) return 'moderate';
      return 'low';
    };

    const getDangerText = (distance: number) => {
      if (distance < 10) return '🔴 Severe (<10km)';
      if (distance < 25) return '🟡 Moderate (<25km)';
      return '🟢 Low (<40km)';
    };

    return {
      formatDateTime,
      getDangerClass,
      getDangerText
    };
  }
});
</script>

<style scoped>
.table-container {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid var(--border-light);
  background: rgba(0, 0, 0, 0.2);
}

.history-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.history-table th {
  background: rgba(255, 255, 255, 0.02);
  color: var(--text-sub);
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 12px 18px;
  border-bottom: 1px solid var(--border-light);
}

.history-table td {
  padding: 14px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}

.table-row {
  transition: background-color 0.2s;
}

.table-row:hover {
  background-color: rgba(255, 255, 255, 0.015);
}

.danger-badge {
  display: inline-block;
  padding: 4px 10px;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 20px;
}

.danger-badge.severe {
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.25);
}

.danger-badge.moderate {
  background: rgba(245, 158, 11, 0.1);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.25);
}

.danger-badge.low {
  background: rgba(16, 185, 129, 0.1);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.25);
}
</style>
