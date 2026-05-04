import { BrowserRouter, Routes, Route } from "react-router-dom";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { AppLayout } from "@/components/layout/AppLayout";
import { ChatPage } from "@/components/chat/ChatPage";
import { DocumentsPage } from "@/components/documents/DocumentsPage";
import { EvaluationPage } from "@/components/evaluation/EvaluationPage";
import { LoginPage } from "@/components/auth/LoginPage";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AuthProvider, useAuthState } from "@/hooks/useAuth";

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<ChatPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/evaluation" element={<EvaluationPage />} />
      </Route>
    </Routes>
  );
}

function App() {
  const auth = useAuthState();

  return (
    <ErrorBoundary>
      <AuthProvider value={auth}>
        <BrowserRouter>
          <TooltipProvider>
            <AppRoutes />
          </TooltipProvider>
        </BrowserRouter>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
