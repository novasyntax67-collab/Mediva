import "./globals.css";
import React from "react";
import FirebaseInitializer from "@/components/FirebaseInitializer";

export const metadata = {
  title: "Healthcare Platform",
  description: "Next-generation remote patient monitoring & telehealth platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <FirebaseInitializer />
        <main>{children}</main>
      </body>
    </html>
  );
}
