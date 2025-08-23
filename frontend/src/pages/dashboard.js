import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import Logo from "@/components/Logo";
import axios from "axios";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

// Function to get URL parameters
function getUrlParameter(name) {
  name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
  const regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
  const results = regex.exec(location.search);
  return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}

// Function to poll payment status
async function pollPaymentStatus(sessionId, attempts = 0) {
  const maxAttempts = 5;
  const pollInterval = 2000; // 2 seconds

  if (attempts >= maxAttempts) {
    return { status: 'timeout' };
  }

  try {
    const token = localStorage.getItem("token");
    const response = await axios.get(`${BACKEND_URL}/api/payments/checkout/status/${sessionId}`, {
      headers: { Authorization: `Bearer ${token}` }
    });

    if (response.data.payment_status === 'paid') {
      return { status: 'success' };
    } else if (response.data.status === 'expired') {
      return { status: 'expired' };
    }

    // If payment is still pending, continue polling
    await new Promise(resolve => setTimeout(resolve, pollInterval));
    return await pollPaymentStatus(sessionId, attempts + 1);
  } catch (error) {
    console.error('Error checking payment status:', error);
    return { status: 'error' };
  }
}

export default function Dashboard() {
  const [active, setActive] = useState("Accueil");
  const [user, setUser] = useState(null);
  const [todayQuests, setTodayQuests] = useState([]);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState(null);
  const router = useRouter();

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem("token");
      const userData = localStorage.getItem("user");
      
      if (!token || !userData) {
        router.push("/login");
        return;
      }
      
      const parsedUser = JSON.parse(userData);
      setUser(parsedUser);

      // Check if returning from Stripe payment
      const sessionId = getUrlParameter('session_id');
      const purchaseStatus = getUrlParameter('purchase');
      
      if (sessionId && purchaseStatus === 'success') {
        setPaymentStatus('checking');
        pollPaymentStatus(sessionId).then(result => {
          if (result.status === 'success') {
            setPaymentStatus('success');
            // Update user data to reflect paid access
            const updatedUser = { ...parsedUser, has_paid_access: true };
            localStorage.setItem("user", JSON.stringify(updatedUser));
            setUser(updatedUser);
            // Clean URL
            window.history.replaceState({}, document.title, "/dashboard");
          } else {
            setPaymentStatus('failed');
          }
        });
      }
      
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
      } else if (error.response?.status === 403) {
        // User doesn't have paid access
        console.log("Paid access required");
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
      setSidebarOpen(false); // Close mobile menu after selection
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Chargement...</div>
      </div>
    );
  }

  // Payment success banner
  const PaymentSuccessBanner = () => {
    if (paymentStatus === 'checking') {
      return (
        <div className="bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-4 m-4 rounded">
          <p className="font-medium">🔄 Vérification du paiement en cours...</p>
        </div>
      );
    }
    
    if (paymentStatus === 'success') {
      return (
        <div className="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 m-4 rounded">
          <p className="font-medium">🎉 Paiement réussi ! Bienvenue dans Énergie & Bien-être™</p>
          <p className="text-sm mt-1">Vous avez maintenant accès à toutes les fonctionnalités.</p>
        </div>
      );
    }

    if (paymentStatus === 'failed') {
      return (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 m-4 rounded">
          <p className="font-medium">❌ Problème avec le paiement</p>
          <p className="text-sm mt-1">Veuillez contacter le support si le problème persiste.</p>
        </div>
      );
    }

    return null;
  };

  // Access required screen
  if (user && !user.has_paid_access) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full text-center">
          <Logo className="h-12 mx-auto mb-6" />
          <h1 className="text-2xl font-bold text-[var(--color-primary)] mb-4">
            Accès Premium Requis
          </h1>
          <p className="text-gray-600 mb-6">
            Pour accéder aux fonctionnalités complètes d'Énergie & Bien-être™, un accès premium est nécessaire.
          </p>
          <div className="space-y-4">
            <button 
              onClick={() => router.push('/pricing')}
              className="btn w-full"
            >
              Débloquer l'accès - 39€
            </button>
            <button 
              onClick={handleLogout}
              className="w-full px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Se déconnecter
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Mobile menu button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-[var(--color-primary)] text-white rounded-md"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Sidebar */}
      <aside className={`${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      } lg:translate-x-0 fixed lg:static inset-y-0 left-0 z-40 w-64 bg-[var(--color-primary)] text-white flex flex-col p-6 transition-transform duration-300 ease-in-out`}>
        
        {/* Close button for mobile */}
        <button
          onClick={() => setSidebarOpen(false)}
          className="lg:hidden absolute top-4 right-4 text-white"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="flex items-center mb-10 mt-8 lg:mt-0">
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
        <div className="mt-auto text-sm text-gray-300">par Discipline-90 — 2025</div>
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-30"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <main className="flex-1 p-4 lg:p-10 pt-16 lg:pt-10">
        <PaymentSuccessBanner />
        
        <h1 className="text-2xl lg:text-3xl font-bold text-[var(--color-primary)] mb-6">{active}</h1>

        {active==="Accueil" && (
          <div>
            <p className="text-gray-700 text-base lg:text-lg mb-6">
              Bienvenue {user?.full_name} — retrouve ton énergie en un coup d'œil ⚡
            </p>
            {dashboardStats && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 lg:gap-6 mb-8">
                <div className="bg-white p-4 lg:p-6 rounded-lg shadow">
                  <h3 className="text-base lg:text-lg font-semibold text-[var(--color-primary)]">Quêtes du jour</h3>
                  <p className="text-2xl lg:text-3xl font-bold text-[var(--color-secondary)]">
                    {dashboardStats.today_stats.quests_completed}/{dashboardStats.today_stats.total_quests}
                  </p>
                </div>
                <div className="bg-white p-4 lg:p-6 rounded-lg shadow">
                  <h3 className="text-base lg:text-lg font-semibold text-[var(--color-primary)]">Points gagnés</h3>
                  <p className="text-2xl lg:text-3xl font-bold text-[var(--color-secondary)]">
                    {dashboardStats.today_stats.total_points}
                  </p>
                </div>
                <div className="bg-white p-4 lg:p-6 rounded-lg shadow">
                  <h3 className="text-base lg:text-lg font-semibold text-[var(--color-primary)]">Progression</h3>
                  <p className="text-2xl lg:text-3xl font-bold text-[var(--color-secondary)]">
                    {dashboardStats.today_stats.completion_percentage}%
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {active==="Quêtes" && (
          <div className="space-y-6">
            <h2 className="text-lg lg:text-xl font-semibold text-[var(--color-secondary)]">Tes quêtes du jour</h2>
            <div className="grid gap-4">
              {todayQuests.map((quest) => (
                <div key={quest.id} className="bg-white p-4 lg:p-6 rounded-lg shadow flex flex-col lg:flex-row justify-between lg:items-center">
                  <div className="mb-4 lg:mb-0">
                    <h3 className="font-semibold text-[var(--color-primary)]">{quest.title}</h3>
                    <p className="text-gray-600 text-sm lg:text-base">{quest.description}</p>
                    <p className="text-sm text-[var(--color-secondary)]">
                      {quest.points_reward} points
                    </p>
                  </div>
                  <div className="flex-shrink-0">
                    {quest.status === "done" ? (
                      <span className="px-4 py-2 bg-green-100 text-green-800 rounded-lg font-medium text-sm">
                        ✅ Terminée
                      </span>
                    ) : (
                      <button 
                        onClick={() => completeQuest(quest.id)}
                        className="w-full lg:w-auto px-4 py-2 bg-[var(--color-secondary)] text-white rounded-lg hover:opacity-90"
                      >
                        Terminer
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            {dashboardStats && (
              <div className="bg-white rounded-xl shadow-md p-4 lg:p-6 mt-8">
                <h3 className="text-base lg:text-lg font-bold text-[var(--color-primary)] mb-4">Progression hebdomadaire</h3>
                <div className="h-64 lg:h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={dashboardStats.weekly_data}>
                      <XAxis dataKey="day" className="text-xs lg:text-sm" />
                      <YAxis className="text-xs lg:text-sm" />
                      <Tooltip />
                      <Line type="monotone" dataKey="valeur" stroke="#3FB28C" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>
        )}

        {active==="Profil" && user && (
          <div className="bg-white p-4 lg:p-6 rounded-lg shadow">
            <div className="space-y-4">
              <div>
                <label className="font-semibold text-[var(--color-primary)]">Nom :</label>
                <p className="text-gray-700">{user.full_name}</p>
              </div>
              <div>
                <label className="font-semibold text-[var(--color-primary)]">Email :</label>
                <p className="text-gray-700 break-words">{user.email}</p>
              </div>
              <div>
                <label className="font-semibold text-[var(--color-primary)]">Métier :</label>
                <p className="text-gray-700 capitalize">{user.profession}</p>
              </div>
              <div>
                <label className="font-semibold text-[var(--color-primary)]">Statut :</label>
                <p className="text-gray-700">
                  {user.has_paid_access ? (
                    <span className="text-green-600 font-medium">✅ Accès Premium</span>
                  ) : (
                    <span className="text-orange-600 font-medium">⏳ Accès Limité</span>
                  )}
                </p>
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