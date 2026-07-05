
class ChatDialog extends HTMLElement {

    constructor() {
        super();
        this._history = [];
        this._user_message_count = 0;
    }
  
_appendUserMessage(text, store = true) {

    // Increment turn counter
    this._user_message_count += 1;
    const turn = this._user_message_count;

    // Store history
    if (store) {
        this._history.push({
            role: "user",
            content: text,
            turn
        });
    }

    // ── Turn container ─────────────────────────────
    const turnEl = document.createElement("div");
    turnEl.className = "chat-turn";
    turnEl.dataset.turn = turn;

    // ── User row (right aligned) ───────────────────
    const userRow = document.createElement("div");
    userRow.className = "chat-user-row";

    // Action icons
    const actions = document.createElement("div");
    actions.className = "chat-user-actions";

    const deleteIcon = document.createElement("span");
    deleteIcon.className = "chat-icon delete";
    deleteIcon.title = "Delete";
    deleteIcon.textContent = "🗑️";
    
    /*add the edit icon here*/
const editIcon = document.createElement("span");
editIcon.className = "chat-icon edit";
editIcon.title = "Edit";
editIcon.textContent = "✏️";

editIcon.addEventListener("click", (ev) => {
    const turnEl = ev.currentTarget.closest(".chat-turn");
    const turn = turnEl ? Number(turnEl.dataset.turn) : undefined;
    if (!Number.isFinite(turn)) return;

    this.dispatchEvent(new CustomEvent("chat:edit-turn", {
        bubbles: true,
        composed: true,
        detail: { turn }
    }));
});

    

    // Emit custom event (no direct deletion here)
    deleteIcon.addEventListener("click", (ev) => {
        const turnEl = ev.currentTarget.closest(".chat-turn");
        const turn = turnEl ? Number(turnEl.dataset.turn) : undefined;
        
        console.log('Emitting delete turn ', turn )
        if (!Number.isFinite(turn)) return;

        
        this.dispatchEvent(new CustomEvent("chat:delete-turn", {
            bubbles: true,
            composed: true,
            detail: { turn }
        }));
    });


    actions.appendChild(editIcon);
    actions.appendChild(deleteIcon);

    
    // User pill
    const pill = document.createElement("div");
    pill.className = "chat-user-pill";
    pill.innerHTML = `<span class="xbadge me-2">user</span>${text}`;

    userRow.appendChild(actions);
    userRow.appendChild(pill);

    // ── Assistant container ─────────────────────────
    const assistantRow = document.createElement("div");
    assistantRow.className = "chat-assistant-row";

    // Assemble
    turnEl.appendChild(userRow);
    turnEl.appendChild(assistantRow);

    this._historyEl.appendChild(turnEl);
    this._autoScroll();
}

    
deleteTurn(turn) {

    // Remove DOM
    const turnEl = this._historyEl.querySelector(
        `[data-turn="${turn}"]`
    );
    if (turnEl) {
        turnEl.remove();
    }

    // Remove history entries for this turn
    this._history = this._history.filter(
        item => item.turn !== turn
    );

    // Optional: update counter if last turn deleted
    //if (turn === this.user_message_count) {
     //   this.user_message_count -= 1;
    //}
}

v1_appendUserMessage(text, store = true) {

    this.user_message_count += 1;
    const turn = this.user_message_count;

    if (store) {
        this._history.push({
            role: "user",
            content: text,
            turn
        });
    }

    // 🔴 Turn container
    const turnEl = document.createElement("div");
    turnEl.className = "chat-turn";
    turnEl.dataset.turn = turn;

    // User row (right aligned)
    const userRow = document.createElement("div");
    userRow.className = "chat-user-row";

    const pill = document.createElement("div");
    pill.className = "chat-user-pill";
    pill.innerHTML = `<span class="xbadge me-2">user</span>${text}`;

    userRow.appendChild(pill);

    // Assistant row (full width)
    const assistantRow = document.createElement("div");
    assistantRow.className = "chat-assistant-row";

    turnEl.appendChild(userRow);
    turnEl.appendChild(assistantRow);

    this._historyEl.appendChild(turnEl);
    this._autoScroll();
}

addAssistantResponseAsHTML(html, turn_counter = undefined) {

    this._history.push({
        role: "assistant",
        content: html,
        turn: turn_counter ?? this.user_message_count
    });

    let turnEl;

    if (turn_counter !== undefined) {
        turnEl = this._historyEl.querySelector(
            `[data-turn="${turn_counter}"]`
        );
    } else {
        // last turn
        turnEl = this._historyEl.querySelector(
            ".chat-turn:last-of-type"
        );
    }

    if (!turnEl) return;

    const assistantRow = turnEl.querySelector(".chat-assistant-row");

    const msg = document.createElement("div");
    msg.className = "msg assistant";
    msg.innerHTML = html;

    assistantRow.appendChild(msg);
    this._autoScroll();
}
 
   
    
    

    getHistory() {
        return JSON.parse(JSON.stringify(this._history));
    }

    setHistory(historyArray) {
        if (!Array.isArray(historyArray)) return;

        this._history = historyArray
            .map(m => ({
                role: (m.role || "").toLowerCase(),
                content: String(m.content || "")
            }))
            .filter(m => m.role === "user" || m.role === "assistant");

        this._redrawHistory();
    }

    showBusy(value) {
        let indicator = this.querySelector("#busy-indicator");

        if (value) {
            if (!indicator) {
                indicator = document.createElement("div");
                indicator.id = "busy-indicator";
                indicator.style.padding = "8px";
                indicator.style.color = "red";
                indicator.style.fontStyle = "italic";
                indicator.style.fontWeight = "bold";
                indicator.textContent = "...busy...";
                this._historyEl.insertAdjacentElement("afterend", indicator);
            }
            indicator.style.display = "block";
        } else if (indicator) {
            indicator.style.display = "none";
        }
    }

    _redrawHistory() {
        if (!this._historyEl) return;

        this._historyEl.innerHTML = "";
        for (const msg of this._history) {
            if (msg.role === "user") {
                this._appendUserMessage(msg.content, false);
            } else {
                this._appendAssistantMessage(msg.content, false);
            }
        }
        this._historyEl.scrollTop = this._historyEl.scrollHeight;
    }

    
connectedCallback() {
    if (this._rendered) return;
    this._rendered = true;

    this.innerHTML = `
        <div class="wf-chatbox">

            <div class="wf-chatbox-header">
                <div class="wf-chatbox-logo"></div>
            </div>

            <div class="wf-chatbox-title">
                Waterflood insights analytics
            </div>

            <!--div class="wf-chatbox-subtitle">
                Here are some suggestions to get you started.
            </div-->

            <!--div id="history" class="wf-chatbox-suggestions"></div-->
            <div class="wf-chatbox-history"></div>


            <div id="busy-indicator" style="display:none;">
                ...busy...
            </div>

            <div class="wf-chatbox-input-row">
                <input id="chatInput"
                       class="wf-chatbox-input"
                       placeholder="Ask ..."
                       type="text">

                <button id="sendBtn"
                        class="wf-chatbox-send"
                        type="button">
                    ➤
                </button>
            </div>

        </div>
    `;

    this._historyEl = this.querySelector(".wf-chatbox-history");
    
    this._inputEl = this.querySelector("#chatInput");
    this._sendBtn = this.querySelector("#sendBtn");

    this._sendBtn.addEventListener("click", () => this._handleSend());

    this._inputEl.addEventListener("keydown", evt => {
        if (evt.key === "Enter") {
            evt.preventDefault();
            this._handleSend();
        }
    });
}
    
    
    
    
    _handleSend() {
        const text = (this._inputEl.value || "").trim();
        if (!text) return;

        this._appendUserMessage(text);
        this._inputEl.value = "";
        //console.log('Dispatching user query event chat:user_message');
        this.dispatchEvent(new CustomEvent("chat:user_message", {
            bubbles: true,
            detail: { text }
        }));
    }

    


    _appendAssistantMessage(text, store = true) {
        if (store) this._history.push({ role: "assistant", content: text });

        const wrap = document.createElement("div");
        wrap.style.marginBottom = "8px";

        const bubble = document.createElement("div");
        bubble.style.background = "#f0f0f0";
        bubble.style.padding = "8px";
        bubble.style.borderRadius = "6px";
        bubble.innerHTML = text.replace(/\n/g, "<br>");

        wrap.appendChild(bubble);
        this._historyEl.appendChild(wrap);
        this._autoScroll();
    }

    _appendAssistantTableFromPresenter(item) {
        const wrap = document.createElement("div");
        wrap.style.marginBottom = "8px";

        const bubble = document.createElement("div");
        bubble.style.background = "#f0f0f0";
        bubble.style.padding = "8px";
        bubble.style.borderRadius = "6px";

        if (item.title) {
            bubble.innerHTML += `<strong>${item.title}</strong><br>`;
        }

        const table = document.createElement("table");
        table.style.width = "100%";
        table.style.borderCollapse = "collapse";

        const headerRow = document.createElement("tr");
        item.data.columns.forEach(col => {
            const th = document.createElement("th");
            th.textContent = col.header;
            th.style.border = "1px solid #ccc";
            th.style.padding = "4px";
            headerRow.appendChild(th);
        });
        table.appendChild(headerRow);

        item.data.rows.forEach(row => {
            const tr = document.createElement("tr");
            item.data.columns.forEach(col => {
                const td = document.createElement("td");
                td.textContent = row[col.field] ?? "";
                td.style.border = "1px solid #ccc";
                td.style.padding = "4px";
                tr.appendChild(td);
            });
            table.appendChild(tr);
        });

        bubble.appendChild(table);
        wrap.appendChild(bubble);
        this._historyEl.appendChild(wrap);
        this._autoScroll();
    }

    receiveAssistantResponseAsPlainText(text, options = {}) {
        
        
        function escapeHtml(str) {
          return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
        }
        
        text = escapeHtml( text ).replace(/\n/g, "<br>");
        
        
        const prefix = options.prefix ?? "";//"⚠️";

        const wrap = document.createElement("div");
        wrap.style.marginBottom = "8px";

        const bubble = document.createElement("div");
        bubble.style.background = "#fff5f5";
        bubble.style.border = "1px solid #fecaca";
        bubble.style.padding = "8px";
        bubble.style.borderRadius = "6px";
        bubble.style.fontFamily = "monospace";
        bubble.innerHTML = `<strong>${prefix}</strong> ${text}`;

        wrap.appendChild(bubble);
        this._historyEl.appendChild(wrap);
        this._autoScroll();
    }

    clearChat() {
        if (this._historyEl) this._historyEl.innerHTML = "";
    }

    _autoScroll() {
        setTimeout(() => {
            this._historyEl.scrollTop = this._historyEl.scrollHeight;
        }, 0);
    }

    getLastUserMessage() {
        for (let i = this._history.length - 1; i >= 0; i--) {
            if (this._history[i].role === "user") {
                return this._history[i].content;
            }
        }
        return null;
    }
}

customElements.define("chat-dialog", ChatDialog);


















class BackupChatDialog extends HTMLElement {

    constructor() {
        super();
        this._history = [];
        this._user_message_count = 0;
    }
  
_appendUserMessage(text, store = true) {

    // Increment turn counter
    this._user_message_count += 1;
    const turn = this._user_message_count;

    // Store history
    if (store) {
        this._history.push({
            role: "user",
            content: text,
            turn
        });
    }

    // ── Turn container ─────────────────────────────
    const turnEl = document.createElement("div");
    turnEl.className = "chat-turn";
    turnEl.dataset.turn = turn;

    // ── User row (right aligned) ───────────────────
    const userRow = document.createElement("div");
    userRow.className = "chat-user-row";

    // Action icons
    const actions = document.createElement("div");
    actions.className = "chat-user-actions";

    const deleteIcon = document.createElement("span");
    deleteIcon.className = "chat-icon delete";
    deleteIcon.title = "Delete";
    deleteIcon.textContent = "🗑️";
    
    /*add the edit icon here*/
const editIcon = document.createElement("span");
editIcon.className = "chat-icon edit";
editIcon.title = "Edit";
editIcon.textContent = "✏️";

editIcon.addEventListener("click", (ev) => {
    const turnEl = ev.currentTarget.closest(".chat-turn");
    const turn = turnEl ? Number(turnEl.dataset.turn) : undefined;
    if (!Number.isFinite(turn)) return;

    this.dispatchEvent(new CustomEvent("chat:edit-turn", {
        bubbles: true,
        composed: true,
        detail: { turn }
    }));
});

    

    // Emit custom event (no direct deletion here)
    deleteIcon.addEventListener("click", (ev) => {
        const turnEl = ev.currentTarget.closest(".chat-turn");
        const turn = turnEl ? Number(turnEl.dataset.turn) : undefined;
        
        console.log('Emitting delete turn ', turn )
        if (!Number.isFinite(turn)) return;

        
        this.dispatchEvent(new CustomEvent("chat:delete-turn", {
            bubbles: true,
            composed: true,
            detail: { turn }
        }));
    });


    actions.appendChild(editIcon);
    actions.appendChild(deleteIcon);

    
    // User pill
    const pill = document.createElement("div");
    pill.className = "chat-user-pill";
    pill.innerHTML = `<span class="xbadge me-2">user</span>${text}`;

    userRow.appendChild(actions);
    userRow.appendChild(pill);

    // ── Assistant container ─────────────────────────
    const assistantRow = document.createElement("div");
    assistantRow.className = "chat-assistant-row";

    // Assemble
    turnEl.appendChild(userRow);
    turnEl.appendChild(assistantRow);

    this._historyEl.appendChild(turnEl);
    this._autoScroll();
}

    
deleteTurn(turn) {

    // Remove DOM
    const turnEl = this._historyEl.querySelector(
        `[data-turn="${turn}"]`
    );
    if (turnEl) {
        turnEl.remove();
    }

    // Remove history entries for this turn
    this._history = this._history.filter(
        item => item.turn !== turn
    );

    // Optional: update counter if last turn deleted
    //if (turn === this.user_message_count) {
     //   this.user_message_count -= 1;
    //}
}

v1_appendUserMessage(text, store = true) {

    this.user_message_count += 1;
    const turn = this.user_message_count;

    if (store) {
        this._history.push({
            role: "user",
            content: text,
            turn
        });
    }

    // 🔴 Turn container
    const turnEl = document.createElement("div");
    turnEl.className = "chat-turn";
    turnEl.dataset.turn = turn;

    // User row (right aligned)
    const userRow = document.createElement("div");
    userRow.className = "chat-user-row";

    const pill = document.createElement("div");
    pill.className = "chat-user-pill";
    pill.innerHTML = `<span class="xbadge me-2">user</span>${text}`;

    userRow.appendChild(pill);

    // Assistant row (full width)
    const assistantRow = document.createElement("div");
    assistantRow.className = "chat-assistant-row";

    turnEl.appendChild(userRow);
    turnEl.appendChild(assistantRow);

    this._historyEl.appendChild(turnEl);
    this._autoScroll();
}

addAssistantResponseAsHTML(html, turn_counter = undefined) {

    this._history.push({
        role: "assistant",
        content: html,
        turn: turn_counter ?? this.user_message_count
    });

    let turnEl;

    if (turn_counter !== undefined) {
        turnEl = this._historyEl.querySelector(
            `[data-turn="${turn_counter}"]`
        );
    } else {
        // last turn
        turnEl = this._historyEl.querySelector(
            ".chat-turn:last-of-type"
        );
    }

    if (!turnEl) return;

    const assistantRow = turnEl.querySelector(".chat-assistant-row");

    const msg = document.createElement("div");
    msg.className = "msg assistant";
    msg.innerHTML = html;

    assistantRow.appendChild(msg);
    this._autoScroll();
}
 
    this_is_old_xaddAssistantResponseAsHTML(html, turn_counter = undefined ) {
        this._history.push({
            role: "assistant",
            content: html,
            user_message_count:this.user_message_count 
        });
        
        // Robust default
        const targetCount = turn_counter ?? this.user_message_count;

        
        //refactor this so the new html is added under the div for which dataset.userMessageCount is turn_counter
        const container = this.querySelector(".chat-scroll");
        const msg = document.createElement("div");
        msg.className = "msg assistant";
        msg.innerHTML = html;
        container.appendChild(msg);
        container.scrollTop = container.scrollHeight;
        
        
    }
    
    this_is_old_x_appendUserMessage(text, store = true) {
        
        this.user_message_count = this.user_message_count + 1  
        const msgCount = this.user_message_count;
        
        if (store) this._history.push({ role: "user", content: text, user_message_count:msgCount});

        const wrap = document.createElement("div");
        wrap.className = "d-flex justify-content-end mb-2";
        
        wrap.dataset.userMessageCount = msgCount;
        
        const bubble = document.createElement("div");
        bubble.className = "p-2 rounded-3 shadow-sm chat-user-pill";
        //bubble.style.background = "#d1fae5";
        //bubble.style.maxWidth = "80%";
        bubble.innerHTML = `<span class="xbadge me-2">user</span>${text}`;

        wrap.appendChild(bubble);
        this._historyEl.appendChild(wrap);
        this._autoScroll();
    }

    
    
    

    getHistory() {
        return JSON.parse(JSON.stringify(this._history));
    }

    setHistory(historyArray) {
        if (!Array.isArray(historyArray)) return;

        this._history = historyArray
            .map(m => ({
                role: (m.role || "").toLowerCase(),
                content: String(m.content || "")
            }))
            .filter(m => m.role === "user" || m.role === "assistant");

        this._redrawHistory();
    }

    showBusy(value) {
        let indicator = this.querySelector("#busy-indicator");

        if (value) {
            if (!indicator) {
                indicator = document.createElement("div");
                indicator.id = "busy-indicator";
                indicator.style.padding = "8px";
                indicator.style.color = "red";
                indicator.style.fontStyle = "italic";
                indicator.style.fontWeight = "bold";
                indicator.textContent = "...busy...";
                this._historyEl.insertAdjacentElement("afterend", indicator);
            }
            indicator.style.display = "block";
        } else if (indicator) {
            indicator.style.display = "none";
        }
    }

    _redrawHistory() {
        if (!this._historyEl) return;

        this._historyEl.innerHTML = "";
        for (const msg of this._history) {
            if (msg.role === "user") {
                this._appendUserMessage(msg.content, false);
            } else {
                this._appendAssistantMessage(msg.content, false);
            }
        }
        this._historyEl.scrollTop = this._historyEl.scrollHeight;
    }

    connectedCallback() {
        if (this._rendered) return;
        this._rendered = true;


        this.innerHTML = `
            <div style="padding:10px; display:flex; flex-direction:column; height:80%;">
                <div id="history" class="chat-scroll p-2 border rounded bg-white"
                     sssstyle="min-height:100px; overflow-y:auto; margin-bottom:10px;"></div>

                <div id="busy-indicator" class="chat-busy-indicator"
                     xxxstyle="padding:8px; color:red; font-style:italic; font-weight:bold; display:none;">
                    ...busy...
                </div>

                <div style="display:flex; justify-content:flex-end; margin:5px;">

                    <button id="sendBtn"
                            class="btn btn-success px-3 chat-send-button"
                            xxstyle="border:1px solid darkgreen; border-radius:5px;min-width:200px">
                        Go
                    </button>

                    <button id="clearBtn" class="btn xxbtn-sm btn-secondary xxmb-2 chat-clear-button">Clear</button>


                </div>

                <div class="d-flex gap-2 align-items-stretch">
                    <textarea id="chatInput" class="form-control form-control-sm chat-text-input"
                              rows="2" placeholder="Write your message here..."
                              ccstyle="font-size:1.3rem;"></textarea>

                </div>
            </div>
        `;

        this._historyEl = this.querySelector("#history");
        this._inputEl = this.querySelector("#chatInput");
        this._sendBtn = this.querySelector("#sendBtn");
        this._clearBtn = this.querySelector("#clearBtn");

        this._sendBtn.addEventListener("click", () => this._handleSend());
        this._clearBtn.addEventListener("click", () => this.clearChat());

        this._inputEl.addEventListener("keydown", evt => {
            if (evt.key === "Enter" && !evt.shiftKey) {
                evt.preventDefault();
                this._handleSend();
            }
        });
    }

    _handleSend() {
        const text = (this._inputEl.value || "").trim();
        if (!text) return;

        this._appendUserMessage(text);
        this._inputEl.value = "";
        //console.log('Dispatching user query event chat:user_message');
        this.dispatchEvent(new CustomEvent("chat:user_message", {
            bubbles: true,
            detail: { text }
        }));
    }

    


    _appendAssistantMessage(text, store = true) {
        if (store) this._history.push({ role: "assistant", content: text });

        const wrap = document.createElement("div");
        wrap.style.marginBottom = "8px";

        const bubble = document.createElement("div");
        bubble.style.background = "#f0f0f0";
        bubble.style.padding = "8px";
        bubble.style.borderRadius = "6px";
        bubble.innerHTML = text.replace(/\n/g, "<br>");

        wrap.appendChild(bubble);
        this._historyEl.appendChild(wrap);
        this._autoScroll();
    }

    _appendAssistantTableFromPresenter(item) {
        const wrap = document.createElement("div");
        wrap.style.marginBottom = "8px";

        const bubble = document.createElement("div");
        bubble.style.background = "#f0f0f0";
        bubble.style.padding = "8px";
        bubble.style.borderRadius = "6px";

        if (item.title) {
            bubble.innerHTML += `<strong>${item.title}</strong><br>`;
        }

        const table = document.createElement("table");
        table.style.width = "100%";
        table.style.borderCollapse = "collapse";

        const headerRow = document.createElement("tr");
        item.data.columns.forEach(col => {
            const th = document.createElement("th");
            th.textContent = col.header;
            th.style.border = "1px solid #ccc";
            th.style.padding = "4px";
            headerRow.appendChild(th);
        });
        table.appendChild(headerRow);

        item.data.rows.forEach(row => {
            const tr = document.createElement("tr");
            item.data.columns.forEach(col => {
                const td = document.createElement("td");
                td.textContent = row[col.field] ?? "";
                td.style.border = "1px solid #ccc";
                td.style.padding = "4px";
                tr.appendChild(td);
            });
            table.appendChild(tr);
        });

        bubble.appendChild(table);
        wrap.appendChild(bubble);
        this._historyEl.appendChild(wrap);
        this._autoScroll();
    }

    receiveAssistantResponseAsPlainText(text, options = {}) {
        
        
        function escapeHtml(str) {
          return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
        }
        
        text = escapeHtml( text ).replace(/\n/g, "<br>");
        
        
        const prefix = options.prefix ?? "";//"⚠️";

        const wrap = document.createElement("div");
        wrap.style.marginBottom = "8px";

        const bubble = document.createElement("div");
        bubble.style.background = "#fff5f5";
        bubble.style.border = "1px solid #fecaca";
        bubble.style.padding = "8px";
        bubble.style.borderRadius = "6px";
        bubble.style.fontFamily = "monospace";
        bubble.innerHTML = `<strong>${prefix}</strong> ${text}`;

        wrap.appendChild(bubble);
        this._historyEl.appendChild(wrap);
        this._autoScroll();
    }

    clearChat() {
        if (this._historyEl) this._historyEl.innerHTML = "";
    }

    _autoScroll() {
        setTimeout(() => {
            this._historyEl.scrollTop = this._historyEl.scrollHeight;
        }, 0);
    }

    getLastUserMessage() {
        for (let i = this._history.length - 1; i >= 0; i--) {
            if (this._history[i].role === "user") {
                return this._history[i].content;
            }
        }
        return null;
    }
}

customElements.define("backup-chat-dialog", BackupChatDialog);

