import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata={title:"CarePlan Workspace",description:"Asynchronous pharmacy care-plan workflow"};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
