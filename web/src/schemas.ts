import { z } from "zod";

export const MetricPointSchema = z.object({
  ts: z.string(), temp: z.number(), hum: z.number()
});
export const LatestSchema = MetricPointSchema.extend({
  id: z.string(), online: z.boolean()
});
export const StatusSchema = z.object({
  id: z.string(), online: z.boolean(), updatedAt: z.string()
});
export const ErrorSchema = z.object({
  id: z.string(), ts: z.string(), msg: z.string()
});
export const MetricsSchema = z.array(MetricPointSchema);
export const ErrorsSchema = z.array(ErrorSchema);
