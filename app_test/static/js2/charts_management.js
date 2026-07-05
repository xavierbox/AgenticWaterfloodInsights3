
/*function haversineDistance(p1, p2) {
    const toRad = angle => angle * Math.PI / 180;
    const R = 6371; // Earth radius in km
    const dLat = toRad(p2.lat - p1.lat);
    const dLon = toRad(p2.lon - p1.lon);
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos(toRad(p1.lat)) * Math.cos(toRad(p2.lat)) *
      Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(a));
  }*/


/*attaches a configuration dialog to each chart that can be triggered with right-click */
function attach_chart_config_dialog(chartId) {
    const menu = document.getElementById('trace-config-menu');
    const selector = document.querySelector('#trace-selector ul');

    let currentChartId = chartId;

    const chart = document.getElementById(chartId);
    chart.addEventListener('contextmenu', e => {
        e.preventDefault();

        const chartEl = e.target.closest('.js-plotly-plot');
        if (chartEl) currentChartId = chartEl.id;

        menu.style.display = 'block';
        menu.style.left = e.clientX + 'px';
        menu.style.top = Math.max(80, e.clientY) + 'px';

        renderSelector(currentChartId);
        loadTrace(currentChartId, 0);
    });

    function renderSelector(id) {
        selector.innerHTML = '';
        const data = document.getElementById(id).data;
        data.forEach((trace, i) => {
        const li = document.createElement('li');
        li.textContent = trace.name || `Trace ${i}`;
        li.onclick = () => {
            document.querySelectorAll('#trace-selector li').forEach(el => el.classList.remove('active'));
            li.classList.add('active');
            loadTrace(id, i);
        };
        if (i === 0) li.classList.add('active');
        selector.appendChild(li);
        });
    }

    function loadTrace(id, i) {
        const chart = document.getElementById(id);
        const trace = chart.data[i];
        trace.marker ??= {};
        trace.line ??= {};
        trace.textfont ??= {};

        const modeParts = (trace.mode || '').split('+').filter(Boolean);
        const hasMarkers = modeParts.includes('markers');
        const hasLines = modeParts.includes('lines');
        const hasText = modeParts.includes('text');

        document.getElementById('markerToggle').checked = hasMarkers;
        document.getElementById('markerShape').value = trace.marker.symbol || 'circle';
        document.getElementById('markerColor').value = trace.marker.color || '#000000';
        document.getElementById('markerSize').value = trace.marker.size ?? 6;

        document.getElementById('lineToggle').checked = hasLines;
        document.getElementById('lineColor').value = trace.line.color || '#000000';
        document.getElementById('lineWidth').value = trace.line.width ?? 2;

        document.getElementById('textToggle').checked = hasText;
        document.getElementById('textSize').value = trace.textfont.size ?? 12;

        document.getElementById('applyConfig').onclick = () => {
        const updatedMode = [];
        if (document.getElementById('markerToggle').checked) updatedMode.push('markers');
        if (document.getElementById('lineToggle').checked) updatedMode.push('lines');
        if (document.getElementById('textToggle').checked) updatedMode.push('text');

        const update = {
            mode: [updatedMode.join('+') || 'lines'],
            marker: {
            symbol: document.getElementById('markerShape').value,
            color: document.getElementById('markerColor').value,
            size: Number(document.getElementById('markerSize').value)
            },
            line: {
            color: document.getElementById('lineColor').value,
            width: Number(document.getElementById('lineWidth').value)
            },
            textfont: {
            size: Number(document.getElementById('textSize').value)
            },
            textposition: document.getElementById('textToggle').checked ? 'top center' : 'none'
        };

        Plotly.restyle(id, update, [i]);
        };
    }

    interact(menu).draggable({
        modifiers: [
        interact.modifiers.restrict({
            restriction: 'parent',
            elementRect: { top: 0, left: 0, bottom: 1, right: 1 },
            endOnly: true
        })
        ],
        listeners: {
        move(event) {
            const target = event.target;
            let x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
            let y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;
            //x = Math.max(0, Math.min(window.innerWidth - target.offsetWidth, x));
            //y = Math.max(y, 80);
            target.style.transform = `translate(${x}px, ${y}px)`;
            target.setAttribute('data-x', x);
            target.setAttribute('data-y', y);
        }
        }
    });
    }

  
        

function relayout( container){

        //container.style.padding = '20px';
        let inner_offset = 5; 
        let pad = 5;
    
        let body = document.getElementsByTagName('body')[0];
        const styles = getComputedStyle(body);
        //let color = styles.getPropertyValue('--tint-color')
    
        const update = {
            //title: {text: 'some new title'}, // updates the title
            'width':   (parseInt( container.offsetWidth ) - pad).toString(),   // updates the xaxis range
            'height':  ( parseInt(container.offsetHeight ) - pad).toString(),   // updates the end of the yaxis range
            
            //'paper_bgcolor': color,
            'textposition':  'top center',
            //'plot_bgcolor':  'darkblue',
    
     

            //'x': inner_offset,
            'margin': {
            'l': inner_offset,
            'r': inner_offset,
            'b': 10*inner_offset,
            't': 5*inner_offset,
            //'pad': 4  
            },
            'autosize': true,
            
            };
        Plotly.relayout(container, update);
    
}

    
/*find the well series and index in that series*/
function findWellInLocationsChart( container, name ){

    let index = -1;
    let series = undefined 

    let data = container.data;
    for(let aseries of data){
        let well_names = aseries.text;
        index = well_names.indexOf(name);

        if (index !== -1) {
            series = aseries;
            break;
        }
    }
return [index, series];
}

function highlightWellsInLocationsChart( locs_container, names, key, color, size, opacity ){

        let highlightedTraceIndexes = [];
        if( locs_container.data == undefined ){
            return;
        }

        locs_container.data.forEach((trace, index) => {
                if (trace.name === key) {
                    highlightedTraceIndexes.push(index);
                }
        });
        if (highlightedTraceIndexes.length > 0) {
            //console.log('Deleting traces at indexes:', highlightedTraceIndexes);
            Plotly.deleteTraces(locs_container, highlightedTraceIndexes);
        }

        if(names ==  undefined)
            return; 

        let lats  = [] 
        let longs = [] 
        let text  = [];
        for( let name of names){
            const [index,series] = findWellInLocationsChart( locs_container, name );

            if (index!=-1){
                //const [lat,long] = [series['lat'][index], series['lon'][index]];
                const [lat,long] = [series['x'][index], series['y'][index]];
                
                lats.push(lat);
                longs.push(long);
                text.push(name);
            }
        }
            
        let marker_color = color == undefined ?  highlighted_marker_color : color;
        let marker_size = size == undefined ?  highlighted_marker_size : 10+size;
        let marker_opacity = opacity == undefined ?  highlighted_marker_opacity : opacity-0.1;

        let newTrace = {
                name : key,
                //type:"scattermap",
                type:"scatter",
                mode: "markers",
                //lat: lats,
               // lon: longs,
                x: lats,
                y: longs,
                
                text: text,
                //line: {
                //    width: 33,
                //    color: 'red'
                //  },

                marker: { size: marker_size, color:marker_color, opacity: marker_opacity  },
        }
 
        
        Plotly.addTraces(locs_container, newTrace);
    
    
            /*optional zoom-in*/
            // ✅ Center only — NO zoom
            if (lats.length > 0 && longs.length > 0) {

                // Compute center point of highlighted wells
                const xCenter = (Math.min(...lats) + Math.max(...lats)) / 2;
                const yCenter = (Math.min(...longs) + Math.max(...longs)) / 2;

                // Read current range so scale stays unchanged
                const xRange = locs_container.layout.xaxis.range;
                const yRange = locs_container.layout.yaxis.range;

                const xHalfSpan = (xRange[1] - xRange[0]) / 2;
                const yHalfSpan = (yRange[1] - yRange[0]) / 2;

                // Recenter with the same zoom level
                Plotly.relayout(locs_container, {
                    'xaxis.range': [xCenter - xHalfSpan, xCenter + xHalfSpan],
                    'yaxis.range': [yCenter - yHalfSpan, yCenter + yHalfSpan]
                });
            }


    
    
    
    
    

}

function populate_locations_plot( data ){
    
 
    //debugger;
    
    //let app_layout = Id('main-layout');
    //let where = locations_chart_pane;
    //let locs_container = app_layout.get_pane(where);// Id('locs-chart');

    let tabs = document.getElementById("middle-tabs")
    let locs_container = tabs.getTabPage("Map");

     

    if(2<1){ 
    let key = 'locations';
    let layout = data[key]['layout'];
    Plotly.react(locs_container, data[key]['data'], layout )//, config )
    .then((p)=>{
        locs_chart_initialized = true;
        set_selected_well_names( undefined );
        //resizeObserver.observe(locs_container);
    });
    }
    else{
    let key = 'locations';
    //l = getThemedLayout(data[key]['layout'],isDark);
    let l = data[key]['layout'];
    //l['height'] = locs_container.offsetHeight;
    l['autosize'] = true;
    locs_chart_initialized = true;

    const selectedPoints = [];
    let drawingMode = false;


    let config = {responsive:true,scrollZoom: true  }


    //l = getThemedLayout(l,isDark)
    const themeLayout = plotlyLayouts[currentTheme] || plotlyLayouts.light;
    l = getThemedLayout(l, themeLayout);


    Plotly.newPlot(locs_container, data[key]['data'], l, config )
    .then((p)=>{

        //attach_chart_config_dialog(locs_container.id);

        //console.log('-------------------Locations chart initialized---------------------');
        locs_chart_initialized = true;
        //relayout( locs_container );
        //set_selected_well_names( undefined );


        p.on('plotly_deselect', function () {
            console.log('No data selected');
            set_selected_well_names(undefined);
        });

        p.on('plotly_selected', function(eventData) {
            if (eventData) {
                console.log("Selection type:", eventData.range ? "box" : "lasso");
                console.log("Selected data points:", eventData.points);

                let local_selected_well_names = [];
                for( let point of eventData.points){
                    let index = point.pointIndex;
                    let well_name = point.data.text[index];
                    local_selected_well_names.push(well_name);
                }

                set_selected_well_names( local_selected_well_names );
                console.log('Selected well names:', local_selected_well_names);
            }
            else{
                console.log('No data selected');
                set_selected_well_names(undefined);

            }
        });

        p.on('plotly_click', function(data){
            console.log('Clicked point:', data);
            //if (drawingMode) return;

            const point = data.points[0];
            //alert(`You clicked on (${point.lat}, ${point.lon}) well name is ${point.text}`);



            window.dispatchEvent(new CustomEvent('well-name-selected', {
                detail: { name: point.text }
            }));



        });



    }); 


    }






    // this works !!
    // Plotly chart initialization
    //app_layout.addEventListener('pane-resized', (evt)=>{
    //if( evt.detail.id.includes(where) )
    //{relayout( locs_container );}}) ;



    }


/*called when the user selects some wells with the lasso in the locations chart
  the window also emits an event that other component can subscribe to
*/
function set_selected_well_names( names ){
    selected_well_names = names != undefined ? Array.from(names) : undefined;   
    console.log('Selected well names in locs chart', selected_well_names!=undefined);

    if( (names!=undefined) && (names.length > 0) ){
      //Id('well-selection-indicator').classList.add('active');
      for(let element of document.querySelectorAll('.well-selection-indicator')) 
        {element.style.display = 'block';element.classList.add('active');}
      }
      
    
    else 
      for(let element of document.querySelectorAll('.well-selection-indicator')) 
    {element.style.display = 'none';element.classList.remove('active');}
    //Id('well-selection-indicator').style.display = 'block';

    //Id('well-selection-indicator').classList.remove('active');

 
    window.dispatchEvent(new CustomEvent('wells-names-selected-in-locs-chart', {
        detail: { names: selected_well_names }
    }));
}

function set_selected_well_names_in_scatter_chart( names ){
    selected_well_names_in_scatter_chart = names != undefined ? Array.from(names) : undefined;   
    console.log('Selected well names in scatter chart ', selected_well_names_in_scatter_chart!=undefined);

    window.dispatchEvent(new CustomEvent('wells-names-selected-in-scatter-chart', {
        detail: { names: selected_well_names_in_scatter_chart }
    }));
}

function process_well_names_selected_in_scatter_chart( names ){

    debugger;
    let key = 'Highlighted';
    //let app_layout = Id('main-layout');
    //let where = locations_chart_pane;
    //let locs_container = app_layout.get_pane(where);
    let locs_container = getMapContainer();
    highlightWellsInLocationsChart( locs_container, names, key );
}

function process_wells_selected_in_locs_chart( names ){


    /*Delete the traces added sometime before.*/
    function deleteTracesInLegendGroup(plotDiv, legendGroup) {
        let tracesToDelete = [];
        if( plotDiv.data == undefined ) 
        return new Promise((resolve, reject) => {resolve();});  

        plotDiv.data.forEach((trace, index) => {
            if (trace.legendgroup == legendGroup){
                tracesToDelete.push(index);
            }
        });
        if(tracesToDelete.length < 1 )
            return new Promise((resolve, reject) => {resolve();});

        
        return Plotly.deleteTraces(plotDiv, tracesToDelete);
        
        
    }

    function highlightInWellChartsSelectedWells(names, data, groupName){
        
        if( names == undefined ) return;
        let traceIndex = -1;
        let markersAdded = 0;
        let points = [];

        for(let trace of data){
            traceIndex = traceIndex + 1;
            let text = trace.text;
            if(text == undefined) continue;

            for( let name of names ){
                
                let index = text.indexOf(name);
                if( index !=-1 ) {
                    //console.log('found well name', name, 'in trace', traceIndex, ' point index', index, 'axes',trace.xaxis,trace.yaxis  ); 
                    points.push( {x:trace.x[index], y:trace.y[index],text:trace.text[index],xaxis:trace.xaxis,yaxis:trace.yaxis} )
                    markersAdded+=1;
                }
            }
        }

        /*now lets create a new trace*/
        let traceMap = {};
        let counter = 0;
        let showlegend = true;

        for (let pt of points) {
            let key = `${pt.xaxis}-${pt.yaxis}`;
            if (!traceMap[key]) {

                showlegend =  counter == 0 ? true : false
                counter+=1;

                traceMap[key] = {
                    x: [],
                    y: [],
                    text: [],
                    marker:{
                        size: highlighted_marker_size,
                        color: highlighted_marker_color
                    },
                    textfont: {
                        size: marker_text_size // smaller text size
                    },
                    textposition: 'top center', // text above the marker
                    xaxis: pt.xaxis,
                    yaxis: pt.yaxis,
                    mode: 'markers+text',
                    type: 'scatter',
                    name: groupName,
                    legendgroup: groupName,
                    showlegend: showlegend
                };
            }
            traceMap[key].x.push(pt.x);
            traceMap[key].y.push(pt.y);
            traceMap[key].text.push(pt.text);
        }

        // Convert grouped traces into an array
        let traces = Object.values(traceMap);
        //console.log( 'tracess to add')
        //console.log( traces )

        return Plotly.addTraces(plot, traces );//, plot.layout, plot.config);
    }

    //can i highlight the wells in the wells selected in the charts in the locs chart? 
    let plot = Id('sector-plot-wells');
    if(plot!=undefined){
        let data = plot.data;
        deleteTracesInLegendGroup(plot, 'Selected loc.'). then( ()=>{
        if( (names!=undefined) && (names.length > 0) ){
            highlightInWellChartsSelectedWells(names, data, 'Selected loc.');
        }
        });
    }

}



