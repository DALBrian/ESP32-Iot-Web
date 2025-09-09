import { api } from "./client";
import type { Latest, MetricPoint, Status, DeviceError } from "../types";
import { LatestSchema, MetricsSchema, StatusSchema, ErrorsSchema } from "../schemas";

export async function fetchLatest(): Promise<Latest> {
  const { data } = await api.get("/latest");
  return LatestSchema.parse(data);
}

export async function fetchMetrics(): Promise<MetricPoint[]> {
  const { data } = await api.get("/metrics");
  return MetricsSchema.parse(data);
}

export async function fetchStatus(): Promise<Status> {
  const { data } = await api.get("/status");
  return StatusSchema.parse(data);
}

export async function fetchErrors(): Promise<DeviceError[]> {
  const { data } = await api.get("/errors");
  return ErrorsSchema.parse(data);
}
