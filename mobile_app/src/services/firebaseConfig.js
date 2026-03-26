import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

// These values match your google-services.json
const firebaseConfig = {
  apiKey: "AIzaSyApG9VHknwZvajUM4UeTV4TKAua4zNyoX0",
  authDomain: "med-monitor-iot.firebaseapp.com",
  projectId: "med-monitor-iot",
  storageBucket: "med-monitor-iot.firebasestorage.app",
  messagingSenderId: "562308828182",
  appId: "1:562308828182:android:77d25e038f279a62903937"
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);
