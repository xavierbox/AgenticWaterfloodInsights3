from flask import Flask, render_template
from enum import Enum
import pprint
from flask import Flask, jsonify, render_template
from pydantic import BaseModel, Field

import sys,os 

sys.path.append(".//")
sys.path.append("..//")
sys.path.append("..//..//")



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
from  app_test.visualization_system.visualization_backend.plots_catalog.plot_models_catalog import *  #.plot_models_catalog import * #PlotCatalogItem, get_historical_data_plot_catalog
 

@app.route("/")
def index():
    return render_template("index.html")


@app.get("/fetch_known_plots_catalog")
def fetch_known_plots_catalog():

    print('[fetch_known_plots_catalog] called')


    catalog = get_historical_data_plot_catalog()
    print(catalog)
    return jsonify(catalog.model_dump(mode="json"))



if __name__ == "__main__":
    app.run(debug=True)

    