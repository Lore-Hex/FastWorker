"""Confidential sessions keep chat state in memory and use TrustedRouter's private route."""

from __future__ import annotations

from fastapi.testclient import TestClient

from coworker.providers import (
    AssistantTurn,
    ModelCapabilities,
    ProviderClient,
    ToolCall,
)
from coworker.permissions import Mode
from coworker.server import SessionManager, create_app
from coworker.sessions import CONFIDENTIAL_MODEL, CONFIDENTIAL_SESSION_PREFIX


class CapturingProvider(ProviderClient):
    def __init__(self, turns: list[AssistantTurn]) -> None:
        self.turns = list(turns)
        self.models: list[str] = []

    def complete(self, *, model, messages, tools=None, **settings):
        self.models.append(model)
        return self.turns.pop(0)

    def capabilities(self, model):
        return ModelCapabilities()


def _text(text: str) -> AssistantTurn:
    return AssistantTurn(text=text, finish_reason="stop")


def _tool(name: str, arguments: dict) -> AssistantTurn:
    return AssistantTurn(
        tool_calls=[ToolCall(id="call_confidential", name=name, arguments=arguments)]
    )


def _receive_until(ws, wanted: str) -> list[dict]:
    events: list[dict] = []
    while True:
        event = ws.receive_json()
        events.append(event)
        if event["type"] == wanted:
            return events


def test_confidential_chat_uses_fixed_route_and_never_persists(tmp_path):
    data_dir = tmp_path / "state"
    provider = CapturingProvider([_text("private answer")])
    manager = SessionManager(
        workspace=tmp_path, data_dir=data_dir, provider=provider
    )
    client = TestClient(create_app(manager))
    session_id = f"{CONFIDENTIAL_SESSION_PREFIX}chat"

    with client.websocket_connect(
        f"/ws/session/{session_id}?agent=chat&confidential=1"
    ) as ws:
        ready = ws.receive_json()
        assert ready["type"] == "ready"
        assert ready["data"]["confidential"] is True
        assert ready["data"]["model"] == CONFIDENTIAL_MODEL

        # A hostile/stale client model cannot move the session off its private route.
        ws.send_json(
            {
                "type": "user_message",
                "text": "do not save this",
                "model": "openai:gpt-5.5",
            }
        )
        events = _receive_until(ws, "turn_done")
        assert any(
            e["type"] == "assistant_message"
            and e["data"]["text"] == "private answer"
            for e in events
        )
        assert [m["role"] for m in manager.session_messages(session_id)] == [
            "system",
            "user",
            "assistant",
        ]

    assert provider.models == [CONFIDENTIAL_MODEL]
    assert manager.session_store.load(session_id) is None
    assert session_id not in {s["session_id"] for s in manager.list_sessions()}
    assert not (data_dir / "conversations" / f"{session_id}.jsonl").exists()
    assert manager.session_messages(session_id) == []

    # Cleanup is idempotent because socket close already erased the live engine.
    deleted = client.delete(f"/v1/sessions/{session_id}").json()
    assert deleted["ok"] is True
    assert manager.session_messages(session_id) == []

    # A new process has no route back to the transcript.
    reborn = SessionManager(workspace=tmp_path, data_dir=data_dir)
    assert reborn.session_store.load(session_id) is None
    assert reborn.session_messages(session_id) == []


def test_confidential_approval_is_live_only_and_tool_action_still_runs(tmp_path):
    data_dir = tmp_path / "state"
    provider = CapturingProvider(
        [
            _tool("write_file", {"path": "result.txt", "content": "kept outside chat\n"}),
            _text("done"),
        ]
    )
    manager = SessionManager(
        workspace=tmp_path, data_dir=data_dir, provider=provider
    )
    client = TestClient(create_app(manager))
    session_id = f"{CONFIDENTIAL_SESSION_PREFIX}approval"

    with client.websocket_connect(
        f"/ws/session/{session_id}?workspace={tmp_path}&agent=cowork&confidential=1"
    ) as ws:
        assert ws.receive_json()["data"]["model"] == CONFIDENTIAL_MODEL
        ws.send_json({"type": "user_message", "text": "write the result"})
        _receive_until(ws, "permission_required")

        # The pending tool call is not checkpointed to either conversation or Inbox storage.
        assert manager.session_store.load(session_id) is None
        assert manager.inbox.pending(session_id) == []
        assert manager.list_audit(session_id=session_id) == []

        ws.send_json({"type": "approval", "decision": "once"})
        events = _receive_until(ws, "turn_done")
        assert any(
            e["type"] == "tool_finished" and e["data"]["status"] == "ok"
            for e in events
        )

    # Incognito-style boundary: external effects remain, local chat/audit history does not.
    assert (tmp_path / "result.txt").read_text() == "kept outside chat\n"
    assert manager.session_store.load(session_id) is None
    assert manager.inbox.pending(session_id) == []
    assert manager.list_audit(session_id=session_id) == []


def test_confidential_question_does_not_create_durable_inbox_item(tmp_path):
    provider = CapturingProvider(
        [
            _tool(
                "ask_user",
                {
                    "question": "Which environment?",
                    "options": ["staging", "production"],
                },
            ),
            _text("using staging"),
        ]
    )
    manager = SessionManager(
        workspace=tmp_path, data_dir=tmp_path / "state", provider=provider
    )
    client = TestClient(create_app(manager))
    session_id = f"{CONFIDENTIAL_SESSION_PREFIX}question"

    with client.websocket_connect(
        f"/ws/session/{session_id}?agent=cowork&confidential=1"
    ) as ws:
        ws.receive_json()
        ws.send_json({"type": "user_message", "text": "deploy it"})
        events = _receive_until(ws, "question_requested")
        question = events[-1]
        assert question["data"]["question"] == "Which environment?"
        assert manager.inbox.pending(session_id) == []
        assert manager.session_store.load(session_id) is None

        ws.send_json({"type": "question_response", "answer": "staging"})
        _receive_until(ws, "turn_done")

    assert manager.inbox.pending(session_id) == []
    assert manager.session_store.load(session_id) is None


def test_confidential_directory_grant_is_live_only(tmp_path):
    provider = CapturingProvider(
        [
            _tool(
                "request_directory",
                {
                    "reason": "Read the supporting files",
                    "path": str(tmp_path),
                    "writable": False,
                },
            ),
            _text("directory granted"),
        ]
    )
    manager = SessionManager(
        workspace=tmp_path, data_dir=tmp_path / "state", provider=provider
    )
    client = TestClient(create_app(manager))
    session_id = f"{CONFIDENTIAL_SESSION_PREFIX}directory"

    with client.websocket_connect(
        f"/ws/session/{session_id}?agent=cowork&confidential=1"
    ) as ws:
        ws.receive_json()
        ws.send_json({"type": "user_message", "text": "read the supporting files"})
        _receive_until(ws, "directory_requested")
        assert manager.inbox.pending(session_id) == []
        assert manager.session_store.load(session_id) is None

        ws.send_json(
            {
                "type": "directory_response",
                "granted": True,
                "path": str(tmp_path),
                "writable": False,
            }
        )
        events = _receive_until(ws, "turn_done")
        assert any(
            e["type"] == "tool_finished" and e["data"]["status"] == "ok"
            for e in events
        )

    assert manager.inbox.pending(session_id) == []
    assert manager.session_store.load(session_id) is None


def test_confidential_plan_approval_is_live_only(tmp_path):
    provider = CapturingProvider(
        [
            _tool("propose_plan", {"plan": "1. Inspect the code. 2. Make the change."}),
            _text("plan complete"),
        ]
    )
    manager = SessionManager(
        workspace=tmp_path,
        data_dir=tmp_path / "state",
        provider=provider,
        mode=Mode.PLAN,
    )
    client = TestClient(create_app(manager))
    session_id = f"{CONFIDENTIAL_SESSION_PREFIX}plan"

    with client.websocket_connect(
        f"/ws/session/{session_id}?agent=cowork&confidential=1"
    ) as ws:
        ws.receive_json()
        ws.send_json({"type": "user_message", "text": "make a plan"})
        _receive_until(ws, "plan_proposed")
        assert manager.inbox.pending(session_id) == []
        assert manager.session_store.load(session_id) is None

        ws.send_json(
            {
                "type": "plan_response",
                "approved": True,
                "mode": "interactive",
            }
        )
        events = _receive_until(ws, "turn_done")
        assert any(
            e["type"] == "tool_finished" and e["data"]["status"] == "ok"
            for e in events
        )

    assert manager.inbox.pending(session_id) == []
    assert manager.session_store.load(session_id) is None


def test_confidential_model_is_in_the_curated_catalog():
    from coworker.providers.matrix import MATRIX

    assert MATRIX[CONFIDENTIAL_MODEL].label.startswith("Confidential")
