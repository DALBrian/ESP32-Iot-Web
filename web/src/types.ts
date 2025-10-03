export type MetricPoint = { ts: string; temp: number; hum: number };
export type Latest = MetricPoint & { id: string; online: boolean };
export type Status = { id: string; online: boolean; updatedAt: string | null };
export type DeviceError = { id: string; ts: string; msg: string };
