import { render,screen } from "@testing-library/react";
import { describe,expect,it } from "vitest";
import { CarePlanStatus } from "@/components/CarePlanStatus";
const id="123e4567-e89b-12d3-a456-426614174000";
describe("CarePlanStatus",()=>{
  it("shows a download only after completion",()=>{const{rerender}=render(<CarePlanStatus id={id} error={null} data={{id,status:"processing",content:null,error:null}}/>);expect(screen.queryByText(/Download/)).not.toBeInTheDocument();rerender(<CarePlanStatus id={id} error={null} data={{id,status:"completed",content:{problem_list:[],goals:[],pharmacist_interventions:[],monitoring_plan:[]},error:null}}/>);expect(screen.getByText(/Download/)).toBeInTheDocument();});
});
