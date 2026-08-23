import { expect, test } from "@playwright/test";
const id="123e4567-e89b-12d3-a456-426614174000";
test("submits and reaches a completed care plan",async({page})=>{
  await page.route("**/api/care-plans",route=>route.request().method()==="POST"?route.fulfill({status:202,contentType:"application/json",body:JSON.stringify({message:"Received",careplan_id:id,status:"pending"})}):route.continue());
  await page.route(`**/api/care-plans/${id}/status`,route=>route.fulfill({contentType:"application/json",body:JSON.stringify({id,status:"completed",content:{problem_list:["Medication review"],goals:["Improve adherence"],pharmacist_interventions:["Counsel patient"],monitoring_plan:["Follow up"]},error:null})}));
  await page.goto("/");
  await page.getByLabel("Medication").fill("IVIG");
  await page.getByRole("button",{name:"Generate care plan"}).click();
  await expect(page.getByText("completed",{exact:true})).toBeVisible();
  await expect(page.getByText("Medication review")).toBeVisible();
  await expect(page.getByRole("link",{name:"Download care plan"})).toBeVisible();
});
