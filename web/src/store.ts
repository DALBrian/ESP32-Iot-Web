import { create } from "zustand";
import type { Latest, MetricPoint, Status, DeviceError } from "./types";
import {
  fetchLatest,
  fetchMetrics,
  fetchStatus,
  fetchErrors,
} from "./api/endpoints";

type State = {
  latest?: Latest;
  metrics: MetricPoint[];
  status?: Status;
  errors: DeviceError[];
  lastError?: string;
  loading: boolean;
};

type Actions = {
  loadAll: () => Promise<void>;
  pollLatest: (ms?: number) => () => void; // returns cleanup fn
};

const STORAGE_KEY = "iot_last_snapshot";

export const useStore = create<State & Actions>((set, get) => ({
  latest: undefined,
  metrics: [],
  status: undefined,
  errors: [],
  lastError: undefined,
  loading: false,

  loadAll: async () => {
    set({ loading: true, lastError: undefined });
    try {
      const [latest, metrics, status, errors] = await Promise.all([
        fetchLatest(),
        fetchMetrics(),
        fetchStatus(),
        fetchErrors(),
      ]);
      set({ latest, metrics, status, errors, loading: false });

      // 緩存最後一次可用資料（API 掛掉時顯示）
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ latest, metrics, status }),
      );
    } catch (e: any) {
      set({ loading: false, lastError: e?.message || "Load failed" });
      // 從快取回填
      const cached = localStorage.getItem(STORAGE_KEY);
      if (cached) {
        const { latest, metrics, status } = JSON.parse(cached);
        set({ latest, metrics, status });
      }
    }
  },

  pollLatest: (ms = 3000) => {
    let alive = true;
    const tick = async () => {
      try {
        const latest = await fetchLatest();
        const metrics = [
          ...get().metrics,
          { ts: latest.ts, temp: latest.temp, hum: latest.hum },
        ].slice(-300); // 保持最多 300 點
        set({ latest, metrics, lastError: undefined });
        localStorage.setItem(
          STORAGE_KEY,
          JSON.stringify({ latest, metrics, status: get().status }),
        );
      } catch (e: any) {
        set({ lastError: e?.message || "Polling error" });
      } finally {
        if (alive) setTimeout(tick, ms);
      }
    };
    tick();
    return () => {
      alive = false;
    };
  },
}));
