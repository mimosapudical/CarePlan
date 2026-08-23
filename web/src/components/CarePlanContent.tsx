import type { CarePlanContent as Content } from "@/lib/schemas";
const sections: Array<[string, keyof Content]> = [["Problem list","problem_list"],["Goals","goals"],["Pharmacist interventions","pharmacist_interventions"],["Monitoring plan","monitoring_plan"]];
export function CarePlanContent({ content }: { content: Content }) { return <div className="care-content">{sections.map(([title,key]) => <section key={key}><h3>{title}</h3><ul>{(content[key] as string[]).map((item) => <li key={item}>{item}</li>)}</ul></section>)}</div>; }
