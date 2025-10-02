import { Card, CardContent } from "@/components/ui/card";
import { Upload, Brain, BarChart3, TrendingUp, Filter, AlertCircle } from "lucide-react";
import featureAI from "@/assets/feature-ai.jpg";
import featureInteractive from "@/assets/feature-interactive.jpg";
import featureUpload from "@/assets/feature-upload.jpg";

const features = [
  {
    icon: Upload,
    title: "Upload Inteligente",
    description: "CSV, XLSX ou Google Sheets. Detecção semântica automática de colunas: faturamento, meta, pedidos.",
    image: featureUpload,
  },
  {
    icon: Brain,
    title: "IA Sugere KPIs",
    description: "Receita líquida, margem, atingimento de meta, crescimento MoM/MTD/YTD e muito mais.",
    image: featureAI,
  },
  {
    icon: BarChart3,
    title: "Gráficos Recomendados",
    description: "Linhas, barras, pizza por tempo e dimensão (produto, vendedor, canal, região).",
    image: featureInteractive,
  },
  {
    icon: TrendingUp,
    title: "Forecast Automático",
    description: "Previsões quando há histórico suficiente. Projeções baseadas em dados reais.",
    image: featureAI,
  },
  {
    icon: Filter,
    title: "Filtros Dinâmicos",
    description: "Período, segmentos e dimensões. Dashboard 100% interativo e responsivo.",
    image: featureInteractive,
  },
  {
    icon: AlertCircle,
    title: "Alertas Configuráveis",
    description: "Notificações de quedas MoM, descontos altos ou metas não atingidas.",
    image: featureUpload,
  },
];

const Features = () => {
  return (
    <section className="py-24 bg-background">
      <div className="container px-4">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-4xl font-bold mb-4">
            Tudo que você precisa para{" "}
            <span className="bg-gradient-hero bg-clip-text text-transparent">
              análise comercial
            </span>
          </h2>
          <p className="text-xl text-muted-foreground">
            Da planilha ao dashboard em minutos. IA faz o trabalho pesado por você.
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Card 
                key={feature.title} 
                className="group hover:shadow-lg transition-smooth border-2 overflow-hidden"
              >
                <div className="h-48 overflow-hidden bg-gradient-card">
                  <img 
                    src={feature.image} 
                    alt={feature.title}
                    className="w-full h-full object-cover transition-transform group-hover:scale-105"
                  />
                </div>
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="p-3 rounded-lg bg-gradient-card">
                      <Icon className="h-6 w-6 text-primary" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                      <p className="text-muted-foreground leading-relaxed">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default Features;
