import Logo from "@/components/Logo";
import Link from "next/link";
import { useState } from "react";

export default function Home() {
  const [selectedProfession, setSelectedProfession] = useState("");

  return (
    <main className="flex flex-col items-center justify-center min-h-screen px-4 lg:px-6 py-8 lg:py-12 bg-white text-center">
      {/* Logo et nom complet */}
      <div className="mb-8 lg:mb-10">
        <Logo className="h-16 lg:h-20 mb-4" showFullName={true} />
        <div className="text-sm lg:text-base text-[var(--color-secondary)] font-medium">
          par Discipline-90
        </div>
      </div>

      <h1 className="text-2xl lg:text-4xl font-extrabold text-[var(--color-primary)] mb-4 px-2">
        Votre dose de récupération en 8 minutes
      </h1>
      <h2 className="text-lg lg:text-2xl font-semibold text-[var(--color-secondary)] mb-6">
        Pensée pour les soignants
      </h2>
      <p className="max-w-xl text-sm lg:text-lg text-gray-600 mb-8 lg:mb-10 px-2">
        Une app simple, apaisante et gamifiée pour retrouver énergie et équilibre,
        même avec des horaires décalés.
      </p>
      <select 
        className="border border-gray-300 rounded-lg px-4 py-2 mb-6 focus:outline-none focus:ring-2 focus:ring-[var(--color-secondary)] w-full max-w-sm text-sm lg:text-base"
        value={selectedProfession}
        onChange={(e) => setSelectedProfession(e.target.value)}
      >
        <option value="">Sélectionnez votre profession…</option>
        <option value="infirmier">Infirmier / Infirmière</option>
        <option value="aide-soignant">Aide-soignant(e)</option>
        <option value="medecin">Médecin</option>
        <option value="autre">Autre</option>
      </select>
      <Link href="/login" className="btn text-sm lg:text-base">Commencer maintenant</Link>
      
      <section className="mt-12 lg:mt-16 max-w-2xl text-center px-4">
        <h3 className="text-lg lg:text-2xl font-bold text-[var(--color-primary)] mb-4">Fonctionnalités clés</h3>
        <ul className="text-gray-700 space-y-2 lg:space-y-3 text-sm lg:text-base">
          <li>✔️ Exercices rapides de relaxation et respiration</li>
          <li>✔️ Routines bien-être intégrées à votre quotidien</li>
          <li>✔️ Suivi simple et gamifié de vos pauses</li>
        </ul>
      </section>
      
      <footer className="mt-16 lg:mt-20 text-gray-500 text-xs lg:text-sm">
        Fabriqué pour les soignants — par Discipline-90
      </footer>
    </main>
  )
}