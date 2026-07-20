from enum import Enum
import pprint, random, os, sys, traceback    
from flask import Flask, jsonify, render_template, request
from pydantic import BaseModel, Field, ValidationError
import pickle

sys.path.append("./")
sys.path.append("../")
sys.path.append("../../")

from visualization_backend.plotting.plot_models_catalog import * #PlotCatalogItem, get_historical_data_plot_catalog
from visualization_backend.global_constants import *  
from visualization_backend.global_models import UIState

from temporal_and_aux import * 
from visualization_system.visualization_backend.all_classes import * 

app = Flask(__name__)

# these are just mocks 
def get_config():
    return None 

cleaned = lambda x: "\n".join(" ".join(line.lstrip().split()) for line in x.splitlines()).strip()


class DataDrivenStorage:
        
    def __init__( self, config_vars ):
        pass 

    def get_project_dataset(self, project_name=None, filters=None):
        #path =  "../datasets/Demo1/"
        #path =  Path("../datasets/IX5I_4P/") 
        path = Path("C:\\Work\\2026\\KOC_phase2\\AgenticWaterfloodInsights3\\datasets\\IX5I_4P\\")

        inj, prod, locs = self.fetch_data(path) 
        return inj, prod, locs

    def fetch_data(self,path:Path):
        inj  = pd.read_csv(path / "injectors.csv")
        pinj = pd.read_csv(path / "producers.csv")
        locs = pd.read_csv(path / "locations.csv")
        inj['DATE'] = pd.to_datetime( inj['DATE'],dayfirst=True)
        inj['DAY']   = inj['DATE'].dt.day
        inj['MONTH'] = inj['DATE'].dt.month
        inj['YEAR']  = inj['DATE'].dt.year
        pinj['DATE'] = pd.to_datetime( pinj['DATE'],dayfirst=True)
        pinj['DAY']   = pinj['DATE'].dt.day
        pinj['MONTH'] = pinj['DATE'].dt.month
        pinj['YEAR']  = pinj['DATE'].dt.year


        print( inj.shape, pinj.shape, locs.shape)
        return inj, pinj, locs

def initialize_system( llm ):
   

    #IMPORTS
    from visualization_system.visualization_backend.analyst.semantics.semantic_models import SemanticCatalog, semantic_catalog
    from visualization_system.visualization_backend.analyst.semantics.semantic_models import idioms as all_idiom_rules
    vis_system = AgenticSystem( llm )


    idiom = 'duckdb'
    idiom_rules = all_idiom_rules[idiom]
    semantic_catalog_model = SemanticCatalog.model_validate( semantic_catalog )

    analyst = vis_system.data_analyst_component
    analyst.init_semantic_models( semantic_catalog_model,idiom_rules)
    



    return vis_system


llm = azure_llm_if()
vis_system = initialize_system(llm)


# data changes
# this mocks data comming from the UI
# so we just update tge analyst 
inj,prod,locs = DataDrivenStorage( get_config() ).get_project_dataset(123, {}) 

ui_state = None 
vis_system.data_analyst_component.set_data( {'injectors':inj, 
                                             'producers':prod, 
                                             'locations': locs } )



def check_needs_refreshing( new_ui_state, last_ui_state ):

    needs_data_refreshing, needs_simuation_data_refreshing = False, False 

    if last_ui_state.project_changed( new_ui_state ):
        needs_data_refreshing, needs_simuation_data_refreshing = True, True 

    if last_ui_state.data_filters_changed( new_ui_state ):
        needs_data_refreshing = True 

    if last_ui_state.selected_study != new_ui_state.selected_study:
        needs_simuation_data_refreshing = True 

    return needs_data_refreshing, needs_simuation_data_refreshing
     
def refresh_vis_data_if_needed(vis_system, new_ui_state):

    last_ui_state = vis_system.last_query
    (needs_data_refreshing,needs_simuation_data_refreshing) = check_needs_refreshing(new_ui_state,last_ui_state)
 

    if not any( [needs_data_refreshing,needs_simuation_data_refreshing]):
        print("dont need to refreh data at all")

    else:
        if needs_data_refreshing:
            print("We need to reload the dataset")

        if needs_simuation_data_refreshing:
            print("We need to reload the simulation data")

        refresh_vis_system_data(vis_system, 
                                new_ui_state, 
                                needs_data_refreshing, 
                                needs_simuation_data_refreshing )
    
def refresh_vis_system_data( vis_system, new_ui_state, data_refresh_needed, sim_refresh_needed ):
    print("[refresh_vis_system_data]") 
    pprint.pprint(new_ui_state.model_dump() )

    if data_refresh_needed:
        project_name = new_ui_state.project_name

        # the storate was developed a while ago and the naming for filters is different
        filters = {
            'project_name': new_ui_state.project_name,
            'date': new_ui_state.selected_dates,
            'name': new_ui_state.selected_wells,
            'subzone': new_ui_state.selected_subzone,
            'sectors': new_ui_state.selected_sectors
        }
        print('filters are ', filters )

        # reload the dataset 
        # update the tables (only) of the vis_system smart_data
        inj, prod, locs = DataDrivenStorage( get_config() ).get_project_dataset(filters['project_name'], filters) 

        #print(inj)
        #print(prod)
        #print(locs)
        
        
        
        
        injectors = inj# crm_dataset.injectors_df
        producers = prod#crm_dataset.producers_df
        locations = locs#crm_dataset.locations_df
        #display( locations.sample(4) )
        
        vis_system.data_analyst_component.set_data( {'injectors':injectors, 
                                             'producers':producers, 
                                             'locations': locations } )

        
        #display( crm_dataset.injectors_df.head(5))
        #display( crm_dataset.producers_df.head(5))
        #display( crm_dataset.locations_df.head(5))
     

# this is waht must come from the UI. We need the project name and the query
# if any of those isnt there, then retrurn an error message 
# also need the selected_subzone 
# {
#    "project_name": "IX5I_4P",
#    "selected_wells": null,       or ['name1','name2',....] 
#    "selected_subzone": "WARA1",   
#    "selected_sectors": null,     or [1,2,3] 
#    "selected_study": null,       or "the_name"
#    "query": "h"
#}


def update_ui_state_request( data ):
    global vis_system 
    new_ui_state = UIState.model_validate( data )
    refresh_vis_data_if_needed(vis_system, new_ui_state)

    return new_ui_state

@app.post("/process_analyst_query")
def process_analyst_query():

    global llm, vis_system 
    data = request.get_json()
   
    try:
        last_ui_state = vis_system.last_query 
        new_ui_state  = update_ui_state_request( data )
        query = new_ui_state.query

        #figure = get_dummy_plotly_figure()
        #print("Returning a preview figure")
        #return jsonify(figure), 200

        '''
        query = """Explain VRR briefly and then 
        plot the yearly liquid production of the 5 top producers based on the cummulated 
        oil production in 2018, then show the cummulated liquid production since year 2015 for 
        the first two of those wells.  
        """

        #this is what the presenter consumes 
        print('running the system...')
        execution_state = vis_system.run( query )
        print("system ran",flush=True)

        print( execution_state )

        print("running the presenter...")
        presenter = PresenterComponent4(llm)
        ui_items = presenter.run( execution_state )
        print(ui_items)
        print("presenter ran",flush=True)
        '''

        
        #with open("ui_items.pkl", "wb") as file:
        #    pickle.dump(ui_items, file)
        with open("ui_items.pkl", "rb") as file:
            loaded_data = pickle.load(file)


        ui_items = loaded_data.items
        #print( ui_items )
        json_safe_items = [item.model_dump(mode="json") for item in ui_items]
        return jsonify({'data': json_safe_items})


        


    except ValidationError as e:

        return jsonify({
                    "status": "error",
                    "message": "Validation failed",
                    "details": e.errors() 
                }), 422

    except Exception as e:
        return jsonify({
                    "status": "error",
                    "message": "Error in the backend",
                    "details": str(e) 
                }), 500
 


    return jsonify( {"all":query} ) 





crm_dataset = "I am the crm dataset"
crm_simulation_results = "I am the crm simulation results"
data = { 'crm_dataset': crm_dataset, 'crm_simulation_results': crm_simulation_results }


@app.get("/")
def index():
    #return render_template("catalog1.html")
    #return render_template("index.html")
    return render_template("test_tabs_control.html")#//("index.html")

@app.get("/fetch_known_plots_catalog")
def fetch_known_plots_catalog():
    catalog = get_historical_data_plot_catalog()
    print(catalog)
    return jsonify(catalog.model_dump(mode="json"))



@app.post("/generate_dashboard_plots")
def generate_dashboard_plots():
    payload = request.get_json()

    items = [PlotCatalogItem.model_validate(item) for item in payload]
    if not items:
        return jsonify({"ok": False, "message": "No items provided"}), 400

    for item in items:
        pprint.pprint(item.model_dump(mode="json"))


    print( type(items[0]) )

    generate_plots(data, items)



    return jsonify({
        "ok": True,
        "count": len(items),
    })



    #catalog = get_historical_data_plot_catalog()
    #return jsonify(catalog.model_dump(mode="json"))


@app.route("/process_catalog_preview_request", methods=["POST"])
def process_catalog_preview_request():
      
    data = request.get_json()
    print("[process_catalog_preview_request]", data)

    try:
        figure = get_dummy_plotly_figure()
        print("Returning a preview figure")
        return jsonify(figure), 200
        
    except Exception as e:
        print(f"[Backend Error] Plotly rendering failed: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "status": "error", 
            "message": f"Internal Server Error: Failed to generate preview chart configuration ({str(e)})."
        }), 500





if __name__ == "__main__":
    app.run(debug=True, port =5050)

