import { Button } from "@/components/ui/button";
import { BarChart4 } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

const Header = () => {
  const location = useLocation();
  
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between px-4">
        <Link to="/" className="flex items-center gap-2">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-hero">
            <BarChart4 className="h-6 w-6 text-primary-foreground" />
          </div>
          <span className="text-xl font-bold">AutoDash</span>
        </Link>
        
        <nav className="hidden md:flex items-center gap-6">
          <Link 
            to="/" 
            className={`text-sm font-medium transition-smooth ${
              location.pathname === "/" ? "text-foreground" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Início
          </Link>
          <Link 
            to="/dashboard" 
            className={`text-sm font-medium transition-smooth ${
              location.pathname === "/dashboard" ? "text-foreground" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Dashboard
          </Link>
          <a href="#pricing" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-smooth">
            Preços
          </a>
        </nav>
        
        <div className="flex items-center gap-3">
          <Button variant="ghost" className="hidden sm:inline-flex">
            Entrar
          </Button>
          <Button variant="default" asChild>
            <Link to="/dashboard">Ver Dashboard</Link>
          </Button>
        </div>
      </div>
    </header>
  );
};

export default Header;
