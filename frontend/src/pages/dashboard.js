import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import Logo from "@/components/Logo";
import axios from "axios";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

export default function Dashboard() {
  const [active, setActive] = useState("Accueil");
  const [user, setUser] = useState(null);
  const [todayQuests, setTodayQuests] = useState([]);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem("token");
      const userData = localStorage.getItem("user");
      
      if (!token || !userData) {
        router.push("/login");
        return;
      }
      
      setUser(JSON.parse(userData));
      fetchData(token);
    }
  }, [router]);

  const fetchData = async (token) => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      
      // Fetch today's quests
      const questsResponse = await axios.get(`${BACKEND_URL}/api/user-quests/today`, { headers });
      setTodayQuests(questsResponse.data);
      
      // Fetch dashboard stats
      const statsResponse = await axios.get(`${BACKEND_URL}/api/dashboard/stats`, { headers });
      setDashboardStats(statsResponse.data);
      
    } catch (error) {
      console.error("Error fetching data:", error);
      if (error.response?.status === 401) {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        router.push("/login");
      }
    } finally {
      setLoading(false);
    }
  };

  const completeQuest = async (questId) => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      await axios.post(`${BACKEND_URL}/api/user-quests/${questId}/complete`, {}, { headers });
      
      // Refresh data
      fetchData(token);
    } catch (error) {
      console.error("Error completing quest:", error);
    }
  };

  const handleLogout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
    }
    router.push("/login");
  };

  const handleNavigation = (item) => {
    if (item === "Déconnexion") {
      handleLogout();
    } else {
      setActive(item);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Chargement...</div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <aside className="w-64 bg-[var(--color-primary)] text-white flex flex-col p-6">
        <div className="flex items-center mb-10">
          <Logo className="h-8 mr-3" />
          <span className="font-bold text-lg">Énergie & Bien-être™</span>
        </div>
        <nav className="flex flex-col space-y-4">
          {["Accueil","Quêtes","Profil","Déconnexion"].map(item=>(
            <button key={item} onClick={()=>handleNavigation(item)}
              className={`text-left px-3 py-2 rounded-md transition ${active===item?"bg-[var(--color-secondary)] text-white font-semibold":"hover:bg-[var(--color-secondary)]/70"}`}>
              {item}
            </button>
          ))}
        </nav>
        <div className="mt-auto text-sm text-gray-300">Discipline 90™ — 2025</div>
      </aside>

      <main className="flex-1 p-10">
        <h1 className="text-3xl font-bold text-[var(--color-primary)] mb-6">{active}</h1>

        {active==="Accueil" && (
          <div>
            <p className="text-gray-700 text-lg mb-6">
              Bienvenue {user?.full_name} — retrouve ton énergie en un coup d'œil ⚡
            </p>
            {dashboardStats && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-white p-6 rounded-lg shadow">
                  <h3 className="text-lg font-semibold text-[var(--color-primary)]">Quêtes du jour</h3>
                  <p className="text-3xl font-bold text-[var(--color-secondary)]">
                    {dashboardStats.today_stats.quests_completed}/{dashboardStats.today_stats.total_quests}
                  </p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                  <h3 className="text-lg font-semibold text-[var(--color-primary)]">Points gagnés</h3>
                  <p className="text-3xl font-bold text-[var(--color-secondary)]">
                    {dashboardStats.today_stats.total_points}
                  </p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                  <h3 className="text-lg font-semibold text-[var(--color-primary)]">Progression</h3>
                  <p className="text-3xl font-bold text-[var(--color-secondary)]">
                    {dashboardStats.today_stats.completion_percentage}%
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {active==="Quêtes" && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-[var(--color-secondary)]">Tes quêtes du jour</h2>
            <div className="grid gap-4">
              {todayQuests.map((quest) => (
                <div key={quest.id} className="bg-white p-6 rounded-lg shadow flex justify-between items-center">
                  <div>
                    <h3 className="font-semibold text-[var(--color-primary)]">{quest.title}</h3>
                    <p className="text-gray-600">{quest.description}</p>
                    <p className="text-sm text-[var(--color-secondary)]">
                      {quest.duration_minutes} min • {quest.points} points
                    </p>
                  </div>
                  <div>
                    {quest.status === "completed" ? (
                      <span className="px-4 py-2 bg-green-100 text-green-800 rounded-lg font-medium">
                        ✅ Terminée
                      </span>
                    ) : (
                      <button 
                        onClick={() => completeQuest(quest.id)}
                        className="px-4 py-2 bg-[var(--color-secondary)] text-white rounded-lg hover:opacity-90"
                      >
                        Terminer
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            {dashboardStats && (
              <div className="bg-white rounded-xl shadow-md p-6 mt-8">
                <h3 className="text-lg font-bold text-[var(--color-primary)] mb-4">Progression hebdomadaire</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={dashboardStats.weekly_data}>
                    <XAxis dataKey="day" /><YAxis /><Tooltip />
                    <Line type="monotone" dataKey="valeur" stroke="#3FB28C" strokeWidth={3} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}

        {active==="Profil" && user && (
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="space-y-4">
              <div>
                <label className="font-semibold text-[var(--color-primary)]">Nom :</label>
                <p className="text-gray-700">{user.full_name}</p>
              </div>
              <div>
                <label className="font-semibold text-[var(--color-primary)]">Email :</label>
                <p className="text-gray-700">{user.email}</p>
              </div>
              <div>
                <label className="font-semibold text-[var(--color-primary)]">Métier :</label>
                <p className="text-gray-700 capitalize">{user.profession}</p>
              </div>
              <div>
                <label className="font-semibold text-[var(--color-primary)]">Membre depuis :</label>
                <p className="text-gray-700">{new Date(user.created_at).toLocaleDateString('fr-FR')}</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}