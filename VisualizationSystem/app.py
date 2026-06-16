from enum import Enum
import pprint, random, os, sys, traceback    
from flask import Flask, jsonify, render_template, request
from pydantic import BaseModel, Field, ValidationError
sys.path.append("./")
sys.path.append("../")
sys.path.append("../../")

from VisualizationSystem.visualization_backend.plotting.plot_models_catalog import * #PlotCatalogItem, get_historical_data_plot_catalog
from VisualizationSystem.visualization_backend.global_constants import *  
from VisualizationSystem.visualization_backend.global_models import UIState



def get_dummy_plotly_figure():
    # 1. Define your baseline historical production trends
    baseline_y = [120, 150, 140, 180, 210, 190]
    
    # 2. Generate a new array adding random noise (-20 to +20) to each month
    randomized_y = [val + random.randint(-20, 20) for val in baseline_y]
    
    # Ensure values don't accidentally drop below zero barrels per day
    randomized_y = [max(0, val) for val in randomized_y]

    dummy_plotly_figure = { 
        "data": [
            {
                "x": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "y": randomized_y,  # 👈 Fixed: Using the randomized array instead of a static one
                "type": "scatter",       
                "mode": "lines+markers", 
                "name": "Oil Production",
                "line": {
                    "color": "#001f9c",  
                    "width": 3
                },
                "marker": {
                    "color": "#cfe0ff",
                    "size": 8
                }
            }
        ],
        "layout": {
            "title": {
                "text": "Historical Well Production Profile",
                "font": {"color": "#ffffff"}
            },
            "paper_bgcolor": "rgba(0,0,0,0)", 
            "plot_bgcolor": "rgba(0,0,0,0)",  
            "xaxis": {
                "title": "Timeline",
                "gridcolor": "rgba(255,255,255,0.1)",
                "tickfont": {"color": "#ffffff"},
                "titlefont": {"color": "#ffffff"}
            },
            "yaxis": {
                "title": "Barrels per Day (BPD)",
                "gridcolor": "rgba(255,255,255,0.1)",
                "tickfont": {"color": "#ffffff"},
                "titlefont": {"color": "#ffffff"}
            },
            "margin": {"t": 50, "b": 50, "l": 50, "r": 50}
        }
    }

    return dummy_plotly_figure



app = Flask(__name__)



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
@app.post("/process_analyst_query")
def process_analyst_query():

    data = request.get_json()
       
 
    try:
        ui_state = UIState.model_validate( data )
        query    = ui_state.query
        print("[process_analyst_query]", query )
        print( ui_state )
        
        figure = get_dummy_plotly_figure()
        print("Returning a preview figure")
        return jsonify(figure), 200
    

    except ValidationError as e:

        return jsonify({
                    "status": "error",
                    "message": "Validation failed",
                    "details": e.errors() 
                }), 422


 


    return jsonify( {"all":"is good"} ) 


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

