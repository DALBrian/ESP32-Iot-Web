import type { DeviceError } from "../types";

export default function ErrorList({ items }: { items: DeviceError[] }) {
  return (
    <div>
      <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>最近錯誤</h3>
      <ul style={{ margin: 0, paddingLeft: 18 }}>
        {items.slice(0, 10).map((e) => (
          <li key={e.id}>
            <code>{new Date(e.ts).toLocaleString()}</code> — {e.msg}
          </li>
        ))}
      </ul>
    </div>
  );
}
