import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";
import type { MetricPoint } from "../types";

type Props = { data: MetricPoint[] };

export default function RealtimeChart({ data }: Props) {
  return (
    <div style={{ width: "100%", height: 320 }}>
      <ResponsiveContainer>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="ts"
            tickFormatter={(v) => new Date(v).toLocaleTimeString()}
          />
          <YAxis yAxisId="left" domain={["auto", "auto"]} />
          <YAxis
            yAxisId="right"
            orientation="right"
            domain={["auto", "auto"]}
          />
          <Tooltip labelFormatter={(v) => new Date(v).toLocaleString()} />
          <Legend />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="temp"
            name="Temp (°C)"
            dot={false}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="hum"
            name="Hum (%)"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
