<template>
  <div class="app-container">
    <!-- Sidebar Navigation -->
    <aside class="sidebar">
      <div class="flex-col gap-sm" style="margin-bottom: 40px;">
        <h2 style="display: flex; align-items: center; gap: 8px; font-weight: 700;">
          <span style="color: var(--color-cyan);">⚡</span> RPi Radar
        </h2>
        <p style="font-size: 0.8em; color: var(--text-sub);">LIGHTNING DETECTOR 3B</p>
      </div>

      <nav class="flex-col gap-sm" style="flex-grow: 1;">
        <button 
          class="nav-btn" 
          :class="{ active: currentTab === 'dashboard' }"
          @click="currentTab = 'dashboard'"
        >
          📊 Dashboard
        </button>
        <button 
          class="nav-btn" 
          :class="{ active: currentTab === 'settings' }"
          @click="currentTab = 'settings'"
        >
          ⚙️ Calibration
        </button>
      </nav>

      <div class="flex-col gap-sm" style="border-top: 1px solid var(--border-light); padding-top: 20px;">
        <div style="display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: var(--text-sub);">
          <span 
            style="width: 8px; height: 8px; border-radius: 50%;" 
            :style="{ backgroundColor: wsConnected ? 'var(--color-green)' : 'var(--color-red)' }"
          ></span>
          {{ wsConnected ? 'Live Connection Connected' : 'Connecting to Server...' }}
        </div>
      </div>
    </aside>

    <!-- Main Content Area -->
    <main class="main-content">
      <!-- Toast Notification Alert Overlay -->
      <div class="toast-container" v-if="toast">
        <div class="toast" :class="toast.type">
          <div class="toast-icon">{{ toast.icon }}</div>
          <div class="toast-content">
            <h4>{{ toast.title }}</h4>
            <p>{{ toast.message }}</p>
          </div>
          <button class="toast-close" @click="toast = null">×</button>
        </div>
      </div>

      <!-- Header -->
      <header style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <h1 class="title-glowing" style="font-size: 2rem; margin-bottom: 4px;">
            {{ currentTab === 'dashboard' ? 'Tracker Dashboard' : 'Calibration Console' }}
          </h1>
          <p style="color: var(--text-sub); font-size: 0.95rem;">
            {{ currentTab === 'dashboard' ? 'Real-time observation within a 40km range' : 'AS3935 sensor and display configurations' }}
          </p>
        </div>
        <div style="font-size: 0.9rem; text-align: right; color: var(--text-sub);">
          <div>System local time</div>
          <div style="font-family: var(--font-mono); font-weight: 500; color: #fff; margin-top: 4px;">
            {{ timeStr }}
          </div>
        </div>
      </header>

      <!-- Active Tab View Rendering -->
      <div v-if="currentTab === 'dashboard'" class="flex-col gap-lg">
        <div class="grid-3" style="grid-template-columns: 2fr 1fr 1fr; align-items: stretch;">
          <LightningRadar :strikes="recentStrikes" />
          <StatsCard :stats="stats" />
          <StrikeSimulator @simulated="fetchData" />
        </div>
        <StrikeHistory :strikes="recentStrikes" />
      </div>

      <div v-else-if="currentTab === 'settings'">
        <SensorConfig />
      </div>
    </main>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onUnmounted } from 'vue';
import LightningRadar from './components/LightningRadar.vue';
import StatsCard from './components/StatsCard.vue';
import StrikeHistory from './components/StrikeHistory.vue';
import SensorConfig from './components/SensorConfig.vue';
import StrikeSimulator from './components/StrikeSimulator.vue';

interface Strike {
  id: number;
  timestamp: string;
  distance: number;
  intensity: number;
}

interface Stats {
  amount_24h: number;
  amount_7d: number;
  avg_distance: number;
  avg_intensity: number;
  closest_distance: number | null;
}

interface Toast {
  title: string;
  message: string;
  type: 'strike-toast' | 'warning-toast';
  icon: string;
}

export default defineComponent({
  name: 'App',
  components: {
    LightningRadar,
    StatsCard,
    StrikeHistory,
    SensorConfig,
    StrikeSimulator
  },
  setup() {
    const currentTab = ref('dashboard');
    const recentStrikes = ref<Strike[]>([]);
    const stats = ref<Stats>({
      amount_24h: 0,
      amount_7d: 0,
      avg_distance: 0.0,
      avg_intensity: 0.0,
      closest_distance: null
    });
    
    // Live Alerts
    const toast = ref<Toast | null>(null);
    let toastTimeout: number | null = null;
    
    // WebSockets
    const wsConnected = ref(false);
    let socket: WebSocket | null = null;
    let reconnectTimeout: number | null = null;

    // Time ticker
    const timeStr = ref('');
    let clockInterval: number | null = null;

    const showToast = (title: string, message: string, type: 'strike-toast' | 'warning-toast', icon: string) => {
      if (toastTimeout) window.clearTimeout(toastTimeout);
      toast.value = { title, message, type, icon };
      toastTimeout = window.setTimeout(() => {
        toast.value = null;
      }, 6000);
    };

    const fetchData = async () => {
      try {
        const strikesRes = await fetch('/api/strikes/recent?limit=30');
        if (strikesRes.ok) {
          recentStrikes.value = await strikesRes.json();
        }
        
        const statsRes = await fetch('/api/strikes/stats');
        if (statsRes.ok) {
          stats.value = await statsRes.json();
        }
      } catch (err) {
        console.error('Failed to fetch data from API:', err);
      }
    };

    const connectWebSocket = () => {
      if (socket) return;
      
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws`;
      
      socket = new WebSocket(wsUrl);
      
      socket.onopen = () => {
        wsConnected.value = true;
        console.log('WebSocket connection established.');
      };
      
      socket.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === 'strike') {
          const newStrike: Strike = msg.data;
          // Prepend new strike to list and limit to recent 30 items
          recentStrikes.value = [newStrike, ...recentStrikes.value].slice(0, 30);
          
          // Re-fetch aggregates
          fetchData();
          
          // Notify user
          showToast(
            '⚠️ Lightning Strike Detected!',
            `Distance: ${newStrike.distance}km | Intensity: ${newStrike.intensity}`,
            'strike-toast',
            '⚡'
          );
        } else if (msg.type === 'warning') {
          showToast(
            '⚠️ Hardware Alert',
            msg.data.message,
            'warning-toast',
            '⚠️'
          );
        }
      };
      
      socket.onclose = () => {
        wsConnected.value = false;
        socket = null;
        console.log('WebSocket closed. Retrying connection in 5 seconds...');
        reconnectTimeout = window.setTimeout(connectWebSocket, 5000);
      };
      
      socket.onerror = (err) => {
        console.error('WebSocket encountered an error:', err);
        if (socket) socket.close();
      };
    };

    onMounted(() => {
      fetchData();
      connectWebSocket();
      
      // Setup time updater
      const updateClock = () => {
        const now = new Date();
        timeStr.value = now.toLocaleTimeString();
      };
      updateClock();
      clockInterval = window.setInterval(updateClock, 1000);
    });

    onUnmounted(() => {
      if (reconnectTimeout) window.clearTimeout(reconnectTimeout);
      if (toastTimeout) window.clearTimeout(toastTimeout);
      if (clockInterval) window.clearInterval(clockInterval);
      if (socket) {
        socket.onclose = null; // prevent reconnect trigger
        socket.close();
      }
    });

    return {
      currentTab,
      recentStrikes,
      stats,
      toast,
      wsConnected,
      timeStr,
      fetchData
    };
  }
});
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 100;
  animation: alert-toast 6s forwards;
}

.toast {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-radius: 12px;
  backdrop-filter: blur(12px);
  min-width: 300px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
  color: #fff;
}

.toast.strike-toast {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.4);
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.15);
}

.toast.warning-toast {
  background: rgba(245, 158, 11, 0.15);
  border: 1px solid rgba(245, 158, 11, 0.4);
  box-shadow: 0 0 20px rgba(245, 158, 11, 0.15);
}

.toast-icon {
  font-size: 1.5rem;
}

.toast-content h4 {
  margin: 0 0 4px 0;
  font-weight: 600;
}

.toast-content p {
  margin: 0;
  font-size: 0.9em;
  color: var(--text-sub);
}

.toast-close {
  margin-left: auto;
  font-size: 1.25rem;
  opacity: 0.5;
  cursor: pointer;
  background: none;
  border: none;
  color: inherit;
  line-height: 1;
}

.toast-close:hover {
  opacity: 1;
}
</style>
