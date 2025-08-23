import { useRouter } from "next/router";
import Logo from "@/components/Logo";
import Link from "next/link";
import { useState } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function Login() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    email: "",
    password: ""
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await axios.post(`${BACKEND_URL}/api/auth/login`, formData);
      
      if (typeof window !== 'undefined') {
        localStorage.setItem("token", response.data.access_token);
        localStorage.setItem("user", JSON.stringify(response.data.user));
      }
      
      router.push("/dashboard");
    } catch (error) {
      console.error("Login error:", error);
      setError(error.response?.data?.detail || "Erreur de connexion");
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
        <h1 className="text-2xl font-bold text-[var(--color-primary)] mb-2">Connexion</h1>
        <p className="text-gray-600 mb-6">Accédez à votre espace personnel</p>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}
        
        <form className="space-y-4" onSubmit={handleSubmit}>
          <input 
            type="email" 
            name="email"
            placeholder="Adresse email" 
            className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-secondary)]" 
            value={formData.email}
            onChange={handleChange}
            required 
          />
          <input 
            type="password" 
            name="password"
            placeholder="Mot de passe" 
            className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-secondary)]" 
            value={formData.password}
            onChange={handleChange}
            required 
          />
          <button 
            type="submit" 
            className="btn w-full"
            disabled={loading}
          >
            {loading ? "Connexion..." : "Se connecter"}
          </button>
        </form>
        <p className="mt-6 text-sm text-gray-600">
          Pas encore de compte ? <Link href="/register" className="text-[var(--color-secondary)] font-medium hover:underline">Créer un compte</Link>
        </p>
      </div>
    </div>
  );
}