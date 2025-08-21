import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, useLocation, useNavigate } from "react-router-dom";
import axios from "axios";
import "./App.css";

// Import shadcn components
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Progress } from "./components/ui/progress";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Slider } from "./components/ui/slider";
import { Separator } from "./components/ui/separator";

// Lucide icons
import { 
  Heart, Droplets, Moon, Activity, Brain, Star, Trophy, 
  Target, CheckCircle, Play, User, Settings, LogOut,
  ArrowRight, Sparkles, Zap, Shield, Clock, Users
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Utils
const getUrlParameter = (name) => {
  name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
  const regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
  const results = regex.exec(window.location.search);
  return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
};

// Landing Page Component
const LandingPage = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedProfession, setSelectedProfession] = useState('');
  const [professions, setProfessions] = useState([]);

  useEffect(() => {
    // Charger les professions
    const loadProfessions = async () => {
      try {
        const response = await axios.get(`${API}/professions`);
        setProfessions(response.data);
      } catch (err) {
        console.error('Error loading professions:', err);
      }
    };
    
    loadProfessions();
  }, []);

  const handlePayment = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API}/checkout/session`, {
        origin_url: window.location.origin
      });
      
      if (response.data.url) {
        window.location.href = response.data.url;
      }
    } catch (err) {
      setError('Erreur lors de la création du paiement');
      console.error('Payment error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-green-50">
      {/* Header */}
      <header className="container mx-auto px-4 py-6">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <div className="w-12 h-12 bg-gradient-to-r from-slate-800 to-emerald-600 rounded-lg flex items-center justify-center border border-slate-200 shadow-sm">
                <span className="text-white font-bold text-lg">E&B</span>
              </div>
            </div>
            <div>
              <span className="text-xl font-bold text-slate-800">Énergie & Bien-être™</span>
              <div className="text-xs text-slate-600">par Discipline 90™</div>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-5xl font-bold text-slate-800 mb-6">
            Votre dose de récupération en 8 minutes
            <span className="block text-emerald-600 mt-2">pensée pour les soignants</span>
          </h1>
          
          <p className="text-xl text-slate-600 mb-8 max-w-2xl mx-auto">
            Une app simple, apaisante et gamifiée pour retrouver énergie et équilibre, 
            même avec des horaires décalés.
          </p>

          {/* Sélecteur de profession */}
          <div className="max-w-md mx-auto mb-8">
            <Label className="block text-left mb-3 text-slate-700 font-medium">
              Choisissez votre métier
            </Label>
            <select 
              value={selectedProfession}
              onChange={(e) => setSelectedProfession(e.target.value)}
              className="w-full p-4 border border-slate-200 rounded-lg bg-white text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            >
              <option value="">Sélectionnez votre profession...</option>
              {professions.map((prof) => (
                <option key={prof.slug} value={prof.slug}>
                  {prof.icon} {prof.label}
                </option>
              ))}
              <option value="autre">Autre (préciser)</option>
            </select>
          </div>

          <Button 
            size="lg" 
            className="px-8 py-4 text-lg bg-emerald-600 hover:bg-emerald-700"
            onClick={handlePayment}
            disabled={isLoading}
          >
            {isLoading ? 'Chargement...' : 'Commencer maintenant'}
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
          
          {error && (
            <p className="text-red-500 mt-4">{error}</p>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-slate-800 mb-4">Fonctionnalités clés</h2>
          <p className="text-slate-600 max-w-2xl mx-auto">
            Des outils pensés pour s'intégrer naturellement dans votre quotidien de soignant
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <Zap className="h-8 w-8 text-emerald-600 mb-2" />
              <CardTitle>Jauge d'énergie du jour</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600">Visualisez votre niveau d'énergie calculé selon vos habitudes</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Target className="h-8 w-8 text-emerald-600 mb-2" />
              <CardTitle>Quêtes & habitudes simples</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600">Objectifs quotidiens adaptés à vos contraintes horaires</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Star className="h-8 w-8 text-emerald-600 mb-2" />
              <CardTitle>Skill tree bien-être</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600">Progression gamifiée à travers 5 branches de développement</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Brain className="h-8 w-8 text-emerald-600 mb-2" />
              <CardTitle>Bibliothèque express</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600">Recettes, étirements et conseils rapides pour vos pauses</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Sparkles className="h-8 w-8 text-emerald-600 mb-2" />
              <CardTitle>Ambiances immersives</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600">Thèmes visuels et sonores pour favoriser la détente</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Trophy className="h-8 w-8 text-emerald-600 mb-2" />
              <CardTitle>Badges & niveaux</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600">Système de récompenses pour maintenir la motivation</p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* How it Works */}
      <section className="bg-white py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-slate-800 mb-12">Comment ça marche</h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Settings className="h-8 w-8 text-emerald-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">1. Choisissez vos objectifs</h3>
              <p className="text-slate-600">Définissez vos objectifs d'hydratation, sommeil et activité en 2 minutes</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="h-8 w-8 text-emerald-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">2. Cochez vos habitudes</h3>
              <p className="text-slate-600">Suivez vos progrès quotidiens et terminez votre quête du jour</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Trophy className="h-8 w-8 text-emerald-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">3. Progressez de niveau</h3>
              <p className="text-slate-600">Gagnez des badges, montez de niveau et améliorez votre énergie</p>
            </div>
          </div>
        </div>
      </section>

      {/* Results Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-slate-800 mb-4">Résultats attendus</h2>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-4xl mx-auto">
          <Card className="text-center">
            <CardContent className="pt-6">
              <Droplets className="h-10 w-10 text-blue-500 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Hydratation régulière</h3>
              <p className="text-sm text-slate-600">Maintenez votre niveau d'énergie tout au long de la journée</p>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardContent className="pt-6">
              <Moon className="h-10 w-10 text-indigo-500 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Sommeil de qualité</h3>
              <p className="text-sm text-slate-600">Récupérez mieux entre vos gardes</p>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardContent className="pt-6">
              <Brain className="h-10 w-10 text-emerald-500 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Sérénité au travail</h3>
              <p className="text-sm text-slate-600">Gérez mieux le stress des situations intenses</p>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardContent className="pt-6">
              <Activity className="h-10 w-10 text-orange-500 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Mouvement quotidien</h3>
              <p className="text-sm text-slate-600">Maintenez votre forme physique malgré les horaires</p>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardContent className="pt-6">
              <Star className="h-10 w-10 text-yellow-500 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Motivation durable</h3>
              <p className="text-sm text-slate-600">Le système de récompenses maintient l'engagement</p>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardContent className="pt-6">
              <Shield className="h-10 w-10 text-purple-500 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Résilience renforcée</h3>
              <p className="text-sm text-slate-600">Développez votre capacité d'adaptation</p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Pricing */}
      <section className="bg-emerald-50 py-16">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-slate-800 mb-4">Tarif simple</h2>
          
          <Card className="max-w-md mx-auto">
            <CardHeader>
              <CardTitle className="text-2xl">Accès complet</CardTitle>
              <CardDescription>Toutes les fonctionnalités incluses</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-emerald-600 mb-4">39€</div>
              <p className="text-slate-600 mb-6">Paiement unique • Mises à jour incluses</p>
              
              <Button 
                size="lg" 
                className="w-full bg-emerald-600 hover:bg-emerald-700"
                onClick={handlePayment}
                disabled={isLoading}
              >
                {isLoading ? 'Chargement...' : 'Obtenir l\'accès'}
              </Button>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* FAQ */}
      <section className="container mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-center text-slate-800 mb-12">Questions fréquentes</h2>
        
        <div className="max-w-2xl mx-auto space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Ai-je besoin de Notion ?</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600">Non, c'est une webapp complète qui fonctionne dans votre navigateur.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Combien de temps par jour ?</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600">5 à 10 minutes suffisent pour suivre vos habitudes et compléter votre quête quotidienne.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Fonctionne hors ligne ?</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600">L'app fonctionne en PWA avec cache partiel pour une utilisation hors connexion limitée.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Remboursement possible ?</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600">Oui, remboursement intégral sous 14 jours si l'accès n'a pas été activé.</p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-800 text-white py-8">
        <div className="container mx-auto px-4 text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <Heart className="h-6 w-6 text-emerald-500" />
            <span className="text-lg font-semibold">Énergie & Bien-être™ par Discipline 90™</span>
          </div>
          <p className="text-slate-400 text-sm">
            Contact • Mentions légales • CGV • Politique de confidentialité
          </p>
        </div>
      </footer>
    </div>
  );
};

// Dashboard Component
const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [professionProgress, setProfessionProgress] = useState(null);

  // Mock user ID for demo
  const userId = "demo-user-123";

  useEffect(() => {
    const initializeUser = async () => {
      try {
        // Try to get user by demo email
        let userData;
        try {
          const response = await axios.get(`${API}/users/email/demo@example.com`);
          userData = response.data;
        } catch (error) {
          // Create demo user if doesn't exist
          const createResponse = await axios.post(`${API}/users`, {
            email: "demo@example.com",
            name: "Utilisateur Demo",
            profession_slug: "infirmier"  // Default profession for demo
          });
          userData = createResponse.data;
        }
        
        setUser(userData);
        
        // Get dashboard data
        const dashResponse = await axios.get(`${API}/dashboard/${userData.id}`);
        setDashboardData(dashResponse.data);
        
      } catch (error) {
        console.error('Error loading dashboard:', error);
      } finally {
        setLoading(false);
      }
    };

    initializeUser();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Chargement de votre tableau de bord...</p>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-600">Erreur lors du chargement des données</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <div className="w-8 h-8 bg-gradient-to-r from-slate-800 to-emerald-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">E&B</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-800">Énergie & Bien-être</h1>
                <div className="flex items-center space-x-2">
                  <p className="text-sm text-slate-600">Bonjour {user?.name || 'Soignant'} !</p>
                  {user?.profession_icon && user?.profession_label && (
                    <Badge variant="outline" className="text-xs">
                      {user.profession_icon} {user.profession_label}
                    </Badge>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="outline" className="px-3 py-1">
                <Star className="h-4 w-4 mr-1" />
                Niveau {dashboardData.level}
              </Badge>
              <Badge variant="outline" className="px-3 py-1">
                <Trophy className="h-4 w-4 mr-1" />
                {dashboardData.xp_total} XP
              </Badge>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left Column - Energy & Quest */}
          <div className="lg:col-span-2 space-y-6">
            {/* Energy Gauge */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Zap className="h-5 w-5 text-emerald-600 mr-2" />
                  Énergie du jour
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center mb-4">
                  <div className="text-4xl font-bold text-emerald-600 mb-2">
                    {dashboardData.energy_percentage}%
                  </div>
                  <Progress value={dashboardData.energy_percentage} className="w-full h-3" />
                </div>
                <p className="text-sm text-slate-600 text-center">
                  {dashboardData.energy_percentage >= 70 
                    ? "Excellente énergie ! Continuez comme ça !" 
                    : "Quelques ajustements et vous allez briller !"
                  }
                </p>
              </CardContent>
            </Card>

            {/* Daily Quest */}
            {dashboardData.daily_quest && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Target className="h-5 w-5 text-orange-500 mr-2" />
                    Quête du jour
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold mb-1">{dashboardData.daily_quest.title}</h3>
                      <p className="text-sm text-slate-600">{dashboardData.daily_quest.description}</p>
                      <Badge className="mt-2">+{dashboardData.daily_quest.points_reward} XP</Badge>
                    </div>
                    <Button 
                      size="sm" 
                      variant={dashboardData.daily_quest.user_quest?.status === 'done' ? 'outline' : 'default'}
                      disabled={dashboardData.daily_quest.user_quest?.status === 'done'}
                    >
                      {dashboardData.daily_quest.user_quest?.status === 'done' ? (
                        <CheckCircle className="h-4 w-4" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Profession Quest */}
            {dashboardData.profession_quest && (
              <Card className="border-l-4 border-l-emerald-500">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <span className="mr-2">{user?.profession_icon || '🩺'}</span>
                    Quête {user?.profession_label || 'Métier'}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold mb-1">{dashboardData.profession_quest.title}</h3>
                      <p className="text-sm text-slate-600">{dashboardData.profession_quest.description}</p>
                      <Badge variant="secondary" className="mt-2">
                        +{dashboardData.profession_quest.points_reward} XP
                      </Badge>
                    </div>
                    <Button size="sm" variant="outline">
                      <Play className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Quick Habits Update */}
            <HabitsTracker 
              userId={user?.id} 
              habitLog={dashboardData.habit_log}
              userSettings={user?.settings || {}}
              onUpdate={(newData) => setDashboardData({...dashboardData, ...newData})}
            />
          </div>

          {/* Right Column - Quote, Stats & Progression */}
          <div className="space-y-6">
            {/* Daily Quote */}
            {dashboardData.quote && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Sparkles className="h-5 w-5 text-yellow-500 mr-2" />
                    Citation du jour
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <blockquote className="italic text-slate-700 mb-2">
                    "{dashboardData.quote.text}"
                  </blockquote>
                  {dashboardData.quote.author && (
                    <p className="text-sm text-slate-500">— {dashboardData.quote.author}</p>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Progression Métier */}
            {dashboardData.user_progression && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Trophy className="h-5 w-5 text-yellow-500 mr-2" />
                    Progression {user?.profession_label}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center mb-4">
                    <p className="text-sm text-slate-600 mb-2">
                      Niveau {dashboardData.user_progression.niveau_actuel || 1} / 5
                    </p>
                    <Progress 
                      value={(dashboardData.user_progression.niveau_actuel || 1) * 20} 
                      className="w-full h-2" 
                    />
                    <p className="text-xs text-slate-500 mt-1">
                      {dashboardData.user_progression.xp_total || 0} XP métier
                    </p>
                  </div>
                  <div className="text-center">
                    <Button variant="outline" size="sm" className="text-xs">
                      Voir progression complète
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Progress to Next Level */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Trophy className="h-5 w-5 text-yellow-500 mr-2" />
                  Progression générale
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center mb-4">
                  <p className="text-sm text-slate-600 mb-2">Niveau {dashboardData.level}</p>
                  <Progress 
                    value={(150 - dashboardData.xp_to_next_level) / 150 * 100} 
                    className="w-full h-2" 
                  />
                  <p className="text-xs text-slate-500 mt-1">
                    {dashboardData.xp_to_next_level} XP jusqu'au niveau {dashboardData.level + 1}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Actions rapides</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Brain className="h-4 w-4 mr-2" />
                  Respiration 2 min
                </Button>
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Activity className="h-4 w-4 mr-2" />
                  Étirements express
                </Button>
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Moon className="h-4 w-4 mr-2" />
                  Préparation sommeil
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
};

// Habits Tracker Component
const HabitsTracker = ({ userId, habitLog, userSettings, onUpdate }) => {
  const [habits, setHabits] = useState({
    water_ml: habitLog?.water_ml || 0,
    sleep_h: habitLog?.sleep_h || 0,
    nutrition_score_0_100: habitLog?.nutrition_score_0_100 || 0,
    activity_min: habitLog?.activity_min || 0,
    serenity_min: habitLog?.serenity_min || 0,
    mood_1_10: habitLog?.mood_1_10 || 5,
    stress_0_10: habitLog?.stress_0_10 || 5
  });

  const goals = {
    water_goal_ml: userSettings.water_goal_ml || 2000,
    sleep_goal_h: userSettings.sleep_goal_h || 7.5,
    activity_goal_min: userSettings.activity_goal_min || 30,
    serenity_goal_min: userSettings.serenity_goal_min || 10
  };

  const updateHabit = async (key, value) => {
    const newHabits = { ...habits, [key]: value };
    setHabits(newHabits);

    try {
      const response = await axios.put(`${API}/habits/${userId}`, { [key]: value });
      if (response.data.points_earned > 0) {
        // Show points notification (simplified)
        console.log(`+${response.data.points_earned} points gagnés !`);
      }
    } catch (error) {
      console.error('Error updating habit:', error);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Activity className="h-5 w-5 text-blue-500 mr-2" />
          Suivi des habitudes
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="physical" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="physical">Physique</TabsTrigger>
            <TabsTrigger value="mental">Mental</TabsTrigger>
          </TabsList>
          
          <TabsContent value="physical" className="space-y-4">
            {/* Hydration */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label className="flex items-center">
                  <Droplets className="h-4 w-4 text-blue-500 mr-2" />
                  Hydratation
                </Label>
                <span className="text-sm text-slate-600">
                  {habits.water_ml}ml / {goals.water_goal_ml}ml
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <Slider
                  value={[habits.water_ml]}
                  onValueChange={([value]) => updateHabit('water_ml', value)}
                  max={goals.water_goal_ml * 1.5}
                  step={250}
                  className="flex-1"
                />
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => updateHabit('water_ml', habits.water_ml + 250)}
                >
                  +250ml
                </Button>
              </div>
              <Progress 
                value={Math.min(100, (habits.water_ml / goals.water_goal_ml) * 100)} 
                className="mt-2 h-2" 
              />
            </div>

            {/* Sleep */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label className="flex items-center">
                  <Moon className="h-4 w-4 text-indigo-500 mr-2" />
                  Sommeil
                </Label>
                <span className="text-sm text-slate-600">
                  {habits.sleep_h}h / {goals.sleep_goal_h}h
                </span>
              </div>
              <Slider
                value={[habits.sleep_h]}
                onValueChange={([value]) => updateHabit('sleep_h', value)}
                max={12}
                step={0.5}
                className="mb-2"
              />
              <Progress 
                value={Math.min(100, (habits.sleep_h / goals.sleep_goal_h) * 100)} 
                className="h-2" 
              />
            </div>

            {/* Activity */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label className="flex items-center">
                  <Activity className="h-4 w-4 text-orange-500 mr-2" />
                  Activité
                </Label>
                <span className="text-sm text-slate-600">
                  {habits.activity_min}min / {goals.activity_goal_min}min
                </span>
              </div>
              <Slider
                value={[habits.activity_min]}
                onValueChange={([value]) => updateHabit('activity_min', value)}
                max={120}
                step={5}
                className="mb-2"
              />
              <Progress 
                value={Math.min(100, (habits.activity_min / goals.activity_goal_min) * 100)} 
                className="h-2" 
              />
            </div>

            {/* Nutrition */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label className="flex items-center">
                  <Heart className="h-4 w-4 text-green-500 mr-2" />
                  Nutrition
                </Label>
                <span className="text-sm text-slate-600">{habits.nutrition_score_0_100}/100</span>
              </div>
              <Slider
                value={[habits.nutrition_score_0_100]}
                onValueChange={([value]) => updateHabit('nutrition_score_0_100', value)}
                max={100}
                step={10}
                className="mb-2"
              />
              <Progress value={habits.nutrition_score_0_100} className="h-2" />
            </div>
          </TabsContent>

          <TabsContent value="mental" className="space-y-4">
            {/* Serenity */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label className="flex items-center">
                  <Brain className="h-4 w-4 text-purple-500 mr-2" />
                  Sérénité
                </Label>
                <span className="text-sm text-slate-600">
                  {habits.serenity_min}min / {goals.serenity_goal_min}min
                </span>
              </div>
              <Slider
                value={[habits.serenity_min]}
                onValueChange={([value]) => updateHabit('serenity_min', value)}
                max={60}
                step={5}
                className="mb-2"
              />
              <Progress 
                value={Math.min(100, (habits.serenity_min / goals.serenity_goal_min) * 100)} 
                className="h-2" 
              />
            </div>

            {/* Mood */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label>Humeur (1-10)</Label>
                <span className="text-sm text-slate-600">{habits.mood_1_10}/10</span>
              </div>
              <Slider
                value={[habits.mood_1_10]}
                onValueChange={([value]) => updateHabit('mood_1_10', value)}
                min={1}
                max={10}
                step={1}
                className="mb-2"
              />
              <div className="flex justify-between text-xs text-slate-500">
                <span>😟</span>
                <span>😐</span>
                <span>😊</span>
              </div>
            </div>

            {/* Stress */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label>Niveau de stress (0-10)</Label>
                <span className="text-sm text-slate-600">{habits.stress_0_10}/10</span>
              </div>
              <Slider
                value={[habits.stress_0_10]}
                onValueChange={([value]) => updateHabit('stress_0_10', value)}
                min={0}
                max={10}
                step={1}
                className="mb-2"
              />
              <div className="flex justify-between text-xs text-slate-500">
                <span>😌</span>
                <span>😐</span>
                <span>😰</span>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

// Payment Success Component
const PaymentSuccess = () => {
  const navigate = useNavigate();
  const [status, setStatus] = useState('checking');
  const sessionId = getUrlParameter('session_id');

  useEffect(() => {
    const checkPaymentStatus = async () => {
      if (!sessionId) {
        setStatus('error');
        return;
      }

      try {
        const response = await axios.get(`${API}/checkout/status/${sessionId}`);
        
        if (response.data.payment_status === 'paid') {
          setStatus('success');
        } else {
          setStatus('pending');
          // Retry after 2 seconds
          setTimeout(checkPaymentStatus, 2000);
        }
      } catch (error) {
        console.error('Payment check error:', error);
        setStatus('error');
      }
    };

    checkPaymentStatus();
  }, [sessionId]);

  if (status === 'checking' || status === 'pending') {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Card className="max-w-md w-full mx-4">
          <CardContent className="pt-6 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold mb-2">Vérification du paiement...</h2>
            <p className="text-slate-600">Merci de patienter quelques instants.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Card className="max-w-md w-full mx-4">
          <CardContent className="pt-6 text-center">
            <CheckCircle className="h-16 w-16 text-emerald-600 mx-auto mb-4" />
            <h2 className="text-2xl font-semibold text-emerald-600 mb-2">Paiement confirmé !</h2>
            <p className="text-slate-600 mb-6">
              Bienvenue dans Énergie & Bien-être pour soignants™. 
              Votre accès a été activé avec succès.
            </p>
            <Button 
              onClick={() => navigate('/app/dashboard')}
              className="w-full bg-emerald-600 hover:bg-emerald-700"
            >
              Accéder au tableau de bord
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <Card className="max-w-md w-full mx-4">
        <CardContent className="pt-6 text-center">
          <div className="h-16 w-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-red-600 text-2xl">⚠</span>
          </div>
          <h2 className="text-xl font-semibold text-red-600 mb-2">Erreur de paiement</h2>
          <p className="text-slate-600 mb-6">
            Une erreur s'est produite lors de la vérification du paiement.
          </p>
          <Button 
            onClick={() => navigate('/')}
            variant="outline"
            className="w-full"
          >
            Retour à l'accueil
          </Button>
        </CardContent>
      </Card>
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
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;