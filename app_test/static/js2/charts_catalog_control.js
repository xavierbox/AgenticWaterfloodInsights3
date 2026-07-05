
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
              data-role="charts-catalog-special-card"
              class="charts-catalog-special-card"
            >
              <div class="charts-catalog-special-card-content">
                <div class="tela-logo"></div>

                <div>
                  <div class="charts-catalog-special-button">
                    Create Custom Plot
                  </div>

                  <div class="charts-catalog-special-text">
                    Can't find what you need?<br>
                    Ask Tela to create it for you.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="pane xxwf-panel">
          <div class="wf-panel-header">Description + parameters</div>

          <div class="wf-panel-body charts-catalog-middle-body">
            <div
              data-role="charts-catalog-description"
              class="charts-catalog-description-box"
            >
              Select a plot to see its description and parameters.
            </div>

            <div class="charts-catalog-section-title">Parameters</div>

            <div
              data-role="charts-catalog-parameter-editor"
              class="charts-catalog-parameter-editor"
            ></div>

            <div class="charts-catalog-actions">
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
              <span class="charts-catalog-preview-label">Preview</span>
            </div>

            <div
              data-role="charts-catalog-preview"
              class="charts-catalog-preview-panel"
            >
              Preview placeholder...
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
              class="btn btn-warning w-100"
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

    this.querySelector(
      '[data-role="charts-catalog-description"]'
    ).textContent = "Select a plot to see its description and parameters.";

    this.renderCategoryFilters();
    this.renderCatalog1();
    this.applyCategoryFilter();
    this.updateSelectedCompactList();
    this.updateParameterButtonsState();
  }

  renderCategoryFilters() {
    const container = this.querySelector(
      '[data-role="charts-catalog-category-filters"]'
    );

    if (!container || !this.catalog?.items) return;

    const categories = [
      "All",
      ...new Set(this.catalog.items.map(plot => plot.category || "General"))
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
        this.applyCategoryFilter();
      });

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

    this.querySelector(
      '[data-role="charts-catalog-description"]'
    ).textContent =
      this.selectedPlot.application ||
      this.selectedPlot.description ||
      "No description available.";

    this.renderParameterEditor(this.selectedPlot);
    this.updateParameterButtonsState();
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
      container.innerHTML = `
        <div class="alert alert-secondary">
          This plot has no editable parameters.
        </div>
      `;
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
    if (!this.catalog || !this.selectedPlot) {
      this.applyButton.disabled = true;
      this.resetButton.disabled = true;
      return;
    }

    const selectedIndex = this.catalog.items.findIndex(
      p => p.function === this.selectedPlot.function
    );

    const isDisplayedPlotSelected =
      selectedIndex >= 0 && this.selectedPlotIndexes.includes(selectedIndex);

    this.applyButton.disabled = !isDisplayedPlotSelected;
    this.resetButton.disabled = !isDisplayedPlotSelected;
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

