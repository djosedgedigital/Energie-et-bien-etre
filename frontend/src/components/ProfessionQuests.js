import React, { useEffect, useState } from "react";
import axios from "axios";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { CheckCircle, Play } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ProfessionQuests = ({ userId, professionSlug }) => {
  const [quests, setQuests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [completing, setCompleting] = useState({});

  useEffect(() => {
    const load = async () => {
      if (!professionSlug) return;
      setLoading(true);
      try {
        // Ensure quests are assigned once for the user
        await axios.post(`${API}/professions/${professionSlug}/assign-quests/${userId}`);
      } catch (e) {
        // Ignore if already assigned or any non-critical error
      }

      try {
        const res = await axios.get(`${API}/professions/${professionSlug}/quests`);
        setQuests(res.data || []);
      } catch (err) {
        console.error("Error fetching profession quests", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [professionSlug, userId]);

  if (loading) {
    return <div className="text-sm text-slate-500">Chargement des quêtes...</div>;
  }

  if (!quests || quests.length === 0) {
    return <div className="text-sm text-slate-500">Aucune quête recommandée pour l'instant.</div>;
  }

  return (
    <div className="space-y-3">
      {quests.map((q, idx) => (
        <div key={`${q.title}-${idx}`} className="flex items-start justify-between border rounded-lg p-3 bg-white">
          <div>
            <div className="font-semibold text-slate-800">{q.title}</div>
            {q.description && (
              <div className="text-sm text-slate-600">{q.description}</div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary">+{q.points_reward || 0} XP</Badge>
            <Button size="sm" variant="outline">
              <Play className="h-4 w-4" />
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ProfessionQuests;
