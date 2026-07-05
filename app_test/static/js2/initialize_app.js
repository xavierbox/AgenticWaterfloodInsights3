    /*
    This file is associated with initializing the app, loading the projects
    list, displaying it. The user can also select a project and open it. 
    Opening a project just populates the description (data, RMUS) in the UI.
    No data is fetched yet other than the project_description.
    */

    function get_and_display_list_of_projects(){
    /*
        iurl = 'get_list_of_projects';
        toggleLoading(true, 'Fetching projects list'); 
        get_server(iurl, 'GET' )
            .then( (resp) =>{

                let projects_description = resp.data['projects_description'];
                
                //let project_list = Id('project-list-component');
                //project_list.setProjects(projects_description);// = projects;            
            
                let project_list = document.querySelector('projects-container-component');
                return project_list.setProjects(projects_description);// = projects;
            
                //display_projects_page(true);
                //toggleLoading(false); 
            })
            .then( ()=>{
                display_projects_page(true);
                toggleLoading(false); 
            } )
             .catch ((error) =>{
              toggleLoading(false); 
                console.log(error);
                Swal.fire({title: "No projects found",html: error.message,icon: "error"});
            });
      */      
    }

    function display_projects_page( value ){
        
        let projects_page = document.querySelector('projects-container-component');//Id('projects-component-container');

        
        if(projects_page.classList.contains('hidden')){
            projects_page.classList.remove('hidden')
            document.getElementById('all-app-wrapper').classList.add('hidden');
            document.getElementById('projects-list-button').innerText = 'Projects';
            //Id("projects-toggle-icon1").remove('hidden')
            //Id("projects-toggle-icon2").add('hidden')
        }
        
        else{ 
            //Id("projects-toggle-icon1").add('hidden')
            //Id("projects-toggle-icon2").remove('hidden')
            document.getElementById('projects-list-button').innerText = '⬅️ Projects';
            projects_page.classList.add('hidden');
            document.getElementById('all-app-wrapper').classList.remove('hidden');

        }
        //if(value == false){
        //    Id('all-app-wrapper').classList.remove('hidden');
            
            
        //}
     
        return;
        
        
        
        /*
        if(value == true){
            //Id('projects-component-container').classList.remove('hidden');
            document.querySelector('projects-container-component').classList.remove('hidden');
            Id('all-app-wrapper').classList.add('hidden');
        }
        else{
            //Id('projects-component-container').classList.add('hidden');
            document.querySelector('projects-container-component').classList.add('hidden');
            Id('all-app-wrapper').classList.remove('hidden');
        }*/
    }

    function initMapContainer(){
        let middleTabs = document.getElementById('middle-tabs');
        let layout = document.getElementById('main-layout');

        layout.set('middle', middleTabs );

        // Font Awesome icon node
        const mapIcon = document.createElement("i");
        mapIcon.className = "fa-solid fa-map";
        mapIcon.style.setProperty("margin-right", "10px");

        middleTabs.addTab("Map", mapIcon);
        middleTabs.disableClose("Map");
        middleTabs.addTab("Dashboard");
        
        layout.set('middle',middleTabs);
    }
    function getMapContainer(){
        let middleTabs = document.getElementById('middle-tabs');
        return middleTabs.getTabPage("Map");
    }

    function build_app_layout() {
        
        debugger;




        let layout = document.getElementById('main-layout');

        let x1 = Id('side-bar-top');
        let x2 = Id('side-bar-bottom');
        let x3 = Id('top-right-pagination');
        let x4 = Id('data-tab1');
        let x5 = Id('field-tab-button');
        let x6 = Id('flash');


        layout.set('left-top',Id('side-bar-top'));
        layout.set('left-bottom',Id('side-bar-bottom'));
        layout.set('right-top',Id('top-right-pagination'));
        document.getElementById('data-tab1').click()
        document.getElementById('field-tab-button').click()
        //layout.append( 'left-top', Id('flash'));

        initMapContainer();
        
        const workflows = [
            '💧 Liquid history match', 
            '🤖 Dynamic dashboards',   
            '⚖️ Static pattern flow balancing',
            '🧬 Genetic optimization'
        ]
        document.getElementById('workflow-selector').set_data(workflows);
    } 

    function init_theme_selector() {
        /*Load theme names directly from css*/
    const selector = document.getElementById("themeSelector");
    const themes = Array.from(document.styleSheets)
        .flatMap(sheet => { try { return Array.from(sheet.cssRules); } catch { return []; } })
        .filter(rule => rule.selectorText && rule.selectorText.startsWith(':root[data-theme='))
        .map(rule => rule.selectorText.match(/"([^"]+)"/)[1]);

      selector.innerHTML = [...new Set(themes)].filter(Boolean).map(t => {
        const text = t.split('-')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
        return `<option value="${t}">${text}</option>`;
    }).join(''); 
                          
    selector.addEventListener("change", function(event) {
        const selectedValue = event.target.value;
        selectTheme(selectedValue); 
    });
          
    }

    function init_splash_screen(){
        
        return; 

 
    
/*spash scrteen and navbar*/
    document.querySelector(".splash-launch").classList.remove('hidden');
    document.querySelector(".projects-component-container").classList.add('hidden');
    document.querySelector(".navbar").classList.add('hidden');
    document.querySelector("#all-app-wrapper").classList.add('hidden');

    document.querySelector(".splash-launch").addEventListener("click", (event) => {
        event.stopPropagation();
        document.querySelector(".splash-wrapper").classList.add('hidden');
        //document.querySelector(".projects-component-container").classList.remove('hidden');
        document.querySelector(".navbar").classList.remove('hidden');
        //document.querySelector(".projects-component-container").classList.toggle('hidden');
        
    });
    
    // 1. Select the main wrapper div
    const splashWrapper = document.querySelector(".splash-wrapper"); 

    // 2. Safety check: Exit if the splash wrapper is not found (avoids console errors)
    if (!splashWrapper) return;

    // 3. Construct the dynamic path to your resource file
    // Assumes dataiku.defaultProjectKey is already defined in your environment
    // Ensure the filename splash_background4.png is correct.
    const imagePath = `/local/projects/${dataiku.defaultProjectKey}/resources/splash_background3.png`;

    // 4. Set the background-image style directly on the element
    splashWrapper.style.backgroundImage = `url('${imagePath}')`;
    
    // Debug: Add this line to verify the path in your browser console
    console.log("Setting splash background to:", splashWrapper.style.backgroundImage);
    
    
            
    }

    function load_empty_app(){
        
 
        debugger;
        build_app_layout();

        init_theme_selector(); 
        selectTheme(GlobalState.currentTheme);

        
        //get_and_display_list_of_projects();
        //init_splash_screen();

    }
  
             
             
             
function populate_project_description(data) {
    // Helper function to update sectors based on the selected subzone
    function update_sectors(subzone_selected) {
        const reservoir = Object.keys(data['reservoirs'])[0];
        const sectors = data['reservoirs'][reservoir][subzone_selected] || [];
        Id('sector-selector').set_data(sectors);
    }

    function rmu_selection_changed(evt) {
        const subzone_selected = Id('reservoir-unit-selector').getValue();
        update_sectors(subzone_selected);
    }

    // Pick the first reservoir regardless of how many there are
    const reservoir = Object.keys(data['reservoirs'])[0];
    const subzone_names = Object.keys(data['reservoirs'][reservoir]);
    
    const unitSelector = Id('reservoir-unit-selector');
    unitSelector.setData(subzone_names);
    unitSelector.dataset.info = JSON.stringify(data);

    // Manage event listeners safely
    unitSelector.removeEventListener('change', rmu_selection_changed);
    unitSelector.addEventListener('change', rmu_selection_changed);



    // Populate the remaining metadata fields
    document.getElementById('end-date').value = new Date(data['dates'][1]).toISOString().slice(0, 10);
    document.getElementById('start-date').value = new Date(data['dates'][0]).toISOString().slice(0, 10);
    
    document.getElementById('study-selector').set_data(data['studies']);
    document.getElementById('project_name').innerHTML = data['project_name'];
             
             
    // Handle the single item edge case explicitly
    if (subzone_names.length === 1) {
        const singleSubzone = subzone_names[0];
        
        // Programmatically assign the value if your component supports setValue()
        if (typeof unitSelector.setValue === 'function') {
            unitSelector.setValue(singleSubzone);
        } else {
            unitSelector.value = singleSubzone;
        }
        
        // Programmatically trigger the sector update logic immediately
        update_sectors(singleSubzone);
             
             toggleLoading(true);
        Id("apply-data-selection-button").click();
             toggleLoading(false);
             
    }
    
             
             
}
   
             
             
             
             
    function old_populate_project_description( data ){
        function rmu_selection_changed(evt){
                let subzone_selected =Id('reservoir-unit-selector').getValue();
                let data = JSON.parse( Id('reservoir-unit-selector').dataset.info );
                let reservoir = Object.keys(data['reservoirs'])[0];
                let sectors = data['reservoirs'][reservoir][subzone_selected];
                Id('sector-selector').set_data( sectors );
        }
        //pick the first reservoir regardless of how many there are.
        let reservoir = Object.keys(data['reservoirs'])[0];
        let subzone_names = Object.keys(data['reservoirs'][reservoir]);
        Id('reservoir-unit-selector').setData( subzone_names);
        Id('reservoir-unit-selector').dataset.info = JSON.stringify(data);
    
        Id('reservoir-unit-selector').removeEventListener('change', rmu_selection_changed );
        Id('reservoir-unit-selector').addEventListener('change', rmu_selection_changed );
    
        Id('end-date').value = new Date(data['dates'][1]).toISOString().slice(0, 10);
        Id('start-date').value = new Date(data['dates'][0]).toISOString().slice(0, 10);
        
        let study_selector = Id('study-selector');
        //console.log( study_selector )
        Id('study-selector').set_data(data['studies']);
        //Id('workflow-selector').set_data(data['workflows']);     
        
        Id('project_name').innerHTML = data['project_name'];
    
    }

    function nom_awaitable_open_project( project_name ) {
        
        let iurl = 'get_project_description'
        let layout = document.getElementById('main-layout');

        let message = JSON.stringify( {project_name:project_name} )
        toggleLoading(true);
        get_server(iurl, 'POST', message )
        .then( (resp) =>{
            console.log('get_project_description returned', resp);
            project_description = resp.data;
            selected_well_names= undefined;

            populate_project_description(project_description);
            display_projects_page(false);

            if(locs_chart_initialized == true){
            let chart_keys = ['fractions','historical_production', 'activity'];
            console.log('clearing all charts!!!')
            const chartDivs = [
                document.getElementById('chart-1'),
                document.getElementById('chart-2'),
                document.getElementById('chart-3'),
                document.getElementById('chart-4'),
                document.getElementById('sector-plot-wells'),

                document.getElementById('workflows-charts-container'),
                document.getElementById('results-charts-container')
                ];

                chartDivs[0].innerHTML='';
                chartDivs[1].innerHTML='';
                chartDivs[2].innerHTML='';
                chartDivs[3].innerHTML='';

                //layout.clear('middle');
                //locs_container.data = [] 
                let locs_container = layout.get_pane('middle');//Id('locs-chart');
                Plotly.newPlot(locs_container, [], locs_container.layout);
                //Plotly.replaceAllTraces(locs_container, [] );
                locs_chart_initialized = false;
                
            /*PlotlyNewPlot(chartDivs[0], [] );
            PlotlyNewPlot(chartDivs[1], [] );
            PlotlyNewPlot(chartDivs[2], [] );
            PlotlyNewPlot(chartDivs[3], [] );*/
        }
            


            document.getElementById('field-tab-button').click()
            document.getElementById('data-tab1').click();
            toggleLoading(false);

            })
        .catch ((error) =>{
            console.log(error);
            Swal.fire({title: "Failed to get the project description",html: error.message,icon: "error"});
            toggleLoading(false);
            });
    }

    function open_project(projectName, projectDescription) {
        
        const layout = document.getElementById('main-layout');
        selected_well_names = undefined;

        populate_project_description(projectDescription);
        display_projects_page(false);

        if (!locs_chart_initialized) {
            return;
        }

        const chartDivs = [
            document.getElementById('chart-1'),
            document.getElementById('chart-2'),
            document.getElementById('chart-3'),
            document.getElementById('chart-4')
        ];

        chartDivs.forEach(div => {
            div.innerHTML = '';
        });

        const locs_container = layout.get_pane('middle');
        Plotly.newPlot(locs_container, [], locs_container.layout);

        locs_chart_initialized = false;
    }




    async function old_open_project( project_name ) {
        
      let iurl = 'get_project_description'
      let message = JSON.stringify( {project_name:project_name} )
      let layout = document.getElementById('main-layout');


      try{ 
        let resp = await get_server(iurl, 'POST', message )
        
        console.log('get_project_description returned', resp);
        let the_project_description = resp.data;
        selected_well_names= undefined;

        populate_project_description(the_project_description);
        display_projects_page(false);

        if(locs_chart_initialized == true){
            let chart_keys = ['fractions','historical_production', 'activity'];
            console.log('clearing all charts!!!')
            const chartDivs = [
                document.getElementById('chart-1'),
                document.getElementById('chart-2'),
                document.getElementById('chart-3'),
                document.getElementById('chart-4'),
                document.getElementById('sector-plot-wells'),

                document.getElementById('workflows-charts-container'),
                document.getElementById('results-charts-container')
                ];

                chartDivs[0].innerHTML='';
                chartDivs[1].innerHTML='';
                chartDivs[2].innerHTML='';
                chartDivs[3].innerHTML='';

                //layout.clear('middle');
                //locs_container.data = [] 
                let locs_container = layout.get_pane('middle');//Id('locs-chart');
                Plotly.newPlot(locs_container, [], locs_container.layout);
                //Plotly.replaceAllTraces(locs_container, [] );
                locs_chart_initialized = false;
                
            /*PlotlyNewPlot(chartDivs[0], [] );
            PlotlyNewPlot(chartDivs[1], [] );
            PlotlyNewPlot(chartDivs[2], [] );
            PlotlyNewPlot(chartDivs[3], [] );*/
        }
      }
      catch (error) {
        console.log(error);
        Swal.fire({title: "Failed to get the project description",html: error.message,icon: "error"});
      }   
 
  }




    function openWellDetailDialog(wellName, chartData, tableData) {
        const dialog = document.getElementById("dell-detail-dialog");
        dialog.style.display = "flex";
    
        document.getElementById("dell-detail-dialog-header").textContent = wellName;
    
        PlotlyNewPlot("dell-detail-dialog-chart", chartData, {
          margin: { t: 20 },
          responsive: true
        });
    
        const tbody = document.getElementById("dell-detail-dialog-table-body");
        tbody.innerHTML = "";
        tableData.forEach(row => {
          const tr = document.createElement("tr");
          tr.innerHTML = `<td>${row.well}</td><td>${row.distance}</td><td>${row.type}</td>`;
          tbody.appendChild(tr);
        });
      }

    
      function closeWellDetailDialog() {
        document.getElementById("dell-detail-dialog").style.display = "none";
      }
    
      function init_floating_well_dialog() {
        const dialog = document.getElementById("dell-detail-dialog");
        let offsetX = 0, offsetY = 0, isDragging = false;
      
        dialog.addEventListener('mousedown', (e) => {
          // Exclude certain elements from triggering drag
          if (e.target.closest('button, input, textarea, select, .plotly')) return;
      
          isDragging = true;
          offsetX = e.clientX - dialog.offsetLeft;
          offsetY = e.clientY - dialog.offsetTop;
          document.body.style.userSelect = 'none';
        });
      
        document.addEventListener('mousemove', (e) => {
          if (isDragging) {
            const newX = e.clientX - offsetX;
            const newY = Math.max(45, e.clientY - offsetY); // clamp to 80px minimum from top
            dialog.style.left = `${newX}px`;
            dialog.style.top = `${newY}px`;
          }
        });
      
        document.addEventListener('mouseup', () => {
          isDragging = false;
          document.body.style.userSelect = '';
        });
      }
      