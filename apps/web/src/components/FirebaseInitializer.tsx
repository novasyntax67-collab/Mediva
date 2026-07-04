"use client";

import { useEffect } from "react";
import { getFirebaseAnalytics } from "@/lib/firebase";

export default function FirebaseInitializer() {
  useEffect(() => {
    getFirebaseAnalytics().catch((err) => {
      console.error("Failed to initialize Firebase Analytics:", err);
    });
  }, []);

  return null;
}
