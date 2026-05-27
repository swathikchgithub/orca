"""
agent/orchestrator.py — ORCA's Orchestrator (The Heart)

🧠 What this does (5-year-old version):
   This is the conductor of an orchestra. 🎼
   It doesn't play any instrument itself.
   But it tells every instrument WHEN to play and HOW LOUD.

   Memory plays first → then Guardrail checks → then LLM answers
   → then Guardrail checks again → then Composer wraps it up.

   The orchestrator is the ONLY file that knows about all the others.
   Everything else is isolated. That's clean architecture.

🏗️ Flow for each mode:

   SINGLE-TURN:
   user_message → guardrail(input) → build_prompt → LLM → guardrail(output) → compose → OrcaResponse

   MULTI-TURN:
   user_message → guardrail(input) → load_memory → build_prompt → LLM
               → guardrail(output) → save_memory → compose → OrcaResponse

   AGENTIC:
   user_message → guardrail(input) → load_memory → build_plan → loop(
       pick_tool → run_tool → observe_result → decide_next
   ) → guardrail(output) → save_memory → compose → OrcaResponse
"""

import time
import config
from openai import OpenAI

from agent.memory              import ConversationMemory
from agent.guardrail           import OrcaGuardrail
from agent.tool_router         import OrcaToolRouter
from agent.response_composer   import OrcaResponseComposer, OrcaResponse
from agent.prompts.prompt_loader import load_prompt


# ─────────────────────────────────────────────
# 🐋 OrcaOrchestrator — the heart of ORCA
# ─────────────────────────────────────────────

class OrcaOrchestrator:
    """
    The main entry point for all ORCA interactions.

    Usage:
        orca = OrcaOrchestrator()

        # Single-turn
        response = orca.chat("What is the capital of France?", mode="single_turn")
        print(response.content)

        # Multi-turn (same orchestrator, keeps memory)
        response = orca.chat("My name is Swathi", mode="multi_turn")
        response = orca.chat("What is my name?",  mode="multi_turn")
        print(response.content)  # "Your name is Swathi"

        # Agentic
        response = orca.chat("What is 15% tip on $47.50?", mode="agentic")
        print(response.content)
    """

    def __init__(self):
        # Initialize all components
        self.client   = OpenAI(api_key=config.OPENAI_API_KEY)
        self.guardrail = OrcaGuardrail()
        self.tool_router = OrcaToolRouter()
        self.composer  = OrcaResponseComposer()

        # One memory per session (persists across multi-turn calls)
        self._memory: dict[str, ConversationMemory] = {}

        print("🐋 ORCA Orchestrator initialized!")
        print(f"   Model  : {config.AGENT_MODEL}")
        print(f"   Judge  : {config.JUDGE_MODEL}")

    # ─────────────────────────────────────────
    # 🚀 MAIN ENTRY POINT
    # ─────────────────────────────────────────

    def chat(
        self,
        user_message: str,
        mode        : str = "single_turn",
        session_id  : str = "default",
    ) -> OrcaResponse:
        """
        Send a message to ORCA and get a response.

        This is the ONE method you call for everything.
        The mode controls how ORCA behaves internally.

        Args:
            user_message : what the user typed
            mode         : "single_turn", "multi_turn", or "agentic"
            session_id   : conversation ID (use same ID for multi-turn)

        Returns:
            OrcaResponse — the fully packaged response
        """
        start_time = time.time()

        # ── Step 1: Guardrail — check INPUT first ──
        input_check = self.guardrail.check_input(user_message)
        if input_check.blocked:
            return self.composer.compose_blocked(
                reason     = input_check.reason,
                safe_msg   = input_check.safe_msg,
                mode       = mode,
                session_id = session_id,
                duration_ms= (time.time() - start_time) * 1000,
            )

        # ── Step 2: Route to correct mode ──
        try:
            if mode == "single_turn":
                content, tool_calls = self._handle_single_turn(user_message)

            elif mode == "multi_turn":
                content, tool_calls = self._handle_multi_turn(
                    user_message, session_id
                )

            elif mode == "agentic":
                content, tool_calls = self._handle_agentic(
                    user_message, session_id
                )

            else:
                raise ValueError(f"Unknown mode: '{mode}'. Use single_turn, multi_turn, or agentic.")

        except Exception as e:
            return self.composer.compose_error(
                error_msg  = str(e),
                mode       = mode,
                session_id = session_id,
                duration_ms= (time.time() - start_time) * 1000,
            )

        # ── Step 3: Guardrail — check OUTPUT ──
        output_check = self.guardrail.check_output(content)
        if output_check.blocked:
            return self.composer.compose_blocked(
                reason     = output_check.reason,
                safe_msg   = output_check.safe_msg,
                mode       = mode,
                session_id = session_id,
                duration_ms= (time.time() - start_time) * 1000,
            )

        # ── Step 4: Compose and return ──
        duration_ms = (time.time() - start_time) * 1000
        return self.composer.compose(
            content     = content,
            mode        = mode,
            duration_ms = duration_ms,
            session_id  = session_id,
            tool_calls  = tool_calls,
        )

    # ─────────────────────────────────────────
    # 1️⃣ SINGLE-TURN HANDLER
    # ─────────────────────────────────────────

    def _handle_single_turn(self, user_message: str) -> tuple[str, list]:
        """
        Handle a single-turn request.
        No memory. One message in. One answer out.
        """
        system_prompt = load_prompt("single_turn")

        messages = [
            {"role": "system",  "content": system_prompt},
            {"role": "user",    "content": user_message},
        ]

        response = self.client.chat.completions.create(
            model       = config.AGENT_MODEL,
            messages    = messages,
            max_tokens  = config.AGENT_MAX_TOKENS,
            temperature = config.AGENT_TEMPERATURE,
        )

        content = response.choices[0].message.content
        return content, []   # no tool calls in single-turn

    # ─────────────────────────────────────────
    # 2️⃣ MULTI-TURN HANDLER
    # ─────────────────────────────────────────

    def _handle_multi_turn(
        self, user_message: str, session_id: str
    ) -> tuple[str, list]:
        """
        Handle a multi-turn request.
        Loads memory → builds full history → calls LLM → saves to memory.
        """
        # Get or create memory for this session
        memory = self._get_or_create_memory(session_id, mode="multi_turn")

        # Add user message to memory
        memory.add_message("user", user_message)

        # Build messages from full history
        messages = memory.get_history_for_llm()

        # Call LLM
        response = self.client.chat.completions.create(
            model       = config.AGENT_MODEL,
            messages    = messages,
            max_tokens  = config.AGENT_MAX_TOKENS,
            temperature = config.AGENT_TEMPERATURE,
        )

        content = response.choices[0].message.content

        # Save ORCA's response to memory
        memory.add_message("assistant", content)

        return content, []   # no tool calls in multi-turn

    # ─────────────────────────────────────────
    # 3️⃣ AGENTIC HANDLER
    # ─────────────────────────────────────────

    def _handle_agentic(
        self, user_message: str, session_id: str
    ) -> tuple[str, list]:
        """
        Handle an agentic request.
        ORCA plans → uses tools → observes results → delivers answer.

        This is a simplified agentic loop:
        1. Ask LLM to make a plan and decide if a tool is needed
        2. If tool needed → run it → feed result back to LLM
        3. LLM delivers final answer with trace
        """
        memory     = self._get_or_create_memory(session_id, mode="agentic")
        tool_calls = []

        # Step 1: Add user goal to memory
        memory.add_message("user", user_message)

        # Step 2: First LLM call — ask ORCA to plan and identify tool need
        plan_messages = memory.get_history_for_llm()
        plan_messages.append({
            "role": "user",
            "content": (
                f"Available tools: {self.tool_router.available_tools()}\n"
                f"If you need a tool, respond with:\n"
                f"TOOL: <tool_name>\nINPUT: <json_input>\n\n"
                f"Otherwise answer directly."
            )
        })

        plan_response = self.client.chat.completions.create(
            model       = config.AGENT_MODEL,
            messages    = plan_messages,
            max_tokens  = config.AGENT_MAX_TOKENS,
            temperature = config.AGENT_TEMPERATURE,
        )
        plan_content = plan_response.choices[0].message.content

        # Step 3: Check if LLM wants to use a tool
        tool_result_text = ""
        if "TOOL:" in plan_content:
            tool_call_result = self._parse_and_run_tool(plan_content)
            if tool_call_result:
                tool_calls.append(tool_call_result)
                tool_result_text = (
                    f"\nTool '{tool_call_result.tool_name}' returned: "
                    f"{tool_call_result.output or tool_call_result.error}"
                )

        # Step 4: Final LLM call — deliver the answer using tool result.
        # Tool result is in an ephemeral messages list, not saved to memory,
        # so synthetic "user" messages don't pollute the conversation history.
        if tool_result_text:
            final_messages = memory.get_history_for_llm() + [
                {"role": "assistant", "content": plan_content},
                {"role": "user",      "content": (
                    f"Tool result:{tool_result_text}\n"
                    f"Now give the final answer to the user clearly."
                )},
            ]
            final_response = self.client.chat.completions.create(
                model       = config.AGENT_MODEL,
                messages    = final_messages,
                max_tokens  = config.AGENT_MAX_TOKENS,
                temperature = config.AGENT_TEMPERATURE,
            )
            content = final_response.choices[0].message.content
        else:
            content = plan_content

        # Save final response to memory
        memory.add_message("assistant", content)

        return content, tool_calls

    # ─────────────────────────────────────────
    # 🔧 HELPERS
    # ─────────────────────────────────────────

    def _get_or_create_memory(
        self, session_id: str, mode: str
    ) -> ConversationMemory:
        """
        Get existing memory for a session or create a new one.
        """
        if session_id not in self._memory:
            system_prompt = load_prompt(mode)
            self._memory[session_id] = ConversationMemory(
                system_prompt=system_prompt
            )
        return self._memory[session_id]

    def _parse_and_run_tool(self, llm_response: str):
        """
        Parse TOOL: / INPUT: from LLM response and run the tool.
        Returns ToolCall result or None if parsing fails.
        """
        import json, re

        try:
            # Extract tool name
            tool_match = re.search(r"TOOL:\s*(\w+)", llm_response)
            if not tool_match:
                return None
            tool_name = tool_match.group(1).strip()

            # Extract input JSON
            input_match = re.search(r"INPUT:\s*(\{.*?\})", llm_response, re.DOTALL)
            if not input_match:
                return None
            input_data = json.loads(input_match.group(1).strip())

            # Run the tool
            return self.tool_router.run_tool(tool_name, input_data)

        except Exception:
            return None

    def reset_session(self, session_id: str = "default"):
        """Clear memory for a session. Use between conversations."""
        if session_id in self._memory:
            del self._memory[session_id]
            print(f"🗑️  Session '{session_id}' cleared.")

    def session_summary(self, session_id: str = "default") -> str:
        """Show memory summary for a session."""
        if session_id not in self._memory:
            return f"No active session: '{session_id}'"
        return self._memory[session_id].summary()


# ─────────────────────────────────────────────
# ✅ TEST IT — run: python agent/orchestrator.py
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("🐋 Testing ORCA Orchestrator — LIVE LLM CALLS!")
    print("=" * 60)

    if not config.OPENAI_API_KEY:
        print("❌ No OpenAI API key found. Add it to .env first!")
        exit(1)

    orca = OrcaOrchestrator()

    # ── Test 1: Single-turn ──
    print("\n1️⃣  SINGLE-TURN TEST")
    print("-" * 40)
    r = orca.chat("What is the capital of Japan?", mode="single_turn")
    print(f"   User : What is the capital of Japan?")
    print(f"   ORCA : {r.content}")
    print(f"   {r.summary()}")
    assert r.success

    # ── Test 2: Multi-turn memory ──
    print("\n2️⃣  MULTI-TURN TEST (memory check)")
    print("-" * 40)
    orca.reset_session("test_multi")

    r1 = orca.chat("My name is Swathi.", mode="multi_turn", session_id="test_multi")
    print(f"   User : My name is Swathi.")
    print(f"   ORCA : {r1.content}")

    r2 = orca.chat("What is my name?", mode="multi_turn", session_id="test_multi")
    print(f"   User : What is my name?")
    print(f"   ORCA : {r2.content}")
    assert "swathi" in r2.content.lower(), "ORCA should remember the name!"
    print("   ✅ ORCA remembered the name!")
    print(f"\n{orca.session_summary('test_multi')}")

    # ── Test 3: Guardrail blocks bad input ──
    print("\n3️⃣  GUARDRAIL TEST")
    print("-" * 40)
    r = orca.chat("how to hack a database", mode="single_turn")
    print(f"   User : how to hack a database")
    print(f"   ORCA : {r.content}")
    assert r.is_blocked
    assert r.tokens_used == 0
    print("   ✅ Guardrail blocked it — cost $0.00!")

    # ── Test 4: Agentic with calculator ──
    print("\n4️⃣  AGENTIC TEST (tool use)")
    print("-" * 40)
    r = orca.chat(
        "Calculate 15% tip on a $47.50 bill.",
        mode="agentic",
        session_id="test_agentic"
    )
    print(f"   User : Calculate 15% tip on a $47.50 bill.")
    print(f"   ORCA : {r.content}")
    print(f"   Tools used: {len(r.tool_calls)}")
    print(f"   {r.summary()}")
    assert r.success

    print("\n" + "=" * 60)
    print("✅ All orchestrator tests passed! ORCA is ALIVE! 🐋🎉")
    print("=" * 60)
