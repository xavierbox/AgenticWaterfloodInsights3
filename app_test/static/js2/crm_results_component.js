 
class CRMResultsComponent extends HTMLElement {

    _medium_quality_range = [0.5, 0.62];
    _lambdas_taus_flat_data 
    _current_data 
    _lastWellSelected;// for the sankey diagrams
    _koval_crm_flat_data
    text_to_color = {} 
    /*
    const sampleData = {
    case_name: "TestModel1",
    data: [
    { INJECTOR: "I01", PRODUCER: "P1", ALLOCATION: 0.992909593, TAU: 0.349081711, TAUP: 49.99999996, PRODUCTIVITY: 0, Lo: 0, MODEL: "CRMP", R2: 0.991063231, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" },
    { INJECTOR: "I02", PRODUCER: "P1", ALLOCATION: 0.474019881, TAU: 0.349081711, TAUP: 49.99999996, PRODUCTIVITY: 0, Lo: 0, MODEL: "CRMP", R2: 0.991063231, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" },
    { INJECTOR: "I03", PRODUCER: "P1", ALLOCATION: 0.089225377, TAU: 0.349081711, TAUP: 49.99999996, PRODUCTIVITY: 0, Lo: 0, MODEL: "CRMP", R2: 0.991063231, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" },
    { INJECTOR: "I04", PRODUCER: "P1", ALLOCATION: 0.217863424, TAU: 0.349081711, TAUP: 49.99999996, PRODUCTIVITY: 0, Lo: 0, MODEL: "CRMP", R2: 0.991063231, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" },
    { INJECTOR: "I05", PRODUCER: "P1", ALLOCATION: 0.088541907, TAU: 0.349081711, TAUP: 49.99999996, PRODUCTIVITY: 0, Lo: 0, MODEL: "CRMP", R2: 0.991063231, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" },
    { INJECTOR: "I01", PRODUCER: "P2", ALLOCATION: 0.013931884, TAU: 29.33999056, TAUP: 50, PRODUCTIVITY: 0, Lo: 0.959811962, MODEL: "CRMP", R2: 0.937868466, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" },
    { INJECTOR: "I02", PRODUCER: "P2", ALLOCATION: 0, TAU: 29.33999056, TAUP: 50, PRODUCTIVITY: 0, Lo: 0.959811962, MODEL: "CRMP", R2: 0.937868466, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" },
    { INJECTOR: "I03", PRODUCER: "P2", ALLOCATION: 0, TAU: 29.33999056, TAUP: 50, PRODUCTIVITY: 0, Lo: 0.959811962, MODEL: "CRMP", R2: 0.937868466, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" },
    { INJECTOR: "I04", PRODUCER: "P2", ALLOCATION: 0.099183015, TAU: 29.33999056, TAUP: 50, PRODUCTIVITY: 0, Lo: 0.959811962, MODEL: "CRMP", R2: 0.937868466, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" },
    { INJECTOR: "I05", PRODUCER: "P2", ALLOCATION: 0.102164928, TAU: 29.33999056, TAUP: 50, PRODUCTIVITY: 0, Lo: 0.959811962, MODEL: "CRMP", R2: 0.937868466, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" }
    // ... add the rest of the rows similarly
    ]
    };*/


    clipR2Values(data, minValue = -0.5) {
      return data.map(item => {
        return Object.fromEntries(
          Object.entries(item).map(([key, value]) => {
            if (key.toLowerCase() === 'r2' && typeof value === 'number') {
              return [key, Math.max(value, minValue)];
            }
            return [key, value];
          })
        );
      });
    }

//api 
setData = ( case_name, 
            lambdas_taus_flat_data, 
            liquid_history_match_chart, 
            injection_allocation_chart,

           koval_crm_flat_data,
           koval_crm_history_match_chart,

           liquid_max_date, koval_max_date
          
          ) => {

         // Set case name
        this.querySelector("#case-name").textContent = case_name;

        //copy the crm (parameters, not rates) tables. Pick one as the --current-- one   
        //this._lambdas_taus_flat_data = lambdas_taus_flat_data;
        // Apply before assignment
        if(lambdas_taus_flat_data!=undefined)
        this._lambdas_taus_flat_data = this.clipR2Values(lambdas_taus_flat_data);
        else this._lambdas_taus_flat_data = undefined;
       
        //this._koval_crm_flat_data = koval_crm_flat_data;
        if(koval_crm_flat_data!=undefined)
        this._koval_crm_flat_data =  this.clipR2Values(koval_crm_flat_data); 
        else this._koval_crm_flat_data = undefined;
    
        this._current_data = this._lambdas_taus_flat_data;  
        this.drawBarChartAndButtons( this._current_data );
    
        //console.log( '***************************',this._current_data )

        // liquid history match stuff 
        this.draw_liquid_history_match_charts(this._lambdas_taus_flat_data, 
                                              liquid_history_match_chart,
                                              injection_allocation_chart, 
                                              koval_crm_history_match_chart, 
                                              this._koval_crm_flat_data,
                                              liquid_max_date, koval_max_date
                                            );           
          

        
          

}

drawBarChartAndButtons( flat_data ){


    //console.log('drawing box and buttons...')
    this.querySelector('.sim-results-component-top-left').classList.add('hidden');
    this.querySelector('#sim-results-component-bar-chart').innerHTML  = "";
    this.querySelector('.sim-results-component-button-grid').innerHTML  = "";
    this.text_to_color = {};

    if(flat_data==undefined) return;


    // Convert raw data into a Map structure
    const df = flat_data;
    let r2Values = df.map(row => row.R2 ?? row.r2 );
    let avgR2 = r2Values.map(v => Math.max(0, Math.min(1, v))).reduce((a, b) => a + b, 0) / r2Values.length
    
    //switched to quality score 
    r2Values = df.map(row => row.QUALITY_SCORE ?? row.quality_score );
    avgR2 = r2Values.map(v => Math.max(0, Math.min(1, v))).reduce((a, b) => a + b, 0) / r2Values.length
 
    
    

    // Determine overall fit quality
    let overallQuality = "Unknown";
    if (avgR2 < this._medium_quality_range[0])        overallQuality = "poor";
    else if (avgR2 < this._medium_quality_range[1])   overallQuality = "medium";
    else                    overallQuality = "good";

    //big fat square at the left 
    this.querySelector('.sim-results-component-top-left').classList.remove('hidden');
    const qualityBox = this.querySelector("#sim-results-component-fit-box");
    const qualityMap = {
      poor:   { bg: "red",    label: "Poor" },
      medium: { bg: "orange", label: "Medium" },
      good:   { bg: "green",  label: "Good" }
    };

    const q = qualityMap[overallQuality];
    qualityBox.style.backgroundColor = q.bg;
    qualityBox.textContent = q.label;

    // List of unique producers  
    const producers = [...new Set(df.map(row => row.PRODUCER))];
    // Compute fit quality for each producer
    const producerMap = {};
    producers.forEach(p => {
      const pRows = df.filter(row => row.PRODUCER === p);
      //const avg   = pRows.reduce((sum, r) => sum + r.R2, 0) / pRows.length;
      const avg   = pRows.reduce((sum, r) => sum + r.QUALITY_SCORE, 0) / pRows.length;
      
        
        
      let fit = "poor";
      if (avg >= this._medium_quality_range[1]) fit = "good";
      else if (avg >= this._medium_quality_range[0]) fit = "medium";
      producerMap[p] = fit;
    });

    // Define producerNames array here
    const producerNames = Object.keys(producerMap);

    // Bar chart
    const counts = {
      good: producerNames.filter(p => producerMap[p] === 'good').length,
      medium: producerNames.filter(p => producerMap[p] === 'medium').length,
      poor: producerNames.filter(p => producerMap[p] === 'poor').length
    };
      
    PlotlyNewPlot('sim-results-component-bar-chart', [{
            x: ['Good', 'Medium', 'Poor'],
            y: [counts.good, counts.medium, counts.poor],
            type: 'bar',// mode:'markers',
            marker: { 'size':10,color: ['#4caf50', '#ff9800', '#f44336']},
            text: [counts.good, counts.medium, counts.poor],
            textposition: 'auto'
            }], {
            title: {'text':'Fit Quality Distribution',   'font': {'size': 10 },},
 
            autosize:true,   
            margin: {
              l: 35,  // left margin
              r: 35,  // right margin
              t: 30,  // top margin
              b: 20   // bottom margin
          },
            x:{ automargin:true},  yaxis: {
            title: {
              text: 'Count',
              font: {
                size: 10
              }
            }
            },
      
            responsive: true
            }, {responsive: true}
    );
      
    // Render fit buttons
    const buttonGrid = this.querySelector(".sim-results-component-button-grid");
    buttonGrid.innerHTML = "";
    producerNames.forEach(name => {
    const btn = document.createElement("button");
    const quality = producerMap[name];
    btn.className = `fit-button fit-${quality}`;
    btn.textContent = name;
    this.text_to_color[name] = qualityMap[quality].bg;

    btn.addEventListener("click", () => {

      let color = qualityMap[quality].bg;
      //console.log('in the component, the color is ', color )
      let event = new CustomEvent('well-clicked', {detail: { name: name,color:color }});
      this.dispatchEvent(event);  
    });

    buttonGrid.appendChild(btn);
    });



}



connectedCallback() {
this._lastWellSelected = { name: null, type: null };
this.render();

this.connectEventsLiquid()

this.connectEvenstOther()
}

// Line fit Chart
draw_liquid_history_match_charts(lambdas_taus_flat_data, liquid_history_match_chart, injection_allocation_chart,
  koval_crm_history_match_chart,koval_crm_flat_data,
  liquid_max_date, koval_max_date) {
  
  let df = lambdas_taus_flat_data;
  if( liquid_history_match_chart!=undefined){

    let chart_data = liquid_history_match_chart['data']
    let layout = { ...liquid_history_match_chart['layout'], autosize:true, height:300 }
    let config = { ...liquid_history_match_chart['config'], responsive: true}
    let container = this.querySelector("#history-match-chart");
    container.innerHTML = ""; // Clear the container before plotting
    PlotlyNewPlot(container, chart_data, layout, config );
  }

  if( df != undefined){
    let table_container = this.querySelector("#history-match-table"); 
    table_container.setData(df, ['INJECTOR', 'PRODUCER', 'ALLOCATION', 'PRODUCTIVITY', 'LO', 'QUALITY_SCORE', 'TAU', 'TAUP',  'MODEL', 'R2', 'SUBZONE']);
  }

  if(koval_crm_flat_data!=undefined){
    let table_container = this.querySelector("#koval-table"); 
    table_container.setData(koval_crm_flat_data,['PRODUCER','VP','KVAL','QUALITY_SCORE','WO','FO']);
  }

  if( injection_allocation_chart != undefined) {
    let chart_data = injection_allocation_chart['data']
    let layout = { ...injection_allocation_chart['layout'], autosize:true, height:400 }
    let config = { ...injection_allocation_chart['config'], responsive: true}

    let liquid_history_match_chart_container = this.querySelector("#history-match-chart2"); 
    liquid_history_match_chart_container.innerHTML = ""; // Clear the container before plotting
    PlotlyNewPlot(liquid_history_match_chart_container, chart_data, layout, config ).then((p)=>{

      p.on('plotly_click', (eventData) => {
        const point = eventData.points[0]; // first clicked point
        let event = new CustomEvent('well-clicked', {detail: { name: point['label'],color:'cyan' }});
        this.dispatchEvent(event);
    });
  });


 // <div id="koval-history-match-chart" style="width: 100%; height: 100%;"></div>
  if(koval_crm_history_match_chart != undefined){

    let chart_data = koval_crm_history_match_chart['data']
    let layout = { ...koval_crm_history_match_chart['layout'], autosize:true, height:300 }
    let config = { ...koval_crm_history_match_chart['config'], responsive: true}


    PlotlyNewPlot("koval-history-match-chart", chart_data, layout, config )

  }

 
  // Draws the initial Sankey diagram with all injectors and producers
  let injectors_table = this.querySelectorAll('stringlist-component')[0];
  const injectors = [...new Set(df.map(row => row.INJECTOR))];

  injectors_table.setData(injectors);
  injectors_table.addEventListener("clicked", (evt) =>{
      let inj = evt.detail.cell_text;
      this._lastWellSelected = { name: inj, type: "injector" };
      this.drawSankeyInjectorWithContext(inj);
  })
  injectors_table.select_row( 0 );
  this.drawSankeyInjectorWithContext(injectors[0]);

  let producers_table =  this.querySelectorAll('stringlist-component')[1];
  const producers = [...new Set(df.map(row => row.PRODUCER))];
  producers_table.setData(producers);
      
      
  producers_table.addEventListener("clicked", (evt) =>{
      let well = evt.detail.cell_text;
      this._lastWellSelected = { name: well, type: "producer" };
      this.drawSankeyProducerWithContext(well);
  })


}}


drawSankeyInjectorWithContext(injectorName) {
  const data = this._lambdas_taus_flat_data;
  
  // Step 1: Get all producers connected to selected injector
  const directLinks = data.filter(row =>
  row.INJECTOR === injectorName && row.ALLOCATION > 0
  );
  const producers = [...new Set(directLinks.map(r => r.PRODUCER))];
  
  // Step 2: Get all other injectors connected to those producers (excluding selected injector)
  const secondLinks = data.filter(row =>
  producers.includes(row.PRODUCER) &&
  row.INJECTOR !== injectorName &&
  row.ALLOCATION > 0
  );
  
  const otherInjectors = [...new Set(secondLinks.map(r => r.INJECTOR))];
  
  // Create node labels: [selected injector], producers, other injectors
  const nodeLabels = [injectorName, ...producers, ...otherInjectors];
  
  // Utility to get index in node list
  const indexOf = label => nodeLabels.indexOf(label);
  
  // Step 3: Build first layer links: injector → producer
  const links1 = directLinks.map(row => ({
  source: indexOf(injectorName),
  target: indexOf(row.PRODUCER),
  value: row.ALLOCATION,
  label: `Alloc: ${row.ALLOCATION.toFixed(3)}`
  }));
  
  // Step 4: Build second layer links: producer → other injectors
  const links2 = secondLinks.map(row => ({
  source: indexOf(row.PRODUCER),
  target: indexOf(row.INJECTOR),
  value: row.ALLOCATION,
  label: `Alloc: ${row.ALLOCATION.toFixed(3)}`
  }));
  
  const allLinks = [...links1, ...links2];
  
  // Sankey plot data
  const sankeyData = {
  type: "sankey",
  orientation: "h",
  node: {
    pad: 15,
    thickness: 20,
    line: { color: "black", width: 0.5 },
    label: nodeLabels,
    color: nodeLabels.map(label =>
      label === injectorName
        ? "blue"
        : producers.includes(label)
        ? "green"
        : "orange"
    )
  },
  link: {
    source: allLinks.map(l => l.source),
    target: allLinks.map(l => l.target),
    value: allLinks.map(l => l.value),
    label: allLinks.map(l => l.label)
  }
  };
  
  PlotlyReact("sankey-diagram", [sankeyData], {
  margin: { t: 20, b: 20 },
  autosize: true,
  responsive: true,
  title: `Injector ${injectorName} → Producers → Connected Injectors`,
  legend: { orientation: "v" }
  });
  
  //this._lastSankeyData = sankeyData;
  //this._lastSankeyLayout = layout;
  
}
  
drawSankeyProducerWithContext(producerName) {
  const data = this._lambdas_taus_flat_data;
  
  // Step 1: Find injectors connected to selected producer
  const incoming = data.filter(row =>
  row.PRODUCER === producerName && row.ALLOCATION > 0
  );
  const injectors = [...new Set(incoming.map(r => r.INJECTOR))];
  
  // Step 2: Find other producers connected to those injectors
  const outgoing = data.filter(row =>
  injectors.includes(row.INJECTOR) &&
  row.PRODUCER !== producerName &&
  row.ALLOCATION > 0
  );
  const otherProducers = [...new Set(outgoing.map(r => r.PRODUCER))];
  
  // Step 3: Build full node list: [other producers, injectors, selected producer]
  const nodeLabels = [...otherProducers, ...injectors, producerName];
  const indexOf = label => nodeLabels.indexOf(label);
  
  const links1 = incoming.map(row => ({
  source: indexOf(row.INJECTOR),
  target: indexOf(producerName),
  value: row.ALLOCATION,
  label: `Alloc: ${row.ALLOCATION.toFixed(3)}`
  }));
  
  const links2 = outgoing.map(row => ({
  source: indexOf(row.PRODUCER),
  target: indexOf(row.INJECTOR),
  value: row.ALLOCATION,
  label: `Alloc: ${row.ALLOCATION.toFixed(3)}`
  }));
  
  const allLinks = [...links2, ...links1];
  
  // Step 4: Assign fixed horizontal positions (x)
  const x = nodeLabels.map(label => {
  if (label === producerName) return 0.9; // far right
  if (injectors.includes(label)) return 0.5; // middle
  return 0.1; // left for other producers
  });
  
  const sankeyData = {
  type: "sankey",
  orientation: "h",
  node: {
    pad: 15,
    thickness: 20,
    line: { color: "black", width: 0.5 },
    label: nodeLabels,
    color: nodeLabels.map(label => {
      if (label === producerName) return "green";
      if (injectors.includes(label)) return "blue";
      return "orange";
    }),
    x: x
  },
  link: {
    source: allLinks.map(l => l.source),
    target: allLinks.map(l => l.target),
    value: allLinks.map(l => l.value),
    label: allLinks.map(l => l.label)
  }
  };
  
  PlotlyReact("sankey-diagram", [sankeyData], {
  margin: { t: 20, b: 20 },
  autosize: true,
  responsive: true,
  title: `Other Producers → Injectors → ${producerName}`,
  legend: { orientation: "v" }
  });
  
  
}


connectEventsLiquid(){
// sim-results-component-main tab switching

const buttons = this.querySelectorAll(".tab-button");
const pages = this.querySelectorAll(".sim-results-component-page-content");
/*
buttons.forEach((btn) => {
  btn.addEventListener("click", () => {

    console.log('this is one of the tabs for sankey', btn)
    buttons.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");

    pages.forEach((p) => p.classList.remove("active"));
    const target = document.getElementById(btn.dataset.target);
    target.classList.add("active");

    
    if (btn.dataset.target === "page1") {
      console.log("clicked page1", this._lastWellSelected);
    const { name, type } = this._lastWellSelected || {};
    if (name && type === "injector") {
    this.drawSankeyInjectorWithContext(name);
    } else if (name && type === "producer") {
    this.drawSankeyProducerWithContext(name);
    } else {
    this.drawSankey(); // default overview
    }
    }
        
    if (btn.dataset.target === "page2") {console.log('page 2',this._lastWellSelected);}
    
  });
});*/

// Well tab toggle
this.querySelectorAll(".sim-results-component-well-tab").forEach(tab => {
  tab.addEventListener("click", () => {

 
    //console.log("clicked tab",this._lastWellSelected);

    this.querySelectorAll(".sim-results-component-well-tab").forEach(t => t.classList.remove("selected"));
    this.querySelectorAll(".sim-results-component-well-tab").forEach(t => t.classList.remove("active"));
    
    tab.classList.add("selected");tab.classList.add("active");

    this.querySelectorAll(".sim-results-component-well-tab-content").forEach(c => c.classList.remove("selected"));
    this.querySelectorAll(".sim-results-component-well-tab-content").forEach(c => c.classList.remove("active"));
    //this.querySelector('#'+tab.dataset.target).classList.add("selected");
    //this.querySelector('#'+tab.dataset.target).classList.add("active");


    /********************************************************/
    // Get selected well from the current list
    let activeListId = tab.dataset.target;
    let wellListContainer = this.querySelector(`#${activeListId}`);
    wellListContainer.classList.add("selected");
    wellListContainer.classList.add("active");

    const stringList = wellListContainer.querySelector('stringlist-component');
    const selected = stringList?.selected?.();
    const selectedName = selected?.[0]?.cell_text;

    if (activeListId === "injector-list") {
      if (selectedName) {
        this._lastWellSelected = { name: selectedName, type: "injector" };
        this.drawSankeyInjectorWithContext(selectedName);
      }
    } else if (activeListId === "producer-list") {
      if (selectedName) {
        this._lastWellSelected = { name: selectedName, type: "producer" };
        this.drawSankeyProducerWithContext(selectedName);
      }
    }
    /************************************************************** */    







    

  });
});

this.querySelector(".sim-results-component-close-button").addEventListener('click', () =>{

    this.dispatchEvent(new CustomEvent('close-clicked'));


}); 


let lists = this.querySelectorAll('stringlist-component')

for( let e of lists){ 

  e.addEventListener('clicked', (evt) =>{
    let w = evt.detail.cell_text;

    let event = new CustomEvent('well-clicked', {detail: { name: w, color:this.text_to_color[w] || 'cyan' }});
    this.dispatchEvent(event);
  });

}


}

connectEvenstOther(){

  let buttons = [ this.querySelector("#liquid-show"),this.querySelector('#koval-show') ];
  for( let b of buttons){
    b.addEventListener('click', (evt) =>{

      if( b == buttons[0]){
        buttons[0].classList.add('active');
        buttons[1].classList.remove('active');
        this.querySelectorAll('.liquid-results').forEach(e => e.classList.remove('hidden'));
        this.querySelectorAll('.koval-results').forEach(e => e.classList.add('hidden'));

        this._current_data = this._lambdas_taus_flat_data;  
        this.drawBarChartAndButtons( this._current_data );
      }else{
        buttons[1].classList.add('active');
        buttons[0].classList.remove('active');
        this.querySelectorAll('.liquid-results').forEach(e => e.classList.add('hidden'));
        this.querySelectorAll('.koval-results').forEach(e => e.classList.remove('hidden'));

        this._current_data = this._koval_crm_flat_data;
        this.drawBarChartAndButtons( this._koval_crm_flat_data );

      }
    });
  }
    
    
    /*Details*/
    const historyDetailsBtn = this.querySelector("#history-match-details-btn");
const historyTable = this.querySelector("#history-match-table");

historyDetailsBtn.addEventListener("click", () => {
  historyTable.classList.toggle("hidden");
});

const kovalDetailsBtn = this.querySelector("#koval-details-btn");
const kovalTable = this.querySelector("#koval-table");

kovalDetailsBtn.addEventListener("click", () => {
  kovalTable.classList.toggle("hidden");
});
    
    
    
}

render() {
this.innerHTML = `
<div style='display:flex; flex-direction:column; height:100%; justify-content:space-evenly'>


<div style='display:flex; flex-direction:row; justify-content:start;'>
  <button id='liquid-show' class="btn btn-sm active" data-target="liquid-results-container">Liquid </button>
  <button id='koval-show' class="btn btn-sm" data-target="koval-results-container">Watercut</button>
</div>

<!--top part-->
<div class style='display:flex; flex-direction:column; height:100%;'>

      <!-- Top Bar -->
     <div class="sim-results-component-top-bar" style='display:flex; flex-direction:row;'>
         <div class="sim-results-component-top-left" style='width:30%; padding:10px'>
             <div>
             <label><strong>Simulation Case</strong></label><br />
             <span id="case-name">Loading...</span>
             </div>
             <div>
             <p></p>
             <label><strong>Overall fit quality</strong></label>
             <div id="sim-results-component-fit-box">Loading...</div>
             </div>
         </div>

         <div class="sim-results-component-top-right" style='width:70%'>
                 <div id="sim-results-component-bar-chart" style="width: 100%; height: 220px;"></div>
         </div>
     </div>
     <div class="sim-results-component-button-grid" id="sim-results-component-button-grid"></div>

      <div class='liquid-results' style='height:100%;margin-top:10px;'>
        <div id="history-match-chart" style="width: 100%; height: 100%;"></div>
      </div>

      <div class='liquid-results' style='height:100%;margin-top:10px;'>
      <button id="history-match-details-btn" class="btn btn-sm">
        Details
      </button>
        <table-component class='hidden' id='history-match-table'></table-component>
      </div>


      <div class="koval-results hidden" style='display:flex; height:100%;margin-top:10px;'>
        <div class="koval-results" id="koval-history-match-chart" style="width: 100%; height: 100%;"></div>
      </div>

      <div class="koval-results hidden"  style='height:100%;margin-top:10px;'>
      <button id="koval-details-btn"  class="btn btn-sm">
        Details
      </button>
        <table-component class='hidden' id='koval-table'></table-component>
      </div>



</div>



<div class="liquid-results" style='backgorund-color:red; display:flex; flex-direction:column; height:100%;'>



  <div style='display:flex; height:100%;margin-top:10px;'>
        <div id="history-match-chart2" style="width: 100%; height: 100%;"></div>
  </div>

  <h5>Well support</h5>
  <div class="sim-results-component-well-support-container" >
     <div class="sim-results-component-well-list">
       <div class="sim-results-component-sim-results-component-well-tabs">
         <button class="btn btn-sm sim-results-component-well-tab selected " data-target="injector-list">Injectors</button>
         <button class="btn btn-sm sim-results-component-well-tab" data-target="producer-list">Producers</button>
       <p></p>
         </div>
  
      
       <div id="injector-list" style='max-height:350px;overflow-y:scroll;'  class="sim-results-component-well-tab-content active">
        <stringlist-component style='width:40%' ></stringlist-component>
         <!--ul>
           <li>Injector A</li>
           <li>Injector B</li>
           <li>Injector C</li>
         </ul-->
       </div>
       <div id="producer-list" style = 'max-height:350px;overflow-y:scroll;'  class="sim-results-component-well-tab-content">
        <stringlist-component style='width:40%' ></stringlist-component>
         <!-- ul>
           <li>Producer X</li>
           <li>Producer Y</li>
           <li>Producer Z</li>
         </ul-->
       </div>
     </div>
  
     <div id="sankey-diagram" style="flex: 1; min-width: 200px; height: 350px;"></div>
  
  
  </div>

</div>


<div class = 'koval-results'>
</div>

 <div>
 <hr>
 <button class='sim-results-component-close-button btn btn-danger'>Close </button>
<p></p>
 </div>
</div>
`;

// After injecting HTML, initialize script-based behavior:
//this.setup();
}


}
customElements.define("crm-results-component", CRMResultsComponent);


