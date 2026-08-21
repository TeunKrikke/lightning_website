/**
 * Offline Storage & Synchronization Engine for PWA
 */

export interface QueuedAction {
  id: string;
  type: string;
  url: string;
  method: string;
  payload: any;
  timestamp: number;
}

const STORAGE_KEYS = {
  STRIKES: 'lightning_pwa_strikes',
  STATS: 'lightning_pwa_stats',
  CONFIG: 'lightning_pwa_config',
  REGISTERS: 'lightning_pwa_registers',
  QUEUE: 'lightning_pwa_sync_queue'
};

class OfflineSyncManager {
  private syncListeners: Array<(syncedCount: number) => void> = [];

  /**
   * Save data to local storage for offline viewing
   */
  public saveCache(key: 'strikes' | 'stats' | 'config' | 'registers', data: any): void {
    try {
      const storageKey = STORAGE_KEYS[key.toUpperCase() as keyof typeof STORAGE_KEYS];
      if (storageKey) {
        localStorage.setItem(storageKey, JSON.stringify(data));
      }
    } catch (e) {
      console.warn('Failed to save to local offline cache:', e);
    }
  }

  /**
   * Read cached data when server is unreachable
   */
  public getCache<T>(key: 'strikes' | 'stats' | 'config' | 'registers'): T | null {
    try {
      const storageKey = STORAGE_KEYS[key.toUpperCase() as keyof typeof STORAGE_KEYS];
      if (storageKey) {
        const item = localStorage.getItem(storageKey);
        return item ? JSON.parse(item) : null;
      }
    } catch (e) {
      console.warn('Failed to read from local offline cache:', e);
    }
    return null;
  }

  /**
   * Get all currently pending offline queued actions
   */
  public getQueue(): QueuedAction[] {
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.QUEUE);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  }

  /**
   * Enqueue a pending mutation action while offline
   */
  public enqueueAction(type: string, url: string, payload: any, method: string = 'POST'): QueuedAction {
    const queue = this.getQueue();
    const action: QueuedAction = {
      id: `action_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
      type,
      url,
      method,
      payload,
      timestamp: Date.now()
    };

    queue.push(action);
    localStorage.setItem(STORAGE_KEYS.QUEUE, JSON.stringify(queue));
    console.log(`[Offline Sync] Action queued: ${type} (${url})`, action);
    return action;
  }

  /**
   * Clear the sync queue
   */
  public clearQueue(): void {
    localStorage.setItem(STORAGE_KEYS.QUEUE, JSON.stringify([]));
  }

  /**
   * Register a listener for sync events
   */
  public onSynced(callback: (count: number) => void): void {
    this.syncListeners.push(callback);
  }

  /**
   * Check if backend server is responsive
   */
  public async isServerReachable(): Promise<boolean> {
    if (!navigator.onLine) return false;
    try {
      const res = await fetch('/api/sensor/status', { method: 'GET', cache: 'no-store' });
      return res.ok;
    } catch (e) {
      return false;
    }
  }

  /**
   * Execute background synchronization of all queued actions when online connection is restored
   */
  public async syncPendingActions(): Promise<number> {
    const queue = this.getQueue();
    if (queue.length === 0) return 0;

    console.log(`[Offline Sync] Attempting to sync ${queue.length} pending actions...`);
    const isReachable = await this.isServerReachable();
    if (!isReachable) {
      console.log('[Offline Sync] Server unreachable. Deferring sync.');
      return 0;
    }

    let syncedCount = 0;
    const remainingQueue: QueuedAction[] = [];

    for (const action of queue) {
      try {
        const res = await fetch(action.url, {
          method: action.method || 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: action.payload ? JSON.stringify(action.payload) : undefined
        });

        if (res.ok || res.status === 202) {
          syncedCount++;
          console.log(`[Offline Sync] Successfully synced action ${action.id} (${action.type})`);
        } else {
          console.warn(`[Offline Sync] Server returned ${res.status} for ${action.id}, keeping in queue.`);
          remainingQueue.push(action);
        }
      } catch (err) {
        console.error(`[Offline Sync] Failed to sync action ${action.id}:`, err);
        remainingQueue.push(action);
      }
    }

    localStorage.setItem(STORAGE_KEYS.QUEUE, JSON.stringify(remainingQueue));

    if (syncedCount > 0) {
      this.syncListeners.forEach((cb) => cb(syncedCount));
    }

    return syncedCount;
  }
}

export const offlineSync = new OfflineSyncManager();
