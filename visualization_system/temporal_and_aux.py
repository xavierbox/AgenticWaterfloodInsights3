

import random


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


