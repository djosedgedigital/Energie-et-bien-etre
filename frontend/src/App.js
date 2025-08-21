import { useState, useEffect } from "react";

import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import axios from "axios";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./components/ui/card";
import { Button } from "./components/ui/button";
import { Badge } from "./components/ui/badge";
import { Progress } from "./components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import {
  Activity,
  ArrowRight,
  Brain,
  CheckCircle,
  Droplets,
  Heart,
  Moon,
  Settings,
  Shield,
  Sparkles,
  Star,
  Target,
  Trophy,
  Zap,
  Play
} from "lucide-react";
import ProfessionQuests from "./components/ProfessionQuests";
import Admin from "./pages/Admin";
import { Toaster } from "./components/ui/toaster";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Utility
function getUrlParameter(name) {
  name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
  const regex = new RegExp("[\\?&]" + name + "=([^&#]*)");
  const results = regex.exec(window.location.search);
  return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}

// Landing Component
const LandingPage = () => {
  const [isLoading, setIsLoading] = useState(false);

  const handlePayment = async () => {
    try {
      setIsLoading(true);
      const origin = window.location.origin;
      const res = await axios.post(`${API}/checkout/session`, { origin_url: origin });
      if (res.data.url) {
        window.location.href = res.data.url;
      }
    } catch (err) {
      console.error("Payment error", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img
              alt="Énergie & Bien-être"
              src="/assets/logo-full.png"
              className="h-12 w-auto rounded-md shadow-sm border border-slate-200 bg-white object-contain"
            />
            <div>
              <h1 className="text-xl font-bold text-slate-800">Énergie & Bien-être</h1>
              <p className="text-sm text-slate-600">La récupération ludique pour soignants</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button onClick={handlePayment} className="bg-emerald-600 hover:bg-emerald-700">Obtenir l'accès</Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-12">
        <p className="text-slate-600">Bienvenue dans Énergie & Bien-être™. Faites défiler pour découvrir les fonctionnalités.</p>
      </main>
    </div>
  );
};

// Dashboard with Profession Progression + Quests
const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchProgression = async (u = user) => {
    if (!u?.profession_slug) return;
    try {
      const { data } = await axios.get(`${API}/professions/${u.profession_slug}/progression/full`, {
        params: { user_id: u.id }
      });
      setProgress(data);
    } catch (e) {
      console.warn('No progression yet');
    }
  };

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const me = await axios.get(`${API}/user/me`);
        setUser(me.data);
        if (me.data?.profession_slug) {
          await fetchProgression(me.data);
        }
      } catch (e) {
        console.error('Unable to load user', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img alt="Énergie & Bien-être" src="/assets/logo-full.png" className="h-10 w-auto" />
          </div>
        </div>
      </header>
      <div className="container mx-auto px-4 py-8 space-y-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>

        {/* Progression Card */}
        <Card>
          <CardHeader>
            <CardTitle>Progression métier</CardTitle>
            <CardDescription>
              {progress?.profession_label || user?.profession_label || 'Métier non défini'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-slate-600">Niveau {progress?.progression_niveau || 1} / {progress?.tier_max || 5}</div>
              <div className="text-sm">{typeof progress?.progression_xp === 'number' ? `${progress?.progression_xp}%` : '0%'}</div>
            </div>
            <Progress value={typeof progress?.progression_xp === 'number' ? progress?.progression_xp : 0} />
            {progress?.next_objective && (
              <div className="text-xs text-slate-500 mt-2">Prochain objectif : {progress.next_objective}</div>
            )}
          </CardContent>
        </Card>

        {/* Profession Quests */}
        {user?.profession_slug && (
          <Card>
            <CardHeader>
              <CardTitle>Quêtes recommandées — {user?.profession_label}</CardTitle>
            </CardHeader>
            <CardContent>
              <ProfessionQuests
                user={user}
                userId={user?.id}
                professionSlug={user?.profession_slug}
                refreshProgression={fetchProgression}
              />
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/app/dashboard" element={<Dashboard />} />
          <Route path="/payment/success" element={<PaymentSuccess />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </BrowserRouter>
      <Toaster />
    </div>
  );
}

function PaymentSuccess() {
  const navigate = useNavigate();
  useEffect(() => {
    const sessionId = getUrlParameter("session_id");
    if (sessionId) {
      (async () => {
        try {
          const res = await axios.get(`${API}/checkout/status/${sessionId}`);
          if (res.data?.payment_status === "paid") {
            setTimeout(() => navigate("/app/dashboard"), 1200);
          }
        } catch (e) {}
      })();
    }
  }, [navigate]);

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <Card className="max-w-md w-full">
        <CardHeader>
          <CardTitle>Paiement confirmé</CardTitle>
          <CardDescription>Redirection vers le tableau de bord…</CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}

export default App;