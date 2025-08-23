import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import Logo from "@/components/Logo";
import Link from "next/link";
import axios from "axios";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

export default function Pricing() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [user, setUser] = useState(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const userData = localStorage.getItem("user");
      if (userData) {
        setUser(JSON.parse(userData));
      }
    }
  }, []);

  const handlePurchase = async () => {
    if (!user) {
      router.push("/login");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const token = localStorage.getItem("token");
      const originUrl = window.location.origin;

      const response = await axios.post(`${BACKEND_URL}/api/payments/checkout/session`, {
        origin_url: originUrl
      }, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      // Redirect to Stripe Checkout
      if (response.data.url) {
        window.location.href = response.data.url;
      }
    } catch (error) {
      console.error("Payment error:", error);
      setError(error.response?.data?.detail || "Erreur lors du paiement");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b bg-white">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <Logo className="h-10" showFullName={true} />
          <div className="space-x-4">
            {user ? (
              <Link href="/dashboard" className="text-[var(--color-primary)] hover:text-[var(--color-secondary)]">
                Tableau de bord
              </Link>
            ) : (
              <>
                <Link href="/login" className="text-[var(--color-primary)] hover:text-[var(--color-secondary)]">
                  Connexion
                </Link>
                <Link href="/register" className="btn text-sm">
                  S'inscrire
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-16 lg:py-24 bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-secondary)] text-white">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-3xl lg:text-5xl font-bold mb-6">
            Votre dose de récupération en 8 minutes
          </h1>
          <p className="text-lg lg:text-xl mb-8 max-w-3xl mx-auto opacity-90">
            Pensée pour les soignants. Une app simple, apaisante et gamifiée pour retrouver énergie et équilibre, même avec des horaires décalés.
          </p>
          <button 
            onClick={handlePurchase}
            disabled={loading}
            className="bg-white text-[var(--color-primary)] px-8 py-4 rounded-lg font-bold text-lg hover:shadow-lg transition-all duration-300 disabled:opacity-50"
          >
            {loading ? "Chargement..." : "Commencer maintenant"}
          </button>
          {error && (
            <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded max-w-md mx-auto">
              {error}
            </div>
          )}
        </div>
      </section>

      {/* Problem/Solution */}
      <section className="py-16 lg:py-20">
        <div className="container mx-auto px-4">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-2xl lg:text-3xl font-bold text-[var(--color-primary)] mb-6">
                Les défis du quotidien soignant
              </h2>
              <ul className="space-y-4 text-gray-700">
                <li className="flex items-start">
                  <span className="text-red-500 mr-3">❌</span>
                  <span>Fatigue accumulée et stress constant</span>
                </li>
                <li className="flex items-start">
                  <span className="text-red-500 mr-3">❌</span>
                  <span>Horaires décalés perturbant le sommeil</span>
                </li>
                <li className="flex items-start">
                  <span className="text-red-500 mr-3">❌</span>
                  <span>Peu de temps pour prendre soin de soi</span>
                </li>
                <li className="flex items-start">
                  <span className="text-red-500 mr-3">❌</span>
                  <span>Manque d'outils adaptés aux contraintes professionnelles</span>
                </li>
              </ul>
            </div>
            <div>
              <h2 className="text-2xl lg:text-3xl font-bold text-[var(--color-secondary)] mb-6">
                Notre promesse
              </h2>
              <ul className="space-y-4 text-gray-700">
                <li className="flex items-start">
                  <span className="text-green-500 mr-3">✅</span>
                  <span>Routines ultra-courtes (2-8 minutes)</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-3">✅</span>
                  <span>Gamification motivante avec système de points</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-3">✅</span>
                  <span>Suivi de l'énergie et du bien-être</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-3">✅</span>
                  <span>Conçu spécifiquement pour les soignants</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 lg:py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl lg:text-4xl font-bold text-center text-[var(--color-primary)] mb-12">
            Fonctionnalités clés
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="w-12 h-12 bg-[var(--color-secondary)] rounded-lg flex items-center justify-center mb-4">
                <span className="text-white text-xl">⚡</span>
              </div>
              <h3 className="text-xl font-bold text-[var(--color-primary)] mb-3">Jauge d'énergie</h3>
              <p className="text-gray-600">Suivez votre énergie quotidienne basée sur vos habitudes de bien-être</p>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="w-12 h-12 bg-[var(--color-secondary)] rounded-lg flex items-center justify-center mb-4">
                <span className="text-white text-xl">🎯</span>
              </div>
              <h3 className="text-xl font-bold text-[var(--color-primary)] mb-3">Quêtes quotidiennes</h3>
              <p className="text-gray-600">Missions courtes et adaptées à votre emploi du temps chargé</p>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="w-12 h-12 bg-[var(--color-secondary)] rounded-lg flex items-center justify-center mb-4">
                <span className="text-white text-xl">🌳</span>
              </div>
              <h3 className="text-xl font-bold text-[var(--color-primary)] mb-3">Skill Tree</h3>
              <p className="text-gray-600">Développez vos compétences bien-être : stress, sommeil, résilience</p>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="w-12 h-12 bg-[var(--color-secondary)] rounded-lg flex items-center justify-center mb-4">
                <span className="text-white text-xl">📚</span>
              </div>
              <h3 className="text-xl font-bold text-[var(--color-primary)] mb-3">Bibliothèque</h3>
              <p className="text-gray-600">Recettes express, étirements, playlists et fiches bien-être</p>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="w-12 h-12 bg-[var(--color-secondary)] rounded-lg flex items-center justify-center mb-4">
                <span className="text-white text-xl">🎵</span>
              </div>
              <h3 className="text-xl font-bold text-[var(--color-primary)] mb-3">Ambiances</h3>
              <p className="text-gray-600">Thèmes visuels et sonores : Forêt, Océan, Aube, Nuit douce</p>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="w-12 h-12 bg-[var(--color-secondary)] rounded-lg flex items-center justify-center mb-4">
                <span className="text-white text-xl">🏆</span>
              </div>
              <h3 className="text-xl font-bold text-[var(--color-primary)] mb-3">Badges & Récompenses</h3>
              <p className="text-gray-600">Système de gamification motivant avec niveaux et récompenses</p>
            </div>
          </div>
        </div>
      </section>

      {/* Target Audience */}
      <section className="py-16 lg:py-20">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl lg:text-4xl font-bold text-[var(--color-primary)] mb-8">
            Pour qui ?
          </h2>
          <div className="grid md:grid-cols-4 gap-6 max-w-4xl mx-auto">
            <div className="p-6">
              <div className="w-16 h-16 bg-[var(--color-secondary)] rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-2xl">👩‍⚕️</span>
              </div>
              <h3 className="font-bold text-[var(--color-primary)]">Infirmiers</h3>
              <p className="text-sm text-gray-600 mt-2">Libéral ou établissement</p>
            </div>
            <div className="p-6">
              <div className="w-16 h-16 bg-[var(--color-secondary)] rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-2xl">👨‍⚕️</span>
              </div>
              <h3 className="font-bold text-[var(--color-primary)]">Aides-soignants</h3>
              <p className="text-sm text-gray-600 mt-2">Toutes spécialités</p>
            </div>
            <div className="p-6">
              <div className="w-16 h-16 bg-[var(--color-secondary)] rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-2xl">🩺</span>
              </div>
              <h3 className="font-bold text-[var(--color-primary)]">Médecins</h3>
              <p className="text-sm text-gray-600 mt-2">Généralistes & spécialistes</p>
            </div>
            <div className="p-6">
              <div className="w-16 h-16 bg-[var(--color-secondary)] rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-2xl">🏥</span>
              </div>
              <h3 className="font-bold text-[var(--color-primary)]">Professionnels</h3>
              <p className="text-sm text-gray-600 mt-2">Kinés, psychologues...</p>
            </div>
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="py-16 lg:py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl lg:text-4xl font-bold text-center text-[var(--color-primary)] mb-12">
            Comment ça marche
          </h2>
          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="w-16 h-16 bg-[var(--color-primary)] text-white rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold">
                1
              </div>
              <h3 className="text-xl font-bold text-[var(--color-primary)] mb-3">Définissez vos objectifs</h3>
              <p className="text-gray-600">Eau, sommeil, activité, sérénité - personnalisez selon vos besoins</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-[var(--color-primary)] text-white rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold">
                2
              </div>
              <h3 className="text-xl font-bold text-[var(--color-primary)] mb-3">Réalisez vos quêtes</h3>
              <p className="text-gray-600">5-10 minutes par jour suffisent pour maintenir votre bien-être</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-[var(--color-primary)] text-white rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold">
                3
              </div>
              <h3 className="text-xl font-bold text-[var(--color-primary)] mb-3">Suivez vos progrès</h3>
              <p className="text-gray-600">Gagnez des points, débloquez badges et montez de niveau</p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-16 lg:py-20">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl lg:text-4xl font-bold text-[var(--color-primary)] mb-8">
            Un investissement unique pour votre bien-être
          </h2>
          <div className="max-w-md mx-auto bg-white border-2 border-[var(--color-secondary)] rounded-2xl p-8 shadow-lg">
            <div className="mb-6">
              <div className="text-5xl font-bold text-[var(--color-primary)]">39€</div>
              <div className="text-gray-600">Paiement unique</div>
              <div className="text-sm text-[var(--color-secondary)] font-medium mt-2">
                Mises à jour incluses à vie
              </div>
            </div>
            <ul className="text-left space-y-3 mb-8">
              <li className="flex items-center">
                <span className="text-green-500 mr-3">✓</span>
                <span>Accès complet à toutes les fonctionnalités</span>
              </li>
              <li className="flex items-center">
                <span className="text-green-500 mr-3">✓</span>
                <span>Utilisable hors ligne (PWA)</span>
              </li>
              <li className="flex items-center">
                <span className="text-green-500 mr-3">✓</span>
                <span>Mises à jour automatiques</span>
              </li>
              <li className="flex items-center">
                <span className="text-green-500 mr-3">✓</span>
                <span>Support client dédié</span>
              </li>
            </ul>
            <button 
              onClick={handlePurchase}
              disabled={loading}
              className="btn w-full text-lg disabled:opacity-50"
            >
              {loading ? "Chargement..." : "Commencer maintenant"}
            </button>
            {error && (
              <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">
                {error}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-16 lg:py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl lg:text-4xl font-bold text-center text-[var(--color-primary)] mb-12">
            Questions fréquentes
          </h2>
          <div className="max-w-3xl mx-auto space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <h3 className="font-bold text-[var(--color-primary)] mb-2">Combien de temps par jour ?</h3>
              <p className="text-gray-600">Entre 5 et 10 minutes suffisent. L'app est conçue pour s'adapter aux contraintes des soignants.</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <h3 className="font-bold text-[var(--color-primary)] mb-2">Fonctionne-t-elle hors ligne ?</h3>
              <p className="text-gray-600">Oui, c'est une PWA qui fonctionne partiellement hors ligne avec cache des audios de respiration.</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <h3 className="font-bold text-[var(--color-primary)] mb-2">Politique de remboursement ?</h3>
              <p className="text-gray-600">Remboursement sous 14 jours si l'application n'a pas été activée.</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <h3 className="font-bold text-[var(--color-primary)] mb-2">Une licence = un utilisateur ?</h3>
              <p className="text-gray-600">Oui, chaque licence est personnelle et liée à un compte utilisateur unique.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[var(--color-primary)] text-white py-12">
        <div className="container mx-auto px-4 text-center">
          <Logo className="h-10 mx-auto mb-6" showFullName={true} />
          <p className="text-lg mb-4">par Discipline-90</p>
          <div className="flex justify-center space-x-8 text-sm">
            <a href="#" className="hover:text-[var(--color-secondary)]">Mentions légales</a>
            <a href="#" className="hover:text-[var(--color-secondary)]">CGV</a>
            <a href="#" className="hover:text-[var(--color-secondary)]">Confidentialité</a>
          </div>
        </div>
      </footer>
    </div>
  );
}