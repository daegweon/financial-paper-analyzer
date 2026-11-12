import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "PaperSignal | Financial Research", description: "Evidence-grounded finance paper analysis" };
export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) {return <html lang="ko"><body>{children}</body></html>}
