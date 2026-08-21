<template>
  <div class="glass-card flex-col gap-md" style="align-items: center; justify-content: center; position: relative; overflow: hidden;">
    <div style="width: 100%; display: flex; justify-content: space-between; align-items: center;">
      <h3 style="font-size: 1.1rem; font-weight: 600;">Lightning Radar</h3>
      <span class="range-badge">40km Range</span>
    </div>

    <!-- Radar Screen SVG -->
    <div class="radar-screen">
      <svg :viewBox="`0 0 ${size} ${size}`" width="100%" height="100%">
        <!-- Background Grid Rings -->
        <circle :cx="cx" :cy="cy" :r="r4" class="radar-ring" />
        <circle :cx="cx" :cy="cy" :r="r3" class="radar-ring" />
        <circle :cx="cx" :cy="cy" :r="r2" class="radar-ring" />
        <circle :cx="cx" :cy="cy" :r="r1" class="radar-ring" />

        <!-- Crosshair Axes -->
        <line :x1="cx" y1="0" :x2="cx" :y2="size" class="radar-axis" />
        <line x1="0" :y1="cy" :x2="size" :y2="cy" class="radar-axis" />

        <!-- Rotating Sweeping Beam -->
        <line 
          :x1="cx" 
          :y1="cy" 
          :x2="cx" 
          :y2="0" 
          class="radar-sweep" 
        />

        <!-- Ring Distance Labels -->
        <text :x="cx + 6" :y="cy - r1 + 4" class="radar-label">10k</text>
        <text :x="cx + 6" :y="cy - r2 + 4" class="radar-label">20k</text>
        <text :x="cx + 6" :y="cy - r3 + 4" class="radar-label">30k</text>
        <text :x="cx + 6" :y="cy - r4 + 14" class="radar-label">40km</text>

        <!-- Strike Dots -->
        <g v-for="dot in plottedStrikes" :key="dot.id">
          <!-- Ripple Animation Ring for very recent strikes (last 30s) -->
          <circle 
            v-if="dot.isNew" 
            :cx="dot.x" 
            :cy="dot.y" 
            :r="8" 
            class="strike-ripple"
            :style="{ stroke: dot.color }" 
          />
          <!-- Core Strike Indicator Dot -->
          <circle 
            :cx="dot.x" 
            :cy="dot.y" 
            :r="dot.isNew ? 5 : 3.5" 
            :fill="dot.color"
            :opacity="dot.opacity"
            class="strike-dot" 
          />
        </g>
      </svg>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed, PropType } from 'vue';

interface Strike {
  id: number;
  timestamp: string;
  distance: number;
  intensity: number;
}

export default defineComponent({
  name: 'LightningRadar',
  props: {
    strikes: {
      type: Array as PropType<Strike[]>,
      required: true
    }
  },
  setup(props) {
    const size = 260;
    const cx = size / 2;
    const cy = size / 2;
    
    // Ring radii mapped relative to size
    const r4 = size * 0.46;  // 40km
    const r3 = size * 0.355; // 30km
    const r2 = size * 0.25;  // 20km
    const r1 = size * 0.145; // 10km

    const getAngle = (id: number) => {
      // Use Golden Angle (137.5 degrees) * ID to spread strikes evenly
      return (id * 137.5) % 360;
    };

    const plottedStrikes = computed(() => {
      const now = new Date().getTime();
      return props.strikes.map((strike) => {
        const angle = getAngle(strike.id);
        
        // Map 0-40km to 0-r4 pixels
        const distanceRatio = Math.min(Math.max(strike.distance, 0), 40) / 40;
        const radius = distanceRatio * r4;
        
        // Calculate SVG Coordinates (rotate by -90 deg so 0 deg is north)
        const rad = ((angle - 90) * Math.PI) / 180;
        const x = cx + radius * Math.cos(rad);
        const y = cy + radius * Math.sin(rad);

        // Evaluate age to calculate fading
        const strikeTime = new Date(strike.timestamp).getTime();
        const ageSec = (now - strikeTime) / 1000;
        
        const isNew = ageSec < 30; // 30 seconds pulse
        
        // Opacity drops from 1.0 to 0.15 over 30 minutes
        const opacity = Math.max(0.15, 1.0 - (ageSec / 1800));

        // Color maps from red (very close) to cyan (far)
        let color = '#00f2fe'; // cyan
        if (strike.distance < 10) {
          color = '#ef4444'; // red
        } else if (strike.distance < 20) {
          color = '#f59e0b'; // orange
        } else if (strike.distance < 30) {
          color = '#7c3aed'; // purple
        }

        return {
          id: strike.id,
          x,
          y,
          color,
          opacity,
          isNew
        };
      });
    });

    return {
      size,
      cx,
      cy,
      r1,
      r2,
      r3,
      r4,
      plottedStrikes
    };
  }
});
</script>

<style scoped>
.range-badge {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-cyan);
  background: rgba(0, 242, 254, 0.08);
  border: 1px solid rgba(0, 242, 254, 0.2);
  padding: 4px 8px;
  border-radius: 12px;
}

.radar-screen {
  width: 260px;
  height: 260px;
  background: radial-gradient(circle, rgba(16, 24, 48, 0.6) 0%, rgba(6, 6, 12, 0.9) 100%);
  border: 2px solid rgba(255, 255, 255, 0.05);
  border-radius: 50%;
  position: relative;
  box-shadow: inset 0 0 30px rgba(0, 242, 254, 0.05), 0 0 25px rgba(0, 0, 0, 0.5);
}

.radar-ring {
  fill: none;
  stroke: rgba(0, 242, 254, 0.08);
  stroke-width: 1px;
}

.radar-axis {
  stroke: rgba(255, 255, 255, 0.03);
  stroke-dasharray: 2 4;
  stroke-width: 1px;
}

.radar-sweep {
  stroke: var(--color-cyan);
  stroke-width: 1.5px;
  opacity: 0.25;
  transform-origin: center;
  animation: radar-sweep 8s linear infinite;
  filter: drop-shadow(0 0 6px var(--color-cyan));
}

.radar-label {
  fill: var(--text-muted);
  font-size: 8px;
  font-family: var(--font-mono);
  font-weight: 500;
}

.strike-dot {
  filter: drop-shadow(0 0 4px currentColor);
}

.strike-ripple {
  fill: none;
  stroke-width: 1.5px;
  transform-origin: center;
  animation: pulse-ring 1.8s cubic-bezier(0.215, 0.610, 0.355, 1) infinite;
}
</style>
