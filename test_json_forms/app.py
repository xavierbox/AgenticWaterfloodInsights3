from enum import Enum
import pprint
from flask import Flask, jsonify, render_template
from pydantic import BaseModel, Field



app = Flask(__name__)


class Mode(str, Enum):
    fast = "fast"
    accurate = "accurate"


class NestedParams(BaseModel):
    enabled: bool = True
    threshold: float = 0.75
    label: str = "nested label"


class DummyConfig(BaseModel):
    text_value: str = "hello"
    int_value: int = Field(10, ge=0, le=100)
    float_value: float = Field(3.14, ge=0.0, le=10.0)
    bool_value: bool = True
    enum_value: Mode = Mode.fast
    string_list: list[str] = ["A", "B"]
    nested: NestedParams = NestedParams()

#from VisualizationSystem.visualization_backend.plot_models_catalog import generate_plots
#from VisualizationSystem.visualization_backend.plot_models_catalog import generate_plots
from  plot_models_catalog import * #PlotCatalogItem, get_historical_data_plot_catalog
 

crm_dataset = "I am the crm dataset"
crm_simulation_results = "I am the crm simulation results"
data = { 'crm_dataset': crm_dataset, 'crm_simulation_results': crm_simulation_results }


@app.get("/")
def index():
    #return render_template("catalog1.html")
    return render_template("catalog5.html")



@app.get("/fetch_known_plots_catalog")
def fetch_known_plots_catalog():
    catalog = get_historical_data_plot_catalog()
    return jsonify(catalog.model_dump(mode="json"))

from flask import request, jsonify

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



@app.get("/api/dummy-config")
def dummy_config():
    obj = DummyConfig()

    return jsonify({
        "schema": DummyConfig.model_json_schema(),
        "data": obj.model_dump(mode="json"),
    })


if __name__ == "__main__":
    app.run(debug=True)
