import Header from "@/components/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from "recharts";
import { TrendingUp, TrendingDown, DollarSign, Target, ShoppingCart, Users } from "lucide-react";

// Dados de exemplo - Receita mensal
const revenueData = [
  { month: "Jan", receita: 45000, meta: 50000 },
  { month: "Fev", receita: 52000, meta: 50000 },
  { month: "Mar", receita: 48000, meta: 50000 },
  { month: "Abr", receita: 61000, meta: 55000 },
  { month: "Mai", receita: 55000, meta: 55000 },
  { month: "Jun", receita: 67000, meta: 60000 },
];

// Dados de exemplo - Vendas por produto
const productData = [
  { produto: "Produto A", vendas: 4000 },
  { produto: "Produto B", vendas: 3000 },
  { produto: "Produto C", vendas: 2000 },
  { produto: "Produto D", vendas: 2780 },
  { produto: "Produto E", vendas: 1890 },
];

// Dados de exemplo - Distribuição por canal
const channelData = [
  { name: "E-commerce", value: 45 },
  { name: "Varejo", value: 30 },
  { name: "Atacado", value: 15 },
  { name: "Marketplace", value: 10 },
];

const COLORS = ["hsl(var(--primary))", "hsl(var(--accent))", "hsl(var(--success))", "hsl(var(--warning))"];

const Dashboard = () => {
  return (
    <div className="min-h-screen bg-gradient-subtle">
      <Header />
      
      <main className="container px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Dashboard Comercial</h1>
          <p className="text-muted-foreground">Análise completa de performance de vendas</p>
        </div>

        {/* KPIs Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="border-2">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Receita Total
              </CardTitle>
              <DollarSign className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">R$ 328.000</div>
              <p className="text-xs text-success flex items-center gap-1 mt-1">
                <TrendingUp className="h-3 w-3" />
                +12,5% vs mês anterior
              </p>
            </CardContent>
          </Card>

          <Card className="border-2">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Atingimento de Meta
              </CardTitle>
              <Target className="h-4 w-4 text-accent" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">111,7%</div>
              <p className="text-xs text-success flex items-center gap-1 mt-1">
                <TrendingUp className="h-3 w-3" />
                Meta superada
              </p>
            </CardContent>
          </Card>

          <Card className="border-2">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total de Pedidos
              </CardTitle>
              <ShoppingCart className="h-4 w-4 text-success" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">1.248</div>
              <p className="text-xs text-destructive flex items-center gap-1 mt-1">
                <TrendingDown className="h-3 w-3" />
                -3,2% vs mês anterior
              </p>
            </CardContent>
          </Card>

          <Card className="border-2">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Ticket Médio
              </CardTitle>
              <Users className="h-4 w-4 text-warning" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">R$ 262,82</div>
              <p className="text-xs text-success flex items-center gap-1 mt-1">
                <TrendingUp className="h-3 w-3" />
                +16,3% vs mês anterior
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Gráficos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Gráfico de Receita vs Meta */}
          <Card className="border-2">
            <CardHeader>
              <CardTitle>Receita vs Meta - 2024</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={revenueData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="month" stroke="hsl(var(--muted-foreground))" />
                  <YAxis stroke="hsl(var(--muted-foreground))" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: "hsl(var(--card))", 
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px"
                    }}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="receita" 
                    stroke="hsl(var(--primary))" 
                    strokeWidth={2}
                    name="Receita"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="meta" 
                    stroke="hsl(var(--accent))" 
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    name="Meta"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Gráfico de Vendas por Produto */}
          <Card className="border-2">
            <CardHeader>
              <CardTitle>Top 5 Produtos - Vendas</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={productData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="produto" stroke="hsl(var(--muted-foreground))" />
                  <YAxis stroke="hsl(var(--muted-foreground))" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: "hsl(var(--card))", 
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px"
                    }}
                  />
                  <Legend />
                  <Bar dataKey="vendas" fill="hsl(var(--primary))" name="Vendas (R$)" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Gráfico de Pizza e Ações */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="border-2 lg:col-span-1">
            <CardHeader>
              <CardTitle>Distribuição por Canal</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={channelData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {channelData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: "hsl(var(--card))", 
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px"
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="border-2 lg:col-span-2 bg-gradient-card">
            <CardHeader>
              <CardTitle>Insights & Ações Recomendadas</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 rounded-lg bg-success/10 border border-success/20">
                <h4 className="font-semibold text-success mb-2 flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Performance Positiva
                </h4>
                <p className="text-sm text-muted-foreground">
                  Receita de Junho superou a meta em 11,7%. Produto A mantém liderança com crescimento constante.
                </p>
              </div>

              <div className="p-4 rounded-lg bg-warning/10 border border-warning/20">
                <h4 className="font-semibold text-warning mb-2 flex items-center gap-2">
                  <Target className="h-4 w-4" />
                  Atenção Necessária
                </h4>
                <p className="text-sm text-muted-foreground">
                  Número de pedidos caiu 3,2%. Considere campanhas para aumentar volume de vendas.
                </p>
              </div>

              <div className="pt-4 flex gap-3">
                <Button variant="default">
                  Exportar Relatório
                </Button>
                <Button variant="outline">
                  Configurar Alertas
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
