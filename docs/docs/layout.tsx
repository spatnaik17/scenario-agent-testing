import { GithubStarsScript } from "./components/GithubStars";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <GithubStarsScript repo="langwatch/scenario" />
    </>
  );
}
