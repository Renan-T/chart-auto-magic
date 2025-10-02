import { Button } from "@/components/ui/button";
import { Upload, TrendingUp } from "lucide-react";
import heroImage from "@/assets/hero-dashboard.jpg";

const Hero = () => {
  return (
    <section className="relative min-h-[90vh] flex items-center justify-center bg-gradient-subtle overflow-hidden">
      <div className="absolute inset-0 bg-gradient-card opacity-50" />
      
      <div className="container relative z-10 px-4 py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-8">
            <div className="inline-block">
              <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium">
                <TrendingUp className="h-4 w-4" />
                Powered by AI
              </span>
            </div>
            
            <h1 className="text-5xl lg:text-6xl font-bold leading-tight">
              Dashboards comerciais em{" "}
              <span className="bg-gradient-hero bg-clip-text text-transparent">
                minutos
              </span>
            </h1>
            
            <p className="text-xl text-muted-foreground leading-relaxed max-w-xl">
              Transforme qualquer planilha comercial em um dashboard interativo. 
              IA detecta KPIs, sugere gráficos e gera insights automaticamente.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4">
              <Button size="lg" variant="hero" className="group">
                <Upload className="h-5 w-5 transition-transform group-hover:scale-110" />
                Começar Agora
              </Button>
              <Button size="lg" variant="outline">
                Ver Demo
              </Button>
            </div>
            
            <div className="flex items-center gap-8 pt-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-primary">5min</div>
                <div className="text-sm text-muted-foreground">Setup médio</div>
              </div>
              <div className="h-12 w-px bg-border" />
              <div className="text-center">
                <div className="text-3xl font-bold text-success">15+</div>
                <div className="text-sm text-muted-foreground">KPIs automáticos</div>
              </div>
              <div className="h-12 w-px bg-border" />
              <div className="text-center">
                <div className="text-3xl font-bold text-accent">100%</div>
                <div className="text-sm text-muted-foreground">Sem código</div>
              </div>
            </div>
          </div>
          
          <div className="relative lg:block hidden">
            <div className="absolute -inset-4 bg-gradient-hero opacity-20 blur-3xl rounded-full" />
            <img
              src={heroImage}
              alt="Dashboard interativo do AutoDash"
              className="relative rounded-2xl shadow-xl border-2 border-border"
            />
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
