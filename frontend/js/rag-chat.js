(function () {
  "use strict";

  const STORAGE_KEY = "rag_chat_history_v1";
  const MAX_STORED_MESSAGES = 18;
  const CHAT_OPEN_CLASS = "rag-chat-open";

  let isStreaming = false;

  // ensurePageShell();

  const root = document.createElement("div");
  root.className = "rag-chat-root";
  root.innerHTML = `
    <button class="rag-chat-overlay" type="button"></button>
    <button class="rag-chat-toggle" type="button" title="Chat với AI" aria-label="Chat với AI"></button>
    <section class="rag-chat-panel">
      <header class="rag-chat-header">
        <div class="rag-chat-header-row">
          <div class="column-left">
            <h3 class="rag-chat-title">SenseState AI Assistant</h3>
            <p class="rag-chat-subtitle">Online</p>
          </div>
          <div class="column-right">
            <button class="rag-chat-back" type="button" aria-label="Back">Back</button>
          </div>
        </div>
      </header>
      <div class="rag-chat-messages" id="rag-chat-messages"></div>
      <form class="rag-chat-form" id="rag-chat-form">
        <div class="rag-chat-input-wrap">
          <textarea
            class="rag-chat-input"
            id="rag-chat-input"
            placeholder="Căn hộ ở Hà Nội phong thủy tốt dưới 3 tỷ"
            rows="1"
          ></textarea>
          <button class="rag-chat-send" id="rag-chat-send" type="submit">Gửi</button>
        </div>
      </form>
    </section>
  `;

  document.body.appendChild(root);

  const toggleButton = root.querySelector(".rag-chat-toggle");
  const overlayButton = root.querySelector(".rag-chat-overlay");
  const backButton = root.querySelector(".rag-chat-back");
  const messageList = root.querySelector("#rag-chat-messages");
  const form = root.querySelector("#rag-chat-form");
  const input = root.querySelector("#rag-chat-input");
  const sendButton = root.querySelector("#rag-chat-send");

  toggleButton.addEventListener("click", () => {
    setOpenState(!root.classList.contains("open"));
    if (root.classList.contains("open")) {
      input.focus();
      scrollToBottom();
    }
  });

  backButton.addEventListener("click", () => {
    setOpenState(false);
  });

  overlayButton.addEventListener("click", () => {
    setOpenState(false);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && root.classList.contains("open")) {
      setOpenState(false);
    }
  });

  input.addEventListener("input", () => {
    autoResizeInput();
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (isStreaming) {
      return;
    }

    const query = input.value.trim();
    if (!query) {
      return;
    }

    addMessage("user", query);
    input.value = "";
    autoResizeInput();

    const assistantBubble = addMessage("assistant", "", { streaming: true });

    setStreamingState(true);
    try {
      const result = await streamRagAnswer(query, assistantBubble.textEl);
      renderAssistantMessage(assistantBubble.textEl, result.answer);
      persistMessages();
    } catch (error) {
      setMessageText(assistantBubble.textEl, "Có lỗi xảy ra, vui lòng thử lại.");
      console.error(error);
    } finally {
      assistantBubble.textEl.classList.remove("streaming");
      setStreamingState(false);
      scrollToBottom();
    }
  });

  function setStreamingState(state) {
    isStreaming = state;
    sendButton.disabled = state;
    input.disabled = state;
  }

  function setOpenState(isOpen) {
    root.classList.toggle("open", isOpen);
    document.body.classList.toggle(CHAT_OPEN_CLASS, isOpen);
  }

  function ensurePageShell() {
    if (document.querySelector(".rag-chat-page-shell")) {
      return;
    }

    const shell = document.createElement("div");
    shell.className = "rag-chat-page-shell";
    document.body.insertBefore(shell, document.body.firstChild);

    const children = Array.from(document.body.children).filter((node) => {
      return node !== shell && node !== document.currentScript;
    });

    for (const node of children) {
      shell.appendChild(node);
    }
  }

  function autoResizeInput() {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
  }

  function addMessage(role, text, options = {}) {
    const wrap = document.createElement("div");
    wrap.className = `rag-chat-msg-wrap ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "rag-chat-bubble";
    setMessageText(bubble, text);

    if (role === "assistant" && !options.streaming) {
      renderAssistantMessage(bubble, text);
    }

    if (options.streaming) {
      bubble.classList.add("streaming");
    }

    wrap.appendChild(bubble);
    messageList.appendChild(wrap);
    scrollToBottom();

    return { wrap, textEl: bubble };
  }

  function setMessageText(targetEl, text) {
    const safeText = typeof text === "string" ? text : "";
    targetEl.dataset.rawText = safeText;
    targetEl.textContent = safeText;
  }

  function renderAssistantMessage(targetEl, text) {
    const safeText = typeof text === "string" ? text : "";
    targetEl.dataset.rawText = safeText;
    targetEl.textContent = "";

    const linkPattern = /\[([^\]]+)\]\(([^)]+)\)/g;
    let lastIndex = 0;
    let match;

    while ((match = linkPattern.exec(safeText)) !== null) {
      const [rawMatch, label, href] = match;
      const startIndex = match.index;

      if (startIndex > lastIndex) {
        targetEl.appendChild(document.createTextNode(safeText.slice(lastIndex, startIndex)));
      }

      const link = document.createElement("a");
      link.className = "rag-chat-source";
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.href = normalizeAssistantHref(href);
      link.textContent = label;
      targetEl.appendChild(link);

      lastIndex = startIndex + rawMatch.length;
    }

    if (lastIndex < safeText.length) {
      targetEl.appendChild(document.createTextNode(safeText.slice(lastIndex)));
    }

    if (lastIndex === 0) {
      targetEl.textContent = safeText;
    }
  }

  function normalizeAssistantHref(rawHref) {
    const safeHref = typeof rawHref === "string" ? rawHref.trim() : "";
    if (!safeHref) {
      return "#";
    }

    const idMatch = safeHref.match(/\?id=(\d+)/);
    if (idMatch && idMatch[1]) {
      return `property-single.html?id=${encodeURIComponent(idMatch[1])}`;
    }

    return safeHref;
  }


  async function streamRagAnswer(query, textEl) {
    const response = await fetch("/api/rag/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      const detail = await readErrorBody(response);
      throw new Error(detail || "Request failed");
    }

    if (!response.body) {
      return fallbackNonStreaming(query, textEl);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let fullText = "";
    let finalAnswer = "";
    let meta = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const rawLine of lines) {
        const line = rawLine.trim();
        if (!line) {
          continue;
        }

        const payload = JSON.parse(line);
        if (payload.type === "meta") {
          meta = payload;
        }

        if (payload.type === "token") {
          fullText += payload.content || "";
          setMessageText(textEl, fullText);
          scrollToBottom();
        }

        if (payload.type === "done") {
          finalAnswer = payload.answer || fullText;
          setMessageText(textEl, finalAnswer);
        }

        if (payload.type === "error") {
          throw new Error(payload.message || "Streaming error");
        }
      }
    }

    if (!finalAnswer) {
      finalAnswer = fullText;
      setMessageText(textEl, finalAnswer);
    }

    const sources = extractSources(meta?.results || []);
    return { answer: finalAnswer, sources };
  }

  async function readErrorBody(response) {
    try {
      const errorData = await response.json();
      return errorData?.detail?.error || JSON.stringify(errorData);
    } catch {
      return "";
    }
  }

  function extractSources(results) {
    const out = [];
    const seen = new Set();

    for (const item of results) {
      const id = item?.parent_id;
      if (typeof id !== "number" || seen.has(id)) {
        continue;
      }
      seen.add(id);
      out.push({ id });
      if (out.length >= 3) {
        break;
      }
    }

    return out;
  }

  function persistMessages() {
    const records = [];
    for (const wrap of messageList.querySelectorAll(".rag-chat-msg-wrap")) {
      const role = wrap.classList.contains("user") ? "user" : "assistant";
      const bubble = wrap.querySelector(".rag-chat-bubble");
      const text = bubble ? bubble.dataset.rawText || bubble.textContent : "";
      const sources = [];
      for (const link of wrap.querySelectorAll(".rag-chat-source")) {
        const href = link.getAttribute("href") || "";
        const id = Number(new URL(href, window.location.href).searchParams.get("id"));
        if (Number.isFinite(id)) {
          sources.push({ id });
        }
      }
      records.push({ role, text, sources });
    }

    const trimmed = records.slice(-MAX_STORED_MESSAGES);
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
  }

  function restoreMessages() {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) {
      addMessage(
        "assistant",
        "Xin chao! Minh la tro ly bat dong san. Ban co the hoi ve khu vuc, gia, dien tich, huong nha..."
      );
      return;
    }

    try {
      const records = JSON.parse(raw);
      if (!Array.isArray(records) || records.length === 0) {
        throw new Error("Invalid chat history");
      }

      for (const record of records) {
        const { wrap } = addMessage(record.role === "user" ? "user" : "assistant", record.text || "");
      }
    } catch {
      addMessage(
        "assistant",
        "Xin chao! Minh la tro ly bat dong san. Ban co the hoi ve khu vuc, gia, dien tich, huong nha..."
      );
      sessionStorage.removeItem(STORAGE_KEY);
    }
  }

  function scrollToBottom() {
    messageList.scrollTop = messageList.scrollHeight;
  }

  restoreMessages();
})();
