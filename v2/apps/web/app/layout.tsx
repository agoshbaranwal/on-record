export const metadata = { title: "On Record", description: "What the climate record actually shows, for your place." };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, background: "#0B1A1C", color: "#F2E7CC",
        font: "16px/1.55 ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}
