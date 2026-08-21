<template>
  <div class="grid-2">
    <!-- Left Panel: Sensor and Display Settings -->
    <div class="glass-card flex-col gap-lg">
      <div style="border-bottom: 1px solid var(--border-light); padding-bottom: 12px;">
        <h3 style="font-size: 1.2rem; font-weight: 600;">Calibration Panel</h3>
        <p style="font-size: 0.85rem; color: var(--text-sub); margin-top: 4px;">Configure the AS3935 sensor registers and the LCD display active hours</p>
      </div>

      <form @submit.prevent="saveSettings" class="flex-col gap-md">
        <!-- Hardware Info Badges -->
        <div style="display: flex; gap: 12px; flex-wrap: wrap;">
          <span class="hw-badge" :class="{ mock: config.is_mock_as3935 }">
            ⚡ AS3935: {{ config.is_mock_as3935 ? 'MOCK / SIMULATED' : 'PHYSICAL HARDWARE' }}
          </span>
          <span class="hw-badge" :class="{ mock: config.is_mock_lcd }">
            🖥️ Waveshare LCD: {{ config.is_mock_lcd ? 'MOCK / SIMULATED' : 'PHYSICAL HARDWARE' }}
          </span>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
          <!-- Capacitance Select -->
          <div class="form-group">
            <label class="form-label">Antenna Capacitance</label>
            <select v-model="config.capacitance" class="select-field">
              <option v-for="c in capacitanceOptions" :key="c" :value="c">{{ c }} pF</option>
            </select>
          </div>

          <!-- Location Select -->
          <div class="form-group">
            <label class="form-label">Location Environment</label>
            <select v-model="config.location" class="select-field">
              <option :value="0">Indoor Mode</option>
              <option :value="1">Outdoor Mode</option>
            </select>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
          <!-- Disturber Select -->
          <div class="form-group">
            <label class="form-label">Disturber Detection</label>
            <select v-model="config.disturber" class="select-field">
              <option :value="1">Enabled</option>
              <option :value="0">Disabled (Masked)</option>
            </select>
          </div>

          <!-- Noise Floor Level -->
          <div class="form-group">
            <label class="form-label">Noise Floor (0-7)</label>
            <select v-model="config.noise_floor" class="select-field">
              <option v-for="n in 8" :key="n-1" :value="n-1">Level {{ n-1 }}</option>
            </select>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
          <!-- Watchdog Threshold -->
          <div class="form-group">
            <label class="form-label">Watchdog Threshold (0-7)</label>
            <select v-model="config.watchdog" class="select-field">
              <option v-for="w in 8" :key="w-1" :value="w-1">Level {{ w-1 }}</option>
            </select>
          </div>

          <!-- Spike Rejection -->
          <div class="form-group">
            <label class="form-label">Spike Rejection (0-7)</label>
            <select v-model="config.spike_rejection" class="select-field">
              <option v-for="s in 8" :key="s-1" :value="s-1">Level {{ s-1 }}</option>
            </select>
          </div>
        </div>

        <div style="border-top: 1px solid var(--border-light); padding-top: 16px;">
          <h4 style="font-size: 0.95rem; font-weight: 600; margin-bottom: 12px; color: var(--color-cyan);">Waveshare LCD Active Hours</h4>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
            <div class="form-group">
              <label class="form-label">Active Start Hour</label>
              <select v-model="config.display_active_start" class="select-field">
                <option v-for="h in 24" :key="h-1" :value="h-1">{{ String(h-1).padStart(2, '0') }}:00</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Active End Hour</label>
              <select v-model="config.display_active_end" class="select-field">
                <option v-for="h in 24" :key="h-1" :value="h-1">{{ String(h-1).padStart(2, '0') }}:00</option>
              </select>
            </div>
          </div>
        </div>

        <div style="display: flex; gap: 12px; margin-top: 8px; align-items: center; flex-wrap: wrap;">
          <button type="submit" class="btn-primary" :disabled="saving">
            {{ saving ? 'Saving Changes...' : 'Save Configuration' }}
          </button>
          <span v-if="saveSuccess && !offlineNotice" class="status-msg success">✓ Calibration updated successfully</span>
          <span v-if="saveSuccess && offlineNotice" class="status-msg warning" style="color: var(--color-gold);">
            ⚡ Offline Mode: Changes saved locally & will sync when reconnected
          </span>
        </div>
      </form>
    </div>

    <!-- Right Panel: Telegram Bot Notification Settings -->
    <div class="glass-card flex-col gap-lg">
      <div style="border-bottom: 1px solid var(--border-light); padding-bottom: 12px;">
        <h3 style="font-size: 1.2rem; font-weight: 600;">Telegram Bot Notifier</h3>
        <p style="font-size: 0.85rem; color: var(--text-sub); margin-top: 4px;">Get instant alerts on your phone whenever lightning is detected</p>
      </div>

      <div class="flex-col gap-md">
        <!-- Enable Toggle -->
        <div class="flex-row" style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
          <input 
            type="checkbox" 
            id="tg-enable" 
            v-model="config.telegram_enabled"
            class="toggle-checkbox"
          />
          <label for="tg-enable" style="font-weight: 500; cursor: pointer; user-select: none;">
            Enable Telegram Notifications
          </label>
        </div>

        <!-- Bot Token -->
        <div class="form-group">
          <label class="form-label">Telegram Bot Token</label>
          <input 
            type="password" 
            v-model="config.telegram_token" 
            class="input-field" 
            placeholder="e.g. 123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
            :disabled="!config.telegram_enabled"
          />
        </div>

        <!-- Chat ID -->
        <div class="form-group">
          <label class="form-label">Telegram Chat ID (User or Group ID)</label>
          <input 
            type="text" 
            v-model="config.telegram_chat_id" 
            class="input-field" 
            placeholder="e.g. -100123456789 or 987654321"
            :disabled="!config.telegram_enabled"
          />
        </div>

        <!-- Test Bot Notification -->
        <div style="border-top: 1px solid var(--border-light); padding-top: 16px; display: flex; flex-direction: column; gap: 12px;">
          <div>
            <button 
              type="button" 
              class="btn-secondary" 
              @click="testTelegram"
              :disabled="!config.telegram_enabled || testing || !config.telegram_token || !config.telegram_chat_id"
              style="width: fit-content;"
            >
              {{ testing ? 'Sending Test...' : 'Send Test Notification' }}
            </button>
          </div>
          <span v-if="testResult" class="status-msg" :class="testResult.success ? 'success' : 'error'">
            {{ testResult.message }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import { offlineSync } from '../services/offlineSync';

interface SensorConfig {
  capacitance: number;
  location: number;
  disturber: number;
  noise_floor: number;
  watchdog: number;
  spike_rejection: number;
  display_active_start: number;
  display_active_end: number;
  telegram_enabled: boolean;
  telegram_token: string;
  telegram_chat_id: string;
  is_mock_as3935: boolean;
  is_mock_lcd: boolean;
}

export default defineComponent({
  name: 'SensorConfig',
  setup() {
    const config = ref<SensorConfig>({
      capacitance: 96,
      location: 0,
      disturber: 1,
      noise_floor: 2,
      watchdog: 2,
      spike_rejection: 2,
      display_active_start: 8,
      display_active_end: 20,
      telegram_enabled: false,
      telegram_token: '',
      telegram_chat_id: '',
      is_mock_as3935: true,
      is_mock_lcd: true
    });

    const saving = ref(false);
    const saveSuccess = ref(false);
    const offlineNotice = ref(false);
    const testing = ref(false);
    const testResult = ref<{ success: boolean; message: string } | null>(null);

    // Multiples of 8 from 8 to 120
    const capacitanceOptions = [8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 104, 112, 120];

    const fetchConfig = async () => {
      try {
        const res = await fetch('/api/sensor/status');
        if (res.ok) {
          const data = await res.json();
          config.value = data;
          offlineSync.saveCache('config', data);
        } else {
          const cached = offlineSync.getCache<SensorConfig>('config');
          if (cached) config.value = cached;
        }
      } catch (err) {
        console.warn('Network offline while fetching config, using cache:', err);
        const cached = offlineSync.getCache<SensorConfig>('config');
        if (cached) config.value = cached;
      }
    };

    const saveSettings = async () => {
      saving.value = true;
      saveSuccess.value = false;
      offlineNotice.value = false;
      try {
        const res = await fetch('/api/sensor/config', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(config.value)
        });
        
        const data = await res.json();
        if (res.ok && !data.offlineQueued) {
          config.value = data;
          offlineSync.saveCache('config', data);
          saveSuccess.value = true;
        } else {
          // Response indicated offline interception or partial server response
          offlineSync.enqueueAction('Update Calibration Settings', '/api/sensor/config', config.value);
          offlineSync.saveCache('config', config.value);
          saveSuccess.value = true;
          offlineNotice.value = true;
        }
      } catch (err) {
        console.warn('Offline network error saving settings, enqueueing:', err);
        offlineSync.enqueueAction('Update Calibration Settings', '/api/sensor/config', config.value);
        offlineSync.saveCache('config', config.value);
        saveSuccess.value = true;
        offlineNotice.value = true;
      } finally {
        saving.value = false;
        setTimeout(() => {
          saveSuccess.value = false;
        }, 5000);
      }
    };

    const testTelegram = async () => {
      testing.value = true;
      testResult.value = null;
      try {
        const res = await fetch('/api/telegram/test', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            token: config.value.telegram_token,
            chat_id: config.value.telegram_chat_id
          })
        });
        const data = await res.json();
        if (res.ok) {
          testResult.value = { success: true, message: '✓ Test message sent successfully!' };
        } else {
          testResult.value = { success: false, message: `✗ Error: ${data.detail || 'Failed'}` };
        }
      } catch (err) {
        testResult.value = { success: false, message: '✗ Connection error testing telegram.' };
        console.error('Failed to test telegram webhook:', err);
      } finally {
        testing.value = false;
      }
    };

    onMounted(fetchConfig);

    return {
      config,
      capacitanceOptions,
      saving,
      saveSuccess,
      offlineNotice,
      testing,
      testResult,
      saveSettings,
      testTelegram
    };
  }
});
</script>

<style scoped>
.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 0.85rem;
  color: var(--text-sub);
  font-weight: 500;
}

.hw-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  background: rgba(16, 185, 129, 0.1);
  color: var(--color-green);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.hw-badge.mock {
  background: rgba(245, 158, 11, 0.1);
  color: var(--color-gold);
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.status-msg {
  font-size: 0.85rem;
  align-self: center;
  font-weight: 500;
}

.status-msg.success {
  color: var(--color-green);
}

.status-msg.error {
  color: var(--color-red);
}

/* Custom Toggle Checkbox */
.toggle-checkbox {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  accent-color: var(--color-cyan);
  cursor: pointer;
}
</style>
