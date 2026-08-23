import { describe, expect, it } from "vitest";
import { CarePlanDetailSchema, CarePlanStatusResponseSchema, CarePlanStatusSchema, CreateCarePlanResponseSchema } from "@/lib/schemas";
const id="123e4567-e89b-12d3-a456-426614174000";
describe("Django contract schemas",()=>{
  it.each(["pending","processing","completed","failed"])("accepts %s",(status)=>expect(CarePlanStatusSchema.parse(status)).toBe(status));
  it("rejects unknown states",()=>expect(()=>CarePlanStatusSchema.parse("done")).toThrow());
  it("requires careplan_id",()=>expect(()=>CreateCarePlanResponseSchema.parse({message:"Received",id,status:"pending"})).toThrow());
  it("keeps detail care_plan and status content distinct",()=>{
    expect(CarePlanDetailSchema.parse({id,status:"completed",history:[],payload:{},care_plan:{},error:null,queued_at:null,created_at:null,updated_at:null}).care_plan).not.toBeNull();
    expect(CarePlanStatusResponseSchema.parse({id,status:"completed",content:{},error:null}).content).not.toBeNull();
  });
});
