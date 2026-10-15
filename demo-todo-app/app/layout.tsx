import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AIOps Demo Todo App",
  description: "Demo Next.js Todo App for Jenkins Pipeline Testing",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
