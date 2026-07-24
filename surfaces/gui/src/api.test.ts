import { afterEach, describe, expect, it, vi } from "vitest";

import { detectProvider, Session } from "./api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("detectProvider", () => {
  it("recognizes TrustedRouter keys before the generic OpenAI prefix", () => {
    expect(detectProvider("sk-tr-v1-test")).toBe("trustedrouter");
    expect(detectProvider("sk-proj-test")).toBe("openai");
  });
});

describe("Session", () => {
  it("marks confidential sockets explicitly in addition to the reserved session id", () => {
    const urls: string[] = [];
    class FakeWebSocket {
      static CONNECTING = 0;
      static OPEN = 1;
      readyState = FakeWebSocket.CONNECTING;
      onopen: (() => void) | null = null;
      onmessage: ((event: { data: string }) => void) | null = null;
      onclose: (() => void) | null = null;

      constructor(url: string) {
        urls.push(url);
      }

      send() {}
      close() {}
    }
    vi.stubGlobal("WebSocket", FakeWebSocket);

    const session = new Session(
      "__confidential__unit",
      "",
      "chat",
      { onEvent: vi.fn() },
      { confidential: true },
    );

    expect(urls[0]).toContain("/ws/session/__confidential__unit?");
    expect(urls[0]).toContain("agent=chat");
    expect(urls[0]).toContain("confidential=1");
    session.close();
  });
});
