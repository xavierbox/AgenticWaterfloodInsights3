class QuickJS_ThreeColLayout extends HTMLElement {
  _renderedTabs;

  constructor() {
    super();
 
    this._savedWidths = null;
      
  }
    
  get_column(name){
    if(name === "left") return this.querySelector(".qsthree-col-layout-col1");
    if(name === "middle") return this.querySelector(".qsthree-col-layout-col2");
    if(name === "right") return this.querySelector(".qsthree-col-layout-col3");
    return null;
  }
    
  get_top_bar(){
      
      return this.querySelector(".layout-top-bar");
      
  }
    
  getTemplate() {
    return `
<div class="layout-top-bar" style="
  height:20px;
  background:transparent;
  display:flex;
  align-items:stretch;
  margin:0;
  padding:0;
  border-top:1px solid grey;
  border-bottom:1px solid grey;

">
  <button 
    class="layout-hide-left-button" 
    name="toggle-left"
    style="
      height:100%;
      width:20px;
      margin:0;
      padding:0;
      border:none;
      background:transparent;
      line-height:1;
      font-size:14px;
      display:flex;
      align-items:center;
      justify-content:center;
    "
  >◀</button>

</div>

      <div class="qsthree-col-layout-main">
        <!-- Column 1 -->
        <div style="overflow-y:hidden;" class="qsthree-col-layout-column qsthree-col-layout-col1" id="left">
          
          <div style="max-height:100%; flex:0 0 50%;" id="left-top">Left Top</div>
          <div class="qsthree-col-layout-horizontal-resizer" id="horizontalResizerTop"></div>

          <!-- middle panel here with its own resizer -->
          <div style="max-height:100%; flex:0 0 25%;" id="left-middle">Left Middle</div>
          <div class="qsthree-col-layout-horizontal-resizer" id="horizontalResizerBottom"></div>

          <div style="max-height:100%; flex:0 0 25%;" id="left-bottom">Left Bottom</div>
        </div>

        <div class="qsthree-col-layout-vertical-resizer" id="vResizer1"></div>

        <!-- Column 2 -->
        <div class="qsthree-col-layout-column qsthree-col-layout-col2" id="middle">
          <div class="qsthree-col-layout-content">Center</div>
        </div>

        <div class="qsthree-col-layout-vertical-resizer" id="vResizer2"></div>

        <!-- Column 3 -->
        <div class="qsthree-col-layout-column qsthree-col-layout-col3" id="right">
          <div class="qsthree-col-layout-content">Right</div>
        </div>
      </div>
    `;
  }

  connectedCallback() {
    this.render();
    this.setup();

    const threeSplit = false;
      if (!threeSplit) {
        // 1. Hide middle pane and its resizer
        this.querySelector('#left-middle')?.classList.add('hidden');
        this.querySelector('#horizontalResizerBottom')?.classList.add('hidden');

        // 2. Expand remaining panes to fill 100% of the space evenly
        this.querySelector('#left-top').style.flex = "0 0 68%";
        this.querySelector('#left-bottom').style.flex = "0 0 32%";

        // 3. Connect the top resizer directly between top and bottom panes
        this.setupHorizontalResizer(
          this.querySelector("#horizontalResizerTop"),
          this.querySelector("#left-top"),
          this.querySelector("#left-bottom")
        );
      } 
      
      
      
      
      
      
  }

  render() {
    this.innerHTML = this.getTemplate();
  }

  setupVerticalResizer(resizer, leftEl, rightEl) {
    let isDragging = false;

    resizer.addEventListener("mousedown", (e) => {
      isDragging = true;
      document.body.classList.add("qsthree-col-layout-resizing");

      const container = resizer.parentElement;
      const startX = e.clientX;
      const startLeftWidth = leftEl.getBoundingClientRect().width;
      const startRightWidth = rightEl.getBoundingClientRect().width;
      const containerWidth = container.clientWidth;

      function onMouseMove(e) {
        if (!isDragging) return;

        const dx = e.clientX - startX;
        let newLeftWidth = startLeftWidth + dx;
        let newRightWidth = startRightWidth - dx;

        if (newLeftWidth < 50 || newRightWidth < 50) return;

        const newLeftPercent = (newLeftWidth / containerWidth) * 100;
        const newRightPercent = (newRightWidth / containerWidth) * 100;

        leftEl.style.width = `${newLeftPercent}%`;
        rightEl.style.width = `${newRightPercent}%`;
      }

      function onMouseUp() {
        isDragging = false;
        document.body.classList.remove("qsthree-col-layout-resizing");
        window.removeEventListener("mousemove", onMouseMove);
        window.removeEventListener("mouseup", onMouseUp);

        [leftEl, rightEl].forEach((el) => {
          resizer.dispatchEvent(
            new CustomEvent("pane-resized", {
              detail: {
                id: el.id,
                offsetWidth: el.offsetWidth,
                offsetHeight: el.offsetHeight,
              },
              bubbles: true,
              composed: true,
            })
          );
        });
      }

      window.addEventListener("mousemove", onMouseMove);
      window.addEventListener("mouseup", onMouseUp);
    });
  }

  setupHorizontalResizer(resizer, topEl, bottomEl) {
    let isDragging = false;

    resizer.addEventListener("mousedown", (e) => {
      isDragging = true;
      document.body.classList.add("qsthree-col-layout-resizing");

      const container = topEl.parentElement;
      const startY = e.clientY;
      const startTopHeight = topEl.getBoundingClientRect().height;
      const startBottomHeight = bottomEl.getBoundingClientRect().height;
      const containerHeight = container.clientHeight;

      function onMouseMove(e) {
        if (!isDragging) return;

        const dy = e.clientY - startY;
        let newTopHeight = startTopHeight + dy;
        let newBottomHeight = startBottomHeight - dy;

        if (newTopHeight < 50 || newBottomHeight < 50) return;

        const newTopPercent = (newTopHeight / containerHeight) * 100;
        const newBottomPercent = (newBottomHeight / containerHeight) * 100;

        topEl.style.flex = `0 0 ${newTopPercent}%`;
        bottomEl.style.flex = `0 0 ${newBottomPercent}%`;
      }

      function onMouseUp() {
        isDragging = false;
        document.body.classList.remove("qsthree-col-layout-resizing");
        window.removeEventListener("mousemove", onMouseMove);
        window.removeEventListener("mouseup", onMouseUp);

        [topEl, bottomEl].forEach((el) => {
          resizer.dispatchEvent(
            new CustomEvent("pane-resized", {
              detail: {
                id: el.id,
                offsetWidth: el.offsetWidth,
                offsetHeight: el.offsetHeight,
              },
              bubbles: true,
              composed: true,
            })
          );
        });
      }

      window.addEventListener("mousemove", onMouseMove);
      window.addEventListener("mouseup", onMouseUp);
    });
  }

  setup() {
      this.querySelector(".layout-hide-left-button").addEventListener("click", () => {

  const left = this.get_column("left");
  const middle = this.get_column("middle");
  const right = this.get_column("right");

  const container = left.parentElement;
  const containerWidth = container.clientWidth;

  if (!left.classList.contains("hidden")) {

    // --- HIDE LEFT ---
    this.querySelector("#vResizer1").classList.add("hidden");

    const lw = left.offsetWidth;
    const mw = middle.offsetWidth;
    const rw = right.offsetWidth;

    this._savedWidths = { lw, mw, rw };

    const remaining = mw + rw;

    const middlePercent = (mw / remaining) * 100;
    const rightPercent = (rw / remaining) * 100;

    left.classList.add("hidden");

    middle.style.width = `${middlePercent}%`;
    right.style.width = `${rightPercent}%`;

  } else {

this.querySelector("#vResizer1").classList.remove("hidden");
    // --- SHOW LEFT ---
    left.classList.remove("hidden");

    if (this._savedWidths) {
      const { lw, mw, rw } = this._savedWidths;
      const total = lw + mw + rw;

      left.style.width = `${(lw / total) * 100}%`;
      middle.style.width = `${(mw / total) * 100}%`;
      right.style.width = `${(rw / total) * 100}%`;
    }
  }

  this.querySelector(".layout-hide-left-button").innerHTML =
    left.classList.contains("hidden") ? "▶" : "◀";

          
  // emit resize event
  [left, middle, right].forEach((el) => {
    el.dispatchEvent(
      new CustomEvent("pane-resized", {
        detail: {
          id: el.id,
          offsetWidth: el.offsetWidth,
          offsetHeight: el.offsetHeight,
        },
        bubbles: true,
        composed: true,
      })
    );
  });

          
          
          
});
      
   
      
      
      
    this.setupVerticalResizer(
      this.querySelector("#vResizer1"),
      this.querySelector(".qsthree-col-layout-col1"),
      this.querySelector("#middle")
    );

    this.setupVerticalResizer(
      this.querySelector("#vResizer2"),
      this.querySelector("#middle"),
      this.querySelector("#right")
    );

    this.setupHorizontalResizer(
      this.querySelector("#horizontalResizerTop"),
      this.querySelector("#left-top"),
      this.querySelector("#left-middle")
    );

    this.setupHorizontalResizer(
      this.querySelector("#horizontalResizerBottom"),
      this.querySelector("#left-middle"),
      this.querySelector("#left-bottom")
    );
  }

  set(where, content) {
    const validPanes = [
      "left-top",
      "left-middle",
      "left-bottom",
      "middle",
      "right",
      "middle-top",
      "middle-bottom",
      "right-top",
      "right-bottom",
    ];

    if (validPanes.includes(where)) {
      if (where === "middle-top") where = "middle";
      if (where === "right-top") where = "right";

      const pane = this.querySelector(`#${where}`);

      if (typeof content === "string") {
        pane.innerHTML = content;
      } else if (content instanceof HTMLElement) {
        pane.innerHTML = "";
        pane.appendChild(content);
      } else {
        console.error("Content must be a string or an HTML element");
      }
    } else {
      console.error("Invalid pane ID");
    }
  }

  clear(where) {
    const validPanes = [
      "left-top",
      "left-middle",
      "left-bottom",
      "middle",
      "right",
      "middle-top",
      "middle-bottom",
      "right-top",
      "right-bottom",
    ];

    if (validPanes.includes(where)) {
      if (where === "middle-top") where = "middle";
      if (where === "right-top") where = "right";

      this.querySelector(`#${where}`).innerHTML = "";
    }
  }

  append(where, content) {
    const validPanes = [
      "left-top",
      "left-middle",
      "left-bottom",
      "middle",
      "right",
      "middle-top",
      "middle-bottom",
      "right-top",
      "right-bottom",
    ];

    if (validPanes.includes(where)) {
      if (where === "middle-top") where = "middle";
      if (where === "right-top") where = "right";

      if (content instanceof HTMLElement) {
        this.querySelector(`#${where}`).appendChild(content);
      } else {
        console.error("Content must be an HTML element");
      }
    } else {
      console.error("Invalid pane ID");
    }
  }

  get_pane(id) {
    const validPanes = [
      "left-top",
      "left-middle",
      "left-bottom",
      "middle",
      "right",
      "middle-top",
      "middle-bottom",
      "right-top",
      "right-bottom",
    ];

    let where = id;

    if (validPanes.includes(id)) {
      if (where === "middle-top") where = "middle";
      if (where === "right-top") where = "right";

      return this.querySelector(`#${where}`);
    } else {
      console.error(
        `Invalid pane ID "${id}". Valid IDs are: ${validPanes.join(", ")}`
      );
      return null;
    }
  }
}

if(!customElements.get('new-three-column-main-layout')){
  customElements.define("new-three-column-main-layout", QuickJS_ThreeColLayout);
}

class TabsComponent extends HTMLElement {
      constructor() {
        super();

        this.tabs = [];
        this.activeIndex = -1;

        this.buttonsContainer = null;
        this.pagesContainer = null;

        this._onButtonClick = this._onButtonClick.bind(this);
      }

      connectedCallback() {
        if (!this.buttonsContainer || !this.pagesContainer) {
          this.innerHTML = `
            <div class="tabs-component">
              <div class="tabs-buttons"></div>
              <div class="tabs-pages"></div>
            </div>
          `;

          this.buttonsContainer = this.querySelector(".tabs-buttons");
          this.pagesContainer = this.querySelector(".tabs-pages");
        }

        this.buttonsContainer.removeEventListener("click", this._onButtonClick);
        this.buttonsContainer.addEventListener("click", this._onButtonClick);

        // this._onWindowResize = this._onWindowResize.bind(this);
        //window.addEventListener("resize", this._onWindowResize);


      }

      disconnectedCallback() {
        this.buttonsContainer?.removeEventListener("click", this._onButtonClick);
         this.buttonsContainer?.removeEventListener("click", this._onButtonClick);
        //window.removeEventListener("resize", this._onWindowResize);
      }


 
      attributeChangedCallback(name, oldValue, newValue) {}

      _onButtonClick(event) {
        const closeButton = event.target.closest(".tabs-button-close");
        const button = event.target.closest(".tabs-button");

        if (!button || !this.buttonsContainer.contains(button)) return;

        const index = Array.from(this.buttonsContainer.children).indexOf(button);
        if (index === -1) return;

        if (closeButton) {
          this.deleteTab(index);
          return;
        }

        this.setActiveTab(index);

        const tab = this.tabs[index];

        this.dispatchEvent(new CustomEvent("tab-selected", {
          detail: {
            name: tab.name,
            index: index
          },
          bubbles: true,
          composed: true
        }));
      }

      _setButtonContent(button, name, icon = null) {
        button.replaceChildren();

        if (icon !== null && icon !== undefined) {
          const iconSpan = document.createElement("span");
          iconSpan.className = "tabs-button-icon";

          if (icon instanceof Node) {
            iconSpan.appendChild(icon);
          } else {
            iconSpan.textContent = String(icon);
          }

          button.appendChild(iconSpan);
        }

        const labelSpan = document.createElement("span");
        labelSpan.className = "tabs-button-label";
        labelSpan.textContent = name;

        const closeSpan = document.createElement("span");
        closeSpan.className = "tabs-button-close";
        closeSpan.textContent = "×";

        button.append(labelSpan, closeSpan);
      }

      addTab(name, icon = null) {
        if (!name) {
          console.warn("TabsComponent.addTab: name is required.");
          return false;
        }

        if (!this.buttonsContainer || !this.pagesContainer) {
          console.warn("TabsComponent.addTab: component is not connected.");
          return false;
        }

        if (this.tabs.some(t => t.name === name)) {
          console.warn(`TabsComponent.addTab: tab "${name}" already exists.`);
          return false;
        }

        const button = document.createElement("button");
        button.className = "tabs-button";
        this._setButtonContent(button, name, icon);

        const page = document.createElement("div");
        page.className = "tabs-page";

        this.buttonsContainer.appendChild(button);
        this.pagesContainer.appendChild(page);

        this.tabs.push({
          name: name,
          icon: icon,
          closeDisabled: false
        });

        if (this.activeIndex === -1) {
          this.setActiveTab(0);
        }

        return true;
      }

      addTabWithContent(name, content, icon = null) {
        const added = this.addTab(name, icon);
        if (!added) return false;

        this.setTabContent(name, content);
        return true;
      }

      deleteTab(nameOrIndex) {
        const index =
          typeof nameOrIndex === "number"
            ? nameOrIndex
            : this.tabs.findIndex(t => t.name === nameOrIndex);

        if (index < 0 || index >= this.tabs.length) return false;

        const wasActive = index === this.activeIndex;
        const wasBeforeActive = index < this.activeIndex;

        this.buttonsContainer.children[index].remove();
        this.pagesContainer.children[index].remove();
        this.tabs.splice(index, 1);

        if (this.tabs.length === 0) {
          this.activeIndex = -1;
          return true;
        }

        if (wasActive) {
          this.activeIndex = -1;
          this.setActiveTab(Math.min(index, this.tabs.length - 1));
        } else if (wasBeforeActive) {
          this.activeIndex -= 1;
        }

        return true;
      }

      setTabContent(nameOrIndex, content) {
        const index =
          typeof nameOrIndex === "number"
            ? nameOrIndex
            : this.tabs.findIndex(t => t.name === nameOrIndex);

        if (index < 0 || index >= this.tabs.length) return false;

        const page = this.pagesContainer.children[index];
        page.replaceChildren();

        if (content == null) return true;

        if (typeof content === "string") {
          page.textContent = content;
        } else if (content instanceof Node) {
          page.appendChild(content);
        } else if (Array.isArray(content) && content.every(x => x instanceof Node)) {
          page.append(...content);
        } else if (
          typeof content === "object" &&
          typeof content.trustedHtml === "string"
        ) {
          page.innerHTML = content.trustedHtml;
        } else {
          page.textContent = String(content);
        }

        return true;
      }
/*_resizePlotlyChartsInPage(page) {
  if (!window.Plotly || !page) 
    {
        alert('returning here');
        return;
    }

 
  const charts = page.querySelectorAll(".js-plotly-plot");

  charts.forEach(function (chart) {
    const innerOffset = 5;
    const pad = 5;

    const width = Math.max(0, chart.offsetWidth - pad);
    const height = Math.max(0, chart.offsetHeight - pad);

    Plotly.relayout(chart, {
      width: width,
      height: height,
      margin: {
        l: innerOffset,
        r: innerOffset,
        b: 10 * innerOffset,
        t: 5 * innerOffset
      },
      autosize: true
    },{"responsive":true});
  });
}*/


      setActiveTab(index) {

       

        if (index < 0 || index >= this.tabs.length) return false;
        if (index === this.activeIndex) return true;

        const oldButton = this.buttonsContainer.children[this.activeIndex];
        const oldPage = this.pagesContainer.children[this.activeIndex];

        if (oldButton) oldButton.classList.remove("active");
        if (oldPage) oldPage.style.display = "none";

        const newButton = this.buttonsContainer.children[index];
        const newPage = this.pagesContainer.children[index];

        newButton.classList.add("active");
        newPage.style.display = "flex";/* "block";*/

        this.activeIndex = index;


        /*requestAnimationFrame(() => {
            this._resizePlotlyChartsInPage(newPage);
        });*/



        return true;
      }


 

      selectTab(nameOrIndex) {
        const index =
          typeof nameOrIndex === "number"
            ? nameOrIndex
            : this.tabs.findIndex(t => t.name === nameOrIndex);

        return this.setActiveTab(index);
      }

      hasTab(name) {
        return this.tabs.some(t => t.name === name);
      }

      getTabCount() {
        return this.tabs.length;
      }

      getActiveTab() {
        if (this.activeIndex < 0 || this.activeIndex >= this.tabs.length) {
          return null;
        }

        return {
          name: this.tabs[this.activeIndex].name,
          index: this.activeIndex,
          button: this.buttonsContainer.children[this.activeIndex],
          page: this.pagesContainer.children[this.activeIndex]
        };
      }

      clearTabs() {
        if (!this.buttonsContainer || !this.pagesContainer) return false;

        this.buttonsContainer.replaceChildren();
        this.pagesContainer.replaceChildren();

        this.tabs = [];
        this.activeIndex = -1;

        return true;
      }

         /**
          Returns the page element associated with a tab.
          This is the <div> that contains all the elements added to the tab
         */
        getTabPage(nameOrIndex) {
        const index =
            typeof nameOrIndex === "number"
            ? nameOrIndex
            : this.tabs.findIndex(t => t.name === nameOrIndex);

        if (index < 0 || index >= this.tabs.length) {
            return null;
        }

        return this.pagesContainer.children[index];
        }

      /*
      this returns the list of children of the tab. Those are the ones added  
      */
      getContent(nameOrIndex) {
        const page = this.getTabPage(nameOrIndex);

        if (!page) return null;

        return page.children;
      }

      disableClose(nameOrIndex, disabled = true) {
        const index =
          typeof nameOrIndex === "number"
            ? nameOrIndex
            : this.tabs.findIndex(t => t.name === nameOrIndex);

        if (index < 0 || index >= this.tabs.length) return false;

        this.tabs[index].closeDisabled = disabled;

        const closeButton =
          this.buttonsContainer.children[index]?.querySelector(".tabs-button-close");

        if (closeButton) {
          closeButton.style.display = disabled ? "none" : "";
        }

        return true;
      }
    }

    if (!customElements.get("tabs-component")) {
  customElements.define("tabs-component", TabsComponent);
}

class ChartsCatalogControl extends HTMLElement {
  
    constructor() {
        super();

        this.catalog = null;
        this.selectedPlot = null;
        this.selectedPlotIndexes = [];
        this.editedParametersByFunction = {};
        this.editor = null;
        this.activeCategory = "All";
    }

    connectedCallback() {
        this.render1();
    }

    setCatalogViewMode(mode) {
    const list = this.querySelector('[data-role="charts-catalog-list"]');
    const genai = this.querySelector('[data-role="charts-catalog-genai-panel"]');
    const workspace = this.querySelector('[data-role="charts-catalog-workspace"]');
    const genaiOutput = this.querySelector('[data-role="charts-catalog-genai-output"]');

    const isGenAi = mode === "genai";

    list.classList.toggle("hidden", isGenAi);
    genai.classList.toggle("hidden", !isGenAi);
    workspace.classList.toggle("hidden", isGenAi);
    genaiOutput.classList.toggle("hidden", !isGenAi);
    }


    render1() {
    this.innerHTML = `
        <div class="wf-main-grid">

        <section class="pane xxwf-panel">
            <div class="wf-panel-header">Plot catalog</div>

            <div class="wf-panel-body charts-catalog-catalog-area">
            <div
                data-role="charts-catalog-category-filters"
                class="wf-filter-placeholder"
            ></div>

            <div
                data-role="charts-catalog-list"
                class="charts-catalog-list-panel"
            ></div>

            <div
                data-role="charts-catalog-genai-panel"
                class="charts-catalog-genai-panel hidden"
            ></div>

        
            </div>
        </section>

        <section class="pane xxwf-panel">
            

            <div class="wf-panel-body charts-catalog-middle-body">

            <div
                data-role="charts-catalog-genai-output"
                class="charts-catalog-genai-output hidden"
            >
                Agent output placeholder...
            </div>



            <div
                data-role="charts-catalog-workspace"
                class="charts-catalog-workspace"
            >

                <div
                data-role="charts-catalog-parameter-editor"
                class="charts-catalog-parameter-editor"
                ></div>

                <div
                data-role="charts-catalog-parameter-actions"
                class="charts-catalog-actions hidden"
                >
                <button
                    data-role="charts-catalog-apply-parameters"
                    class="btn btn-success btn-sm"
                    disabled
                >
                    Apply parameters
                </button>

                <button
                    data-role="charts-catalog-reset-parameters"
                    class="btn btn-primary btn-sm"
                    disabled
                >
                    Reset parameters
                </button>
                </div>

                <div>
                <button
                    data-role="charts-catalog-preview-button"
                    class="btn btn-outline-primary btn-sm charts-catalog-preview-button"
                >
                    Preview
                </button>
                </div>

                <div
                data-role="charts-catalog-preview"
                class="charts-catalog-preview-panel"
                >
                Preview placeholder...
                </div>
            </div>
            </div>
        </section>

        <section class="pane xxwf-panel">
            <div class="wf-panel-header">
            Current selection
            <span
                data-role="charts-catalog-selection-count"
                class="charts-catalog-selection-count"
            >0</span>
            </div>

            <div
            data-role="charts-catalog-selected-list"
            class="charts-catalog-selected-list"
            ></div>

            <div class="charts-catalog-right-footer">
            <button
                data-role="charts-catalog-generate"
      
                class="btn btn-outline-primary btn-sm charts-catalog-preview-button"
            >
                Generate
            </button>

            </div>
        </section>

        </div>
    `;

    this.bindButtons();
    this.updateSelectedCompactList();
    }


    displayPreview(element) {
    const previewContainer = this.querySelector(
        '[data-role="charts-catalog-preview"]'
    );

    previewContainer.replaceChildren();

    if (element) {
        previewContainer.appendChild(element);

        requestAnimationFrame(() => {
        if (window.Plotly) {
            element
            .querySelectorAll?.(".js-plotly-plot")
            ?.forEach(plot => Plotly.Plots.resize(plot));
        }
        });
    }
    }

    attachGenAiChatDialog(chatElement) {
    const container = this.querySelector(
        '[data-role="charts-catalog-genai-panel"]'
    );

    if (!chatElement || !container) {
        console.warn("Could not attach GenAI chat dialog", {
        chatElement,
        container
        });
        return;
    }

    chatElement.style.display = "";
    container.innerHTML = "";
    container.appendChild(chatElement);
    }

    displayGenAiOutput(element) {
    const container = this.querySelector(
        '[data-role="charts-catalog-genai-output"]'
    );

    if (!container) {
        console.warn("GenAI output container not found");
        return;
    }

    container.innerHTML = "";

    if (element) {
        container.appendChild(element);
    }
    }

  bindButtons() {
    this.applyButton = this.querySelector(
      '[data-role="charts-catalog-apply-parameters"]'
    );

    this.resetButton = this.querySelector(
      '[data-role="charts-catalog-reset-parameters"]'
    );

    this.generateButton = this.querySelector(
      '[data-role="charts-catalog-generate"]'
    );

    this.applyButton.addEventListener("click", () => {
      this.applyParameters();
    });

    this.resetButton.addEventListener("click", () => {
      this.resetParameters();
    });

    this.generateButton.addEventListener("click", () => {
    const selected = this.getSelected();

    console.log("Selected plots:", selected);

    this.dispatchEvent(
        new CustomEvent("generate-dashboard-plots", {
        detail: {
            selectedPlots: selected
        },
        bubbles: true,
        composed: true
        })
    );
    });
        

    const specialCard = this.querySelector(
      '[data-role="charts-catalog-special-card"]'
    );

    if (specialCard) {
      specialCard.addEventListener("click", () => {
        document
          .querySelector(".wf-assistant-placeholder")
          ?.scrollIntoView({
            behavior: "smooth",
            block: "start"
          });
      });
    }
  }

  setCatalog(catalog) {
    this.catalog = catalog;
    this.selectedPlot = null;
    this.selectedPlotIndexes = [];
    this.editedParametersByFunction = {};
    this.activeCategory = "All";

    if (this.editor) {
      this.editor.destroy();
      this.editor = null;
    }

    this.querySelector(
      '[data-role="charts-catalog-parameter-editor"]'
    ).innerHTML = "";

    /*this.querySelector(
      '[data-role="charts-catalog-description"]'
    ).textContent = "Select a plot to see its description and parameters.";
    */
    this.renderCategoryFilters();
    this.renderCatalog1();
    this.setCatalogViewMode("catalog");

    this.applyCategoryFilter();
    this.updateSelectedCompactList();
    this.updateParameterButtonsState();
  }

  renderCategoryFilters() {
    const container = this.querySelector(
      '[data-role="charts-catalog-category-filters"]'
    );

    if (!container || !this.catalog?.items) return;

    /*const categories = [
      "All",
      ...new Set(this.catalog.items.map(plot => plot.category || "General"))
    ];*/
    const categories = [
    "All",
    ...new Set([
        ...this.catalog.items.map(plot => plot.category || "General"),
        "GenAi"
    ])
    ];


    container.innerHTML = "";

    categories.forEach(category => {
      const chip = document.createElement("span");
      chip.className = "wf-filter-chip";
      chip.textContent = category;

      if (category === this.activeCategory) {
        chip.classList.add("active");
      }


chip.addEventListener("click", () => {
  this.activeCategory = category;
  this.renderCategoryFilters();

  if (category === "GenAi") {
    this.setCatalogViewMode("genai");
  } else {
    this.setCatalogViewMode("catalog");
    this.applyCategoryFilter();
  }
});



      /*chip.addEventListener("click", () => {
        this.activeCategory = category;
        this.renderCategoryFilters();
        this.applyCategoryFilter();
      });*/

      container.appendChild(chip);
    });
  }

  applyCategoryFilter() {
    if (!this.catalog?.items) return;

    this.querySelectorAll(".charts-catalog-card").forEach(card => {
      const index = Number(card.dataset.index);
      const plot = this.catalog.items[index];

      const visible =
        this.activeCategory === "All" ||
        (plot.category || "General") === this.activeCategory;

      card.classList.toggle("hidden", !visible);
    });
  }

  renderCatalog1() {
    const container = this.querySelector(
      '[data-role="charts-catalog-list"]'
    );

    container.innerHTML = "";

    if (!this.catalog || !Array.isArray(this.catalog.items)) {
      container.innerHTML = `
        <div class="alert alert-secondary">
          No catalog loaded.
        </div>
      `;
      return;
    }

    this.catalog.items.forEach((plot, index) => {
      const card = document.createElement("div");
      card.className = "card charts-catalog-card";
      card.dataset.index = index;

      card.innerHTML = `
        <div class="charts-catalog-card-header">
          <input
            type="checkbox"
            class="form-check-input charts-catalog-card-checkbox"
          />
          <div class="charts-catalog-card-title">${plot.display_name}</div>
        </div>

        <div class="charts-catalog-card-description">
          ${plot.description || ""}
        </div>
      `;

      const header = card.querySelector(".charts-catalog-card-header");

      header.addEventListener("click", event => {
        event.stopPropagation();

        const wasSelected = this.selectedPlotIndexes.includes(index);

        this.togglePlotSelection(index);

        const isSelected = this.selectedPlotIndexes.includes(index);

        if (!wasSelected && isSelected) {
          this.showPlotParameters(index);
        }
      });

      card.addEventListener("click", () => {
        this.showPlotParameters(index);
      });

      container.appendChild(card);
    });

    this.updateCardSelectionStyles1();
  }

  togglePlotSelection(index) {
    const isSelected = this.selectedPlotIndexes.includes(index);

    if (isSelected) {
      this.selectedPlotIndexes =
        this.selectedPlotIndexes.filter(i => i !== index);
    } else {
      this.selectedPlotIndexes.push(index);
    }

    this.updateCardSelectionStyles1();
    this.updateSelectedCompactList();
    this.updateParameterButtonsState();
  }

  updateCardSelectionStyles1() {
    this.querySelectorAll(".charts-catalog-card").forEach(card => {
      const index = Number(card.dataset.index);
      const isSelected = this.selectedPlotIndexes.includes(index);

      card.classList.toggle("selected", isSelected);

      const checkbox = card.querySelector(".charts-catalog-card-checkbox");
      checkbox.checked = isSelected;
    });
  }

  updateSelectedCompactList() {
    const container = this.querySelector(
      '[data-role="charts-catalog-selected-list"]'
    );

    const count = this.querySelector(
      '[data-role="charts-catalog-selection-count"]'
    );

    if (!container || !count) return;

    const selected = this.getSelected();

    count.textContent = selected.length;

    if (selected.length === 0) {
      container.innerHTML = `
        <div class="charts-catalog-selected-empty">
          No plots selected.
        </div>
      `;
      return;
    }

    container.innerHTML = selected
      .map((plot, i) => `
        <div class="charts-catalog-selected-item">
          ${i + 1}. ${plot.display_name}
        </div>
      `)
      .join("");
  }

  showPlotParameters(index) {
    this.selectedPlot = this.catalog.items[index];

    /*this.querySelector(
      '[data-role="charts-catalog-description"]'
    ).textContent =
      this.selectedPlot.application ||
      this.selectedPlot.description ||
      "No description available.";*/

    this.renderParameterEditor(this.selectedPlot);
    this.updateParameterButtonsState();
  }

  hasEditableParameters(plot) {
  return plot?.parameters && Object.keys(plot.parameters).length > 0;
}

  renderParameterEditor(plot) {
    const container = this.querySelector(
      '[data-role="charts-catalog-parameter-editor"]'
    );

    container.innerHTML = "";

    if (this.editor) {
      this.editor.destroy();
      this.editor = null;
    }

    const parameters = plot.parameters || {};

    if (Object.keys(parameters).length === 0) {
      container.innerHTML = ``;
      return;
    }

    const schema = this.buildSchemaFromParameters(parameters);

    const data =
      this.editedParametersByFunction[plot.function] ||
      this.buildDataFromParameters(parameters);

    this.editor = new JSONEditor(container, {
      schema: schema,
      startval: data,
      theme: "bootstrap5",
      disable_edit_json: true,
      disable_properties: true,
      no_additional_properties: true,
      compact: true
    });
  }

  buildSchemaFromParameters(parameters) {
    const properties = {};

    Object.entries(parameters).forEach(([key, param]) => {
      properties[key] = {
        title: param.display_name,
        description: param.description,
        type: this.mapParameterType(param.type)
      };
    });

    return {
      type: "object",
      title: "Parameters",
      properties: properties
    };
  }

  buildDataFromParameters(parameters) {
    const data = {};

    Object.entries(parameters).forEach(([key, param]) => {
      data[key] = param.value;
    });

    return data;
  }

  mapParameterType(type) {
    if (type === "string") return "string";
    if (type === "float") return "number";
    if (type === "int") return "integer";
    if (type === "bool") return "boolean";

    return "string";
  }

  applyParameters() {
    if (!this.selectedPlot || !this.editor) {
      return;
    }

    const errors = this.editor.validate();

    if (errors.length > 0) {
      console.log(errors);
      return;
    }

    this.editedParametersByFunction[this.selectedPlot.function] =
      this.editor.getValue();

    console.log(JSON.stringify({
      message: "Parameters applied",
      function: this.selectedPlot.function,
      parameters: this.editedParametersByFunction[this.selectedPlot.function]
    }, null, 2));
  }

  resetParameters() {
    if (!this.selectedPlot) {
      return;
    }

    delete this.editedParametersByFunction[this.selectedPlot.function];

    this.renderParameterEditor(this.selectedPlot);
    this.updateParameterButtonsState();

    console.log(JSON.stringify({
      message: "Parameters reset",
      display_name: this.selectedPlot.display_name,
      function: this.selectedPlot.function,
      parameters: this.buildDataFromParameters(this.selectedPlot.parameters || {})
    }, null, 2));
  }


  updateParameterButtonsState() {
  const actions = this.querySelector(
    '[data-role="charts-catalog-parameter-actions"]'
  );

  if (!actions) return;

  if (!this.catalog || !this.selectedPlot) {
    actions.classList.add("hidden");
    this.applyButton.disabled = true;
    this.resetButton.disabled = true;
    return;
  }

  const hasParameters = this.hasEditableParameters(this.selectedPlot);

  const selectedIndex = this.catalog.items.findIndex(
    p => p.function === this.selectedPlot.function
  );

  const isDisplayedPlotSelected =
    selectedIndex >= 0 && this.selectedPlotIndexes.includes(selectedIndex);

  const showActions = hasParameters && isDisplayedPlotSelected;

  actions.classList.toggle("hidden", !showActions);

  this.applyButton.disabled = !showActions;
  this.resetButton.disabled = !showActions;
}


  getSelected() {
    if (!this.catalog) {
        return [];
    }

    return this.selectedPlotIndexes.map(index => {
        const originalPlot = this.catalog.items[index];

        const selectedPlot = structuredClone(originalPlot);

        const editedValues =
        this.editedParametersByFunction[originalPlot.function];

        if (editedValues && selectedPlot.parameters) {
        Object.entries(editedValues).forEach(([key, value]) => {
            if (selectedPlot.parameters[key]) {
            selectedPlot.parameters[key].value = value;
            }
        });
        }

        return selectedPlot;
    });
    }


}
customElements.define("charts-catalog-control", ChartsCatalogControl);




class ChartsCatalogControl2 extends HTMLElement {
  constructor() {
    super();

    this.catalog = null;
    this.selectedPlot = null;
    this.selectedPlotIndex = null;
    this.editedParametersByFunction = {};
    this.editor = null;
    this.activeCategory = "All";

    this.applyButton = null;
    this.resetButton = null;
    this.previewButton = null;
    this.generateButton = null;
  }

  connectedCallback() {
    this.render();
  }


  
render() {
  this.innerHTML = `
    <div class="charts-catalog-split-layout">

      <!-- Left column -->
      <section
        data-role="charts-catalog-left-panel"
        class="pane xxwf-panel"
      >
        <div class="wf-panel-header">
          Plot catalog
        </div>

        <div class="wf-panel-body charts-catalog-catalog-area">

          <div
            data-role="charts-catalog-category-filters"
            class="wf-filter-placeholder"
          ></div>

          <div
            data-role="charts-catalog-list"
            class="charts-catalog-list-panel"
          ></div>

          <div
            data-role="charts-catalog-genai-panel"
            class="charts-catalog-genai-panel hidden"
          ></div>

        </div>
      </section>

      <!-- Draggable separator -->
      <div
        data-role="charts-catalog-resizer"
        class="charts-catalog-resizer separator"
      ></div>

      <!-- Right column -->
      <section
        data-role="charts-catalog-right-panel"
        class="pane xxwf-panel"
      >
        <div class="wf-panel-body charts-catalog-middle-body">

          <div
            data-role="charts-catalog-genai-output"
            class="charts-catalog-genai-output hidden"
          >
            Agent output placeholder...
          </div>

          <div
            data-role="charts-catalog-workspace"
            class="charts-catalog-workspace"
          >

            <div
              data-role="charts-catalog-parameter-editor"
              class="charts-catalog-parameter-editor"
            ></div>

            <div
              data-role="charts-catalog-parameter-actions"
              class="charts-catalog-actions hidden"
            >
              <button
                data-role="charts-catalog-apply-parameters"
                class="btn btn-success btn-sm"
                disabled
              >
                Apply parameters
              </button>

              <button
                data-role="charts-catalog-reset-parameters"
                class="btn btn-primary btn-sm"
                disabled
              >
                Reset parameters
              </button>
            </div>

            <div class="charts-catalog-actions">

              <button
                data-role="charts-catalog-preview-button"
                class="btn btn-outline-primary btn-sm charts-catalog-preview-button"
                disabled
              >
                Preview
              </button>

              <button
                data-role="charts-catalog-generate"
                class="btn btn-outline-primary btn-sm"
                disabled
              >
                Dashboard ➕
              </button>

            </div>

            <div
              data-role="charts-catalog-preview"
              class="charts-catalog-preview-panel"
            >
              Preview placeholder...
            </div>

          </div>
        </div>
      </section>

    </div>
  `;

  this.bindButtons();
  this.bindColumnResizer();
  this.updateControlState();
}

resizePreviewPlots() {
  requestAnimationFrame(() => {
    if (!window.Plotly) {
      return;
    }

    this.querySelectorAll(".js-plotly-plot").forEach(plot => {
      window.Plotly.Plots.resize(plot);
    });
  });
}

bindColumnResizer() {
  const layout = this.querySelector(
    ".charts-catalog-split-layout"
  );

  const resizer = this.querySelector(
    '[data-role="charts-catalog-resizer"]'
  );

  if (!layout || !resizer) {
    return;
  }

  const minimumLeftWidth = 260;
  const minimumRightWidth = 400;
  const separatorWidth = 8;

  let dragging = false;

  const stopDragging = event => {
    if (!dragging) {
      return;
    }

    dragging = false;

    resizer.classList.remove("dragging");

    document.body.style.cursor = "";
    document.body.style.userSelect = "";

    if (
      event?.pointerId !== undefined &&
      resizer.hasPointerCapture(event.pointerId)
    ) {
      resizer.releasePointerCapture(event.pointerId);
    }
  };

  resizer.addEventListener("pointerdown", event => {
    dragging = true;

    resizer.classList.add("dragging");
    resizer.setPointerCapture(event.pointerId);

    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";

    event.preventDefault();
  });

  resizer.addEventListener("pointermove", event => {
    if (!dragging) {
      return;
    }

    const bounds = layout.getBoundingClientRect();

    const maximumLeftWidth =
      bounds.width -
      minimumRightWidth -
      separatorWidth;

    const requestedLeftWidth =
      event.clientX - bounds.left;

    const leftWidth = Math.min(
      Math.max(requestedLeftWidth, minimumLeftWidth),
      maximumLeftWidth
    );

    layout.style.gridTemplateColumns =
      `${leftWidth}px ${separatorWidth}px minmax(${minimumRightWidth}px, 1fr)`;

    this.resizePreviewPlots();
  });

  resizer.addEventListener("pointerup", stopDragging);
  resizer.addEventListener("pointercancel", stopDragging);
}

  render_old() {
    this.innerHTML = `
      <div
        class="wf-main-grid charts-catalog-two-column-grid"
        style="grid-template-columns: minmax(280px, 0.9fr) minmax(420px, 1.4fr);"
      >
        <!-- Left column: catalog / GenAI chat -->
        <section class="pane xxwf-panel">
          <div class="wf-panel-header">
            Plot catalog
          </div>

          <div class="wf-panel-body charts-catalog-catalog-area">
            <div
              data-role="charts-catalog-category-filters"
              class="wf-filter-placeholder"
            ></div>

            <div
              data-role="charts-catalog-list"
              class="charts-catalog-list-panel"
            ></div>

            <div
              data-role="charts-catalog-genai-panel"
              class="charts-catalog-genai-panel hidden"
            ></div>
          </div>
        </section>

        <!-- Right column: parameters / preview / GenAI output -->
        <section class="pane xxwf-panel">
          <div class="wf-panel-body charts-catalog-middle-body">
            <div
              data-role="charts-catalog-genai-output"
              class="charts-catalog-genai-output hidden"
            >
              Agent output placeholder...
            </div>

            <div
              data-role="charts-catalog-workspace"
              class="charts-catalog-workspace"
            >
              <div
                data-role="charts-catalog-parameter-editor"
                class="charts-catalog-parameter-editor"
              ></div>

              <div
                data-role="charts-catalog-parameter-actions"
                class="charts-catalog-actions hidden"
              >
                <button
                  data-role="charts-catalog-apply-parameters"
                  class="btn btn-success btn-sm"
                  disabled
                >
                  Apply parameters
                </button>

                <button
                  data-role="charts-catalog-reset-parameters"
                  class="btn btn-primary btn-sm"
                  disabled
                >
                  Reset parameters
                </button>
              </div>

              <div class="charts-catalog-actions"
               
                        >
                <button
                  data-role="charts-catalog-preview-button"
                  class="btn btn-outline-primary btn-sm charts-catalog-preview-button"
                  disabled
                >
                  Preview
                </button>

                <button
                  data-role="charts-catalog-generate"
                  class="btn btn-outline-primary btn-sm charts-catalog-generate-button"
                  disabled
                >
                  Dashboard ➕
                </button>
              </div>

              <div
                data-role="charts-catalog-preview"
                class="charts-catalog-preview-panel"
              >
                Preview placeholder...
              </div>
            </div>
          </div>
        </section>
      </div>
    `;

    this.bindButtons();
    this.updateControlState();
  }
  bindButtons() {
    this.applyButton = this.querySelector(
      '[data-role="charts-catalog-apply-parameters"]'
    );

    this.resetButton = this.querySelector(
      '[data-role="charts-catalog-reset-parameters"]'
    );

    this.previewButton = this.querySelector(
      '[data-role="charts-catalog-preview-button"]'
    );

    this.generateButton = this.querySelector(
      '[data-role="charts-catalog-generate"]'
    );

    this.applyButton?.addEventListener("click", () => {
      this.applyParameters();
    });

    this.resetButton?.addEventListener("click", () => {
      this.resetParameters();
    });

    this.previewButton?.addEventListener("click", () => {
      const selectedPlots = this.getSelected();

      console.log("Preview plot:", selectedPlots);

      this.dispatchEvent(
        new CustomEvent("preview-dashboard-plot", {
          detail: {
            selectedPlot: selectedPlots[0] ?? null
          },
          bubbles: true,
          composed: true
        })
      );
    });

    this.generateButton?.addEventListener("click", () => {
      const selectedPlots = this.getSelected();

      console.log("Selected plots:", selectedPlots);

      this.dispatchEvent(
        new CustomEvent("generate-dashboard-plots", {
          detail: {
            selectedPlots
          },
          bubbles: true,
          composed: true
        })
      );
    });
  }

  setCatalog(catalog) {
    this.catalog = catalog;
    this.selectedPlot = null;
    this.selectedPlotIndex = null;
    this.editedParametersByFunction = {};
    this.activeCategory = "All";

    if (this.editor) {
      this.editor.destroy();
      this.editor = null;
    }

    const editorContainer = this.querySelector(
      '[data-role="charts-catalog-parameter-editor"]'
    );

    if (editorContainer) {
      editorContainer.replaceChildren();
    }

    this.renderCategoryFilters();
    this.renderCatalog();
    this.setCatalogViewMode("catalog");
    this.applyCategoryFilter();
    this.clearPreview();
    this.updateControlState();
  }

  setCatalogViewMode(mode) {
    const list = this.querySelector(
      '[data-role="charts-catalog-list"]'
    );

    const genaiPanel = this.querySelector(
      '[data-role="charts-catalog-genai-panel"]'
    );

    const workspace = this.querySelector(
      '[data-role="charts-catalog-workspace"]'
    );

    const genaiOutput = this.querySelector(
      '[data-role="charts-catalog-genai-output"]'
    );

    const isGenAi = mode === "genai";

    list?.classList.toggle("hidden", isGenAi);
    genaiPanel?.classList.toggle("hidden", !isGenAi);
    workspace?.classList.toggle("hidden", isGenAi);
    genaiOutput?.classList.toggle("hidden", !isGenAi);
  }

  renderCategoryFilters() {
    const container = this.querySelector(
      '[data-role="charts-catalog-category-filters"]'
    );

    if (!container || !Array.isArray(this.catalog?.items)) {
      return;
    }

    const categories = [
      "All",
      ...new Set([
        ...this.catalog.items.map(
          plot => plot.category || "General"
        ),
        "GenAi"
      ])
    ];

    container.replaceChildren();

    categories.forEach(category => {
      const chip = document.createElement("span");

      chip.className = "wf-filter-chip";
      chip.textContent = category;

      if (category === this.activeCategory) {
        chip.classList.add("active");
      }

      chip.addEventListener("click", () => {
        this.activeCategory = category;

        this.renderCategoryFilters();

        if (category === "GenAi") {
          this.setCatalogViewMode("genai");
          return;
        }

        this.setCatalogViewMode("catalog");
        this.applyCategoryFilter();
      });

      container.appendChild(chip);
    });
  }

  applyCategoryFilter() {
    if (!Array.isArray(this.catalog?.items)) {
      return;
    }

    this.querySelectorAll(".charts-catalog-card").forEach(card => {
      const index = Number(card.dataset.index);
      const plot = this.catalog.items[index];

      const isVisible =
        this.activeCategory === "All" ||
        (plot.category || "General") === this.activeCategory;

      card.classList.toggle("hidden", !isVisible);
    });
  }

  renderCatalog() {
    const container = this.querySelector(
      '[data-role="charts-catalog-list"]'
    );

    if (!container) {
      return;
    }

    container.replaceChildren();

    if (!Array.isArray(this.catalog?.items)) {
      container.innerHTML = `
        <div class="alert alert-secondary">
          No catalog loaded.
        </div>
      `;
      return;
    }

    this.catalog.items.forEach((plot, index) => {
      const card = document.createElement("div");

      card.className = "card charts-catalog-card";
      card.dataset.index = String(index);

      card.innerHTML = `
        <div class="charts-catalog-card-header">
          <div class="charts-catalog-card-title">
            ${plot.display_name}
          </div>
        </div>

        <div class="charts-catalog-card-description">
          ${plot.description || ""}
        </div>
      `;

      card.addEventListener("click", () => {
        this.selectPlot(index);
      });

      container.appendChild(card);
    });

    this.updateCardSelectionStyles();
  }

  selectPlot(index) {
    if (!this.catalog?.items?.[index]) {
      return;
    }

    this.selectedPlotIndex = index;
    this.selectedPlot = this.catalog.items[index];

    this.updateCardSelectionStyles();
    this.renderParameterEditor(this.selectedPlot);
    this.updateControlState();

    this.dispatchEvent(
      new CustomEvent("charts-catalog-selection-changed", {
        detail: {
          selectedPlot: this.getSelected()[0] ?? null,
          selectedIndex: index
        },
        bubbles: true,
        composed: true
      })
    );
  }

  updateCardSelectionStyles() {
    this.querySelectorAll(".charts-catalog-card").forEach(card => {
      const index = Number(card.dataset.index);
      const isSelected = index === this.selectedPlotIndex;

      card.classList.toggle("selected", isSelected);
    });
  }

  hasEditableParameters(plot) {
    return Boolean(
      plot?.parameters &&
      Object.keys(plot.parameters).length > 0
    );
  }

  renderParameterEditor(plot) {
    const container = this.querySelector(
      '[data-role="charts-catalog-parameter-editor"]'
    );

    if (!container) {
      return;
    }

    if (this.editor) {
      this.editor.destroy();
      this.editor = null;
    }

    container.replaceChildren();

    const parameters = plot?.parameters || {};

    if (Object.keys(parameters).length === 0) {
      return;
    }

    const schema = this.buildSchemaFromParameters(parameters);

    const data =
      this.editedParametersByFunction[plot.function] ??
      this.buildDataFromParameters(parameters);

    this.editor = new JSONEditor(container, {
      schema,
      startval: data,
      theme: "bootstrap5",
      disable_edit_json: true,
      disable_properties: true,
      no_additional_properties: true,
      compact: true
    });
  }

  buildSchemaFromParameters(parameters) {
    const properties = {};

    Object.entries(parameters).forEach(([key, parameter]) => {
      properties[key] = {
        title: parameter.display_name,
        description: parameter.description,
        type: this.mapParameterType(parameter.type)
      };
    });

    return {
      type: "object",
      title: "Parameters",
      properties
    };
  }

  buildDataFromParameters(parameters) {
    const data = {};

    Object.entries(parameters).forEach(([key, parameter]) => {
      data[key] = parameter.value;
    });

    return data;
  }

  mapParameterType(type) {
    const typeMap = {
      string: "string",
      float: "number",
      int: "integer",
      bool: "boolean"
    };

    return typeMap[type] || "string";
  }

  applyParameters() {
    if (!this.selectedPlot || !this.editor) {
      return;
    }

    const errors = this.editor.validate();

    if (errors.length > 0) {
      console.log("Parameter validation errors:", errors);
      return;
    }

    const values = this.editor.getValue();

    this.editedParametersByFunction[
      this.selectedPlot.function
    ] = values;

    console.log(
      JSON.stringify(
        {
          message: "Parameters applied",
          function: this.selectedPlot.function,
          parameters: values
        },
        null,
        2
      )
    );

    this.dispatchEvent(
      new CustomEvent("charts-catalog-parameters-applied", {
        detail: {
          selectedPlot: this.getSelected()[0] ?? null
        },
        bubbles: true,
        composed: true
      })
    );
  }

  resetParameters() {
    if (!this.selectedPlot) {
      return;
    }

    delete this.editedParametersByFunction[
      this.selectedPlot.function
    ];

    this.renderParameterEditor(this.selectedPlot);
    this.updateControlState();

    console.log(
      JSON.stringify(
        {
          message: "Parameters reset",
          display_name: this.selectedPlot.display_name,
          function: this.selectedPlot.function,
          parameters: this.buildDataFromParameters(
            this.selectedPlot.parameters || {}
          )
        },
        null,
        2
      )
    );
  }

  updateControlState() {
    const parameterActions = this.querySelector(
      '[data-role="charts-catalog-parameter-actions"]'
    );

    const hasSelection = Boolean(this.selectedPlot);
    const hasParameters = this.hasEditableParameters(
      this.selectedPlot
    );

    parameterActions?.classList.toggle(
      "hidden",
      !hasSelection || !hasParameters
    );

    if (this.applyButton) {
      this.applyButton.disabled =
        !hasSelection || !hasParameters;
    }

    if (this.resetButton) {
      this.resetButton.disabled =
        !hasSelection || !hasParameters;
    }

    if (this.previewButton) {
      this.previewButton.disabled = !hasSelection;
    }

    if (this.generateButton) {
      this.generateButton.disabled = !hasSelection;
    }
  }

  getSelected() {
    if (
      !this.catalog ||
      this.selectedPlotIndex === null ||
      !this.catalog.items?.[this.selectedPlotIndex]
    ) {
      return [];
    }

    const originalPlot =
      this.catalog.items[this.selectedPlotIndex];

    const selectedPlot = structuredClone(originalPlot);

    const editedValues =
      this.editedParametersByFunction[originalPlot.function];

    if (editedValues && selectedPlot.parameters) {
      Object.entries(editedValues).forEach(([key, value]) => {
        if (selectedPlot.parameters[key]) {
          selectedPlot.parameters[key].value = value;
        }
      });
    }

    return [selectedPlot];
  }

  displayPreview(element) {
    const previewContainer = this.querySelector(
      '[data-role="charts-catalog-preview"]'
    );

    if (!previewContainer) {
      console.warn("Preview container not found");
      return;
    }

    previewContainer.replaceChildren();

    if (!element) {
      return;
    }

    previewContainer.appendChild(element);

    requestAnimationFrame(() => {
      if (!window.Plotly) {
        return;
      }

      if (element.classList?.contains("js-plotly-plot")) {
        window.Plotly.Plots.resize(element);
      }

      element
        .querySelectorAll?.(".js-plotly-plot")
        .forEach(plot => {
          window.Plotly.Plots.resize(plot);
        });
    });
  }

  clearPreview() {
    const previewContainer = this.querySelector(
      '[data-role="charts-catalog-preview"]'
    );

    if (previewContainer) {
      previewContainer.textContent = "Preview placeholder...";
    }
  }

  attachGenAiChatDialog(chatElement) {
    const container = this.querySelector(
      '[data-role="charts-catalog-genai-panel"]'
    );

    if (!chatElement || !container) {
      console.warn("Could not attach GenAI chat dialog", {
        chatElement,
        container
      });
      return;
    }

    chatElement.style.display = "";
    container.replaceChildren(chatElement);
  }

  displayGenAiOutput(element) {
    const container = this.querySelector(
      '[data-role="charts-catalog-genai-output"]'
    );

    if (!container) {
      console.warn("GenAI output container not found");
      return;
    }

    container.replaceChildren();

    if (element) {
      container.appendChild(element);
    }
  }
}

customElements.define("charts-catalog-control2",ChartsCatalogControl2);






class QuickJS_ComboBoxSelector extends HTMLElement {
    constructor() {
        super();
        this.componentId = this.getAttribute("id") || "";
  
    }
    connectedCallback() {
        this.render();
    }

    //defaultOption.disabled = true;  
    //defaultOption.selected = true;  
    //defaultOption.textContent = 'Select an option...';  
    render() {
        this.innerHTML = `
            <select class="form-select combobox">
                <option disabled selected>Select option</option>
            </select>
        `;
        this.selectElement = this.querySelector("select");
        this.selectElement.addEventListener("change", () => {
            this.dispatchEvent(new CustomEvent("clicked", {
                detail: { text: this.selectElement.value }
            }));
        });
    }

    setData(items) {
        this.selectElement.innerHTML = "";

        let option = document.createElement("option");
        option.setAttribute('disabled', true);
        option.setAttribute('selected', true);
        option.textContent = "Select option";
        //option.value = undefined;
        this.selectElement.appendChild(option);

        items.forEach(item => {
            const option = document.createElement("option");
            option.value = item;
            option.textContent = item;
            this.selectElement.appendChild(option);
        });
    }

    setValue(txt) {
        this.selectElement.value = txt;
        this.dispatchEvent(new CustomEvent("clicked", {
            detail: { text: this.selectElement.value }
        }));
        
    }

    getValue() {
        return this.querySelector('select').value;  

    }

    getOptions() {  
        const select = this.querySelector('select');  
        const options = [];  
        select.querySelectorAll('option').forEach((option) => {  
          if (!option.disabled) {  
            options.push(option.value);  
          }  
        });  
        return options;  
      }  

}
if (!customElements.get("combobox-component")) {
    customElements.define("combobox-component", QuickJS_ComboBoxSelector);
}

class QuickJS_TwoColumnCheckboxList extends HTMLElement {
    constructor() {
        super();
        this.data = [];
        this.componentId = this.getAttribute("id") || "";
    }

    connectedCallback() {
        this.render();
    }

    set_data(items) {
        this.data = items;
        this.render();
    }
    setItems(prefix, count) {
        this.data = Array.from({ length: count }, (_, i) => `${prefix} ${i + 1}`);
        this.render();
    }

    getCheckedItems() {
        return Array.from(this.querySelectorAll("input[type=checkbox]:checked"))
            .map(cb => cb.nextSibling.textContent.trim());
    }

    getAllItems() {
        return this.data;
    }

    render() {
        this.innerHTML = "";
        const container = document.createElement("div");
        container.classList.add("checkbox-rows-container","row", "g-3");

        const col1 = document.createElement("div");
        col1.classList.add("col-6","checkbox-col");
        const col2 = document.createElement("div");
        col2.classList.add("col-6","checkbox-col");

        this.data.forEach((item, index) => {
            const row = document.createElement("div");
            row.classList.add("form-check","checkbox-row");

            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            //checkbox.classList.add("xxform-check-input");
            checkbox.addEventListener("change", () => {
                this.dispatchEvent(new CustomEvent("clicked", {
                    detail: { text: item, checked: checkbox.checked }
                }));
            });

            const label = document.createElement("label");
            label.textContent = item;
            label.classList.add("form-check-label", "ms-2");//, "checkbox-label");
            row.addEventListener("click", () => {
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event("change"));
            });



            row.appendChild(checkbox);
            row.appendChild(label);

            if (index % 2 === 0) {
                col1.appendChild(row);
            } else {
                col2.appendChild(row);
            }
        });

        container.appendChild(col1);
        container.appendChild(col2);
        this.appendChild(container);
    }
}

if (!customElements.get("two-column-checkbox-list")) {
    customElements.define("two-column-checkbox-list", QuickJS_TwoColumnCheckboxList);
}





class OLDChatDialog extends HTMLElement {

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

customElements.define("old-chat-dialog", OLDChatDialog);


