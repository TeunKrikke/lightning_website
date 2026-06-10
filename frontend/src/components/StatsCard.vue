<template>
  <div class="glass-card flex-col gap-lg" style="justify-content: space-between; height: 100%;">
    <h3 style="font-size: 1.1rem; font-weight: 600; margin-bottom: 8px;">Activity Stats</h3>
    
    <div class="flex-col gap-md" style="flex-grow: 1; justify-content: space-around;">
      <!-- Stat Row 1: Strikes Count -->
      <div class="stat-group">
        <span class="stat-label">Strikes (24h / 7d)</span>
        <div class="stat-value" style="font-size: 2.2rem; font-weight: 700; color: #fff; margin-top: 4px;">
          {{ stats.amount_24h }} <span style="font-size: 1.2rem; font-weight: 400; color: var(--text-sub);">/ {{ stats.amount_7d }}</span>
        </div>
      </div>

      <!-- Stat Row 2: Closest Strike -->
      <div class="stat-group">
        <span class="stat-label">Closest Strike</span>
        <div class="stat-value" style="font-size: 1.8rem; font-weight: 700; margin-top: 4px;" :style="{ color: stats.closest_distance !== null && stats.closest_distance < 10 ? 'var(--color-red)' : 'var(--color-gold)' }">
          {{ stats.closest_distance !== null ? `${stats.closest_distance} km` : 'N/A' }}
        </div>
      </div>

      <!-- Average Metrics Grid -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; border-top: 1px solid var(--border-light); padding-top: 16px;">
        <div class="flex-col">
          <span class="stat-label-sub">Avg Distance</span>
          <span class="stat-value-sub">{{ stats.avg_distance }} km</span>
        </div>
        <div class="flex-col">
          <span class="stat-label-sub">Avg Intensity</span>
          <span class="stat-value-sub">{{ stats.avg_intensity }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';

interface Stats {
  amount_24h: number;
  amount_7d: number;
  avg_distance: number;
  avg_intensity: number;
  closest_distance: number | null;
}

export default defineComponent({
  name: 'StatsCard',
  props: {
    stats: {
      type: Object as PropType<Stats>,
      required: true
    }
  }
});
</script>

<style scoped>
.stat-label {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-sub);
  font-weight: 500;
}

.stat-label-sub {
  font-size: 0.75rem;
  color: var(--text-sub);
}

.stat-value-sub {
  font-size: 1.1rem;
  font-weight: 600;
  color: #fff;
  font-family: var(--font-mono);
  margin-top: 4px;
}
</style>
