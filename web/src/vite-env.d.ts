/// <reference types="vite/client" />

declare module "mermaid/dist/mermaid.esm.min.mjs" {
  const mermaid: {
    initialize: (config: Record<string, unknown>) => void;
    render: (id: string, chart: string) => Promise<{ svg: string }>;
  };
  export default mermaid;
}
