import { useEffect } from "react";
import { useStore } from "../store";
import RealtimeChart from "../components/RealtimeChart";
import StatusPill from "../components/StatusPill";
import ErrorList from "../components/ErrorList";

export default function Dashboard() {
  const { latest, metrics, status, errors, lastError, loadAll, pollLatest } =
    useStore();

  useEffect(() => {
    loadAll();
    const stop = pollLatest(3000);
    return () => stop();
  }, [loadAll, pollLatest]);

  return (
    <div style={{ padding: 24, display: "grid", gap: 16 }}>
      <header style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <h1 style={{ margin: 0 }}>IoT Dashboard</h1>
        <StatusPill online={status?.online ?? latest?.online} />
        {latest && (
          <small>Last Update: {new Date(latest.ts).toLocaleString()}</small>
        )}
      </header>

      {lastError && (
        <div
          style={{
            padding: 12,
            background: "#fef2f2",
            border: "1px solid #fecaca",
            borderRadius: 8,
          }}
        >
          API Error：{lastError}
        </div>
      )}

      <section className="card">
        <h2 style={{ marginTop: 0 }}>Real-time Humidity & Temperature</h2>
        <RealtimeChart data={metrics} />
      </section>

      <section
        style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16 }}
      >
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Device Information</h3>
          <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>
            {JSON.stringify(
              {
                id: latest?.id ?? status?.id ?? "unknown",
                online: status?.online ?? latest?.online,
              },
              null,
              2,
            )}
          </pre>
        </div>
        <div className="card">
          <ErrorList items={errors} />
        </div>
      </section>
    </div>
  );
}
