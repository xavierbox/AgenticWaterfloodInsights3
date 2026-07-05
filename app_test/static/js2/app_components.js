

class QuickJS_ThreeColumnMainLayout extends HTMLElement {
    constructor() {
        super();
    }

    getTemplate() {
        // Create the inner HTML structure
        return `
                        <div id="main-layout" class="caaontainer-fluid">
                            <div  class="arow">
                                <div id='columns-container' class="columns-container">
                                    <!-- Left Pane -->
                                    <div id="left-pane" class="col-2 column" style="xxwidth: 30%; position: relative;">
                                        <div id = 'left-top' class="pane flex-grow-1" style="overflow-y: auto;max-height: 100%; flex-basis: 60%;"></div>
                                        <div class="handler" style="flex-basis: 1%;"></div>

                             

                                        <div id = 'left-bottom' class="pane flex-grow-1" style="overflow-y: auto;max-height: 100%; flex-basis: 55%;"></div>
                                    </div>

                                    <!-- Middle Pane -->
                                    <div id="middle-pane" class="col-5 column gx-2" style=xx"width: 35%; position: relative;">
                                        <div id="left-separator" class="separator"  ></div>
                                        <div id = 'middle-top'  class="pane flex-grow-1" style="overflow-y: auto;flex-basis: 100%;"></div>
                                        <div class="handler flex-grow-0 flex-basis: 1%;"></div>
                                        <div id = 'middle-bottom' class="pane flex-grow-0" style="overflow-y: auto;flex-basis: 100%;"></div>
                                    </div>

                                    <!-- Right Pane -->
                                    <div id="right-pane" class="col-5 column" style="xxwidth: 35%position: relative; xxleft:10px">
                                        <div  id = 'right-top' class="pane flex-grow-1" style="overflow-y: auto;flex-basis: 100%;"></div>
                                        <div class="handler flex-grow-0 flex-basis: 1%;"></div>
                                        <div  id = 'right-bottom' class="pane flex-grow-0" style="overflow-y: auto;flex-basis: 100%;">
                                  
                                        </div>
                                        <div id="right-separator" class="separator" style="xxleft:-12px"></div>
                                    </div>
                                </div>
                            </div>
                               
                             
                        </div>

                    `;


    }

    getStyle() {
        return "";
        return `

 
            .pane {
                background-color: transparent;
                border: 1px solid #ddd;
                padding: 10px;
         
            }

            #left-pane .pane:nth-child(1) {
                background-color: transparent; //#ffcccc; /* Random light color */
            }

            #left-pane .pane:nth-child(2) {
                background-color: transparent; //#ccffcc; /* Random light color */
            }

            #left-pane .pane:nth-child(3) {
                background-color: transparent; //#ccccff; /* Random light color */
            }

            #middle-pane .pane:nth-child(1) {
                background-color: transparent; //#ffffcc; /* Random light color */
            }

            #middle-pane .pane:nth-child(2) {
                background-color: transparent; //#ccffff; /* Random light color */
            }

            #right-pane .pane:nth-child(1) {
                background-color: transparent; //#ffccff; /* Random light color */
            }

            #right-pane .pane:nth-child(2) {
                background-color: transparent; //#cce5ff; /* Random light color */
            }

            .columns-container {
                display: flex;
                height: 100vh;
                gap: 0;
            }

            .column {
                display: flex;
                flex-direction: column;
                gap: 5px; /* Small gap between rows */
                xxposition: relative;
                height: calc(100vh - 62px)
                margin-top:10px;
            }

            .separator {
                width: 8px;
                background-color: grey;
                cursor: ew-resize;
                position: absolute;
                top: 0;
                bottom: 0;
                z-index: 1;
            }

            .separator:hover {
                background-color: black;
            }

            .handler:hover {
                background-color: black;
                height: 10px;
            }

            .handler {
                height: 10px;
                background-color: grey;
            }
        `;

    }

    initResizableMessages() {
        return;
        const separator = this.querySelector("#messages-separator");
        const messages = this.querySelector("#messages");
        let xxisResizing = false;
        let xxstartY, xxstartHeight;


        function xxonMouseMove(e) {
            if (!xxisResizing) return;

            //console.log('moving!!!')

            let delta = (e.clientY - xxstartY)
            const newHeight = xxstartHeight - delta;
            messages.style.height = `${newHeight}px`;

            let leftSeparator = this.querySelector('#xxx');

            let h = leftSeparator.offsetHeight + 0.025 * delta;
            //console.log( 'h', h, delta)

            leftSeparator.style.height = h.toString() + 'px';

        }

        function xxonMouseUp() {
            xxisResizing = false;

            //console.log('up!!!')
            document.removeEventListener("mousemove", xxonMouseMove);
            document.removeEventListener("mouseup", xxonMouseUp);
        }

        separator.addEventListener("mousedown", (e) => {
            xxisResizing = true;
            xxstartY = e.clientY;
            xxstartHeight = messages.offsetHeight;
            document.addEventListener("mousemove", xxonMouseMove);
            document.addEventListener("mouseup", xxonMouseUp);
            console.log('down!!!')
        });



    }


    connectedCallback() {
        this.innerHTML = this.getTemplate();
        this.initResizableColumns();
        this.initResizableRows();
        //const style = document.createElement('style');
        //style.textContent = this.getStyle();
        //document.head.appendChild(style);


    }

    initResizableColumns() {
        const leftSeparator = this.querySelector('#left-separator');
        const rightSeparator = this.querySelector('#right-separator');
        const leftPane = this.querySelector('#left-pane');
        const middlePane = this.querySelector('#middle-pane');
        const rightPane = this.querySelector('#right-pane');


        let isResizingLeft = false;
        let lastDownXLeft = 0;

        leftSeparator.addEventListener('mousedown', (e) => {
            isResizingLeft = true;
            lastDownXLeft = e.clientX;
            document.body.style.cursor = 'ew-resize';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizingLeft) return;

            let offset = e.clientX - lastDownXLeft;
            let newLeftWidth = leftPane.offsetWidth + offset;
            let newMiddleWidth = middlePane.offsetWidth - offset;

            //if (newLeftWidth > 50 && newMiddleWidth > 50) {
            leftPane.style.width = `${newLeftWidth}px`;
            middlePane.style.width = `${newMiddleWidth}px`;


            //rightPane.style.margin= "5%";
            //rightPane.style.width = "100%";


            // }

            lastDownXLeft = e.clientX;
        });

        document.addEventListener('mouseup', () => {
            if (isResizingLeft) {
                //console.log('resizing ', leftPane.id );
                //console.log('resizing ', middlePane.id );

                let subpanes = Array.from(leftPane.querySelectorAll('.pane')).concat(Array.from(middlePane.querySelectorAll('.pane')));
                subpanes.push(leftPane);
                subpanes.push(middlePane);
                //console.log('subpanes ', subpanes);
                for (let pane of subpanes) {
                    //console.log('dipathing ', pane.id);
                    this.dispatchEvent(new CustomEvent('pane-resized', {
                        detail: {
                            id: pane.id,
                            offsetWidth: pane.offsetWidth,
                            offsetHeight: pane.offsetHeight
                        }
                    }));
                }


                /*this.dispatchEvent(new CustomEvent('pane-resized', {
    
                    
                    detail: {
                        id: leftPane.id,
                        offsetWidth: leftPane.offsetWidth,
                        offsetHeight: leftPane.offsetHeight
                    }
                }));
    
                this.dispatchEvent(new CustomEvent('pane-resized', {
                    detail: {
                        id: middlePane.id,
                        offsetWidth: middlePane.offsetWidth,
                        offsetHeight: middlePane.offsetHeight
                    }
                }));*/
            }


            isResizingLeft = false;
            document.body.style.cursor = 'default';
        });

        // For the middle-right separator between middle-pane and right-pane

        let isResizingRight = false;
        let lastDownXRight = 0;

        rightSeparator.addEventListener('mousedown', (e) => {
            isResizingRight = true;
            lastDownXRight = e.clientX;
            document.body.style.cursor = 'ew-resize';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizingRight) return;

            let offset = e.clientX - lastDownXRight;
            let newRightWidth = rightPane.offsetWidth - offset;  // Decrease right-pane width on drag left
            let newMiddleWidth = middlePane.offsetWidth + offset;  // Increase middle-pane width on drag left

            //rightPane.style.width = `${newRightWidth}px`;
            //middlePane.style.width = `${newMiddleWidth}px`;

            //old 
            middlePane.style.width = `${newMiddleWidth}px`;

            //let x = window.innerWidth -20 - (leftPane.offsetWidth + offset + newMiddleWidth);
            //console.log(this.parentNode.offsetWidth)
            let x = this.parentNode.offsetWidth - 15 - (leftPane.offsetWidth + offset + newMiddleWidth);
            rightPane.style.width = `${x}px`;
            //rightPane.style.left = '100px';
            lastDownXRight = e.clientX;



        });

        document.addEventListener('mouseup', () => {

            if (isResizingRight) {

                let subpanes = Array.from(rightPane.querySelectorAll('.pane')).concat(Array.from(middlePane.querySelectorAll('.pane')));
                subpanes.push(rightPane);
                subpanes.push(middlePane);
                for (let pane of subpanes) {

                    console.log('here dispatching event ', pane.id);
                    this.dispatchEvent(new CustomEvent('pane-resized', {
                        detail: {
                            id: pane.id,
                            offsetWidth: pane.offsetWidth,
                            offsetHeight: pane.offsetHeight
                        }
                    }));
                }
            }


            isResizingRight = false;
            document.body.style.cursor = 'default';
        });
    }

    initResizableRows() {
        this.querySelectorAll('.handler').forEach(handler => {
            let isDragging = false;

            const onDrag = (e) => {

                if (!isDragging) return;

                const parent = handler.parentNode;
                const prevRow = handler.previousElementSibling;
                const nextRow = handler.nextElementSibling;
                const parentRect = parent.getBoundingClientRect();

                const prevHeight = e.clientY - parentRect.top - prevRow.offsetTop;
                const nextHeight = parentRect.height - prevHeight - handler.offsetHeight;

                //const minHeight = 0; // Minimum height in pixels
                //if (prevHeight > minHeight && nextHeight > minHeight) 
                {
                    handler.style.flexBasis = `${handler.offsetHeight}px`;
                    prevRow.style.flexBasis = `${prevHeight}px`;
                    nextRow.style.flexBasis = `${nextHeight}px`;
                }
            };

            const stopDrag = () => {

                if (isDragging) {
                    const prevRow = handler.previousElementSibling;
                    const nextRow = handler.nextElementSibling;

                    this.dispatchEvent(new CustomEvent('pane-resized', {
                        detail: {
                            id: prevRow.id,
                            newWidth: prevRow.offsetWidth,
                            newHeight: prevRow.offsetHeight
                        }
                    }));

                    this.dispatchEvent(new CustomEvent('pane-resized', {
                        detail: {
                            id: nextRow.id,
                            newWidth: nextRow.offsetWidth,
                            newHeight: nextRow.offsetHeight
                        }
                    }));

                }


                isDragging = false;
                document.body.style.cursor = 'default';
                document.removeEventListener('mousemove', onDrag);
                document.removeEventListener('mouseup', stopDrag);
            };

            handler.addEventListener('mousedown', () => {
                isDragging = true;
                document.body.style.cursor = 'row-resize';
                document.addEventListener('mousemove', onDrag);
                document.addEventListener('mouseup', stopDrag);
            });
        });
    }


    //api 
    /*addDynamicPlotlyChart(where, data, layout, config) {

        function relayout(container) {

            //container.style.padding = '20px';
            let inner_offset = 10;
            let pad = 50;
            const update = {
                title: { text: 'some new title' }, // updates the title
                'width': (parseInt(container.offsetWidth) - pad).toString(),   // updates the xaxis range
                'height': (parseInt(container.offsetHeight) - pad / 2).toString(),   // updates the end of the yaxis range

                //'paper_bgcolor': 'orange',
                //'plot_bgcolor': 'lightgrey',

                //'x': inner_offset,
                'margin': {
                    'l': 78,
                    'r': 78,
                    'b': 48,
                    't': 48,
                    //'pad': 4  
                },
                'autosize': true,

            };
            Plotly.relayout(container, update);

        }
        let container = this.get_pane(where)

        // Plotly chart initialization
        Plotly.newPlot(container, data, layout, config);
        this.addEventListener('pane-resized', (evt) => {
            if (evt.detail.id.includes(where)) {
                relayout(container);
            }
        });
        relayout(container);
    }*/

    // Set content in the specified pane
    set(where, content) {
        const validPanes = ['left-top', 'left-middle', 'left-bottom',
            'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
        ];

        // Check if 'where' is valid
        if (validPanes.includes(where)) {
            const pane = this.querySelector(`#${where}`);

            if (typeof content === 'string') {
                pane.innerHTML = content;  // Set content as innerHTML if it's a string
            } else if (content instanceof HTMLElement) {
                pane.innerHTML = ''; // Clear existing content
                pane.appendChild(content);  // Append the HTML element
            } else {
                console.error('Content must be a string or an HTML element');
            }
        } else {
            console.error('Invalid pane ID');
        }


    }
    clear(where) {
        const validPanes = ['left-top', 'left-middle', 'left-bottom',
            'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
        ];

        // Check if 'where' is valid
        if (validPanes.includes(where)) {
            const pane = this.querySelector(`#${where}`);
            pane.innerHTML = ''; // Clear existing content
        }


    }
    append(where, content) {
        const validPanes = ['left-top', 'left-middle', 'left-bottom',
            'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
        ];

        // Check if 'where' is valid
        if (validPanes.includes(where)) {
            const pane = this.querySelector(`#${where}`);

            //if (typeof content === 'string') {
            //    pane.innerHTML = content;  // Set content as innerHTML if it's a string

            if (content instanceof HTMLElement) {
                //pane.innerHTML = ''; // Clear existing content
                pane.appendChild(content);  // Append the HTML element
            } else {
                console.error('Content must be a an HTML element');
            }
        } else {
            console.error('Invalid pane ID');
        }


    }
    get_pane(id) {
        const validPanes = ['left-top', 'left-middle', 'left-bottom',
            'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
        ];

        // Check if 'where' is valid
        if (validPanes.includes(id)) {
            const pane = this.querySelector(`#${id}`);
            return pane;
        }

    }

}
customElements.define('three-column-main-layout', QuickJS_ThreeColumnMainLayout);

 

class ProjectListComponent extends HTMLElement {
    
    names
    descriptions 
    filtered_descriptions
    tags
    
    constructor() {
    
        super();
    }

    update_project_tags( project_name, tags ){
        
        let description = this.descriptions[project_name];
        this.descriptions[project_name]['tag'] = tags; 
        this.renderProjects();
    }
    
    
    connectedCallback() {
        //const defaultProjects = ["Project Alpha", "Project Beta", "Project Gamma"];
        
       const projects = {
          "DefaultDemoName1": {
            creation_date: "21-12-1983",
            tag: "*"
          },
          "Another": {
            creation_date: "21-12-1983",
            tag: "*"
          }
        };
        
    const title = document.createElement("label");
    title.classList.add("projects-component-title");
    title.textContent = "Projects";
    this.appendChild(title);
    this.appendChild(document.createElement("hr"));
                
    // === Inline Tag Filter UI ===
    const filterRow = document.createElement("div");
    filterRow.classList.add("d-flex", "align-items-center", "mb-3", "gap-2");

    const tagLabel = document.createElement("label");
    tagLabel.textContent = "Tags";
    tagLabel.classList.add("form-label", "mb-0");

    const tagInput = document.createElement("input");
    tagInput.type = "text";
    tagInput.value = "*";
    tagInput.classList.add("tags-input","form-control", "form-control-sm");
    tagInput.style.maxWidth = "200px";

    const applyButton = document.createElement("button");
    applyButton.textContent = "Filter";
    applyButton.classList.add("filter-apply","btn", "btn-sm", "btn-primary");
    applyButton.addEventListener("click", () => {
        // Update current tag input to be used in filtering
        const tagInputEl = this.querySelector(".tags-input");
        this.tags = tagInputEl?.value || "*";

        // Run filtering and rendering
        this.renderProjects();
    });
    
    
    filterRow.appendChild(tagLabel);
    filterRow.appendChild(tagInput);
    filterRow.appendChild(applyButton);
    this.appendChild(filterRow);
        
        
    let items = document.createElement("div");
    items.classList.add("projects-list-container");
        
    this.appendChild(items);
        
    }

    renderProjects() {
        
    
    // Get the container where project cards should be rendered
    const container = this.querySelector(".projects-list-container");
    if (!container) return;

    container.innerHTML = "";  // Clear previous content

    // Case 1: No descriptions loaded
    if (!this.descriptions || Object.keys(this.descriptions).length === 0) {
        container.textContent = "No projects loaded.";
        return;
    }

    // Case 2: Descriptions exist, but none match the filter
    this.filter_projects()
    if (!this.filtered_descriptions || Object.keys(this.filtered_descriptions).length === 0) {
        container.textContent = "No projects found with the given tags.";
        return;
    }

        
    let descriptions = this.filtered_descriptions;
    let tags = this.tags; 
        
        
        
        
       
    const project_names = Object.keys(descriptions);
        
Object.keys(descriptions).forEach(name => {
    const card = document.createElement("div");
    card.classList.add(
        "projects-component-card",
        "card"
    );

    const description = descriptions[name];

    // === CARD ROW: 3 equal columns ===
    const row = document.createElement("div");
    row.classList.add("d-flex", "w-100");

    // === LEFT COLUMN ===
    const leftCol = document.createElement("div");
    leftCol.classList.add("w-100", "d-flex", "flex-column", "text-start");

    const projectName = document.createElement("label");
    projectName.textContent = name;
    projectName.classList.add("project-card-title");

    const creationDateText = document.createElement("div");
    creationDateText.textContent = "Created: " + (description['creation_date'] ?? "no-set");

    const tagWrapper = document.createElement("div");
    tagWrapper.classList.add("mt-2");

    const tagLabel = document.createElement("label");
    tagLabel.textContent = "Tags";
    tagLabel.classList.add("form-label", "me-2");

    const tagText = document.createElement("span");
    tagText.textContent = description['tag'] ?? "no-set";
    tagText.style.cursor = "pointer";
    tagText.style.display = "inline-block";
    tagText.title = "Click to edit tags";

    tagText.addEventListener("click", () => {
        const input = document.createElement("input");
        input.type = "text";
        input.classList.add("form-control", "form-control-sm");
        input.value = tagText.textContent;
        input.style.maxWidth = "200px";

        tagWrapper.replaceChild(input, tagText);
        input.focus();

        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                const newTags = input.value.trim();
                tagText.textContent = newTags;
                tagWrapper.replaceChild(tagText, input);

                const evt = new CustomEvent("tags_changed", {
                    detail: { name, tags: newTags },
                    bubbles: true,
                    composed: true
                });
                this.update_project_tags( name, newTags );
        
                this.dispatchEvent(evt);
            }
        });
    });

    tagWrapper.appendChild(tagLabel);
    tagWrapper.appendChild(tagText);
    leftCol.appendChild(projectName);
    leftCol.appendChild(creationDateText);
    leftCol.appendChild(tagWrapper);

    // === MIDDLE COLUMN ===
    const middleCol = document.createElement("div");
    middleCol.classList.add("w-100");

    // === RIGHT COLUMN ===
    const rightCol = document.createElement("div");
    rightCol.classList.add("w-100", "d-flex", "flex-column", "align-items-end", "text-end");

    const iconRow = document.createElement("div");
    iconRow.classList.add("d-flex", "gap-2", "mb-2", "justify-content-end");

    const deleteBtn = document.createElement("button");
    deleteBtn.innerHTML = `<i class="fas fa-trash-alt"></i>`;
    deleteBtn.classList.add("btn", "btn-sm");
    deleteBtn.style.color = "darkred";
    deleteBtn.title = "Delete project";
    deleteBtn.onclick = () => this.emitDeleteEvent(name);


    const cloneBtn = document.createElement("button");
    cloneBtn.innerHTML = `<i class="fas fa-clone"></i>`;
    cloneBtn.classList.add("btn", "btn-sm");
    cloneBtn.style.color = "cyan";
    cloneBtn.title = "Clone project";
    cloneBtn.onclick = () => this.emitCloneEvent(name);

    iconRow.appendChild(deleteBtn);
    iconRow.appendChild(cloneBtn);

    const openButton = document.createElement("button");
    openButton.textContent = "Open";
    openButton.classList.add("projects-component-button", "btn", "btn-primary");
    openButton.onclick = () => this.emitClickEvent(name);

    rightCol.appendChild(iconRow);
    rightCol.appendChild(openButton);

    row.appendChild(leftCol);
    row.appendChild(middleCol);
    row.appendChild(rightCol);

    card.appendChild(row);

    // ✅ Append the card to the container instead of `this`
    container.appendChild(card);
});

        
/*
    Object.keys(descriptions).forEach(name => {
        const card = document.createElement("div");
        card.classList.add(
            "projects-component-card",
            "card"
           
        );

        let description = descriptions[ name ] ;
        
        // === CARD ROW: 3 equal columns ===
        const row = document.createElement("div");
        row.classList.add("d-flex", "w-100");

        // === LEFT COLUMN ===
        const leftCol = document.createElement("div");
        leftCol.classList.add("w-100", "d-flex", "flex-column", "text-start");

        const projectName = document.createElement("label");
        projectName.textContent = name;
        //projectName.classList.add("fw-bold");
        projectName.classList.add("project-card-title");
        
        

        const creationDateText = document.createElement("div");
        creationDateText.textContent = "Created: "+(description['creation_date'] ?? "no-set");
        //creationDateText.classList.add("text-muted", "small", "mt-1");

        const tagWrapper = document.createElement("div");
        tagWrapper.classList.add("mt-2");
        
        const tagLabel = document.createElement("label");
        tagLabel.textContent = "Tags";
        tagLabel.classList.add("form-label", "me-2"); // optional styling 

        const tagText = document.createElement("span");
        
        tagText.textContent = description['tag'] ?? "no-set";
        //tagText.classList.add("text-muted", "small", "editable-tag", "border", "px-2", "py-1", "rounded");
        tagText.style.cursor = "pointer";
        tagText.style.display = "inline-block";
        tagText.title = "Click to edit tags";

        tagText.addEventListener("click", () => {
            const input = document.createElement("input");
            input.type = "text";
            input.classList.add("form-control", "form-control-sm");
            input.value = tagText.textContent;
            input.style.maxWidth = "200px";

            tagWrapper.replaceChild(input, tagText);
            input.focus();

            input.addEventListener("keydown", (e) => {
                if (e.key === "Enter") {
                    const newTags = input.value.trim();
                    tagText.textContent = newTags;
                    tagWrapper.replaceChild(tagText, input);

                    const evt = new CustomEvent("TagsChanged", {
                        detail: { name, tags: newTags },
                        bubbles: true,
                        composed: true
                    });
                    this.dispatchEvent(evt);
                }
            });
        });

        tagWrapper.appendChild(tagLabel);
        tagWrapper.appendChild(tagText);
        leftCol.appendChild(projectName);
        leftCol.appendChild(creationDateText);
        leftCol.appendChild(tagWrapper);

        // === MIDDLE COLUMN (can be left empty or for future use) ===
        const middleCol = document.createElement("div");
        middleCol.classList.add("w-100");

        // === RIGHT COLUMN ===
        const rightCol = document.createElement("div");
        rightCol.classList.add("w-100", "d-flex", "flex-column", "align-items-end", "text-end");

        // --- Row of Delete + Clone icons ---
        const iconRow = document.createElement("div");
        iconRow.classList.add("d-flex", "gap-2", "mb-2", "justify-content-end");

        const deleteBtn = document.createElement("button");
        deleteBtn.innerHTML = `<i class="fas fa-trash-alt"></i>`;
        deleteBtn.classList.add("btn", "btn-sm");
        deleteBtn.style.color = "darkred";
        deleteBtn.title = "Delete project";
        deleteBtn.addEventListener("click", () => {
            this.dispatchEvent(new CustomEvent("DeleteProject", {
                detail: { name },
                bubbles: true,
                composed: true
            }));
        });

        const cloneBtn = document.createElement("button");
        cloneBtn.innerHTML = `<i class="fas fa-clone"></i>`;
        cloneBtn.classList.add("btn", "btn-sm");
        cloneBtn.style.color = "cyan";
        cloneBtn.title = "Clone project";
        cloneBtn.addEventListener("click", () => {
            this.dispatchEvent(new CustomEvent("CloneProject", {
                detail: { name },
                bubbles: true,
                composed: true
            }));
        });

        iconRow.appendChild(deleteBtn);
        iconRow.appendChild(cloneBtn);

        // --- Open Button ---
        const openButton = document.createElement("button");
        openButton.textContent = "Open";
        openButton.classList.add("projects-component-button", "btn", "btn-primary");
        openButton.onclick = () => this.emitClickEvent(name);

        rightCol.appendChild(iconRow);
        rightCol.appendChild(openButton);

        // === Final assembly ===
        row.appendChild(leftCol);
        row.appendChild(middleCol);
        row.appendChild(rightCol);

        card.appendChild(row);
        this.appendChild(card);
    });
    */


}

    emitCloneEvent(projectName) {
            const event = new CustomEvent("clone", {
                detail: { projectName },
                bubbles: true,
                composed: true
            });
            this.dispatchEvent(event);
        }

    emitDeleteEvent(projectName) {
        const event = new CustomEvent("delete", {
            detail: { projectName },
            bubbles: true,
            composed: true
        });
        this.dispatchEvent(event);
    }

    emitClickEvent(projectName) {
        const event = new CustomEvent("clicked", {
            detail: { projectName },
            bubbles: true,
            composed: true
        });
        this.dispatchEvent(event);
    }

    setProjects( descriptions, tags ){
        
        if( tags == undefined) tags = '*';
        
        this.tags = tags 
        this.descriptions = descriptions; 
        
        this.renderProjects();
        
    }
    
    deleteProject(name) {
        if (!this.descriptions || !this.descriptions[name]) return;

        // Remove the project
        delete this.descriptions[name];

        // Re-apply filtering and re-render
        this.renderProjects();

        // Optionally emit an event confirming deletion
        this.dispatchEvent(new CustomEvent("project-deleted", {
            detail: { name },
            bubbles: true,
            composed: true
        }));
    }

    filter_projects() {
        const all = this.descriptions || {};
        const inputEl = this.querySelector(".tags-input");

        // Extract filter tags from input element
        const rawInput = inputEl?.value || "*";
        const filterTags = this.process_tags_string(rawInput); // Step 1

        // If filterTags contains '*', include all descriptions
        if (filterTags.includes("*")) {
            this.filtered_descriptions = all;
            return;
        }

        const filtered = {};

        for (const [name, desc] of Object.entries(all)) {
            const itemTags = this.process_tags_string(desc.tag || "*");

            // If item's tags contain '*', always include it
            if (itemTags.includes("*")) {
                filtered[name] = desc;
                continue;
            }

            // Check if all filterTags are present in itemTags
            const matchesAll = filterTags.every(
                tag => itemTags.includes(tag)
            );

            if (matchesAll) {
                filtered[name] = desc;
            }
        }

        console.log('Filtered projects')
        console.log(filtered)
        console.log('All')
        console.log(this.descriptions)
        console.log('Stored tags')
        console.log( this.tags)



        this.filtered_descriptions = filtered;
    }

    process_tags_string(str) {
        if (typeof str === "undefined" || str === null || str.trim() === "") {
            str = ["*"];
        }

        return str
            .split(",")
            .map(s => s.trim())
            .filter(s => s.length > 0);
    }  
}



// Register the custom element with the new name
customElements.define("project-list-component", ProjectListComponent);



class ProjectsContainerComponent extends HTMLElement {
    constructor() {
        super();
    }

    connectedCallback() {
        this.render();
        this.initElements();
    }

    initElements() {
        this.projectListComponent = this.querySelector("#project-list-component");
    }

    setProjects(projects_description) {
        if (this.projectListComponent && typeof this.projectListComponent.setProjects === 'function') {
            this.projectListComponent.setProjects(projects_description);
        } else {
            console.warn("project-list-component or its setProjects method not found.");
        }
    }

    render() {
        // Enforce the base class on the host element
        this.classList.add('projects-component-container');

        this.innerHTML = `
            <div class="projects-component-left">
                <h1>Waterflood Insights</h1>
                <h2>Open project</h2>
            </div>
            <div class="projects-component-divider"></div>
            <div class="projects-component-right">       
                <project-list-component id="project-list-component"></project-list-component>
            </div>
        `;
    }
}

customElements.define('projects-container-component', ProjectsContainerComponent);
        
 
  
        
        

class QuickJS_ConnectDatasetComponent extends HTMLElement {
    constructor() {
        super();
        this.folders = [];
        this.selectedFolder = null;
    }

    connectedCallback() {
        this.render();
    }

    setData(foldersArray) {
        if (Array.isArray(foldersArray)) {
            this.folders = foldersArray;
            this.selectedFolder = null;
            this.render();
        }
    }

    getData() {
        return this.folders;
    }

    getSelected() {
        return this.selectedFolder;
    }

    render() {
        this.innerHTML = `
        <div class="connect-dataset-grid connect-dataset-folder-grid"></div>
        <button class="connect-dataset-button">Connect</button>
      `;

        const grid = this.querySelector(".connect-dataset-folder-grid");

        this.folders.forEach(folderName => {
            const folderEl = document.createElement("div");
            folderEl.classList.add("connect-dataset-folder");
            folderEl.dataset.folder = folderName;
            folderEl.innerHTML = `
          <div class="connect-dataset-folder-icon"></div>
          <div class="connect-dataset-folder-label">${folderName}</div>
        `;

            folderEl.addEventListener("click", () => this.selectFolder(folderName));
            grid.appendChild(folderEl);
        });

        const button = this.querySelector(".connect-dataset-button");
        button.addEventListener("click", () => {
            if (this.selectedFolder) {
                this.dispatchEvent(new CustomEvent("clicked", {
                    detail: { folder: this.selectedFolder }
                }));
            } else {
                alert("Please select a folder before connecting.");
            }
        });
    }

    selectFolder(folderName) {
        this.selectedFolder = folderName;
        const allFolders = this.querySelectorAll(".connect-dataset-folder");

        allFolders.forEach(folderEl => {
            folderEl.classList.toggle("open", folderEl.dataset.folder === folderName);
        });
    }
}
customElements.define("connect-dataset-component", QuickJS_ConnectDatasetComponent);




