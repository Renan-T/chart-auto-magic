import { Card, CardContent } from "@/components/ui/card";
import { Users, Rocket, LineChart, Building2 } from "lucide-react";

const useCases = [
  {
    icon: Rocket,
    title: "Founders & Startups",
    description: "Acompanhe métricas comerciais sem contratar analista. Foco no crescimento.",
  },
  {
    icon: Users,
    title: "Times Comerciais",
    description: "Vendedores veem performance em tempo real. Gestores tomam decisões rápidas.",
  },
  {
    icon: LineChart,
    title: "Analistas de Dados",
    description: "Automatize relatórios repetitivos. Dedique tempo a insights estratégicos.",
  },
  {
    icon: Building2,
    title: "Agências & Consultorias",
    description: "Entregue dashboards profissionais para clientes em minutos, não em dias.",
  },
];

const UseCases = () => {
  return (
    <section className="py-24 bg-gradient-subtle">
      <div className="container px-4">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-4xl font-bold mb-4">
            Feito para quem precisa de{" "}
            <span className="bg-gradient-hero bg-clip-text text-transparent">
              resultados rápidos
            </span>
          </h2>
          <p className="text-xl text-muted-foreground">
            Não importa o tamanho da sua operação. AutoDash escala com você.
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {useCases.map((useCase) => {
            const Icon = useCase.icon;
            return (
              <Card 
                key={useCase.title}
                className="border-2 hover:border-primary/50 transition-smooth bg-card"
              >
                <CardContent className="p-6 text-center">
                  <div className="inline-flex p-4 rounded-xl bg-gradient-card mb-4">
                    <Icon className="h-8 w-8 text-primary" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{useCase.title}</h3>
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    {useCase.description}
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default UseCases;
