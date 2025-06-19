import { defineConfig } from "vocs";
import { GithubStars } from "./docs/components/GithubStars";

export default defineConfig({
  title: "Scenario",
  description: "Agent Testing Framework",
  logoUrl: "/images/logo.webp",
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
          link: "/scenario/concepts",
        },
        {
          text: "Writing Scenarios",
          link: "/scenario/writing-scenarios",
        },
        {
          text: "Scripted Simulations",
          link: "/scenario/scripted-simulations",
        },
        {
          text: "Cache",
          link: "/scenario/cache",
        },
        {
          text: "Debug Mode",
          link: "/scenario/debug-mode",
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
          link: `${process.env.BASE_URL ?? "http://localhost:5173"}${process.env.BASE_PATH ?? ""}/reference/python/scenario/index.html`,
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
