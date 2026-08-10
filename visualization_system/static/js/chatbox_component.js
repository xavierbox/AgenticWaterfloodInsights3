class ChatDialog extends HTMLElement {

    /*
    This is just the entry  + tela logo + send button 
    but 
    
    it has a div: wf-chatbox-history-placeholder
    that is hidden, where we can add the chat-history-component, 
    and then we can show it when we want to display the history 
    of the chat.

    Otherwise, the chat-history can be displayed somewhere else 
    */

    constructor() {
        super();
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


            <!--div id="history" class="wf-chatbox-suggestions"></div-->
            <!--div class="wf-chatbox-history"></div-->

            <div class="hidden wf-chatbox-history-placeholder">
            </div>


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

    //this._historyEl = this.querySelector(".wf-chatbox-history");
    
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

class ChartHistoryComponent extends HTMLElement {

            constructor() {
                super();

                this.blockCounter = 0;
                this.chatHistoryContainer = null;
                this._isRendered = false;
            }



clearHistory() {
    if (!this.chatHistoryContainer) {
        return false;
    }

    const charts = this.chatHistoryContainer.querySelectorAll(
        ".chat-history-chart-container"
    );

    charts.forEach((chart) => {
        chart._resizeObserver?.disconnect();

        if (window.Plotly) {
            Plotly.purge(chart);
        }
    });

    this.chatHistoryContainer.innerHTML = "";

    /*
     * blockCounter is intentionally not reset.
     * New blocks will continue using unique IDs.
     */

    return true;
}      
            connectedCallback() {
                this.render();
            }


            render() {
                if (this._isRendered) {
                    return;
                }

                this._isRendered = true;
                this.innerHTML = "";

                this.chatHistoryContainer = document.createElement("div");
                this.chatHistoryContainer.className =
                    "chat-history-container";

                this.appendChild(this.chatHistoryContainer);
            }

            addTurn(userText) {
                if (!this.chatHistoryContainer) {
                    this.render();
                }

                this.blockCounter += 1;

                const blockId = this.blockCounter;

                const block = document.createElement("div");
                block.id = `chat-history-block-${blockId}`;
                block.className = "chat-history-block";
                block.dataset.blockId = String(blockId);

                const actions = document.createElement("div");
                actions.className = "chat-history-block-actions";

                const editButton = document.createElement("button");
                editButton.type = "button";
                editButton.className = "chat-history-block-action";
                editButton.title = "Edit";
                editButton.textContent = "✏️";

                const deleteButton = document.createElement("button");
                deleteButton.type = "button";
                deleteButton.className = "chat-history-block-action";
                deleteButton.title = "Delete";
                deleteButton.textContent = "✕";

                deleteButton.addEventListener("click", () => {
                    this.dispatchEvent(
                        new CustomEvent("chat:delete-block", {
                            detail: {
                                blockId
                            },
                            bubbles: true
                        })
                    );
                });

                actions.appendChild(editButton);
                actions.appendChild(deleteButton);

                const userRow = document.createElement("div");
                userRow.className =
                    "chat-history-row " +
                    "chat-history-row-user " +
                    "chat-history-block-user-text";

                userRow.textContent = userText;

                const content = document.createElement("div");
                content.className = "chat-history-block-content";

                block.appendChild(actions);
                block.appendChild(userRow);
                block.appendChild(content);

                this.chatHistoryContainer.appendChild(block);

                block.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

                return blockId;
            }

            addContent(data, blockId = null) {
                if (!Array.isArray(data)) {
                    return false;
                }

                const block = blockId !== null
                    ? this.chatHistoryContainer.querySelector(
                        `[data-block-id="${blockId}"]`
                    )
                    : this.chatHistoryContainer.lastElementChild;

                if (!block) {
                    return false;
                }

                const content = block.querySelector(
                    ".chat-history-block-content"
                );

                if (!content) {
                    return false;
                }

                data.forEach((item) => {
                    if (item?.type === "text") {
                        this.addTextRow(item, content);
                    }

                    if (item?.type === "chart") {
                        this.addChartRow(item, content);
                    }
                });

                return true;
            }

            addHTMLContent(content, blockId = null) {
                const block = blockId !== null
                    ? this.chatHistoryContainer?.querySelector(
                        `[data-block-id="${blockId}"]`
                    )
                    : this.chatHistoryContainer?.lastElementChild;

                if (!block) {
                    return false;
                }

                const blockContent = block.querySelector(
                    ".chat-history-block-content"
                );

                if (!blockContent) {
                    return false;
                }

                const row = document.createElement("div");
                row.className =
                    "chat-history-row chat-history-row-html";

                row.innerHTML = content;

                blockContent.appendChild(row);

                return true;
            }      

            addTextRow(item, content) {
                const row = document.createElement("div");
                row.className =
                    "chat-history-row chat-history-row-text";

                row.dataset.contentId = item.id ?? "";

                if (item.title) {
                    const title = document.createElement("div");
                    title.className = "chat-history-row-title";
                    title.textContent = item.title;

                    row.appendChild(title);
                }

                const text = document.createElement("div");
                text.className = "chat-history-row-text-content";
                text.textContent = item.data?.text ?? "";

                row.appendChild(text);
                content.appendChild(row);
            }

            addChartRow(item, content) {
                const plotlyFigure = item.data?.plotly;

                if (!plotlyFigure) {
                    return;
                }

                const row = document.createElement("div");
                row.className =
                    "chat-history-row chat-history-row-chart";

                row.dataset.contentId = item.id ?? "";

                if (item.title) {
                    const title = document.createElement("div");
                    title.className = "chat-history-row-title";
                    title.textContent = item.title;

                    row.appendChild(title);
                }

                const chartContainer = document.createElement("div");
                chartContainer.className =
                    "chat-history-chart-container";

                row.appendChild(chartContainer);
                content.appendChild(row);

                const originalLayout = plotlyFigure.layout ?? {};
                const originalMargin = originalLayout.margin ?? {};
                const originalLegend = originalLayout.legend ?? {};

                const layout = {
                    ...originalLayout,

                    autosize: true,

                    margin: {
                        l: 70,
                        r: 40,
                        t: 70,
                        b: 70,
                        ...originalMargin
                    },

                    legend: {
                        ...originalLegend,

                        /*
                        * Keep vertical legends inside the chart area unless
                        * the supplied figure explicitly defines a position.
                        */
                        x: originalLegend.x ?? 1,
                        xanchor: originalLegend.xanchor ?? "right",
                        y: originalLegend.y ?? 1,
                        yanchor: originalLegend.yanchor ?? "top"
                    },

                    xaxis: {
                        ...originalLayout.xaxis,
                        automargin: true
                    },

                    yaxis: {
                        ...originalLayout.yaxis,
                        automargin: true
                    }
                };

                delete layout.width;
                delete layout.height;

                const config = {
                    responsive: true,
                    displaylogo: false,
                    ...plotlyFigure.config
                };

                Plotly.newPlot(
                    chartContainer,
                    plotlyFigure.data ?? [],
                    layout,
                    config
                ).then(() => {
                    requestAnimationFrame(() => {
                        Plotly.Plots.resize(chartContainer);
                    });
                });

                const resizeObserver = new ResizeObserver(() => {
                    if (chartContainer.isConnected) {
                        Plotly.Plots.resize(chartContainer);
                    }
                });

                resizeObserver.observe(row);
                chartContainer._resizeObserver = resizeObserver;


                const addToDashboardButton = document.createElement("button");
                addToDashboardButton.type = "button";
                addToDashboardButton.className = "btn btn-primary chat-history-add-dashboard-button";
                addToDashboardButton.textContent = "Dashboard +";
                row.appendChild(addToDashboardButton);

            }

            deleteBlock(blockId) {
                const normalizedBlockId = Number(blockId);

                if (!Number.isInteger(normalizedBlockId)) {
                    console.warn(
                        "Invalid chat history block ID:",
                        blockId
                    );

                    return false;
                }

                const block = this.chatHistoryContainer?.querySelector(
                    `[data-block-id="${normalizedBlockId}"]`
                );

                if (!block) {
                    console.warn(
                        `Chat history block ${normalizedBlockId} was not found.`
                    );

                    return false;
                }

                const charts = block.querySelectorAll(
                    ".chat-history-chart-container"
                );

                charts.forEach((chart) => {
                    chart._resizeObserver?.disconnect();

                    if (window.Plotly) {
                        Plotly.purge(chart);
                    }
                });
                block.remove();

                return true;
            }
}
if (!customElements.get("chat-history-component")) {
            customElements.define(
                "chat-history-component",
                ChartHistoryComponent
            );
}
