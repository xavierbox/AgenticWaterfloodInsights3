
class InjectorProducerTable extends HTMLElement {
    constructor() {
        super();
        this.data = {};
        this.originalInjectors = [];
        this.something_changed = false;
    }

    connectedCallback() {
        this.innerHTML = `
                    <table class="injector-producer-table">
                        <thead>
                            <tr>
                                <th>Producer</th>
                                <th>Injectors</th>
                                <th class="injector-producer-actions">Actions</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>

                    <div class="injector-producer-overlay"></div>

                    <div class="injector-producer-dialog addInjectorDialog" id="xxxxxxaddInjectorDialog">
                        <div class="injector-producer-dialog-header">
                            <h3>Add Injectors</h3>
                            <button class="injector-producer-close-btn">X</button>
                        </div>
                        <div class="injector-producer-list"></div>
                    </div>

                    <div class="injector-producer-dialog removeInjectorDialog" id="xxxxxremoveInjectorDialog">
                        <div class="injector-producer-dialog-header">
                            <h3>Remove Injectors</h3>
                            <button class="injector-producer-close-btn">X</button>
                        </div>
                        <div class="injector-producer-list"></div>
                    </div>
                `;
        this.renderTable();
        this.querySelectorAll(".injector-producer-close-btn").forEach(btn =>
            btn.addEventListener("click", () => this.closeDialog()));
        
        this.connectEvents();
    }

    connectEvents() {
        let this_object = this; 
        this.querySelector(".injector-producer-table").addEventListener("click", (event)=>this.onCellClick(event));
    }

    
    
onCellClick(event) {

    const cell = event.target;

    if (cell.tagName !== "TD") {
        return;
    }

    const row = cell.closest("tr");
    const rowIndex = row.rowIndex - 1;

    let producers = this.producersInTable();
    const producerName = producers[rowIndex];

    const injectorCell = row.cells[1];
    const rawText = injectorCell?.textContent || "";

    const injectors = rawText
        .split(",")
        .map(inj => inj.trim())
        .filter(inj => inj.length > 0);

    const groups = [
        {
            names: [producerName],
            color: "orange",
            key: "Clicked producers"
        },
        {
            names: injectors,
            color: "cyan",
            key: "Clicked injectors"
        }
    ];

    const eventDetail = new CustomEvent("well-groups-clicked", {
        detail: { groups },
        bubbles: true,
        composed: true
    });

    this.dispatchEvent(eventDetail);
}
    
    
    
    
    old_onCellClick(event) {

        // Find clicked cell
        const cell = event.target;

        // Check if it's in the first column (Producer)
        const cellIndex = cell.cellIndex;
        const isProducerColumn = cellIndex === 0 && cell.tagName === "TD";
        const isInjectorColumn = cellIndex === 1 && cell.tagName === "TD";

        
        if (isProducerColumn) {
            
            const row = cell.closest("tr");
            const rowIndex = row.rowIndex - 1;  // This includes the <thead> row (starts from 0)

            
            let producers = this.producersInTable();
            const producerName = producers[ rowIndex] ;//cell.textContent.trim();
            
            console.log(' row index ', rowIndex );
            console.log(' producers ', producerName);
            
            const customEvent = new CustomEvent("well-clicked", {
                detail: { name: producerName,color:'orange' },
                bubbles: false,
                composed: true
                
            });        
            this.dispatchEvent(customEvent);
        }
        
        if( isInjectorColumn ){
            let rawText = cell.textContent || "";

            // Normalize whitespace and split injectors (if comma-separated)
            const injectors = rawText
                .split(",")
                .map(inj => inj.trim())
                .filter(inj => inj.length > 0); // remove empty entries

            const eventDetail = new CustomEvent("well-clicked", {
                detail: { name: injectors,color:'cyan' },
                bubbles: true,
                composed: true
            });

            this.dispatchEvent(eventDetail);    
            
        }
        
        
    }
        

    
    setData(data) {

        this.data = data;
        this.originalInjectors = [...new Set(Object.values(this.data).flat())];
        this.renderTable();
    }

    getData() {
        return JSON.parse(JSON.stringify(this.data)); // Deep copy
    }

    producersInTable() {
        return Object.keys(this.data);
    }

    injectorsInTable() {

        let uniqueValues = [...new Set(Object.values(this.data).flat())];
        return uniqueValues;
    }



    renderTable() {

        //this.something_changed = false;

        const tableBody = this.querySelector("tbody");
        tableBody.innerHTML = "";
        Object.keys(this.data).forEach(producer => {
            const row = document.createElement("tr");

            const producerCell = document.createElement("td");
            producerCell.innerHTML = `${producer} <button class="injector-producer-trash-btn" onclick="this.closest('injector-producer-table-component').deleteProducer('${producer}')">x</button>`;
            row.appendChild(producerCell);

            const injectorsCell = document.createElement("td");
            injectorsCell.textContent = this.data[producer].join(", ");
            row.appendChild(injectorsCell);

            const actionsCell = document.createElement("td");
            actionsCell.classList.add("injector-producer-actions");

            const addButton = document.createElement("button");
            addButton.innerHTML = "+";
            addButton.classList.add(['injector-producer-add-btn', 'injector-producer-actions-button']);
            addButton.onclick = () => this.showAddDialog(producer);
            actionsCell.appendChild(addButton);

            const removeButton = document.createElement("button");
            removeButton.innerHTML = "-";
            removeButton.classList.add(['injector-producer-remove-btn', 'injector-producer-actions-button']);
            removeButton.onclick = () => this.showRemoveDialog(producer);
            actionsCell.appendChild(removeButton);

            row.appendChild(actionsCell);
            tableBody.appendChild(row);
        });

        //alert('rendering the rates charts ')

        this.render_charts();
    }//'injector-producer-actions-button'        


    render_charts() {
        this.dispatchEvent(new CustomEvent('table-changed'));
    }

    showAddDialog(producer) {

        this.something_changed = false;

        const dialog = this.querySelector(".addInjectorDialog");
        const list = dialog.querySelector(".injector-producer-list");
        list.innerHTML = "";

        const unusedInjectors = this.originalInjectors.filter(inj => !this.data[producer].includes(inj)).sort();
        unusedInjectors.forEach(injector => {
            const item = document.createElement("div");
            item.innerHTML = `<span class='xx'> ${injector} <button class='injector-producer-add-btn injector-producer-actions-button' onclick="this.closest('injector-producer-table-component').addInjector('${producer}', '${injector}')">+</button></span>`;
            list.appendChild(item);
        });

        this.querySelector(".injector-producer-overlay").style.display = "block";
        dialog.style.display = "block";
    }

    showRemoveDialog(producer) {

        this.something_changed = false;

        const dialog = this.querySelector(".removeInjectorDialog");
        const list = dialog.querySelector(".injector-producer-list");
        list.innerHTML = "";

        this.data[producer].forEach(injector => {
            const item = document.createElement("div");

            item.innerHTML = `<span class='xx'>  ${injector} <button class='injector-producer-remove-btn injector-producer-actions-button' onclick="this.closest('injector-producer-table-component').removeInjector('${producer}', '${injector}')">-</button></span>`;
            list.appendChild(item);
        });

        this.querySelector(".injector-producer-overlay").style.display = "block";
        dialog.style.display = "block";
    }

    closeDialog() {

        this.querySelectorAll(".injector-producer-dialog, .injector-producer-overlay").forEach(el => el.style.display = "none");

        this.something_changed = false;

    }

    addInjector(producer, injector) {

        this.something_changed = true;

        this.data[producer].push(injector);
        this.renderTable();
        this.showAddDialog(producer);
    }

    removeInjector(producer, injector) {

        this.something_changed = true;


        this.data[producer] = this.data[producer].filter(item => item !== injector);
        this.renderTable();
        this.showRemoveDialog(producer);
    }

    deleteInjector(injector_name) {

        this.something_changed = true;
 

        for (const producer in this.data) {
            this.data[producer] = this.data[producer].filter(item => item !== injector_name);

            if (this.data[producer].length == 0) {
                delete this.data[producer];
            }
        }

        this.renderTable();
    }

    deleteProducer(producer) {

        this.something_changed = true;
        //console.log('deleteProducer called');

        delete this.data[producer];
        this.renderTable();
    }



}

customElements.define("injector-producer-table-component", InjectorProducerTable);

class CRMSetupElement extends HTMLElement {
    
    
    constructor() {
        super();
        this.has_bhp = false; 
    }
    
    disconnectedCallback() {
      this.querySelectorAll(".js-plotly-plot").forEach(div => {
        Plotly.purge(div);
      });

      this.well_rates = null;
      this.distances_table = null;
      this.extracted_pairs = null;
    }
    

    distances_table;
    extracted_pairs;
    well_rates;
    date1
    date2
    koval_date1
    koval_date2 
    has_nhp 

    setDistanceThreshold(dist) {
        const input = this.querySelector('.model-distance-button');
        if (input) input.value = dist;
    }

    setPairs(data) {
        const table = this.querySelector('injector-producer-table-component');
        if (table) {
            table.setData(data);
            table.classList.remove('hidden');
        }
    }
      
    setState( state ){
        
 
        
           this.querySelector('.model-name').value = state['simulation']['name'];
           this.querySelector('.model-type').value = state['simulation']['type'];
           this.querySelector('.model-balance').value = state['simulation']['balance']['type'];

           this.querySelector('.crm-setup-export-only').checked = state['export_only'];
           this.querySelector('.run-liquid-check').checked = state['run_liquid'];
           this.querySelector('.run-watercut-check').checked = state['run_watercut'];
           this.querySelector('.run-pfm-check').checked = state?.run_pfm ?? false;
           
         
             
           /*set the threshold distance*/
           this.setDistanceThreshold(state['distance']);
        
           /*create a default list of pairs*/
           this.extractPairs( state['distance']*1.0001 );
        
           /*oveerwrite it if the state has it*/
           this.setPairs( state['explicit_entries'] )
           
           /*parameters at the bottom*/
           this.updateAdvancedModelInputs(state);
        
           /*charts dates and trackbars*/
           this.updateDatesAndTrackbars( state );
    }
                  
    updateDatesAndTrackbars( state ){
        
            //array of dates .
            //const dates = this.well_rates['dates'];
            const liquid_dates = state['simulation']['dates'];
            this.date1  = liquid_dates[0];
            this.date2  = liquid_dates[1];
        
            const koval_dates  = state['koval']['dates'];
            this.koval_date1  = koval_dates[0];
            this.koval_date2  = koval_dates[1];
        

            // Get the full timeline of dates
            const allDates = this.well_rates?.dates || [];

            // Get liquid and koval date ranges
            const [liquidStart, liquidEnd] = state.simulation?.dates || [];
            const [kovalStart, kovalEnd] = state.koval?.dates || [];

            // Helper to map date range to [0,1] positions
            function getPercentRange(startDate, endDate, allDates) {
                const total = allDates.length - 1;
                const startIndex = allDates.indexOf(startDate);
                const endIndex = allDates.indexOf(endDate);

                if (startIndex === -1 || endIndex === -1 || total <= 0) return [0, 1];

                return [100.0*startIndex / total, 100.0*endIndex / total];
            }

            // Compute percent positions
            const [liquidMinPct, liquidMaxPct] = getPercentRange(liquidStart, liquidEnd, allDates);
            const [kovalMinPct, kovalMaxPct] = getPercentRange(kovalStart, kovalEnd, allDates);
            
            
            console.log('---------------------Percentages for the tackbars')
            console.log( liquidMinPct, liquidMaxPct )
            console.log( kovalMinPct, kovalMaxPct )
            
            let track1 = this.getElementsByTagName('double-range-component')[0]
            let track2 = this.getElementsByTagName('double-range-component')[1]
            
            track2.setRanges(kovalMinPct, kovalMaxPct);
            track1.setRanges(liquidMinPct, liquidMaxPct);
     
            
            //this.displayDatesFromTrackbarAsText(1);
            //this.displayDatesFromTrackbarAsText(0);
       
            this.querySelector('#liquid-button').click();
            //this.displayDatesFromTrackbarInCharts(0);
            //this.displayDatesFromTrackbarInCharts(0);

 
        
        
    }

    _getMeanAndStdDistance(data) {
        // Step 1: Group by producer
        const groups = {};
        for (const item of data) {
            if (!groups[item.producer]) groups[item.producer] = [];
            groups[item.producer].push(item.distance);
        }

        // Step 2: Collect up to 3 closest distances per producer
        let filteredDistances = [];
        for (const distances of Object.values(groups)) {
            const top3 = distances.sort((a, b) => a - b).slice(0, 1);
            filteredDistances.push(...top3);
        }

        // Step 3: Compute mean and std over all selected distances
        const mean = filteredDistances.reduce((sum, val) => sum + val, 0) / filteredDistances.length;

        const std = filteredDistances.length === 1 ? 0 : Math.sqrt(filteredDistances.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / filteredDistances.length);


        return { mean, std }
    }

    setData(input_distances_table, input_well_rates) {

        console.log( 'input_well_rates received',  Object.keys(input_well_rates))
        
        
        this.distances_table = input_distances_table;
        this.well_rates = input_well_rates;

        const { mean, std } = this._getMeanAndStdDistance(input_distances_table);
        const threshold = Math.round(mean + 0.000000025 * std);
        this.getElementsByClassName('model-distance-button')[0].value = threshold;
        this.getElementsByClassName('extract-pairs-button')[0].click();// = threshold;
        
        let track1 = this.getElementsByTagName('double-range-component')[0]
        track1.setRanges(5.0, 85.0);// = threshold;

        let track2 = this.getElementsByTagName('double-range-component')[1]
        track2.setRanges(5.0, 85.0);// = threshold;
        
        return

    }

    plotRates() {

 
        let ele1 = this.querySelector('.crm-chart-grid');
        //ele1.innerHTML = '';

        let theTable = this.getElementsByTagName('injector-producer-table-component')[0]
        let visibleProducers = theTable.producersInTable();
        let visibleInjectors = theTable.injectorsInTable();
        let well_rates = this.well_rates;
        if ((well_rates == undefined) || (visibleInjectors.length < 1) || (visibleProducers.length < 1)) {
           
            return;
        }
        let allNames = [...visibleProducers, ...visibleInjectors];
        function formatString(str) {
            if (!str) return '';
            const noUnderscores = str.replace(/_/g, ' ');
            return noUnderscores.charAt(0).toUpperCase() + noUnderscores.slice(1);
        }

  

        /*lets build the traces groups*/
        let n = -1
        //let keys = Array.from( Object.keys(this.well_rates) ).filter(key => key !== 'dates');// ['water_injection', 'liquid_production',  'oil_production', 'water_production']
        
        let pressure_key = 0;
        this.has_bhp = false; 
        let keys = ['water_injection', 'liquid_production',  'oil_production', 'water_production']
        if ('producer_pressure' in well_rates) {
            keys.push('producer_pressure');
            pressure_key = 1;
            this.has_bhp = true; 
        }


        const baseLayout = {
          title: {
            text: '',  // will be overridden
            font: { size: chartTitleFontSize }
          },
          xaxis: {
            title: { font: { size: axisTitleFontSize }, standoff: 10 },
            tickfont: { size: tickFontSize }
          },
          yaxis: {
            title: { font: { size: axisTitleFontSize }, standoff: 10 },
            tickfont: { size: tickFontSize }
          },
          hoverlabel: {
            font: { size: hoverFontSize }
          },
          legend: {
            font: {
              size: legendFontSize   
            },
            itemsizing: 'constant' 
          },

          margin: { l: 40, r: 20, t: 40, b: 40 },
          autosize: true,
          automargin: true
        };

        function makeLayout(titleText) {
            return {
              ...JSON.parse(JSON.stringify(baseLayout)),  // deep copy to avoid mutation
              title: {
                ...baseLayout.title,
                text: titleText
              }
            };
          }


        //const allTraces = [];
        let pressure_trace = [] 
        let traces1 = [];
        let traces2 = [];
        let traces3 = [];
        let traces4 = [];
        
        let layout_top = makeLayout('Pressure');
        
        let layout0 = makeLayout('Water injection');
        let layout1 = makeLayout('Liquid production');
        let layout2 = makeLayout('Oil production');
        let layout3 = makeLayout('Water production');


        let traces_ptr = undefined;
        for (let key of keys) {
            n = n + 1
            let x_ = 'x' //+ n.toString();
            traces_ptr = traces1;
            let y_ = 'y' //+ n.toString();
            if (n == 1) {
                traces_ptr = traces2;
            }
            if (n == 2) {
                traces_ptr = traces3;
            }
            if (n == 3) {
                traces_ptr = traces4;
            }
            if (n == 4) {
                traces_ptr = pressure_trace;
            }
            
            
            let rates = well_rates[key]['data']
            let dates = well_rates[key]['dates']
                        

            let kk = 1;
            for (const well in rates) {


                kk = kk + 1;
                let visibility = allNames.includes(well);
                traces_ptr.push({
                    //works extra_stuff: dates, 
                    xaxis: x_, yaxis: y_,
                    x: dates, y: rates[well], mode: 'lines', name: well,
                    type: 'scattergl',
                    line: {
                        width: 1  // thinner line in chart and legend
                    },
                    visible: visibility
                    //legendgroup: 'group'+n.toString(),
                });
            }

        }
        
        let div0 = this.querySelector('#dd0'); 
        div0.innerHTML = '';
        if(pressure_key!==0){
            div0.style.minHeight = '300px';  // can also use % or vh
       
        }
        else{
         div0.style.display = 'none';
        }

        let div1 = this.querySelector('#dd1'); div1.innerHTML = '';
        let div2 = this.querySelector('#dd2'); div2.innerHTML = '';
        div1.style.minHeight = '300px';  // can also use % or vh
        div2.style.minHeight = '300px';  // can also use % or vh
        
        let div21 = this.querySelector('#dd21'); div21.innerHTML = '';
        let div22 = this.querySelector('#dd22'); div22.innerHTML = '';
        div21.style.minHeight = '300px';  // can also use % or vh
        div22.style.minHeight = '300px';  // can also use % or vh
        
        // Sync zoom/pan
        let isSyncing = false;

        function drelayout2(e, targets) {
            if (isSyncing) return;

            let x0 = e['xaxis.range[0]'];
            const x1 = e['xaxis.range[1]'];

            if (x0 !== undefined && x1 !== undefined) {
                isSyncing = true;
                const promises = targets.map(target =>
                    Plotly.relayout(target, { 'xaxis.range': [x0, x1] })
                );

                Promise.all(promises).then(() => {
                    isSyncing = false;
                });

                return;
            }

            const autoX = e['xaxis.autorange'];
            if (autoX !== undefined) {
                isSyncing = true;
                const promises = targets.map(target =>
                    Plotly.relayout(target, {
                        'xaxis.autorange': true,
                        'yaxis.autorange': true
                    })
                );

                Promise.all(promises).then(() => {
                    isSyncing = false;
                    console.log('Finished autorange sync');
                });
            }
        }
 
        async function plotAllAndSync(element_this) {

            let divs = [div1, div2, div21, div22];

            if (pressure_key !== 0) {
                divs.push(div0);
                await PlotlyNewPlot(div0, pressure_trace, layout_top, { responsive: true });
            }


            await PlotlyNewPlot(div1, traces1, layout0, { responsive: true });
            await PlotlyNewPlot(div2, traces2, layout1, { responsive: true });
            await PlotlyNewPlot(div21, traces3, layout2, { responsive: true });
            await PlotlyNewPlot(div22, traces4, layout3, { responsive: true });

            // Sync relayout events across all divs

            divs.forEach((sourceDiv, i) => {
                const others = divs.filter((_, j) => j !== i);
                sourceDiv.on('plotly_relayout', (e) => drelayout2(e, others));
            });

            // Sync visibility for producer charts (dd2, dd21, dd22)
            let producerDivs = [div2, div21, div22];
            let syncLock = false;

            // Function to update injector visibility based on visible producers
            function updateInjectorVisibility() {
                // Get currently visible producers from any producer chart
                let visibleProducers = [];
                div2.data.forEach((trace) => {
                    if (trace.visible === true || trace.visible === undefined) {
                        visibleProducers.push(trace.name);
                    }
                });

                // Get injector-producer mapping from table
                let table = element_this.querySelector('injector-producer-table-component');
                let pairData = table.getData(); // Returns {producer: [injectors]}

                // Find all injectors connected to visible producers
                let connectedInjectors = new Set();
                visibleProducers.forEach(producer => {
                    if (pairData[producer]) {
                        pairData[producer].forEach(inj => connectedInjectors.add(inj));
                    }
                });

                // Batch update all injector visibility in a single call
                const visibilityArray = div1.data.map(trace => connectedInjectors.has(trace.name));
                const allIndices = div1.data.map((_, i) => i);
                Plotly.restyle(div1, {'visible': visibilityArray}, allIndices);
            }

            producerDivs.forEach((sourceDiv) => {
                sourceDiv.on('plotly_restyle', async (data) => {
                    // Prevent recursive updates
                    if (syncLock) return;

                    // Check if visibility was changed
                    if (data[0] && 'visible' in data[0]) {
                        syncLock = true;

                        try {
                            const visibilityChange = data[0].visible;
                            const traceIndices = data[1]; // Array of trace indices that were changed

                            // Get the names of the traces that were changed
                            const changedTraceNames = traceIndices.map(idx => sourceDiv.data[idx].name);

                            // Update other producer charts
                            const otherProducerDivs = producerDivs.filter(div => div !== sourceDiv);

                            // Batch all updates together
                            const updatePromises = [];

                            otherProducerDivs.forEach(targetDiv => {
                                // Find matching traces by name in target chart
                                changedTraceNames.forEach((traceName, i) => {
                                    const targetTraceIndex = targetDiv.data.findIndex(trace => trace.name === traceName);

                                    if (targetTraceIndex !== -1) {
                                        // Apply the visibility change to the matching trace
                                        const visibility = Array.isArray(visibilityChange) ? visibilityChange[i] : visibilityChange;
                                        updatePromises.push(
                                            Plotly.restyle(targetDiv, {'visible': visibility}, [targetTraceIndex])
                                        );
                                    }
                                });
                            });

                            // Wait for all updates to complete before releasing lock
                            await Promise.all(updatePromises);

                            // Update injector chart to show only connected injectors
                            updateInjectorVisibility();

                        } finally {
                            // Use setTimeout to ensure lock is released after all events propagate
                            setTimeout(() => { syncLock = false; }, 50);
                        }
                    }
                });
            });

            element_this.displayDatesFromTrackbarAsText(0);
            element_this.displayDatesFromTrackbarInCharts(0);
        }
        
        // Call it
        plotAllAndSync( this );

        return
    }

    groupByProducer(filteredPairs) {
        const grouped = {};

        filteredPairs.forEach(({ producer, injector }) => {
            if (!grouped[producer]) {
                grouped[producer] = [];
            }
            grouped[producer].push(injector);
        });

        return grouped; // Returns an object instead of an array
    }

    extractPairs(threshold) {

        if (threshold == undefined) this.setDistanceThreshold(1750);

        let extracted_pairs = this.distances_table.filter(entry => entry.distance <= threshold);

        let filtered_for_visualization = this.groupByProducer(extracted_pairs);

        let table = this.getElementsByTagName('injector-producer-table-component')[0];

        table.setData(filtered_for_visualization);
        table.classList.remove('hidden');
    }

    deleteInjector(injector_name) {

        this.getElementsByTagName('injector-producer-table-component')[0].deleteInjector(injector_name);
    }

    deleteProducer(producer_name) {

        this.getElementsByTagName('injector-producer-table-component')[0].deleteProducer(producer_name);
    }

    validateDistanceEntry() {
        let distance_entry = this.querySelector('.model-distance-button');
        let errorMessage = this.querySelector('.distance-entry-error-message');

        // Convert input value to a number

        let result = true;
        // Convert input value to a number
        const value = parseFloat(distance_entry.value);
        const min = parseFloat(distance_entry.min);
        const max = parseFloat(distance_entry.max);

        // Check if the value is out of range
        if (isNaN(value) || value < min || value > max) {
            errorMessage.textContent = 'Please enter a number between 250 and 5000.';
            distance_entry.style.borderColor = "red"; // Highlight input field
            result = false;
        } else {
            errorMessage.textContent = ""; // Clear error message
            distance_entry.style.borderColor = ""; // Reset input border
            result = true;
        }

        return result;
    }

    displayDatesFromTrackbarAsText(which) {

        let this_object = this;
        if( this_object.well_rates == undefined) return;

        let track = this.getElementsByTagName('double-range-component')[which];
        const [percent1, percent2] = track.getValues();

        const dates = this_object.well_rates['dates'];
        const start = dates[0]; // months are 0-indexed
        const end = dates[dates.length - 1];
        const index1 = Math.round((percent1 / 100) * (dates.length - 1));
        const index2 = Math.round((percent2 / 100) * (dates.length - 1));
        //console.log(index1,index2)

        if( which == 0 ){
        this_object.date1 = dates[Math.min(index1, index2)];
        this_object.date2 = dates[Math.max(index1, index2)];
        this_object.getElementsByClassName('date1-text')[which].textContent = `Selected range: ${this_object.date1} → ${this_object.date2}`;
        }
        if( which == 1 ){
            this_object.koval_date1 = dates[Math.min(index1, index2)];
            this_object.koval_date2 = dates[Math.max(index1, index2)];
            this_object.getElementsByClassName('date1-text')[which].textContent = `Selected range: ${this_object.koval_date1} → ${this_object.koval_date2}`;
            }
            
    }

    displayDatesFromTrackbarInCharts(which){

        let this_object = this;
        console.log('update dates shown in charts', this_object.date1, this_object.date2);

        let [date1,date2] = [this_object.date1, this_object.date2];
        if (which==1){
            date1 = this_object.koval_date1, 
            date2 = this_object.koval_date2;
        }

        let shape = {
            type: 'rect', xref: 'x', yref: 'paper',
            x0: date1, y0: 0.005,
            x1: date2, y1: 1,
            fillcolor: "cyan", //"green",
            opacity: 0.2,
            line: { width: 1, dash: 'dashdot', color: 'green' },
            name: "TimeControlIndicator"
        }

        let ids=  [ '#dd1', '#dd2', '#dd21', '#dd22' ];
        for (let id of ids) {
            let chart = this_object.querySelector(id);
            let layout = chart.layout || {};
            let shapes = Array.isArray(layout.shapes) ? layout.shapes : [];
            
            //let layout = chart.layout;
            //let shapes = undefined;
            shapes = 'shapes' in layout ? layout['shapes'] : [];
            shapes = shapes.filter((item) => !item.name.includes('TimeControlIndicator'));
            shapes.push(shape)
            layout['shapes'] = shapes;
            Plotly.relayout(chart, layout);
        }

  
    }

    connectEvents() {

        let this_object = this;
        this.querySelector('.extract-pairs-button').addEventListener('click', () => {

            if (!this.validateDistanceEntry()) {
                alert('Enter a valid distance threshold')
                return;
            }


            /*extract-pairs-button*/
            if (this.distances_table == undefined) {
                alert('No data available');
                return;
            }


            try {
                let distance_threshold = this.querySelector('.model-distance-button').value;
                this.extractPairs(distance_threshold);
            }
            catch (err) {
                console.log('error', err);
                alert('unexpected error occured when extracting pairs data')
            }

        });


        let distance_entry = this.querySelector('.model-distance-button');
        let errorMessage = this.querySelector('.distance-entry-error-message');
  
        distance_entry.addEventListener('input', function () {
            this_object.validateDistanceEntry();
        });

        this.querySelector('injector-producer-table-component').addEventListener('table-changed', () => {
            this.plotRates();
        });
        
        this.querySelector('injector-producer-table-component').addEventListener('well-clicked', (evt) => {
            console.log('Received', evt );
            let name = evt.detail['name'];
            const xevent = new CustomEvent('well-clicked', {
                detail: { name, color: 'orange' },
                bubbles: true,   // 
                composed: true   // optional: allow crossing shadow DOM
            });  
           
            this.dispatchEvent(xevent);
            
        });
           
        

        let track = this.getElementsByTagName('double-range-component')[0];
        track.addEventListener('clicked', (evt) => {
            evt.stopPropagation(); 
            this_object.displayDatesFromTrackbarAsText(0);
        });
        /*show the time indicator*/
        track.addEventListener('mouse-up', (evt) => {
            //if (this._updatingTrackbars) return;
            evt.stopPropagation(); 
            this_object.displayDatesFromTrackbarAsText(0);
            this_object.displayDatesFromTrackbarInCharts(0);
        });


        let track2 = this.getElementsByTagName('double-range-component')[1];
        track2.addEventListener('clicked', (evt) => {
      
            evt.stopPropagation(); 
            this_object.displayDatesFromTrackbarAsText(1);
        });

        /*show the time indicator*/
        track2.addEventListener('mouse-up', (evt) => {
            evt.stopPropagation(); 
            this_object.displayDatesFromTrackbarAsText(1);
            this_object.displayDatesFromTrackbarInCharts(1);
        });

        this.querySelector(".history-match-save-and-run").addEventListener('click', ()=>{
            //console.log('save and run clicked'); 
            this.exportData();
        } );

        this.querySelector(".history-match-close-button").addEventListener('click', ()=>{
            this.dispatchEvent(new CustomEvent('close-clicked', {detail: {}}));
        });
        
        this.querySelector('#liquid-button').addEventListener('click', () => {
            this.querySelector('#watercut-history-match-card').classList.add('hidden');
            this.querySelector('#liquid-history-match-card').classList.remove('hidden');

            this.querySelector('#liquid-button').classList.add('selected');
            this.querySelector('#watercut-button').classList.remove('selected');

            this.displayDatesFromTrackbarAsText(0);
            this.displayDatesFromTrackbarInCharts(0);
        });
        
        this.querySelector('#watercut-button').addEventListener('click', () => {
            this.querySelector('#watercut-history-match-card').classList.remove('hidden');
            this.querySelector('#liquid-history-match-card').classList.add('hidden');
            this.querySelector('#liquid-button').classList.remove('selected');
            this.querySelector('#watercut-button').classList.add('selected');

            this.displayDatesFromTrackbarAsText(1);
            this.displayDatesFromTrackbarInCharts(1);
        });
        
        
        this.querySelector('#liquid-button').click();
    }
 
    connectedCallback() {
        this.innerHTML = this.getTemplate();
        this.connectEvents();
    }
   
    exportData() {
       
        let to_export = {

            export_only:   this.querySelector('.crm-setup-export-only').checked, 
            run_liquid :   this.querySelector('.run-liquid-check').checked,
            run_watercut : this.querySelector('.run-watercut-check').checked,
            run_pfm:       this.querySelector('.run-pfm-check').checked,
            
            name: this.querySelector('.model-name').value,
            distance: parseFloat(this.querySelector('.model-distance-button').value),
            explicit: this.querySelector('injector-producer-table-component').data,
        }

        let liquid_simulation = {
                //simulation name 
                name: this.querySelector('.model-name').value,

                //crm-p, crm-ip,....
                type: this.querySelector('.model-type').value,

                balance: this.querySelector('.model-balance').value, //none, quick, full

                dates: [this.date1, this.date2],

                parameters : {            
                    tau :  {'bounds':[parseFloat(Id('tau-min').value), parseFloat(Id('tau-max').value )], 'init_value': parseFloat(Id('tau-initial').value)},
                    taup : {'bounds':[parseFloat(Id('taup-min').value),parseFloat(Id('taup-max').value)], 'init_value': parseFloat(Id('taup-initial').value)}, 
                    lambda : {'bounds':[parseFloat(Id('lambda-min').value),parseFloat(Id('lambda-max').value)], 'init_value': parseFloat(Id('lambda-initial').value)},
                    productivity_index : {'bounds':[parseFloat(Id('productivity_index-min').value),parseFloat(Id('productivity_index-max').value)], 'init_value': parseFloat(Id('productivity_index-initial').value)},
                    qo_lambda : {'bounds':[parseFloat(Id('qo_lambda-min').value),parseFloat(Id('qo_lambda-max').value)], 'init_value': parseFloat(Id('qo_lambda-initial').value)}
                }  
        } 
      

        let koval_to_export = {

            dates: [this.koval_date1, this.koval_date2],
            name: this.querySelector('.model-name').value,

            parameters: {
                name: this.querySelector('.model-name').value,
                vp: {'bounds':[1.0e5*parseFloat(Id('vp-min').value), 1.0e5*parseFloat(Id('vp-max').value )], 'init_value': 1.0e5*parseFloat(Id('vp-initial').value)},
                kval: {'bounds':[parseFloat(Id('kval-min').value), parseFloat(Id('kval-max').value )], 'init_value': parseFloat(Id('kval-initial').value)},
                wo: {'bounds':[1.0e4*parseFloat(Id('wo-min').value), 1.0e4*parseFloat(Id('wo-max').value )], 'init_value': 1.0e4*parseFloat(Id('wo-initial').value)},
                fo:{'bounds':[parseFloat(Id('fo-min').value), parseFloat(Id('fo-max').value )], 'init_value': parseFloat(Id('fo-initial').value)}   
            }
        }

        to_export['simulation'] = liquid_simulation;
        to_export['koval']  = koval_to_export;

 
        const event = new CustomEvent("clicked", {
            detail: { crm_setup: to_export },
            bubbles: true,
        })

        this.dispatchEvent(event);
        
    }

    
    getTemplate() {
        return `
            <div id='modelling-page' class='page'>

                <!-- h5>Well selection</h5>
                <div id='lasso-selected-indicator' style="line-height: 60px; vertical-align: middle;" class="hidden blue-indicator">Lasso selection active</div>
                <div id='all-selected-indicator' style="line-height: 60px; vertical-align: middle;" class="white-indicator">Applied filters in chart</div>
                <p></p -->

          
                <span class='subtitle'>Apply distance screener</span>

                <div>
                  <div class="input-group input-group-sm">
                    <input type="number" step="250" value="1750" name="distance_threshold"
                           placeholder="Enter a number (250-5000)"
                           class="model-distance-button form-control"
                           min="250" max="5000" required>

                    <button id="extract-pairs-button"
                            class="extract-pairs-button btn btn-primary">
                      Apply
                    </button>
                  </div>

                  <p class="distance-entry-error-message" style="color: red;"></p>
                </div>
                <!--div>
                    <div  class="input-group">
                    <input type="number" step="250" value='1750' name="distance_threshold" 
                    placeholder = 'Enter a number (250-5000)'  
                    class='model-distance-button form-control form-control' min="250" max="5000" required>
                    <button id='extract-pairs-button' class='extract-pairs-button btn btn-primary'>Apply</button>
                    </div>
                     <p class="distance-entry-error-message" style="color: red;  "></p> 
                </div -->
            
              

                <details><summary>Well pairs</summary>
                <div>
                <injector-producer-table-component class='hidden'></injector-producer-table-component>
                </div>
                </details>

                <p></p>

                <!-- Top wide chart -->
                <div class="chart-container0" style="width:100%; margin-bottom:15px;">
                    <div id="dd0" style="width:100%; height:250px; "></div>
                </div>

                <!-- First row of side-by-side charts -->
                <div class="chart-container" style='display:flex; justify-content: space-evenly;'>
           
                        <div id= 'dd1' style="width:49%"></div>
                        <div id= 'dd2' style="width:50%"></div>
                </div>

                <!-- Second row of side-by-side charts -->
                <div class="chart-container2" style='display:flex; justify-content: space-evenly;'>
           
                        <div id= 'dd21' style="width:49%"></div>
                        <div id= 'dd22' style="width:50%"></div>
                </div>

                

                <p></p>

      

                <button id='liquid-button' class='btn btn-sm'>Liquid history match</button>
                <button id='watercut-button' class='btn btn-sm'>Watercut history match</button>

            <div class='card' id='liquid-history-match-card'>    
                <h5>Liquid history match </h5>
                <span class='subtitle'>Training time frame for liquid history match</span>          
                <div>
                    <div style="margin:30px">
                    <span class='date1-text'>Date1</span><double-range-component></double-range-component>                    
                    </div>
                </div>
                <p></p>
                <h5>Model type:</h5>
                <select name="balance" class="form-select model-type" onchange="function s(this)
                    {  
                                                        
                        let model = this.value;
                        let disabled = (model=='crm_tank') || (model=='crmip')
                        console.log('here, model = ', model,' disabled ', disabled )  
                                                                         
                        if( disabled==true)                                   
                        document.getElementById('model-balance-placeholder').classList.add('hidden')
                        else
                        document.getElementById('model-balance-placeholder').classList.remove('hidden')
                                                           
                    }; 
                    s()">
                <!-- 
                    <option value="crm_tank">CRMT</option>
                <option value="crm_p">CRMP</option>
                <option value="crmip">CRMIP</option>
                -->
                <option value="crmp_constrained">CRMP Constrained</option>
                <option value="crmid_constrained">CRMID Constrained</option>
                <option value="crmtank">CRMTank</option>

                <option selected value="OneLayerBalancedCRMID">CRMID Large-scale balanced </option>



                </select>
                <div id='model-balance-placeholder'><label class='mt-3'>Balanced </label>
                    <select class='form-control form-control-sm model-balance' name="balance" id='model-balance'>
                        <option value="none">No</option>
                        <option selected value="quick">Quick</option>
                        <option value="full">Full</option>
                    </select>
                </div>
           
                <!-- *********************************************** -->
                <br>
                <details><summary>Advanced parameters for liquid history match</summary> 
                <p></p>
                <div class='row'>
                    <div class='col-3 text-end'><b>Parameter</b></div>
                    <div class='col-3 text-center'>Initial</div>
                    <div class='col-3 text-center'>Min</div>
                    <div class='col-3 text-center'>Max</div>
                    <hr>
                </div>

                <div class='row'>
                    <div class='col-3 text-end'><b>Tau</b></div>
                    <div class='col-3'><input class='form-control form-control-sm tau-initial' id=  'tau-initial' type="number" min="0.1" max="100" value="1" decimals="1" step="1"></div>
                    <div class='col-3'><input class='form-control form-control-sm tau-min'     id = 'tau-min' type="number"     min="0.1" max="100" value="0.5" decimals="1" step="1"></div>
                    <div class='col-3'><input class='form-control form-control-sm tau-max'     id = 'tau-max' type="number"     min="0.2" max="100" value="50"  decimals="1" step="1"></div>
                </div>

                <div class='row'>
                    <div class='col-3 text-end'><b>Taup</b></div>
                    <div class='col-3'><input class='form-control form-control-sm taup-initial' id='taup-initial' type="number" min="0.1" max="100" value="1" decimals="1" step="1"></div>
                    <div class='col-3'><input class='form-control form-control-sm taup-min' id='taup-min' type="number" min="0.1" max="100" value="0.5"   decimals="1" step="1"></div>
                    <div class='col-3'><input class='form-control form-control-sm taup-max' id='taup-max'  type="number" min="0.2" max="100" value="50" decimals="1" step="1"></div>
                </div>

                <div class='row'>
                    <div class='col-3 text-end'><b>Lambda</b></div>
                    <div class='col-3'><input class='form-control form-control-sm lambda-initial' id = 'lambda-initial' type="number" min="0.1" max="1.0" value="0.1"
                            decimals="1" step="0.1">
                    </div>

                    <div class='col-3'><input class='form-control form-control-sm lambda-min' id = 'lambda-min' type="number" min="0.0" max="2" value="0.0"
                            decimals="1" step="0.1"></div>
                    <div class='col-3'><input class='form-control form-control-sm lambda-max' id = 'lambda-max' type="number" min="0.0" max="2.0" value="1.2"
                            decimals="1" step="0.1"></div>
                </div>

                <div class='row'>
                    <div class='col-3 text-end'><b>Primary coefficient</b></div>
                    <div class='col-3'><input class='form-control form-control-sm qo_lambda-initial' id='qo_lambda-initial' type="number" min="0.0" max="1.5" value="1.0"
                            decimals="1" step="0.1"></div>
                    <div class='col-3'><input class='form-control form-control-sm qo_lambda-min' id='qo_lambda-min' type="number" min="0.0" max="0.1" value="0.0"
                            decimals="1" step="0.1"></div>
                    <div class='col-3'><input class='form-control form-control-sm qo_lambda-max'  id='qo_lambda-max' type="number" min="0.0" max="2.0" value="1.4"
                            decimals="1" step="0.1"></div>
                </div>

                <div class='row'>
                    <div class='col-3 text-end'><b>Productivity index</b></div>
                    <div class='col-3'><input class='form-control form-control-sm productivity-initial' id='productivity_index-initial' type="number" min="0.0" max="1" value="0.0"
                            decimals="1" step="0.1"></div>
                    <div class='col-3'><input class='form-control form-control-sm productivity-min' id='productivity_index-min' type="number" min="0.0" max="2" value="0.0"
                            decimals="1" step="0.1"></div>
                    <div class='col-3'><input class='form-control form-control-sm productivity-max' id='productivity_index-max' type="number" min="0.0" max="2.0" value="1.0"
                            decimals="1" step="0.1"></div>
                </div>

                <div class='hidden row'>
                    <div class='col-3 text-end'><b>Regularization</b></div>
                    <div class='col-3'>
                        <input class='form-control form-control-sm regularization' id='regularization' type="number" min="0.0" max="0.5" value="0.0" decimals="2"
                            step="0.01">
                    </div>

                </div>
             </details>
            </div>


   <!-- *********************************************** -->





   <div class='card' id='watercut-history-match-card'>   
   <h5>Watercut history match </h5>
   <p style='font-size':0.8em;font-weight:italic;color:green'>Watercut will be modelled for the wells with a liquid history match only </p>


   <span class='subtitle'>Training time frame for watercut history match</span>          
   <div>
       <div style="margin:30px">
       <span class='date1-text'>Date1</span><double-range-component></double-range-component>                    
       </div>
   </div>
   <details><summary>Advanced parameters for watercut history match</summary> 
   <br>
   <!-- koval -->
<div class="row">

<div class='col-4 form-group'>
   <h6>Koval pore volume (vp x 10^5)</h6>
   Initial <input type="number" class="form-control form-control-sm" min="0.5" max="500" value="1.1" decimals="1" step="10"
       id='vp-initial'>
   Min <input type="number" class="form-control form-control-sm" min="0.5" max="500" value="1.1" decimals="1" step="10.0"
       id='vp-min'>
   Max <input type="number" class="form-control form-control-sm" min="0.6" max="500" value="50.0" decimals="1" step="10.0"
       id='vp-max'>
</div>

<div class='col-4 form-group'>
   <h6>Koval heterogeneity (kval)</h6>
   Initial <input type="number" class="form-control form-control-sm" min="1.05" max="30" value="1.05" decimals="1"
       step="0.5" id='kval-initial'>
   Min <input type="number" class="form-control form-control-sm" min="1.05" max="50" value="1.05" decimals="1" step="0.5"
       id='kval-min'>
   Max <input type="number" class="form-control form-control-sm" min="1.15" max="70" value="45.0" decimals="1" step="1"
       id='kval-max'>
</div>
   
<div class='col-4 form-group'>
   <h6>Cummulated water (wo x 10^4)</h6>
   Initial <input class="form-control form-control-sm" type="number" min="0.0" max="1.0" value="0.0" decimals="1"
       step="0.5" id='wo-initial'>
   Min <input type="number" class="form-control form-control-sm" min="0.0" max="10.0" value="0.0" decimals="1" step="0.5"
       id='wo-min'>
   Max <input type="number" class="form-control form-control-sm" min="0.1" max="50.0" value="5.0" decimals="1" step="0.5"
       id='wo-max'>
</div>

<div class=" no-hidden col-6">
<div class=' form-group'>
   <h6>Free parameter (fo)</h6>
   Initial <input type="number" class="form-control form-control-sm" min="0.01" max="0.05" value="0.01" decimals="2"
       step="0.01" id='fo-initial'>
   Min <input type="number" class="form-control form-control-sm" min="0.01" max="0.04" value="0.01" decimals="2" step="0.01"
       id='fo-min'>
   Max <input type="number" class="form-control form-control-sm" min="0.01" max="0.05" value="0.05" decimals="2" step="0.01"
       id='fo-max'>
</div>
</div>
</div>


   </details>
</div>











   <br>
   <br>

<div style="display:flex;flex-direction:row;gap:32px;justify-content:start">
  <!-- Run Button -->

  <div>

                    Export only? <input class='crm-setup-export-only' type="checkbox" >
                    
                  
                    <button style='margin:5px' class="history-match-save-and-run btn btn-success">Run</button>


  </div>

    <!-- Checkbox options -->
    <div style='display:flex; flex-direction:column'>
        <div class="form-check form-check-inline">
            <input  type="checkbox" checked class="run-liquid-check" />
            <label>Run liquid history match</label>
        </div>

        <div class="form-check form-check-inline">
            <input   type="checkbox" class="run-watercut-check" />
            <label>Run watercut history match</label>
        </div>

        <div class="form-check form-check-inline">
            <input   type="checkbox" class="run-pfm-check" />
            <label>Run pattern flow balance</label>
        </div>

 

 
    </div>

</div>




                <br>
                 <span class='subtitle'>Simulation name</span>
                <input class="form-control form-control-sm model-name" type="text" value="TestModel1">
                <p></p>
                <div>
                    <hr>



                    <button style='margin:5px' class="history-match-close-button btn btn-danger">Close</button>
                </div>
            </div>
        `;
    }


    

    updateAdvancedModelInputs(state) {
        const kovalParams = state.koval?.parameters || {};
        const crmpParams = state.simulation?.parameters || {};
        

        // Utility to set a group of inputs
        const setParamInputs = (paramName, paramObj,conversion = 1.0) => {
        
    
            if (!paramObj) return;
        

            const { init_value, bounds } = paramObj;
            const [min, max] = bounds || [null, null];
        
        

            const setValue = (id, val, conversion = 1.0 ) => {
                const el = this.querySelector(`#${paramName}-${id}`);
                if (el && val !== undefined) {

                    el.value = val * conversion ;
        
                }
            

            };

            setValue('initial', init_value,conversion);
            setValue('min', min,conversion);
            setValue('max', max,conversion);
        };

        // KOVAL parameters
        for (let [param, value] of Object.entries(kovalParams)) {

    
            if (typeof value === 'object') {
                let unit_conversion = 1.0;
            
                if( param.includes('wo') ) unit_conversion = 1 /10000.00;
                if( param.includes('vp') ) unit_conversion = 1 /100000.00;


                setParamInputs(param, value, unit_conversion);
            }
        }

        // LIQUID HISTORY MATCH parameters
        for (const [param, value] of Object.entries(crmpParams)) {
            if (typeof value === 'object') {
                setParamInputs( param, value);  // using 'primary' for id fallback
            }
        }


    }




}
customElements.define('crm-setup-element', CRMSetupElement);



