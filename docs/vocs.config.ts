import { defineConfig } from "vocs";
import { GithubStars } from "./docs/components/GithubStars";

export default defineConfig({
  title: "Scenario",
  description: "Agent Testing Framework",
  logoUrl: "/images/logo.png",
  iconUrl: "/favicon.ico",
  ogImageUrl:
    "https://vocs.dev/api/og?logo=%logo&title=%title&description=%description",
  editLink: {
    pattern:
      "https://github.com/langwatch/scenario/edit/main/docs/docs/pages/:path",
    text: "Suggest changes to this page",
  },
  socials: [
    {
      icon: "discord",
      link: "https://discord.gg/kT4PhDS2gH",
    },
    {
      icon: "github",
      link: "https://github.com/langwatch/scenario",
    },
    {
      icon: "x",
      link: "https://x.com/langwatchai",
    },
  ],
  sidebar: [
    {
      text: "Introduction",
      items: [
        {
          text: "What is Scenario?",
          link: "/",
        },
        {
          text: "Your First Scenario",
          link: "/introduction/getting-started",
        },
        {
          text: "Simulation-Based Testing",
          link: "/introduction/simulation-based-testing",
        },
      ],
    },
    {
      text: "Scenario Basics",
      items: [
        {
          text: "Concepts",
          link: "/basics/concepts",
        },
        {
          text: "Writing Scenarios",
          link: "/basics/writing-scenarios",
        },
        {
          text: "Scripted Simulations",
          link: "/basics/scripted-simulations",
        },
        {
          text: "Cache",
          link: "/basics/cache",
        },
        {
          text: "Debug Mode",
          link: "/basics/debug-mode",
        },
      ],
    },
    {
      text: "Agent Integration",
      items: [
        {
          text: "Integrating Any Agent",
          link: "/agent-integration",
        },
      ],
    },
    {
      text: "API Reference",
      items: [
        {
          text: "Python",
          link: `${process.env.BASE_URL ?? "http://localhost:5173"}${
            process.env.BASE_PATH ?? ""
          }/reference/python/scenario/index.html`,
        },
      ],
    },
  ],
  basePath: process.env.BASE_PATH,
  baseUrl: process.env.BASE_URL,
  topNav: [
    {
      element: GithubStars({ repo: "langwatch/scenario" }),
    },
  ],
});
