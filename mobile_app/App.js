import React, { useState, useEffect } from 'react';
import { 
  StyleSheet, 
  Text, 
  View, 
  ScrollView, 
  TouchableOpacity, 
  StatusBar,
  Dimensions,
  Platform
} from 'react-native';
import { 
  Activity, 
  Clock, 
  AlertCircle, 
  Plus, 
  Calendar, 
  ChevronRight, 
  MapPin,
  RefreshCcw,
  User
} from 'lucide-react-native';

// --- Firebase Imports ---
import { db } from './src/services/firebaseConfig';
import { 
  doc, 
  onSnapshot, 
  collection, 
  query, 
  orderBy, 
  limit 
} from "firebase/firestore";


const { width } = Dimensions.get('window');

// --- Theme Config ---
const COLORS = {
  bg: '#0F172A',
  card: 'rgba(30, 41, 59, 0.7)',
  primary: '#38BDF8',
  success: '#22C55E',
  warning: '#F59E0B',
  danger: '#EF4444',
  text: '#F8FAFC',
  textMuted: '#94A3B8',
};

// --- Mock Data ---
const MOCK_STATUS = {
  risk_level: 'HIGH',
  risk_score: 4.2,
  last_dose: '09:35 AM',
  predicted: '09:53 AM',
  drift: '+18m',
};

const MOCK_HISTORY = [
  { id: 1, time: '09:35 AM', date: 'Mar 25', status: 'Late', color: COLORS.danger },
  { id: 2, time: '08:22 AM', date: 'Mar 24', status: 'On Time', color: COLORS.success },
  { id: 3, time: '08:09 AM', date: 'Mar 23', status: 'On Time', color: COLORS.success },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Real-time State
  const [riskStatus, setRiskStatus] = useState(MOCK_STATUS);
  const [history, setHistory] = useState(MOCK_HISTORY);
  const [isLoading, setIsLoading] = useState(true);

  // 1. Listen for Risk Status (medicine_001)
  useEffect(() => {
    const docRef = doc(db, "risk_results", "medicine_001");
    const unsubscribe = onSnapshot(docRef, (docSnap) => {
      if (docSnap.exists()) {
        setRiskStatus(docSnap.data());
      }
      setIsLoading(false);
    });

    return () => unsubscribe();
  }, []);

  // 2. Listen for Scan History (Last 10 events)
  useEffect(() => {
    const q = query(
      collection(db, "scan_history"), 
      orderBy("logged_at", "desc"), 
      limit(10)
    );

    const unsubscribe = onSnapshot(q, (querySnapshot) => {
      const scans = [];
      querySnapshot.forEach((doc) => {
        const data = doc.data();
        // Format for UI
        scans.push({
          id: doc.id,
          time: data.timestamp ? data.timestamp.split('T')[1]?.substring(0, 5) : 'N/A',
          date: data.timestamp ? data.timestamp.split('T')[0] : 'N/A',
          status: data.event === 'absent' ? 'Detected' : 'Missing',
          color: data.event === 'absent' ? COLORS.success : COLORS.warning
        });
      });
      if (scans.length > 0) setHistory(scans);
    });

    return () => unsubscribe();
  }, []);

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Med Monitor</Text>
          <Text style={styles.headerSubtitle}>Patient: Grandma</Text>
        </View>
        <TouchableOpacity style={styles.profileBtn}>
          <User size={24} color={COLORS.text} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        
        {/* Risk Status Card (Glassmorphic) */}
        <View style={styles.glassCard}>
          <View style={styles.row}>
            <View style={[styles.statusBadge, { backgroundColor: (riskStatus.risk_level === 'HIGH' ? COLORS.danger : COLORS.success) + '22' }]}>
              <AlertCircle size={16} color={riskStatus.risk_level === 'HIGH' ? COLORS.danger : COLORS.success} />
              <Text style={[styles.statusText, { color: riskStatus.risk_level === 'HIGH' ? COLORS.danger : COLORS.success }]}>{riskStatus.risk_level} RISK</Text>
            </View>
            <TouchableOpacity style={styles.refreshBtn}>
              <RefreshCcw size={16} color={COLORS.primary} />
            </TouchableOpacity>
          </View>

          <View style={styles.scoreContainer}>
            <Text style={styles.scoreLabel}>Adherence Score</Text>
            <Text style={styles.scoreValue}>{riskStatus.risk_score}</Text>
            <View style={styles.progressBarBg}>
              <View style={[styles.progressBarFill, { 
                width: `${Math.min(riskStatus.risk_score * 10, 100)}%`, 
                backgroundColor: riskStatus.risk_score > 3 ? COLORS.danger : COLORS.success 
              }]} />
            </View>
          </View>

          <View style={styles.metricsGrid}>
            <View style={styles.metricItem}>
              <Clock size={20} color={COLORS.textMuted} />
              <Text style={styles.metricLabel}>Last Dose</Text>
              <Text style={styles.metricValue}>{riskStatus.last_dose || 'N/A'}</Text>
            </View>
            <View style={styles.metricItem}>
              <Calendar size={20} color={COLORS.textMuted} />
              <Text style={styles.metricLabel}>Predicted</Text>
              <Text style={styles.metricValue}>{riskStatus.predicted || 'N/A'}</Text>
            </View>
            <View style={styles.metricItem}>
              <Activity size={20} color={COLORS.textMuted} />
              <Text style={styles.metricLabel}>Drift</Text>
              <Text style={styles.metricValue}>{riskStatus.drift ? `+${riskStatus.drift}m` : 'Stable'}</Text>
            </View>
          </View>
        </View>

        {/* Action Button: Detect New Medicine */}
        <TouchableOpacity style={styles.primaryActionBtn}>
          <Plus size={24} color={COLORS.bg} />
          <Text style={styles.primaryActionText}>Add Medicine / Detect RFID</Text>
        </TouchableOpacity>

        {/* History Section */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Adherence Timeline</Text>
          <TouchableOpacity>
            <Text style={styles.seeAllText}>See All</Text>
          </TouchableOpacity>
        </View>

        {history.map((item) => (
          <View key={item.id} style={styles.historyCard}>
            <View style={[styles.historyIndicator, { backgroundColor: item.color }]} />
            <View style={styles.historyInfo}>
              <Text style={styles.historyTime}>{item.time}</Text>
              <Text style={styles.historyDate}>{item.date}</Text>
            </View>
            <View style={styles.historyStatus}>
              <Text style={[styles.statusLabel, { color: item.color }]}>{item.status}</Text>
              <ChevronRight size={20} color={COLORS.textMuted} />
            </View>
          </View>
        ))}

      </ScrollView>

      {/* Tabs */}
      <View style={styles.tabBar}>
        <TouchableOpacity style={styles.tabItem} onPress={() => setActiveTab('dashboard')}>
          <Activity size={24} color={activeTab === 'dashboard' ? COLORS.primary : COLORS.textMuted} />
          <Text style={[styles.tabLabel, { color: activeTab === 'dashboard' ? COLORS.primary : COLORS.textMuted }]}>Dashboard</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.tabItem} onPress={() => setActiveTab('history')}>
          <Clock size={24} color={activeTab === 'history' ? COLORS.primary : COLORS.textMuted} />
          <Text style={[styles.tabLabel, { color: activeTab === 'history' ? COLORS.primary : COLORS.textMuted }]}>History</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.tabItem} onPress={() => setActiveTab('map')}>
          <MapPin size={24} color={activeTab === 'map' ? COLORS.primary : COLORS.textMuted} />
          <Text style={[styles.tabLabel, { color: activeTab === 'map' ? COLORS.primary : COLORS.textMuted }]}>Devices</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
    paddingBottom: 20,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: COLORS.text,
    letterSpacing: -0.5,
  },
  headerSubtitle: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginTop: 4,
  },
  profileBtn: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: COLORS.card,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 100,
  },
  glassCard: {
    backgroundColor: COLORS.card,
    borderRadius: 32,
    padding: 24,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 6,
  },
  statusText: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  refreshBtn: {
    padding: 8,
  },
  scoreContainer: {
    marginTop: 24,
    alignItems: 'center',
  },
  scoreLabel: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginBottom: 8,
  },
  scoreValue: {
    fontSize: 64,
    fontWeight: 'bold',
    color: COLORS.text,
    letterSpacing: -2,
  },
  progressBarBg: {
    width: '100%',
    height: 6,
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 3,
    marginTop: 12,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 3,
  },
  metricsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 32,
    paddingTop: 24,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.05)',
  },
  metricItem: {
    alignItems: 'center',
    gap: 4,
  },
  metricLabel: {
    fontSize: 10,
    color: COLORS.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  metricValue: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  primaryActionBtn: {
    backgroundColor: COLORS.primary,
    height: 64,
    borderRadius: 24,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 20,
    gap: 12,
    elevation: 4,
    shadowColor: COLORS.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 10,
  },
  primaryActionText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.bg,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginTop: 32,
    marginBottom: 16,
    paddingHorizontal: 4,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  seeAllText: {
    fontSize: 14,
    color: COLORS.primary,
  },
  historyCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: 24,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.05)',
  },
  historyIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 16,
  },
  historyInfo: {
    flex: 1,
  },
  historyTime: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  historyDate: {
    fontSize: 12,
    color: COLORS.textMuted,
    marginTop: 2,
  },
  historyStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusLabel: {
    fontSize: 13,
    fontWeight: '500',
  },
  tabBar: {
    position: 'absolute',
    bottom: 0,
    width: width,
    height: 90,
    backgroundColor: 'rgba(15, 23, 42, 0.95)',
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.1)',
  },
  tabItem: {
    alignItems: 'center',
    gap: 4,
  },
  tabLabel: {
    fontSize: 10,
    fontWeight: '500',
  }
});
