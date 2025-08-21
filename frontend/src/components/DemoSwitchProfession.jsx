import { useState } from "react";
import axios from "axios";

export default function DemoSwitchProfession() {
  const [slug, setSlug] = useState("infirmier");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const switchProfession = async () => {
    try {
      setLoading(true);
      await axios.post(`/api/user/_demo/switch-profession/${slug}`);
      setMsg(`Métier changé: ${slug} (DEMO)`);
    } catch (e) {
      setMsg("Erreur: active DEMO_MODE=true côté backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <input
        className="border rounded px-2 py-1"
        value={slug}
        onChange={(e)=>setSlug(e.target.value)}
        placeholder="ex: infirmier"
      />
      <button
        onClick={switchProfession}
        disabled={loading}
        className="rounded bg-[#0E3A53] text-white px-3 py-1.5 hover:opacity-90"
      >
        {loading ? "…" : "Changer (DEMO)"}
      </button>
      {msg && <span className="text-sm opacity-80">{msg}</span>}
    </div>
  );
}
