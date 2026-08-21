import { createApp } from 'vue';
import App from './App.vue';
import './index.css';

const app = createApp(App);
app.mount('#app');

// Register Service Worker for PWA and Offline functionality
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js')
      .then((reg) => {
        console.log('[PWA Service Worker] Registered successfully with scope:', reg.scope);
      })
      .catch((err) => {
        console.error('[PWA Service Worker] Registration failed:', err);
      });
  });
}

