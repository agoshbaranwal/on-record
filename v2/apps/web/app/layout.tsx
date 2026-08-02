import "./tokens.css";

export const metadata = {
  title: "On Record — what the climate record shows where you live",
  description: "Your own city's temperature record since 1940, measured, with every number sourced.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
