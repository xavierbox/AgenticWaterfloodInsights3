function prepare_crm_simulation_export( crm_control_setup, project_setup_details) {
                    

    let subzone = project_setup_details['subzone'];

    let sim_params = {

        project_name: project_setup_details['project_name'],
        name: crm_control_setup['name'], 
        filters : {
            sector: project_setup_details['sector'],
            subzone: project_setup_details['subzone'],
            date: project_setup_details['date'],
        },


        /*managed_folder_name: 'azFolder', 
        app_name: 'WF', 
        data_folder_name: 'data', 
        projects_folder_name: 'projects', 
        studies_folder_name: 'studies',
        dt: 1, 
        max_running_time: 1000, 
       
        primary: true, 
        regularization: 0.0,  */
            
    } 

    sim_params.export_only    =  crm_control_setup.export_only;
    sim_params.run_liquid     =  crm_control_setup.run_liquid;
    sim_params.run_watercut   =  crm_control_setup.run_watercut;
    sim_params.run_pfm   =  crm_control_setup.run_pfm;
    
    sim_params.distance = crm_control_setup.distance; 
    sim_params['explicit'] = {
        'subzone': {
            [subzone]: crm_control_setup.explicit
        }
    };


    //sim_params['explicit'] = { 'subzone': { `{subzone}`: crm_control_setup.explicit} };
    sim_params['simulation'] = crm_control_setup.simulation; 
    sim_params['simulation']['balance']= {'type': crm_control_setup.simulation.balance, 'maxiter': 100,'tolerance': 0.01}
    sim_params['simulation']['optimizer']= {'maxiter': 1234, 'name': 'SLSQP', 'tolerance': 0.001} 
    sim_params['koval'] = crm_control_setup['koval'];

    return sim_params;
}



function display_crm_results_control(resp, study_name) {

    let lambdas_taus_flat_table = resp.data['lambdas_taus'];
    let history_match_chart = resp.data['liquid_history_match_chart']
    let injection_allocation_chart = resp.data['injection_allocation_chart']
    
    let koval_crm_results = resp?.data?.koval_crm_results ?? undefined;
    
    let koval_history_match_chart = resp?.data?.koval_history_match_chart ?? undefined;
    
    let liquid_max_date = resp?.data?.liquid_max_date ?? undefined;
    let koval_max_date = resp?.data?.koval_max_date ?? undefined;
  
    let component = new CRMResultsComponent(); 
    Id('results-charts-container').innerHTML = '';
    Id('results-charts-container').classList.remove('hidden');
    Id('results-charts-container').appendChild(component);
    
    
    //console.log( "setting here ", lambdas_taus_flat_table )
    component.setData(study_name,lambdas_taus_flat_table, history_match_chart,
        injection_allocation_chart, 
        koval_crm_results,
        koval_history_match_chart,

        liquid_max_date, koval_max_date
        
    
    );
    component.addEventListener('close-clicked', ()=>{
        Id('results-charts-container').innerHTML = '';
        Id('results-charts-container').classList.add('hidden'); 
        Id('field-tab-button').click();
    });
    component.addEventListener('well-clicked', (evt) =>{
    
        console.log('remitting ', evt)
        window.dispatchEvent(new CustomEvent('well-clicked', {
        detail: evt.detail//{ name: evt.detail.name }
        
    }));
    
});
}
    


function old_for_maps_display_connectivities_in_map(resp){

    let connectivities = resp.data['lambdas_taus'];


    key = 'Connectivity'
    let app_layout = Id('main-layout');
    //let where = locations_chart_pane;
    //let locs_container = app_layout.get_pane(where);
    let locs_container = getMapContainer();

    //when passed undefined, it clears any other with the key 
    highlightWellsInLocationsChart( locs_container, undefined , key )

    let lats  = [];
    let longs = []; 
    let text  = [];
    let lambdas   = []  
    const minWidth = 1;
    const maxWidth = 8;
    let traces = [ ]
    let last_trace = undefined;
    let counter = -1;

    //let r2_traces = [] 
    //let added_producers = new Set();

    for( let c of connectivities){
    const [index1,series1] = findWellInLocationsChart( locs_container, c['INJECTOR'] );
    const [index2,series2] = findWellInLocationsChart( locs_container, c['PRODUCER'] );

    if ((index1!=-1) && (index2!=-1) && (c['ALLOCATION']>0.05) ){
        counter += 1;
        const [lat1,long1] = [series1['lat'][index1], series1['lon'][index1]];
        const [lat2,long2] = [series2['lat'][index2], series2['lon'][index2]];


        const width = 1 + (8 - 1) * c['ALLOCATION']; // scale 0–1 → 1–8

        let newTrace = {
            legendgroup: key, 
            showlegend: counter == 0, 
            name : key,
            type:"scattermap",
            mode: "lines",
            lat: [lat1,lat2],
            lon: [long1,long2],
            line: {width: width,color: valueToColor(c['ALLOCATION']), },
            //text: [ c['ALLOCATION'].toString(), c['ALLOCATION'].toString() ], 
            //hovertemplate:'%{text}<br>',
            hoverinfo: 'skip'

            }

        traces.push(newTrace);
        last_trace = newTrace;
        }
    }

    if(traces.length < 1 )
    return 

    Plotly.addTraces(locs_container, traces).then ((p)=>{
    console.log('traces added');
    });
    }

/* This will work for scattered charts as Dataiku did not work for maps 
*/
function display_connectivities_in_map(resp){

        let app_layout = Id('main-layout');
        //let where = locations_chart_pane;
        //let locs_container = app_layout.get_pane(where);
        let locs_container = getMapContainer();

        if( locs_container.data == undefined ){
            return;
        }
        
        let connectivities = resp.data['lambdas_taus'];
    
    
        key = 'Connectivity'

    
        //when passed undefined, it clears any other with the key 
        highlightWellsInLocationsChart( locs_container, undefined , key )
    
        let lats  = [];
        let longs = []; 
        let text  = [];
        let lambdas   = []  
        const minWidth = 1;
        const maxWidth = 8;
        let traces = [ ]
        let last_trace = undefined;
        let counter = -1;
    
        //let r2_traces = [] 
        //let added_producers = new Set();
    
        for( let c of connectivities){
        const [index1,series1] = findWellInLocationsChart( locs_container, c['INJECTOR'] );
        const [index2,series2] = findWellInLocationsChart( locs_container, c['PRODUCER'] );
    
        if ((index1!=-1) && (index2!=-1) && (c['ALLOCATION']>0.05) ){
            counter += 1;
            const [lat1,long1] = [series1['x'][index1], series1['y'][index1]];
            const [lat2,long2] = [series2['x'][index2], series2['y'][index2]];
    
    
            const width = 1 + (8 - 1) * c['ALLOCATION']; // scale 0–1 → 1–8
    
            let newTrace = {
                legendgroup: key, 
                showlegend: counter == 0, 
                name : key,
                type:"scatter",
                mode: "lines",
                x: [lat1,lat2],
                y: [long1,long2],
                line: {width: width,color: valueToColor(c['ALLOCATION']), },
                //text: [ c['ALLOCATION'].toString(), c['ALLOCATION'].toString() ], 
                //hovertemplate:'%{text}<br>',
                hoverinfo: 'skip'
    
                }
    
            traces.push(newTrace);
            last_trace = newTrace;
            }
        }
    
        if(traces.length < 1 )
        return 
    
        Plotly.addTraces(locs_container, traces).then ((p)=>{
        console.log('traces added');
        });
        }