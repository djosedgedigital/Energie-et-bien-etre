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
  const pollInterval = 2000;

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
  const [currentQuote, setCurrentQuote] = useState("Prendre soin des autres commence par prendre soin de soi.");
  const [demoStatus, setDemoStatus] = useState(null);
  const [demoCountdown, setDemoCountdown] = useState(null);
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
            const updatedUser = { ...parsedUser, has_paid_access: true };
            localStorage.setItem("user", JSON.stringify(updatedUser));
            setUser(updatedUser);
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
      
      const questsResponse = await axios.get(`${BACKEND_URL}/api/user-quests/today`, { headers });
      setTodayQuests(questsResponse.data);
      
      const statsResponse = await axios.get(`${BACKEND_URL}/api/dashboard/stats`, { headers });
      setDashboardStats(statsResponse.data);
      
      // Check demo status
      const demoResponse = await axios.get(`${BACKEND_URL}/api/demo/status`, { headers });
      setDemoStatus(demoResponse.data);
      
      // Start countdown if demo is active
      if (demoResponse.data.has_demo && demoResponse.data.remaining_seconds > 0) {
        startDemoCountdown(demoResponse.data.remaining_seconds);
      }
      
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

  const startDemoCountdown = (seconds) => {
    setDemoCountdown(seconds);
    const interval = setInterval(() => {
      setDemoCountdown(prev => {
        if (prev <= 1) {
          clearInterval(interval);
          // Refresh data when demo expires
          const token = localStorage.getItem("token");
          if (token) fetchData(token);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const activateDemo = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      const response = await axios.post(`${BACKEND_URL}/api/demo/activate`, {}, { headers });
      
      // Refresh data to show demo features
      fetchData(token);
      
      alert(`🎉 Demo Premium activé pour 10 minutes ! Toutes les fonctionnalités sont débloquées.`);
      
    } catch (error) {
      console.error("Error activating demo:", error);
      alert("Erreur lors de l'activation de la demo. Veuillez réessayer.");
    }
  };

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const completeQuest = async (questId) => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      await axios.post(`${BACKEND_URL}/api/user-quests/${questId}/complete`, {}, { headers });
      fetchData(token);
    } catch (error) {
      console.error("Error completing quest:", error);
      if (error.response?.status === 403) {
        alert("Limite quotidienne atteinte ! Passez Premium pour un accès illimité.");
      }
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
      setSidebarOpen(false);
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

  // Freemium upgrade banner
  const FreemiumBanner = () => {
    if (user?.has_paid_access) return null;
    
    return (
      <div className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-secondary)] text-white p-4 m-4 rounded-lg shadow-lg">
        <div className="flex flex-col lg:flex-row items-center justify-between">
          <div className="mb-4 lg:mb-0">
            <h3 className="text-lg font-bold mb-2">🚀 Débloquez votre potentiel bien-être !</h3>
            <p className="text-sm opacity-90">
              Vous utilisez la version gratuite. Passez Premium pour des quêtes illimitées, statistiques avancées et plus !
            </p>
          </div>
          <button 
            onClick={() => router.push('/pricing')}
            className="bg-white text-[var(--color-primary)] px-6 py-3 rounded-lg font-bold hover:shadow-lg transition-all"
          >
            Passer Premium - 39€
          </button>
        </div>
      </div>
    );
  };

  const energyLevel = dashboardStats?.today_stats?.completion_percentage || 0;
  const getEnergyColor = (level) => {
    if (level >= 80) return "text-green-500";
    if (level >= 60) return "text-yellow-500";
    if (level >= 40) return "text-orange-500";
    return "text-red-500";
  };

  const getEnergyEmoji = (level) => {
    if (level >= 80) return "⚡";
    if (level >= 60) return "🔋";
    if (level >= 40) return "🟡";
    return "🔴";
  };

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
          {["Accueil","Quêtes","Mental","Bibliothèque","Profil","Déconnexion"].map(item=>(
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
        <FreemiumBanner />
        
        <h1 className="text-2xl lg:text-3xl font-bold text-[var(--color-primary)] mb-6">{active}</h1>

        {active==="Accueil" && (
          <div className="space-y-6">
            {/* Citation du jour */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-6 text-center">
              <h3 className="text-lg font-bold text-[var(--color-primary)] mb-2">💭 Citation du jour</h3>
              <p className="text-gray-700 italic">"{currentQuote}"</p>
            </div>

            {/* Jauge d'énergie principale */}
            <div className="bg-white p-6 rounded-lg shadow-lg text-center">
              <h2 className="text-xl font-bold text-[var(--color-primary)] mb-4">
                {getEnergyEmoji(energyLevel)} Votre énergie aujourd'hui
              </h2>
              <div className="relative w-32 h-32 mx-auto mb-4">
                <div className="w-32 h-32 rounded-full border-8 border-gray-200 relative">
                  <div 
                    className="absolute top-0 left-0 w-32 h-32 rounded-full border-8 border-transparent transition-all duration-1000"
                    style={{
                      borderTopColor: energyLevel >= 25 ? '#3FB28C' : 'transparent',
                      borderRightColor: energyLevel >= 50 ? '#3FB28C' : 'transparent',
                      borderBottomColor: energyLevel >= 75 ? '#3FB28C' : 'transparent',
                      borderLeftColor: energyLevel >= 100 ? '#3FB28C' : 'transparent',
                      transform: `rotate(${(energyLevel / 100) * 360}deg)`
                    }}
                  ></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className={`text-3xl font-bold ${getEnergyColor(energyLevel)}`}>
                      {energyLevel}%
                    </span>
                  </div>
                </div>
              </div>
              <p className="text-gray-600">
                {energyLevel >= 80 ? "Excellente énergie ! Vous êtes au top 🌟" :
                 energyLevel >= 60 ? "Bonne énergie, continuez comme ça ! 💪" :
                 energyLevel >= 40 ? "Énergie modérée, prenez soin de vous 🌸" :
                 "Votre corps a besoin de récupération 🌿"}
              </p>
            </div>

            {/* Statistiques du jour */}
            {dashboardStats && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 lg:gap-6">
                <div className="bg-white p-4 lg:p-6 rounded-lg shadow">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-base lg:text-lg font-semibold text-[var(--color-primary)]">Quêtes du jour</h3>
                      <p className="text-2xl lg:text-3xl font-bold text-[var(--color-secondary)]">
                        {dashboardStats.today_stats.quests_completed}/{dashboardStats.today_stats.total_quests}
                      </p>
                    </div>
                    <div className="text-3xl">🎯</div>
                  </div>
                  {!user?.has_paid_access && (
                    <p className="text-xs text-orange-600 mt-1">Version gratuite: 2 max/jour</p>
                  )}
                </div>
                
                <div className="bg-white p-4 lg:p-6 rounded-lg shadow">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-base lg:text-lg font-semibold text-[var(--color-primary)]">Points XP</h3>
                      <p className="text-2xl lg:text-3xl font-bold text-[var(--color-secondary)]">
                        {dashboardStats.today_stats.total_points}
                      </p>
                    </div>
                    <div className="text-3xl">⭐</div>
                  </div>
                  {!user?.has_paid_access && (
                    <p className="text-xs text-orange-600 mt-1">Limité en version gratuite</p>
                  )}
                </div>
                
                <div className="bg-white p-4 lg:p-6 rounded-lg shadow">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-base lg:text-lg font-semibold text-[var(--color-primary)]">Niveau</h3>
                      <p className="text-2xl lg:text-3xl font-bold text-[var(--color-secondary)]">
                        {Math.floor(dashboardStats.today_stats.total_points / 100) + 1}
                      </p>
                    </div>
                    <div className="text-3xl">🏆</div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                    <div 
                      className="bg-[var(--color-secondary)] h-2 rounded-full transition-all duration-500" 
                      style={{width: `${(dashboardStats.today_stats.total_points % 100)}%`}}
                    ></div>
                  </div>
                </div>
              </div>
            )}

            {/* Objectifs rapides */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-bold text-[var(--color-primary)] mb-4">🎯 Objectifs rapides</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl mb-2">💧</div>
                  <p className="text-sm font-medium">Hydratation</p>
                  <p className="text-xs text-gray-600">2L d'eau</p>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl mb-2">😴</div>
                  <p className="text-sm font-medium">Sommeil</p>
                  <p className="text-xs text-gray-600">8h de repos</p>
                </div>
                <div className="text-center p-4 bg-orange-50 rounded-lg">
                  <div className="text-2xl mb-2">🚶</div>
                  <p className="text-sm font-medium">Activité</p>
                  <p className="text-xs text-gray-600">30 min/jour</p>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl mb-2">🧘</div>
                  <p className="text-sm font-medium">Sérénité</p>
                  <p className="text-xs text-gray-600">10 min/jour</p>
                </div>
              </div>
            </div>

            {/* Encouragement freemium */}
            {!user?.has_paid_access && (
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-6 text-center">
                <h3 className="text-lg font-bold text-[var(--color-primary)] mb-2">
                  🌟 Découvrez toutes les fonctionnalités !
                </h3>
                <p className="text-gray-600 mb-4">
                  Quêtes illimitées • Skill Tree • Journal personnel • Ambiances sonores • Bibliothèque complète
                </p>
                <button 
                  onClick={() => router.push('/pricing')}
                  className="btn"
                >
                  Voir toutes les fonctionnalités
                </button>
              </div>
            )}
          </div>
        )}

        {active==="Quêtes" && (
          <div className="space-y-6">
            {/* Limite freemium */}
            {!user?.has_paid_access && (
              <div className="bg-orange-50 border-l-4 border-orange-400 text-orange-700 p-4 rounded">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">
                      🎯 Version gratuite : {Math.max(0, 2 - todayQuests.filter(q => q.status === "done").length)} complétion{Math.max(0, 2 - todayQuests.filter(q => q.status === "done").length) !== 1 ? 's' : ''} restante{Math.max(0, 2 - todayQuests.filter(q => q.status === "done").length) !== 1 ? 's' : ''} aujourd'hui
                    </p>
                    <p className="text-sm mt-1">Passez Premium pour des complétions illimitées !</p>
                  </div>
                  {todayQuests.filter(q => q.status === "done").length >= 2 && (
                    <button 
                      onClick={() => router.push('/pricing')}
                      className="ml-4 bg-orange-500 text-white px-4 py-2 rounded hover:bg-orange-600 text-sm"
                    >
                      Upgrader
                    </button>
                  )}
                </div>
              </div>
            )}
            
            <h2 className="text-lg lg:text-xl font-semibold text-[var(--color-secondary)]">Tes quêtes du jour</h2>
            
            <div className="grid gap-4">
              {todayQuests.map((quest, index) => (
                <div key={quest.id} className="bg-white p-4 lg:p-6 rounded-lg shadow flex flex-col lg:flex-row justify-between lg:items-center">
                  <div className="mb-4 lg:mb-0">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-semibold text-[var(--color-primary)]">{quest.title}</h3>
                      {!user?.has_paid_access && index < 2 && (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">Gratuit</span>
                      )}
                      {!user?.has_paid_access && index >= 2 && (
                        <span className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded">Premium</span>
                      )}
                    </div>
                    <p className="text-gray-600 text-sm lg:text-base">{quest.description}</p>
                    <p className="text-sm text-[var(--color-secondary)]">
                      {quest.points_reward} points XP
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
            
            {/* Zone premium */}
            {!user?.has_paid_access && (
              <div className="bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                <div className="text-4xl mb-4">🔒</div>
                <h3 className="text-lg font-bold text-gray-700 mb-2">Plus de quêtes disponibles en Premium</h3>
                <p className="text-gray-600 mb-4">
                  Débloquez des quêtes personnalisées, des défis hebdomadaires et bien plus !
                </p>
                <button 
                  onClick={() => router.push('/pricing')}
                  className="btn"
                >
                  Passer Premium
                </button>
              </div>
            )}
          </div>
        )}

        {active==="Mental" && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-bold text-[var(--color-primary)] mb-4">🧘 Espace Mental</h3>
              
              {!user?.has_paid_access ? (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">🔒</div>
                  <h4 className="text-xl font-bold text-gray-700 mb-2">Fonctionnalité Premium</h4>
                  <p className="text-gray-600 mb-6">
                    Journal personnel, suivi de l'humeur, exercices de respiration guidée
                  </p>
                  <button 
                    onClick={() => router.push('/pricing')}
                    className="btn"
                  >
                    Débloquer l'Espace Mental
                  </button>
                </div>
              ) : (
                <p className="text-gray-600">Journal, humeur et exercices de respiration disponibles ici.</p>
              )}
            </div>
          </div>
        )}

        {active==="Bibliothèque" && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-bold text-[var(--color-primary)] mb-4">📚 Bibliothèque Bien-être</h3>
              
              {!user?.has_paid_access ? (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">🔒</div>
                  <h4 className="text-xl font-bold text-gray-700 mb-2">Fonctionnalité Premium</h4>
                  <p className="text-gray-600 mb-6">
                    Recettes express, étirements guidés, playlists de relaxation, fiches 5-min bien-être
                  </p>
                  <button 
                    onClick={() => router.push('/pricing')}
                    className="btn"
                  >
                    Accéder à la Bibliothèque
                  </button>
                </div>
              ) : (
                <p className="text-gray-600">Bibliothèque complète disponible pour les membres Premium.</p>
              )}
            </div>
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
                    <span className="text-orange-600 font-medium">⭐ Version Gratuite</span>
                  )}
                </p>
              </div>
              <div>
                <label className="font-semibold text-[var(--color-primary)]">Membre depuis :</label>
                <p className="text-gray-700">{new Date(user.created_at).toLocaleDateString('fr-FR')}</p>
              </div>
              
              {!user.has_paid_access && (
                <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg text-center">
                  <h4 className="font-bold text-[var(--color-primary)] mb-2">🚀 Passez Premium !</h4>
                  <p className="text-sm text-gray-600 mb-3">
                    Débloquez toutes les fonctionnalités pour seulement 39€
                  </p>
                  <button 
                    onClick={() => router.push('/pricing')}
                    className="btn"
                  >
                    Upgrade maintenant
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}