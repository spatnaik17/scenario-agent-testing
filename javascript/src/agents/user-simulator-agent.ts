import { generateText, CoreMessage } from "ai";
import { TestingAgentConfig } from "./types";
import { messageRoleReversal } from "./utils";
import { getProjectConfig } from "../config";
import {
  AgentInput,
  UserSimulatorAgentAdapter,
  DEFAULT_TEMPERATURE,
} from "../domain";
import { mergeAndValidateConfig } from "../utils/config";
import { Logger } from "../utils/logger";

function buildSystemPrompt(description: string): string {
  return `
<role>
You are pretending to be a user, you are testing an AI Agent (shown as the user role) based on a scenario.
Approach this naturally, as a human user would, with very short inputs, few words, all lowercase, imperative, not periods, like when they google or talk to chatgpt.
</role>

<goal>
Your goal (assistant) is to interact with the Agent Under Test (user) as if you were a human user to see if it can complete the scenario successfully.
</goal>

<scenario>
${description}
</scenario>

<rules>
- DO NOT carry over any requests yourself, YOU ARE NOT the assistant today, you are the user
</rules>
`.trim();
}

class UserSimulatorAgent extends UserSimulatorAgentAdapter {
  private logger = new Logger(this.constructor.name);

  constructor(private readonly cfg?: TestingAgentConfig) {
    super();
  }

  call = async (input: AgentInput) => {
    const config = this.cfg;

    const systemPrompt =
      config?.systemPrompt ??
      buildSystemPrompt(input.scenarioConfig.description);
    const messages: CoreMessage[] = [
      { role: "system", content: systemPrompt },
      { role: "assistant", content: "Hello, how can I help you today" },
      ...input.messages,
    ];

    const projectConfig = await getProjectConfig();
    const mergedConfig = mergeAndValidateConfig(config ?? {}, projectConfig);
    if (!mergedConfig.model) {
      throw new Error("Model is required for the user simulator agent");
    }

    // User to assistant role reversal
    // LLM models are biased to always be the assistant not the user, so we need to do
    // this reversal otherwise models like GPT 4.5 is super confused, and Claude 3.7
    // even starts throwing exceptions.
    const reversedMessages = messageRoleReversal(messages);

    const completion = await this.generateText({
      model: mergedConfig.model,
      messages: reversedMessages,
      temperature: mergedConfig.temperature ?? DEFAULT_TEMPERATURE,
      maxOutputTokens: mergedConfig.maxTokens,
    });

    const messageContent = completion.text;
    if (!messageContent) {
      throw new Error("No response content from LLM");
    }

    return { role: "user", content: messageContent } satisfies CoreMessage;
  };

  private async generateText(input: Parameters<typeof generateText>[0]) {
    try {
      return await generateText(input);
    } catch (error) {
      this.logger.error("Error generating text", { error });
      throw error;
    }
  }
}

/**
 * Agent that simulates realistic user behavior in scenario conversations.
 *
 * This agent generates user messages that are appropriate for the given scenario
 * context, simulating how a real human user would interact with the agent under test.
 * It uses an LLM to generate natural, contextually relevant user inputs that help
 * drive the conversation forward according to the scenario description.
 *
 * @param config Optional configuration for the agent.
 * @param config.model The language model to use for generating responses.
 *                     If not provided, a default model will be used.
 * @param config.temperature The temperature for the language model (0.0-1.0).
 *                          Lower values make responses more deterministic.
 *                          Defaults to {@link DEFAULT_TEMPERATURE}.
 * @param config.maxTokens The maximum number of tokens to generate.
 *                        If not provided, uses model defaults.
 * @param config.name The name of the agent.
 * @param config.systemPrompt Custom system prompt to override default user simulation behavior.
 *                           Use this to create specialized user personas or behaviors.
 *
 * @throws {Error} If no model is configured either in parameters or global config.
 *
 * @example
 * ```typescript
 * import { run, userSimulatorAgent, AgentRole, user, agent, AgentAdapter } from '@langwatch/scenario';
 *
 * const myAgent: AgentAdapter = {
 *   role: AgentRole.AGENT,
 *   async call(input) {
 *     return `The user said: ${input.messages.at(-1)?.content}`;
 *   }
 * };
 *
 * async function main() {
 *   // Basic user simulator with default behavior
 *   const basicResult = await run({
 *     name: "User Simulator Test",
 *     description: "A simple test to see if the user simulator works.",
 *     agents: [myAgent, userSimulatorAgent()],
 *     script: [
 *       user(),
 *       agent(),
 *     ],
 *   });
 *
 *   // Customized user simulator
 *   const customResult = await run({
 *     name: "Expert User Test",
 *     description: "User seeks help with TypeScript programming",
 *     agents: [
 *       myAgent,
 *       userSimulatorAgent({
 *         model: openai("gpt-4"),
 *         temperature: 0.3,
 *         systemPrompt: "You are a technical user who asks detailed questions"
 *       })
 *     ],
 *     script: [
 *       user(),
 *       agent(),
 *     ],
 *   });
 *
 *   // User simulator with custom persona
 *   const expertResult = await run({
 *     name: "Expert Developer Test",
 *     description: "Testing with a technical expert user persona.",
 *     agents: [
 *       myAgent,
 *       userSimulatorAgent({
 *         systemPrompt: `
 *           You are an expert software developer testing an AI coding assistant.
 *           Ask challenging, technical questions and be demanding about code quality.
 *           Use technical jargon and expect detailed, accurate responses.
 *         `
 *       })
 *     ],
 *     script: [
 *       user(),
 *       agent(),
 *     ],
 *   });
 * }
 * main();
 * ```
 *
 * **Implementation Notes:**
 * - Uses role reversal internally to work around LLM biases toward assistant roles
 */
export const userSimulatorAgent = (config?: TestingAgentConfig) => {
  return new UserSimulatorAgent(config);
};
