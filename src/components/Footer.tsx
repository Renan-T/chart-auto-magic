import { BarChart4 } from "lucide-react";

const Footer = () => {
  return (
    <footer className="border-t border-border bg-background">
      <div className="container px-4 py-12">
        <div className="grid md:grid-cols-4 gap-8">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-hero">
                <BarChart4 className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="text-lg font-bold">AutoDash</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Dashboards comerciais inteligentes em minutos.
            </p>
          </div>
          
          <div>
            <h3 className="font-semibold mb-3">Produto</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><a href="#" className="hover:text-foreground transition-smooth">Features</a></li>
              <li><a href="#" className="hover:text-foreground transition-smooth">Preços</a></li>
              <li><a href="#" className="hover:text-foreground transition-smooth">Segurança</a></li>
            </ul>
          </div>
          
          <div>
            <h3 className="font-semibold mb-3">Empresa</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><a href="#" className="hover:text-foreground transition-smooth">Sobre</a></li>
              <li><a href="#" className="hover:text-foreground transition-smooth">Blog</a></li>
              <li><a href="#" className="hover:text-foreground transition-smooth">Contato</a></li>
            </ul>
          </div>
          
          <div>
            <h3 className="font-semibold mb-3">Legal</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><a href="#" className="hover:text-foreground transition-smooth">Privacidade</a></li>
              <li><a href="#" className="hover:text-foreground transition-smooth">Termos</a></li>
            </ul>
          </div>
        </div>
        
        <div className="mt-12 pt-8 border-t border-border text-center text-sm text-muted-foreground">
          © {new Date().getFullYear()} AutoDash. Todos os direitos reservados.
        </div>
      </div>
    </footer>
  );
};

export default Footer;
