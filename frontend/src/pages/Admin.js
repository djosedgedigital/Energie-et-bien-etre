import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { adminClient } from "../api/adminClient.ts";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Trash2, RefreshCw } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Admin = () => {
  const [adminEmail, setAdminEmail] = useState(() => localStorage.getItem("adminEmail") || "contact@discipline90.com");
  const [professions, setProfessions] = useState([]);
  const [quests, setQuests] = useState([]);
  const [selectedProfession, setSelectedProfession] = useState("");
  const [loading, setLoading] = useState(false);
  const client = useMemo(() => adminClient(adminEmail), [adminEmail]);

  const [profForm, setProfForm] = useState({ label: "", slug: "", icon: "", order_index: 1, active: true });
  const [questForm, setQuestForm] = useState({ profession_slug: "", title: "", description: "", level: 1, xp_reward: 10, order_index: 1, is_enabled: true });

  const loadAll = async () => {
    setLoading(true);
    try {
      const questUrl = selectedProfession ? `/quests?profession_slug=${encodeURIComponent(selectedProfession)}` : `/quests`;
      const [p, q] = await Promise.all([
        client.get(`/professions`),
        client.get(questUrl),
      ]);
      setProfessions(p.data || []);
      setQuests(q.data || []);
    } catch (e) {
      console.error("Admin load error", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [adminEmail, selectedProfession]);

  const handleProfSubmit = async (e) => {
    e.preventDefault();
    try {
      const { sanitizeSlug } = await import("../helpers/slug");
      const payload = { ...profForm };
      payload.slug = sanitizeSlug(payload.slug || payload.label);
      await client.post(`/professions`, payload);
      setProfForm({ label: "", slug: "", icon: "", order_index: 1, active: true });
      await loadAll();
    } catch (e) {
      alert("Erreur création/maj métier (403 si email admin invalide)");
      console.error(e);
    }
  };

  const handleQuestSubmit = async (e) => {
    e.preventDefault();
    try {
      await client.post(`/quests`, questForm);
      setQuestForm({ profession_slug: "", title: "", description: "", level: 1, xp_reward: 10, order_index: 1, is_enabled: true });
      await loadAll();
    } catch (e) {
      alert("Erreur création quête (403 si email admin invalide)");
      console.error(e);
    }
  };

  const deleteProfession = async (slug) => {
    if (!window.confirm(`Supprimer ${slug} ?`)) return;
    try {
      await client.delete(`/professions/${slug}`);
      await loadAll();
    } catch (e) {
      alert("Erreur suppression métier");
    }
  };

  const deleteQuest = async (id, title) => {
    if (!window.confirm(`Supprimer la quête « ${title} » ?`)) return;
    try {
      await client.delete(`/quests/${id}`);
      await loadAll();
    } catch (e) {
      alert("Erreur suppression quête");
    }
  };

  const [assignForm, setAssignForm] = useState({ user_id: "", slug: "" });
  const handleAssign = async (e) => {
    e.preventDefault();
    try {
      await client.post(`/users/${assignForm.user_id}/set-profession/${assignForm.slug}`);
      alert("Métier appliqué et quêtes affectées (idempotent)");
    } catch (e) {
      alert("Erreur d'affectation (vérifiez user_id et slug)");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img alt="Énergie & Bien-être" src="/assets/logo-emergent-final.png" className="h-12 w-auto rounded-md shadow-sm border border-slate-200 bg-white object-contain" />
          </div>
          <div className="flex items-center gap-2">
            <Label htmlFor="adminEmail" className="text-xs text-slate-500">Email admin</Label>
            <Input id="adminEmail" value={adminEmail} onChange={(e) => setAdminEmail(e.target.value)} className="w-72" />
            <Button variant="outline" size="sm" onClick={loadAll} disabled={loading}>
              <RefreshCw className="h-4 w-4 mr-1" /> Rafraîchir
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        <Card className="mb-6">
          <CardContent className="py-4 text-sm text-slate-600">
            Vous êtes connecté en tant que <strong>{adminEmail}</strong>. Toutes les actions ci-dessous appellent les endpoints /api/admin/* avec l'en-tête X-Admin-Email.
          </CardContent>
        </Card>

        <Tabs defaultValue="professions">
          <TabsList>
            <TabsTrigger value="professions">Métiers</TabsTrigger>
            <TabsTrigger value="quests">Quêtes</TabsTrigger>
          </TabsList>

          <TabsContent value="professions" className="mt-4 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Créer / mettre à jour un métier</CardTitle>
                <CardDescription>Le slug est auto-généré si laissé vide</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleProfSubmit} className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label>Libellé</Label>
                    <Input value={profForm.label} onChange={(e)=>setProfForm({...profForm,label:e.target.value})} required />
                  </div>
                  <div>
                    <Label>Slug (auto si vide)</Label>
                    <Input value={profForm.slug} onChange={(e)=>setProfForm({...profForm,slug:e.target.value})} />
                  </div>
                  <div>
                    <Label>Icône (emoji)</Label>
                    <Input value={profForm.icon} onChange={(e)=>setProfForm({...profForm,icon:e.target.value})} placeholder="🩺" />
                  </div>
                  <div>
                    <Label>Ordre</Label>
                    <Input type="number" value={profForm.order_index} onChange={(e)=>setProfForm({...profForm,order_index:parseInt(e.target.value||'0',10)})} />
                  </div>
                  <div className="flex items-center gap-2">
                    <input id="prof-active" type="checkbox" checked={profForm.active} onChange={(e)=>setProfForm({...profForm,active:e.target.checked})} />
                    <Label htmlFor="prof-active">Actif</Label>
                  </div>
                  <div className="md:col-span-2">
                    <Button type="submit">Enregistrer</Button>
                  </div>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Liste des métiers</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mb-3 flex items-center gap-3">
                  <div>
                    <Label>Filtrer par métier</Label>
                    <select
                      value={selectedProfession}
                      onChange={(e) => setSelectedProfession(e.target.value)}
                      className="border p-2 rounded min-w-[240px]"
                    >
                      <option value="">-- Tous les métiers --</option>
                      {professions.map((p) => (
                        <option key={p.slug} value={p.slug}>{p.label}</option>
                      ))}
                    </select>
                  </div>
                  <Button variant="outline" size="sm" onClick={loadAll} disabled={loading}>Rafraîchir</Button>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="text-left text-slate-500">
                        <th className="py-2 pr-4">Icône</th>
                        <th className="py-2 pr-4">Libellé</th>
                        <th className="py-2 pr-4">Slug</th>
                        <th className="py-2 pr-4">Actif</th>
                        <th className="py-2 pr-4">Ordre</th>
                        <th className="py-2">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {professions.map((p) => (
                        <tr key={p.slug} className="border-t">
                          <td className="py-2 pr-4">{p.icon}</td>
                          <td className="py-2 pr-4">{p.label}</td>
                          <td className="py-2 pr-4">{p.slug}</td>
                          <td className="py-2 pr-4">{p.active ? "Oui" : "Non"}</td>
                          <td className="py-2 pr-4">{p.order_index}</td>
                          <td className="py-2">
                            <Button variant="ghost" size="sm" onClick={() => deleteProfession(p.slug)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="quests" className="mt-4 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Créer une quête</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleQuestSubmit} className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label>Métier (slug)</Label>
                    <Input value={questForm.profession_slug} onChange={(e)=>setQuestForm({...questForm,profession_slug:e.target.value})} required />
                  </div>
                  <div>
                    <Label>Titre</Label>
                    <Input value={questForm.title} onChange={(e)=>setQuestForm({...questForm,title:e.target.value})} required />
                  </div>
                  <div className="md:col-span-2">
                    <Label>Description</Label>
                    <Input value={questForm.description} onChange={(e)=>setQuestForm({...questForm,description:e.target.value})} />
                  </div>
                  <div>
                    <Label>Niveau</Label>
                    <Input type="number" value={questForm.level} onChange={(e)=>setQuestForm({...questForm,level:parseInt(e.target.value||'1',10)})} />
                  </div>
                  <div>
                    <Label>XP</Label>
                    <Input type="number" value={questForm.xp_reward} onChange={(e)=>setQuestForm({...questForm,xp_reward:parseInt(e.target.value||'10',10)})} />
                  </div>
                  <div>
                    <Label>Ordre</Label>
                    <Input type="number" value={questForm.order_index} onChange={(e)=>setQuestForm({...questForm,order_index:parseInt(e.target.value||'1',10)})} />
                  </div>
                  <div className="flex items-center gap-2">
                    <input id="quest-enabled" type="checkbox" checked={questForm.is_enabled} onChange={(e)=>setQuestForm({...questForm,is_enabled:e.target.checked})} />
                    <Label htmlFor="quest-enabled">Actif</Label>
                  </div>
                  <div className="md:col-span-2">
                    <Button type="submit">Créer</Button>
                  </div>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Quêtes par métier</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="text-left text-slate-500">
                        <th className="py-2 pr-4">Métier</th>
                        <th className="py-2 pr-4">Titre</th>
                        <th className="py-2 pr-4">Niveau</th>
                        <th className="py-2 pr-4">XP</th>
                        <th className="py-2 pr-4">Actif</th>
                        <th className="py-2">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {quests.map((q) => (
                        <tr key={q.id} className="border-t">
                          <td className="py-2 pr-4">{q.profession_slug}</td>
                          <td className="py-2 pr-4">{q.title}</td>
                          <td className="py-2 pr-4">{q.level}</td>
                          <td className="py-2 pr-4">{q.xp_reward}</td>
                          <td className="py-2 pr-4">{q.is_enabled ? "Oui" : "Non"}</td>
                          <td className="py-2">
                            <Button variant="ghost" size="sm" onClick={() => deleteQuest(q.id, q.title)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Affecter un métier à un utilisateur</CardTitle>
            <CardDescription>Met à jour le métier et assigne les quêtes (idempotent)</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAssign} className="grid md:grid-cols-2 gap-4">
              <div>
                <Label>User ID</Label>
                <Input value={assignForm.user_id} onChange={(e)=>setAssignForm({...assignForm,user_id:e.target.value})} required />
              </div>
              <div>
                <Label>Métier (slug)</Label>
                <Input value={assignForm.slug} onChange={(e)=>setAssignForm({...assignForm,slug:e.target.value})} required />
              </div>
              <div className="md:col-span-2">
                <Button type="submit">Appliquer</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default Admin;