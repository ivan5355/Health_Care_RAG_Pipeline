import { NavLink, useNavigate } from "react-router-dom";
import { MessageSquare, FileText, BarChart3, LogOut } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const allLinks = [
  { to: "/", icon: MessageSquare, label: "Chat", adminOnly: false },
  { to: "/documents", icon: FileText, label: "Documents", adminOnly: true },
  { to: "/evaluation", icon: BarChart3, label: "Evaluation", adminOnly: false },
];

export function Sidebar() {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const links = allLinks.filter((link) => !link.adminOnly || isAdmin);

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <aside className="w-64 border-r bg-sidebar flex flex-col">
      <div className="p-6 border-b">
        <h1 className="text-lg font-semibold text-sidebar-foreground">
          Healthcare RAG
        </h1>
        <p className="text-xs text-muted-foreground mt-1">
          Document Q&A Pipeline
        </p>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                  : "text-sidebar-foreground hover:bg-sidebar-accent/50"
              }`
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
      {user && (
        <div className="p-3 border-t space-y-2">
          <div className="flex items-center justify-between px-3">
            <span className="text-sm text-sidebar-foreground">{user.username}</span>
            <Badge variant="secondary">{user.role}</Badge>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-3 px-3"
            onClick={handleLogout}
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </Button>
        </div>
      )}
    </aside>
  );
}
