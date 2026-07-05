
function validateProjectDataSelection(read_data) {
    message = ""

    if(read_data['subzone']==undefined) return "\nInvalid RMU selection\n";
    if(read_data['subzone']=='Select option') return "\nInvalid RMU selection\n";

    
    if(!isValidDate( read_data['date'][0])) message = "\nInvalid start date\n";
    if(!isValidDate( read_data['date'][1])) message += "\nInvalid end date\n";

    return message;
}


function get_project_data_selection( ){

    let data = {}
    data['subzone'] = Id('reservoir-unit-selector').getValue();
    data['date']   = [Id('start-date').value, Id('end-date').value];
    data['sector'] = Id('sector-selector').getCheckedItems().map(str => parseInt(str));
    data['project_name'] = Id('project_name').innerHTML;
    

    if((selected_well_names != undefined) && (selected_well_names.length > 0))
        data['name']   = selected_well_names
  
    return data;

}
async function load_open_project_data(read_data){
    /*
    Get the hard-coded charts to show by default
    */
    try{

        let server_response = await get_server(
            'get_default_charts',
            'POST',
            JSON.stringify(read_data)
        );

        let data = server_response.data;

        populate_locations_plot(data);
        all_well_names_visible = data['all_names'];

        const chartDivs = [
            document.getElementById('chart-1'),
            document.getElementById('chart-2'),
            document.getElementById('chart-3'),
            document.getElementById('chart-4'),
            document.getElementById('sector-plot-wells'),

            document.getElementById('workflows-charts-container'),
            document.getElementById('results-charts-container')
        ];

        chartDivs.forEach((div) => {
            div.innerHTML = '';
            attach_chart_config_dialog(div.id);
        });

        PlotlyNewPlot(
            chartDivs[0],
            data['fractions']['data'],
            data['fractions']['layout'],
            {responsive: true}
        ).then((p)=>{});

        PlotlyNewPlot(
            chartDivs[1],
            data['historical_production']['data'],
            data['historical_production']['layout'],
            {responsive: true}
        ).then((p)=>{});

        PlotlyNewPlot(
            chartDivs[2],
            data['activity']['data'],
            data['activity']['layout'],
            {responsive: true}
        ).then((p)=>{});

        PlotlyNewPlot(
            chartDivs[3],
            data['sector_volumes']['data'],
            data['sector_volumes']['layout'],
            {responsive: true}
        ).then((p)=>{});

        let l = data['wells']['layout'];

        let p = PlotlyNewPlot(
            chartDivs[4],
            data['wells']['data'],
            l,
            {responsive: true}
        );

        p.then((p)=>{
            p.on('plotly_selected', function(eventData) {
                if (eventData) {
                    let local_selected_well_names = [];

                    for (let point of eventData.points) {
                        let index = point.pointIndex;
                        let well_name = point.data.text[index];
                        local_selected_well_names.push(well_name);
                    }

                    set_selected_well_names_in_scatter_chart(
                        local_selected_well_names
                    );
                }
                else{
                    console.log('No data selected');
                    set_selected_well_names_in_scatter_chart(undefined);
                }
            });
        });

    }
    catch (error){
        console.log(error);
    }
}

function ddddddddddddload_open_project_data(data) {
    populate_locations_plot(data);
    all_well_names_visible = data['all_names'];

    const chartDivs = [
        document.getElementById('chart-1'),
        document.getElementById('chart-2'),
        document.getElementById('chart-3'),
        document.getElementById('chart-4'),
        document.getElementById('sector-plot-wells'),
        document.getElementById('workflows-charts-container'),
        document.getElementById('results-charts-container')
    ];

    chartDivs.forEach((div) => {
        div.innerHTML = '';
        attach_chart_config_dialog(div.id);
    });

    PlotlyNewPlot(
        chartDivs[0],
        data['fractions']['data'],
        data['fractions']['layout'],
        { responsive: true }
    );

    PlotlyNewPlot(
        chartDivs[1],
        data['historical_production']['data'],
        data['historical_production']['layout'],
        { responsive: true }
    );

    PlotlyNewPlot(
        chartDivs[2],
        data['activity']['data'],
        data['activity']['layout'],
        { responsive: true }
    );

    PlotlyNewPlot(
        chartDivs[3],
        data['sector_volumes']['data'],
        data['sector_volumes']['layout'],
        { responsive: true }
    );

    const wellsPlot = PlotlyNewPlot(
        chartDivs[4],
        data['wells']['data'],
        data['wells']['layout'],
        { responsive: true }
    );

    wellsPlot.then((plot) => {
        plot.on('plotly_selected', function (eventData) {
            if (!eventData) {
                set_selected_well_names_in_scatter_chart(undefined);
                return;
            }

            const local_selected_well_names = eventData.points.map((point) => {
                return point.data.text[point.pointIndex];
            });

            set_selected_well_names_in_scatter_chart(local_selected_well_names);
        });
    });
}


 