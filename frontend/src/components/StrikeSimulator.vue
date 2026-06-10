<template>
  <div class="glass-card flex-col gap-lg" style="height: 100%; justify-content: space-between;">
    <div style="border-bottom: 1px solid var(--border-light); padding-bottom: 12px; width: 100%;">
      <h3 style="font-size: 1.1rem; font-weight: 600;">Simulation Toolkit</h3>
      <p style="font-size: 0.8rem; color: var(--text-sub); margin-top: 4px;">Inject strikes to verify end-to-end functionality</p>
    </div>

    <div class="flex-col gap-md" style="flex-grow: 1; justify-content: center;">
      <!-- Distance Slider -->
      <div class="form-group">
        <div style="display: flex; justify-content: space-between;">
          <label class="sim-label">Distance</label>
          <span style="font-family: var(--font-mono); font-size: 0.9rem; font-weight: 600; color: var(--color-cyan);">
            {{ distance }} km
          </span>
        </div>
        <input 
          type="range" 
          min="1" 
          max="40" 
          v-model.number="distance" 
          class="slider"
        />
        <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted);">
          <span>1km</span>
          <span>20km</span>
          <span>40km</span>
        </div>
      </div>

      <!-- Intensity Input -->
      <div class="form-group">
        <label class="sim-label">Energy Intensity</label>
        <input 
          type="number" 
          min="1" 
          max="50000" 
          v-model.number="intensity" 
          class="input-field"
          style="font-family: var(--font-mono);"
        />
      </div>
    </div>

    <!-- Trigger Button -->
    <div class="flex-col gap-sm" style="width: 100%;">
      <button 
        type="button" 
        class="btn-primary" 
        @click="triggerSimulation"
        :disabled="simulating"
        style="width: 100%;"
      >
        <span v-if="!simulating">⚡ Inject Simulated Strike</span>
        <span v-else>Processing Strike...</span>
      </button>
      <span v-if="simSuccess" class="success-indicator">✓ Strike successfully processed</span>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue';

export default defineComponent({
  name: 'StrikeSimulator',
  emits: ['simulated'],
  setup(props, { emit }) {
    const distance = ref(15);
    const intensity = ref(450);
    const simulating = ref(false);
    const simSuccess = ref(false);

    const triggerSimulation = async () => {
      simulating.value = true;
      simSuccess.value = false;
      try {
        const res = await fetch('/api/strikes/simulate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            distance: distance.value,
            intensity: intensity.value
          })
        });
        if (res.ok) {
          simSuccess.value = true;
          emit('simulated');
          setTimeout(() => {
            simSuccess.value = false;
          }, 3000);
        } else {
          const data = await res.json();
          alert(`Simulation error: ${data.detail || 'Failed'}`);
        }
      } catch (err) {
        console.error('Failed to trigger simulation:', err);
        alert('Network connection error triggering simulation.');
      } finally {
        simulating.value = false;
      }
    };

    return {
      distance,
      intensity,
      simulating,
      simSuccess,
      triggerSimulation
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

.sim-label {
  font-size: 0.8rem;
  color: var(--text-sub);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.slider {
  -webkit-appearance: none;
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
  outline: none;
  cursor: pointer;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--color-cyan);
  box-shadow: 0 0 10px var(--color-cyan);
  transition: transform 0.1s;
}

.slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}

.slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--color-cyan);
  border: none;
  box-shadow: 0 0 10px var(--color-cyan);
  transition: transform 0.1s;
  cursor: pointer;
}

.slider::-moz-range-thumb:hover {
  transform: scale(1.15);
}

.success-indicator {
  font-size: 0.8rem;
  color: var(--color-green);
  text-align: center;
  font-weight: 500;
  margin-top: 4px;
}
</style>
