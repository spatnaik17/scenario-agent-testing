import { openai } from "@ai-sdk/openai";
import scenario, { type AgentAdapter, AgentRole } from "@langwatch/scenario";
import { generateText, tool } from "ai";
import { describe, it, expect } from "vitest";
import { z } from "zod";

// Define the weather tool using zod for parameters
const getCurrentWeather = tool({
  description: "Get the current weather in a given city.",
  parameters: z.object({
    city: z.string().describe("The city to get the weather for."),
  }),
  execute: async ({ city }: { city: string }) => {
    // Simulate weather
    const choices = ["sunny", "cloudy", "rainy", "snowy"];
    const temperature = Math.floor(Math.random() * 31);
    const weather = choices[Math.floor(Math.random() * choices.length)];
    return `The weather in ${city} is ${weather} with a temperature of ${temperature}°C.`;
  },
});

const weatherAgent: AgentAdapter = {
  role: AgentRole.AGENT,
  call: async (input) => {
    const response = await generateText({
      model: openai("gpt-4.1"),
      messages: [
        {
          role: "system",
          content: `
            You are a helpful assistant that may help the user with weather information.
            Do not guess the city if they don't provide it.
          `,
        },
        ...input.messages,
      ],
      tools: { get_current_weather: getCurrentWeather },
      toolChoice: "auto",
    });

    if (response.toolCalls && response.toolCalls.length > 0) {
      const toolCall = response.toolCalls[0];
      const toolCallName = toolCall.toolName;

      if (toolCallName === "get_current_weather") {
        return {
          role: "tool",
          toolCallId: toolCall.toolCallId,
          content: [
            {
              type: "tool-result",
              toolName: toolCallName,
              toolCallId: toolCall.toolCallId,
              result: toolCall.args,
            },
          ],
        };
      }
    }

    return response.text;
  },
};

describe("Weather Agent", () => {
  it("should call the get_current_weather tool in the scenario", async () => {
    const result = await scenario.run({
      name: "checking the weather",
      description: `
        The user is planning a boat trip from Barcelona to Rome,
        and is wondering what the weather will be like.
      `,
      agents: [
        weatherAgent,
        scenario.userSimulatorAgent({ model: openai("gpt-4.1") }),
      ],
      script: [
        scenario.user(),
        scenario.agent(),
        (state) => expect(state.hasToolCall("get_current_weather")).toBe(true),
        scenario.succeed(),
      ],
      setId: "javascript-examples",
    });
    expect(result.success).toBe(true);
  });
});
