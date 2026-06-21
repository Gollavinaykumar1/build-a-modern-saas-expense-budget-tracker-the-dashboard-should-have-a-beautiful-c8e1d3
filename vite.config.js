import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/build-a-modern-saas-expense-budget-tracker-the-dashboard-should-have-a-beautiful-dark-mode-ui-with-p/",
  build: { outDir: "dist", assetsDir: "assets" },
  server: { port: 3000 },
});
