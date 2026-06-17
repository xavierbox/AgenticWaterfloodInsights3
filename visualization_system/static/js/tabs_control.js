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
 