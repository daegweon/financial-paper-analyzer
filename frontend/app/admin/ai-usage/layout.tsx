import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "PaperSignal 관리자 | AI 운영 관리",
  robots: { index: false, follow: false, noarchive: true },
};

export default function AdminAIUsageLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}
