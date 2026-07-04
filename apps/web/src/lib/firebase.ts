import { initializeApp, getApps, getApp } from "firebase/app";
import { getAnalytics, isSupported } from "firebase/analytics";

const firebaseConfig = {
  apiKey: "AIzaSyCgY4KteqvWjoL4iD8fRtzL6dN9RqNtYMU",
  authDomain: "carex-c732a.firebaseapp.com",
  projectId: "carex-c732a",
  storageBucket: "carex-c732a.firebasestorage.app",
  messagingSenderId: "189548087101",
  appId: "1:189548087101:web:34307213f7e0bc0b15a754",
  measurementId: "G-JQ93EBGFZY"
};

// Initialize Firebase
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();

// Analytics helper (only runs on browser environments)
export const getFirebaseAnalytics = async () => {
  if (typeof window !== "undefined" && await isSupported()) {
    return getAnalytics(app);
  }
  return null;
};

export { app };
