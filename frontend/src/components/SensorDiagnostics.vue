<template>
  <div class="flex-col gap-lg">
    <!-- Diagnostics Banner -->
    <div :class="['glass-card', 'status-banner', report.status]">
      <div class="banner-glow-effect"></div>
      <div class="flex-row items-center gap-md" style="display: flex; align-items: center; gap: 16px; position: relative; z-index: 2;">
        <div class="status-indicator-ring">
          <span class="status-icon">{{ statusIcon }}</span>
        </div>
        <div class="flex-col gap-xs" style="flex-grow: 1;">
          <h3 class="status-title">{{ statusTitle }}</h3>
          <p class="status-message">{{ report.message }}</p>
        </div>
        <button class="btn-refresh" @click="runDiagnostics" :disabled="loading">
          <span :class="{ 'spin-effect': loading }">🔄</span>
          {{ loading ? 'Running diagnostics...' : 'Run Diagnostics' }}
        </button>
      </div>
    </div>

    <!-- Main Diagnostic Details Grid -->
    <div class="grid-2">
      <!-- Diagnostic Results and Info -->
      <div class="glass-card flex-col gap-lg">
        <div style="border-bottom: 1px solid var(--border-light); padding-bottom: 12px;">
          <h4 style="font-size: 1.1rem; font-weight: 600; color: #fff;">Hardware Summary</h4>
          <p style="font-size: 0.85rem; color: var(--text-sub); margin-top: 4px;">Connection link and hardware interface diagnostics</p>
        </div>

        <div class="diag-summary-list flex-col gap-md">
          <!-- Sensor Mode Status -->
          <div class="diag-item">
            <span class="diag-label">Sensor Library Driver</span>
            <span :class="['diag-value-badge', report.details.is_mock ? 'warning' : 'success']">
              {{ report.details.is_mock ? 'Mock / Simulation Mode' : 'Physical AS3935' }}
            </span>
          </div>

          <!-- I2C Bus Connection -->
          <div class="diag-item">
            <span class="diag-label">I2C Communication Link</span>
            <span :class="['diag-value-badge', report.details.i2c_connected ? 'success' : 'error']">
              {{ report.details.i2c_connected ? 'Active / Connected' : 'Disconnected / Failed' }}
            </span>
          </div>

          <!-- Error Logs if failed -->
          <div v-if="report.details.error_message" class="error-log-card">
            <h5>Hardware Error Message</h5>
            <code>{{ report.details.error_message }}</code>
          </div>
        </div>

        <!-- Developer Mode Control: Simulate I2C Failure -->
        <div v-if="report.details.is_mock" class="developer-panel">
          <div class="flex-row" style="display: flex; align-items: center; justify-content: space-between;">
            <div>
              <h5 style="font-weight: 600; color: var(--color-gold);">Developer Mode: Simulate I2C Failure</h5>
              <p style="font-size: 0.8rem; color: var(--text-sub); margin-top: 2px;">Force mock sensor reads to throw exceptions to test failure behaviors.</p>
            </div>
            <input 
              type="checkbox" 
              id="simulate-i2c-error" 
              v-model="simulatedError"
              @change="toggleSimulatedError"
              class="toggle-checkbox"
            />
          </div>
        </div>
      </div>

      <!-- Actionable Troubleshooting recommendations -->
      <div class="glass-card flex-col gap-lg">
        <div style="border-bottom: 1px solid var(--border-light); padding-bottom: 12px;">
          <h4 style="font-size: 1.1rem; font-weight: 600; color: #fff;">Troubleshooting & Advice</h4>
          <p style="font-size: 0.85rem; color: var(--text-sub); margin-top: 4px;">Steps to restore or improve sensor tracking accuracy</p>
        </div>

        <ul class="recommendations-list flex-col gap-sm">
          <li v-for="(rec, index) in report.recommendations" :key="index" class="rec-item">
            <span class="rec-bullet">💡</span>
            <span class="rec-text">{{ rec }}</span>
          </li>
          <li v-if="report.recommendations.length === 0" class="rec-item text-sub">
            <span class="rec-bullet">✓</span>
            <span class="rec-text">No actions required. Your sensor configuration is fully healthy.</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- Side-by-side Calibration Register Auditor -->
    <div class="glass-card flex-col gap-md" v-if="report.details.i2c_connected">
      <div style="border-bottom: 1px solid var(--border-light); padding-bottom: 12px; margin-bottom: 8px;">
        <h4 style="font-size: 1.1rem; font-weight: 600; color: #fff;">Register Calibration Audit</h4>
        <p style="font-size: 0.85rem; color: var(--text-sub); margin-top: 4px;">Compares database-stored settings against values physically read from sensor registers</p>
      </div>

      <div style="overflow-x: auto;">
        <table class="audit-table">
          <thead>
            <tr>
              <th>Setting Parameter</th>
              <th>Config Value</th>
              <th>Chip Register Value</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <!-- Capacitance -->
            <tr>
              <td>Antenna Tuning Capacitance</td>
              <td>{{ report.details.capacitance_config }} pF</td>
              <td>{{ report.details.capacitance_read }} pF</td>
              <td>
                <span :class="['audit-badge', report.details.capacitance_match ? 'match' : 'mismatch']">
                  {{ report.details.capacitance_match ? '✓ Match' : '✗ Mismatch' }}
                </span>
              </td>
            </tr>

            <!-- Location -->
            <tr>
              <td>Gain Environment Mode</td>
              <td>{{ report.details.location_config }}</td>
              <td>{{ report.details.location_read }}</td>
              <td>
                <span :class="['audit-badge', report.details.location_match ? 'match' : 'mismatch']">
                  {{ report.details.location_match ? '✓ Match' : '✗ Mismatch' }}
                </span>
              </td>
            </tr>

            <!-- Disturbers -->
            <tr>
              <td>Disturber Filtering</td>
              <td>{{ report.details.disturber_config }}</td>
              <td>{{ report.details.disturber_read }}</td>
              <td>
                <span :class="['audit-badge', report.details.disturber_match ? 'match' : 'mismatch']">
                  {{ report.details.disturber_match ? '✓ Match' : '✗ Mismatch' }}
                </span>
              </td>
            </tr>

            <!-- Noise Floor -->
            <tr>
              <td>Noise Floor Level</td>
              <td>Level {{ report.details.noise_floor_config }}</td>
              <td>Level {{ report.details.noise_floor_read }}</td>
              <td>
                <span :class="['audit-badge', report.details.noise_floor_match ? 'match' : 'mismatch']">
                  {{ report.details.noise_floor_match ? '✓ Match' : '✗ Mismatch' }}
                </span>
              </td>
            </tr>

            <!-- Watchdog -->
            <tr>
              <td>Watchdog Threshold</td>
              <td>Level {{ report.details.watchdog_config }}</td>
              <td>Level {{ report.details.watchdog_read }}</td>
              <td>
                <span :class="['audit-badge', report.details.watchdog_match ? 'match' : 'mismatch']">
                  {{ report.details.watchdog_match ? '✓ Match' : '✗ Mismatch' }}
                </span>
              </td>
            </tr>

            <!-- Spike Rejection -->
            <tr>
              <td>Spike Rejection Level</td>
              <td>Level {{ report.details.spike_rejection_config }}</td>
              <td>Level {{ report.details.spike_rejection_read }}</td>
              <td>
                <span :class="['audit-badge', report.details.spike_rejection_match ? 'match' : 'mismatch']">
                  {{ report.details.spike_rejection_match ? '✓ Match' : '✗ Mismatch' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted } from 'vue';
import { offlineSync } from '../services/offlineSync';

interface DiagnosticDetails {
  is_mock: boolean;
  i2c_connected: boolean;
  error_message: string | null;
  
  capacitance_read: number | null;
  capacitance_config: number;
  capacitance_match: boolean;
  
  location_read: string | null;
  location_config: number;
  location_match: boolean;
  
  disturber_read: string | null;
  disturber_config: number;
  disturber_match: boolean;
  
  noise_floor_read: number | null;
  noise_floor_config: number;
  noise_floor_match: boolean;
  
  watchdog_read: number | null;
  watchdog_config: number;
  watchdog_match: boolean;
  
  spike_rejection_read: number | null;
  spike_rejection_config: number;
  spike_rejection_match: boolean;
}

interface DiagnosticReport {
  status: 'healthy' | 'warning' | 'error';
  message: string;
  timestamp: string;
  details: DiagnosticDetails;
  recommendations: string[];
}

export default defineComponent({
  name: 'SensorDiagnostics',
  setup() {
    const loading = ref(false);
    const simulatedError = ref(false);
    
    const report = ref<DiagnosticReport>({
      status: 'healthy',
      message: 'Running diagnostics...',
      timestamp: new Date().toLocaleTimeString(),
      details: {
        is_mock: true,
        i2c_connected: true,
        error_message: null,
        capacitance_read: 96,
        capacitance_config: 96,
        capacitance_match: true,
        location_read: 'Indoor',
        location_config: 0,
        location_match: true,
        disturber_read: 'Enabled',
        disturber_config: 1,
        disturber_match: true,
        noise_floor_read: 2,
        noise_floor_config: 2,
        noise_floor_match: true,
        watchdog_read: 2,
        watchdog_config: 2,
        watchdog_match: true,
        spike_rejection_read: 2,
        spike_rejection_config: 2,
        spike_rejection_match: true
      },
      recommendations: []
    });

    const runDiagnostics = async () => {
      loading.value = true;
      try {
        const res = await fetch('/api/sensor/diagnostics');
        if (res.ok) {
          const data = await res.json();
          report.value = data;
          offlineSync.saveCache('registers', data);
          if (report.value.details.is_mock) {
            simulatedError.value = !report.value.details.i2c_connected && !!report.value.details.error_message;
          }
        } else {
          const cached = offlineSync.getCache<DiagnosticReport>('registers');
          if (cached) {
            report.value = cached;
            report.value.message = 'Showing cached diagnostic report (Offline Mode)';
          }
        }
      } catch (err) {
        console.warn('Offline network error running diagnostics, using cache:', err);
        const cached = offlineSync.getCache<DiagnosticReport>('registers');
        if (cached) {
          report.value = cached;
          report.value.message = 'Showing cached diagnostic report (Offline Mode)';
        } else {
          report.value.status = 'warning';
          report.value.message = 'Offline mode: No cached diagnostic data available yet.';
        }
      } finally {
        loading.value = false;
      }
    };

    const toggleSimulatedError = async () => {
      try {
        await fetch('/api/sensor/diagnostics/toggle-mock-error', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ enable_error: simulatedError.value })
        });
        // Rerun diagnostics to capture new error state
        runDiagnostics();
      } catch (err) {
        console.error('Failed to toggle simulated error:', err);
      }
    };

    const statusIcon = computed(() => {
      switch (report.value.status) {
        case 'healthy': return '🟢';
        case 'warning': return '🟡';
        case 'error': return '🔴';
        default: return '⚪';
      }
    });

    const statusTitle = computed(() => {
      switch (report.value.status) {
        case 'healthy': return 'Sensor Healthy';
        case 'warning': return 'Sensor Warning';
        case 'error': return 'Hardware Alert';
        default: return 'Sensor Check';
      }
    });

    onMounted(runDiagnostics);

    return {
      loading,
      simulatedError,
      report,
      statusIcon,
      statusTitle,
      runDiagnostics,
      toggleSimulatedError
    };
  }
});
</script>

<style scoped>
.status-banner {
  padding: 24px;
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  border: 1px solid var(--border-light);
}

.status-banner.healthy {
  background: rgba(16, 185, 129, 0.08);
  border-color: rgba(16, 185, 129, 0.3);
}

.status-banner.warning {
  background: rgba(245, 158, 11, 0.08);
  border-color: rgba(245, 158, 11, 0.3);
}

.status-banner.error {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.3);
}

.banner-glow-effect {
  position: absolute;
  top: -50px;
  left: -50px;
  width: 150px;
  height: 150px;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.15;
  pointer-events: none;
}

.healthy .banner-glow-effect {
  background: var(--color-green);
}

.warning .banner-glow-effect {
  background: var(--color-gold);
}

.error .banner-glow-effect {
  background: var(--color-red);
}

.status-indicator-ring {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-light);
  font-size: 1.5rem;
}

.status-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.01em;
}

.status-message {
  font-size: 0.95rem;
  color: var(--text-sub);
  margin-top: 4px;
}

.btn-refresh {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.btn-refresh:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spin-effect {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.diag-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-light);
  border-radius: 8px;
}

.diag-label {
  font-size: 0.9rem;
  color: var(--text-sub);
}

.diag-value-badge {
  font-size: 0.85rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 6px;
}

.diag-value-badge.success {
  background: rgba(16, 185, 129, 0.1);
  color: var(--color-green);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.diag-value-badge.warning {
  background: rgba(245, 158, 11, 0.1);
  color: var(--color-gold);
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.diag-value-badge.error {
  background: rgba(239, 68, 68, 0.1);
  color: var(--color-red);
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.error-log-card {
  padding: 14px;
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.15);
  border-radius: 8px;
  margin-top: 8px;
}

.error-log-card h5 {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-red);
  margin-bottom: 6px;
}

.error-log-card code {
  display: block;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: #fca5a5;
  word-break: break-all;
  white-space: pre-wrap;
}

.developer-panel {
  padding: 14px;
  background: rgba(245, 158, 11, 0.03);
  border: 1px dashed rgba(245, 158, 11, 0.2);
  border-radius: 8px;
  margin-top: 12px;
}

.toggle-checkbox {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  accent-color: var(--color-gold);
  cursor: pointer;
}

.recommendations-list {
  padding-left: 0;
  list-style: none;
}

.rec-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  border: 1px solid var(--border-light);
  line-height: 1.45;
}

.rec-bullet {
  font-size: 1.1rem;
}

.rec-text {
  font-size: 0.9rem;
  color: var(--text-main);
}

.rec-item.text-sub .rec-text {
  color: var(--text-sub);
}

/* Audit table styling */
.audit-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.audit-table th {
  padding: 12px 16px;
  font-size: 0.85rem;
  color: var(--text-sub);
  font-weight: 500;
  border-bottom: 1px solid var(--border-light);
}

.audit-table td {
  padding: 14px 16px;
  font-size: 0.9rem;
  border-bottom: 1px solid var(--border-light);
}

.audit-table tr:last-child td {
  border-bottom: none;
}

.audit-badge {
  font-size: 0.8rem;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
}

.audit-badge.match {
  color: var(--color-green);
  background: rgba(16, 185, 129, 0.08);
}

.audit-badge.mismatch {
  color: var(--color-red);
  background: rgba(239, 68, 68, 0.08);
}
</style>
