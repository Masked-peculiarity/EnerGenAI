import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { LogOut, Settings, UserRound } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useEnergySettings } from "@/hooks/useEnergySettings";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";

export default function ProfileMenu() {
  const { session, profileError, logout } = useAuth();
  const navigate = useNavigate();
  const { settings, setSettings } = useEnergySettings();
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [draft, setDraft] = useState(settings);
  const [error, setError] = useState("");
  const { toast } = useToast();
  if (!session) return <Button variant="outline" asChild><a href="/login">Log in</a></Button>;

  const save = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    for (const [name, value, max] of [["Tariff", draft.tariff, 100000], ["Grid factor", draft.factor, 100]] as const) {
      if (value.trim() && (!Number.isFinite(Number(value)) || Number(value) < 0 || Number(value) > max)) {
        setError(name + " must be between 0 and " + max + ".");
        return;
      }
    }
    setSettings({ tariff: draft.tariff.trim(), factor: draft.factor.trim() });
    setSettingsOpen(false);
    toast({ title: "Settings saved", description: "Your dashboard and Copilot now use these browser settings." });
  };
  return <>
    <DropdownMenu><DropdownMenuTrigger asChild>
      <Button variant="ghost" size="icon" className="h-10 w-10 rounded-full border border-primary/20 p-0" aria-label="Open profile menu">
        <Avatar className="h-9 w-9"><AvatarFallback className="bg-primary/10 font-semibold text-primary">{session.email.charAt(0).toUpperCase()}</AvatarFallback></Avatar>
      </Button>
    </DropdownMenuTrigger><DropdownMenuContent align="end" className="w-64">
      <DropdownMenuLabel><p className="font-medium">Your account</p><p className="mt-1 break-all text-xs font-normal text-muted-foreground">{session.email}</p></DropdownMenuLabel>
      <DropdownMenuSeparator />
      <DropdownMenuItem onSelect={() => setDetailsOpen(true)}><UserRound className="mr-2 h-4 w-4" />User details</DropdownMenuItem>
      <DropdownMenuItem onSelect={() => { setDraft(settings); setError(""); setSettingsOpen(true); }}><Settings className="mr-2 h-4 w-4" />Settings</DropdownMenuItem>
      <DropdownMenuSeparator />
      <DropdownMenuItem className="text-destructive focus:text-destructive" onSelect={() => { logout(); navigate("/login", { replace: true }); }}><LogOut className="mr-2 h-4 w-4" />Log out</DropdownMenuItem>
    </DropdownMenuContent></DropdownMenu>
    <Dialog open={detailsOpen} onOpenChange={setDetailsOpen}><DialogContent><DialogHeader><DialogTitle>User details</DialogTitle><DialogDescription>Your EnerGenAI account and current login session.</DialogDescription></DialogHeader>
      <dl className="space-y-4"><div><dt className="text-sm text-muted-foreground">Email</dt><dd className="mt-1 break-all font-medium">{session.email}</dd></div><div><dt className="text-sm text-muted-foreground">Session expires</dt><dd className="mt-1">{new Date(session.expiresAt).toLocaleString()}</dd></div></dl>
      {profileError && <p role="alert" className="text-sm text-destructive">{profileError}</p>}
      <p className="text-xs text-muted-foreground">Your account stores your email, not a name or profile photo. Energy readings are the shared UCI demonstration dataset.</p>
    </DialogContent></Dialog>
    <Dialog open={settingsOpen} onOpenChange={setSettingsOpen}><DialogContent><DialogHeader><DialogTitle>Settings</DialogTitle><DialogDescription>Energy-estimation preferences saved in this browser, not your account database.</DialogDescription></DialogHeader>
      <form onSubmit={save} className="space-y-4">
        <div><Label htmlFor="profile-tariff">Rate per kWh (your currency)</Label><Input id="profile-tariff" type="number" min="0" max="100000" step="any" placeholder="No default rate" value={draft.tariff} onChange={e => setDraft({ ...draft, tariff: e.target.value })} /></div>
        <div><Label htmlFor="profile-factor">Grid factor (kg CO2 / kWh)</Label><Input id="profile-factor" type="number" min="0" max="100" step="any" placeholder="No default factor" value={draft.factor} onChange={e => setDraft({ ...draft, factor: e.target.value })} /></div>
        <p className="text-xs text-muted-foreground">Leave blank to disable that estimate. Use your utility rate and a region-appropriate emissions factor. Costs cover the appliance channel only.</p>
        {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
        <div className="flex justify-end gap-2"><Button type="button" variant="outline" onClick={() => setSettingsOpen(false)}>Cancel</Button><Button type="submit">Save settings</Button></div>
      </form>
    </DialogContent></Dialog>
  </>;
}
