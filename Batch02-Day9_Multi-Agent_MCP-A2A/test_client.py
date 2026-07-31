"""End-to-end test client for the Legal Multi-Agent System.

Sends a legal question to the Customer Agent and prints the response.
"""

import asyncio
import os
import sys
import time

import httpx
from dotenv import load_dotenv

from common.a2a_client import _extract_text

load_dotenv()

CUSTOMER_AGENT_URL = os.getenv("CUSTOMER_AGENT_URL", "http://localhost:10100")

QUESTION = (
    "If a company breaks a contract and avoids taxes, "
    "what are the legal and regulatory consequences?"
)


async def main() -> None:
    print(f"Connecting to Customer Agent at {CUSTOMER_AGENT_URL}")
    print(f"Question: {QUESTION}")
    print("-" * 60)

    async with httpx.AsyncClient(timeout=300.0) as http_client:
        # Resolve agent card
        card_url = f"{CUSTOMER_AGENT_URL}/.well-known/agent.json"
        try:
            card_resp = await http_client.get(card_url)
            card_resp.raise_for_status()
        except Exception as e:
            print(f"ERROR: Could not reach Customer Agent at {card_url}")
            print(f"  {e}")
            print("Make sure all services are running (./start_all.sh)")
            sys.exit(1)

        from a2a.types import AgentCard, Message, Part, Role, TextPart, MessageSendParams
        from a2a.client import A2AClient
        from uuid import uuid4

        agent_card = AgentCard.model_validate(card_resp.json())
        print(f"Connected to agent: {agent_card.name} v{agent_card.version}")
        print("-" * 60)

        # Build the legacy A2AClient
        client = A2AClient(httpx_client=http_client, agent_card=agent_card)

        # Construct the message
        from a2a.types import SendMessageRequest, MessageSendParams as MSP
        message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=QUESTION))],
            message_id=str(uuid4()),
        )
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MSP(message=message),
        )

        print("Sending request (this may take 30-60s while agents chain)...\n")
        started_at = time.perf_counter()
        response = await client.send_message(request)
        latency = time.perf_counter() - started_at

        result_text = _extract_text(response)
        task_state = ""
        root = response.root if hasattr(response, "root") else response
        result = getattr(root, "result", None)
        status = getattr(result, "status", None)
        state = getattr(status, "state", None)
        if state is not None:
            task_state = getattr(state, "value", str(state))

        if result_text:
            print("RESPONSE:")
            print("=" * 60)
            print(result_text)
            print("=" * 60)
            if task_state:
                print(f"Task state: {task_state}")
            print(f"Latency: {latency:.2f} seconds")
            if task_state == "failed":
                sys.exit(1)
        else:
            print("No text response received. Raw response:")
            print(response)
            if task_state:
                print(f"Task state: {task_state}")
            print(f"Latency: {latency:.2f} seconds")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
