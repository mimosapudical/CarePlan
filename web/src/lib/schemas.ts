import { z } from "zod";

export const CarePlanStatusSchema = z.enum(["pending", "processing", "completed", "failed"]);
export const CarePlanContentSchema = z.object({
  problem_list: z.array(z.string()).default([]),
  goals: z.array(z.string()).default([]),
  pharmacist_interventions: z.array(z.string()).default([]),
  monitoring_plan: z.array(z.string()).default([]),
}).passthrough();

const listLike = z.union([z.string(), z.array(z.string())]);
export const CreateCarePlanInputSchema = z.object({
  patient_first_name: z.string(), patient_last_name: z.string(), referring_provider: z.string(),
  referring_provider_npi: z.string(), patient_mrn: z.string(), patient_primary_diagnosis: z.string(),
  medication_name: z.string(), additional_diagnosis: listLike, medication_history: listLike,
  patient_records: z.string(),
});
export const CreateCarePlanResponseSchema = z.object({ message: z.literal("Received"), careplan_id: z.string().uuid(), status: CarePlanStatusSchema });
export const CarePlanDetailSchema = z.object({
  id: z.string().uuid(), status: CarePlanStatusSchema, history: z.array(z.unknown()), payload: z.record(z.string(), z.unknown()),
  care_plan: CarePlanContentSchema.nullable(), error: z.string().nullable(), queued_at: z.string().nullable(),
  created_at: z.string().nullable(), updated_at: z.string().nullable(),
});
export const CarePlanStatusResponseSchema = z.object({ id: z.string().uuid(), status: CarePlanStatusSchema, content: CarePlanContentSchema.nullable(), error: z.string().nullable() });
export const SearchCarePlansResponseSchema = z.object({ query: z.string(), results: z.array(CarePlanDetailSchema) });

export const OpsCarePlanSchema = z.object({
  id: z.string().uuid(),
  status: CarePlanStatusSchema,
  error: z.string().nullable(),
  queued_at: z.string().nullable(),
  created_at: z.string().nullable(),
  updated_at: z.string().nullable(),
  manual_retry_count: z.number().int().nonnegative(),
  last_manual_retry_at: z.string().nullable(),
  stale: z.boolean(),
}).strict();
export const OpsCarePlanListResponseSchema = z.object({
  results: z.array(OpsCarePlanSchema),
}).strict();
export const OpsRetryResponseSchema = OpsCarePlanSchema;

export type OpsCarePlan = z.infer<typeof OpsCarePlanSchema>;
export type OpsCarePlanListResponse = z.infer<typeof OpsCarePlanListResponseSchema>;
export type OpsRetryResponse = z.infer<typeof OpsRetryResponseSchema>;

export type CarePlanStatus = z.infer<typeof CarePlanStatusSchema>;
export type CarePlanContent = z.infer<typeof CarePlanContentSchema>;
export type CreateCarePlanInput = z.infer<typeof CreateCarePlanInputSchema>;
export type CreateCarePlanResponse = z.infer<typeof CreateCarePlanResponseSchema>;
export type CarePlanDetail = z.infer<typeof CarePlanDetailSchema>;
export type CarePlanStatusResponse = z.infer<typeof CarePlanStatusResponseSchema>;
