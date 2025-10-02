import { Button } from "@/components/ui/button";
import { Upload, ArrowRight } from "lucide-react";

const CTA = () => {
  return (
    <section className="py-24 bg-background">
      <div className="container px-4">
        <div className="relative max-w-4xl mx-auto">
          <div className="absolute inset-0 bg-gradient-hero opacity-10 blur-3xl rounded-3xl" />
          
          <div className="relative bg-gradient-card rounded-3xl border-2 border-border p-12 text-center">
            <h2 className="text-4xl lg:text-5xl font-bold mb-4">
              Pronto para transformar suas{" "}
              <span className="bg-gradient-hero bg-clip-text text-transparent">
                planilhas em insights?
              </span>
            </h2>
            
            <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              Faça upload da sua primeira planilha e veja a mágica acontecer em minutos.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" variant="hero" className="group">
                <Upload className="h-5 w-5 transition-transform group-hover:scale-110" />
                Começar Gratuitamente
              </Button>
              <Button size="lg" variant="outline">
                Agendar Demo
                <ArrowRight className="h-5 w-5" />
              </Button>
            </div>
            
            <p className="text-sm text-muted-foreground mt-6">
              Sem cartão de crédito. Sem instalação. Resultados em 5 minutos.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CTA;
