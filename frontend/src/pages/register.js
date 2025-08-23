import { useRouter } from "next/router";
import Logo from "@/components/Logo";
import Link from "next/link";
import { useState } from "react";
import axios from "axios";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

export default function Register() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    email: "",
    full_name: "",
    profession: "",
    password: "",
    confirmPassword: ""
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    if (formData.password !== formData.confirmPassword) {
      setError("Les mots de passe ne correspondent pas");
      setLoading(false);
      return;
    }

    if (!formData.profession) {
      setError("Veuillez sélectionner votre profession");
      setLoading(false);
      return;
    }

    try {
      const response = await axios.post(`${BACKEND_URL}/api/auth/register`, {
        email: formData.email,
        full_name: formData.full_name,
        profession: formData.profession,
        password: formData.password
      });
      
      if (typeof window !== 'undefined') {
        localStorage.setItem("token", response.data.access_token);
        localStorage.setItem("user", JSON.stringify(response.data.user));
      }
      
      router.push("/dashboard");
    } catch (error) {
      console.error("Registration error:", error);
      setError(error.response?.data?.detail || "Erreur lors de l'inscription");
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="bg-white shadow-lg rounded-xl p-8 w-full max-w-md text-center">
        <Logo className="h-12 mx-auto mb-6" />
        <h1 className="text-2xl font-bold text-[var(--color-primary)] mb-2">Créer un compte</h1>
        <p className="text-gray-600 mb-6">Rejoignez Énergie & Bien-être™ dès aujourd'hui</p>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}
        
        <form className="space-y-4" onSubmit={handleSubmit}>
          <input 
            type="text" 
            name="full_name"
            placeholder="Nom complet" 
            className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-secondary)]" 
            value={formData.full_name}
            onChange={handleChange}
            required 
          />
          <input 
            type="email" 
            name="email"
            placeholder="Adresse email" 
            className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-secondary)]" 
            value={formData.email}
            onChange={handleChange}
            required 
          />
          <select 
            name="profession"
            className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-secondary)]"
            value={formData.profession}
            onChange={handleChange}
            required
          >
            <option value="">Sélectionnez votre profession…</option>
            <option value="infirmier">Infirmier / Infirmière</option>
            <option value="aide-soignant">Aide-soignant(e)</option>
            <option value="medecin">Médecin</option>
            <option value="autre">Autre</option>
          </select>
          <input 
            type="password" 
            name="password"
            placeholder="Mot de passe" 
            className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-secondary)]" 
            value={formData.password}
            onChange={handleChange}
            required 
          />
          <input 
            type="password" 
            name="confirmPassword"
            placeholder="Confirmer le mot de passe" 
            className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-secondary)]" 
            value={formData.confirmPassword}
            onChange={handleChange}
            required 
          />
          <button 
            type="submit" 
            className="btn w-full"
            disabled={loading}
          >
            {loading ? "Inscription..." : "S'inscrire"}
          </button>
        </form>
        <p className="mt-6 text-sm text-gray-600">
          Vous avez déjà un compte ? <Link href="/login" className="text-[var(--color-secondary)] font-medium hover:underline">Se connecter</Link>
        </p>
      </div>
    </div>
  );
}