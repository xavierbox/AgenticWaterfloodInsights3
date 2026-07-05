
const chart_title_font_size = 12;
let  chartTitleFontSize = chart_title_font_size;
const axisTitleFontSize = 10;
const tickFontSize = 9;
const hoverFontSize = 10;
const legendFontSize = 7;
const marker_text_size = 6;

let highlighted_marker_opacity = 0.8;
let highlighted_marker_color = 'orange';
let highlighted_marker_size = 18; 

let selected_well_names_in_scatter_chart = undefined;  //user selected wells in a wells chart 
let all_well_names_visible = undefined;                //all well names in the locations chart selected or not 
let locs_chart_initialized = false;                    //was the locs chart initialized 


//let locations_chart_pane = 'middle-top';

let isDark  = true; 
let currentTheme = "light";   // must be updated by selectTheme(...)

/* ---- Plotly layouts per theme ---- */
const plotlyLayouts = {

  "light": {
    paper_bgcolor: '#FFFFFF',
    plot_bgcolor: '#FFFFFF',
    font: { color: '#000000' },
    xaxis: { color: '#000000', gridcolor: '#DDDDDD', zerolinecolor: '#AAAAAA' },
    yaxis: { color: '#000000', gridcolor: '#DDDDDD', zerolinecolor: '#AAAAAA' },
    newselection: {
      line: { color: '#0000cc', width: 2 },
      fillcolor: 'rgba(0,0,255,0.08)'
    },
      /*legend: {
    font: { size: 9 }
        }*/
  },

  "dark": {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#FFFFFF' },
    xaxis: { color: '#FFFFFF', gridcolor: '#333333', zerolinecolor: '#666666' },
    yaxis: { color: '#FFFFFF', gridcolor: '#333333', zerolinecolor: '#666666' },
    newselection: {
      line: { color: '#00ffff', width: 2 },
      fillcolor: 'rgba(0,255,255,0.15)'
    },
            /*legend: {
    font: { size: 9 }
        }*/
      
  },

  "neon-dark": {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#e6ecff' },
    xaxis: { color: '#e6ecff', gridcolor: '#223366', zerolinecolor: '#3355aa' },
    yaxis: { color: '#e6ecff', gridcolor: '#223366', zerolinecolor: '#3355aa' },
            /*legend: {
    font: { size: 9 }
        }*/
  },
    
    "neon-light": {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { color: '#e6ecff' },

  xaxis: {
    color: '#e6ecff',
    gridcolor: 'rgba(120,160,255,0.35)',
    zerolinecolor: 'rgba(120,160,255,0.55)'
  },

  yaxis: {
    color: '#e6ecff',
    gridcolor: 'rgba(120,160,255,0.35)',
    zerolinecolor: 'rgba(120,160,255,0.55)'
  },

  newselection: {
    line: { color: '#00e5ff', width: 2 },
    fillcolor: 'rgba(0,229,255,0.12)'
  },
        /*legend: {
    font: { size: 9 }
        }*/
},

    

  "blue-light": {
    paper_bgcolor: '#eef3ff',
    plot_bgcolor: '#eef3ff',
    font: { color: '#081a45' },
    xaxis: { color: '#081a45', gridcolor: '#c9d9ff', zerolinecolor: '#aac4ff' },
    yaxis: { color: '#081a45', gridcolor: '#c9d9ff', zerolinecolor: '#aac4ff' },
          /*legend: {
    font: { size: 9 }
        }*/
  }
};


/* ---- APPLY THEME (signature preserved) ---- */
function applyPlotlyTheme(container, isDark) {

  //alert('applyPlotlyTheme here');

  const themeLayout = plotlyLayouts[currentTheme] ||
                      (isDark ? plotlyLayouts.dark : plotlyLayouts.light);

  try {
    const plotDivs = container.querySelectorAll('.js-plotly-plot');

    plotDivs.forEach(div => {
      const newLayout = getThemedLayout(div.layout, themeLayout);
      Plotly.relayout(div, newLayout);
    });

  } catch(e) {
    console.log('Error in applying theme', e);
  }
}


/* ---- layout merge ---- */
function getThemedLayout(layout, theme) {

//alert('Get themed layout here');
  return {
    ...layout,
    ...theme,
    xaxis: { ...layout?.xaxis, ...theme.xaxis },
    yaxis: { ...layout?.yaxis, ...theme.yaxis }
  };
}
            
            
function defaultPlotlyLayoutJS() {

  return {

    // --------------------------------------------------
    // GLOBAL
    // --------------------------------------------------

    autosize: true,

    paper_bgcolor: '#FFFFFF',
    plot_bgcolor: '#FFFFFF',

    font: {
      family: 'Inter, Segoe UI, sans-serif',
      size: 10,
      color: '#000000'
    },

    hoverlabel: {
      font: { size: 10 }
    },

    // --------------------------------------------------
    // TITLE
    // --------------------------------------------------

    title: {
      text: '',
      x: 0.5,
      xanchor: 'center',
      yanchor: 'top',
      font: {
        size: 11
      }
    },

    // --------------------------------------------------
    // LEGEND
    // --------------------------------------------------

    /*legend: {
      orientation: 'h',
      x: 0.01,
      y: 0.99,
      xanchor: 'left',
      yanchor: 'top',
      itemsizing: 'constant',
      font: {
        size: 9
      }
    },*/

    // --------------------------------------------------
    // MARGINS
    // --------------------------------------------------

    margin: {
      l: 45,
      r: 45,
      t: 50,
      b: 35
    },

    // --------------------------------------------------
    // X AXIS
    // --------------------------------------------------

    xaxis: {
      showgrid: true,
      zeroline: false,
      showline: true,

      tickfont: {
        size: 8
      },

      title: {
        text: '',
        standoff: 8,
        font: {
          size: 10
        }
      }
    },

    // --------------------------------------------------
    // Y AXIS
    // --------------------------------------------------

    yaxis: {
      showgrid: true,
      zeroline: false,
      showline: true,

      tickfont: {
        size: 8
      },

      title: {
        text: '',
        standoff: 8,
        font: {
          size: 10
        }
      }
    }

  };
}



/* ---- wrappers ---- */
function PlotlyNewPlot(id, data, layout, config){
  const l = getThemedLayout(layout, plotlyLayouts[currentTheme]);
  //const l = getThemedLayout(defaultPlotlyLayoutJS(), plotlyLayouts[currentTheme]);
  return Plotly.newPlot(id, data, l, config);
}

function PlotlyReact(id, data, layout, config){
  const l = getThemedLayout(layout, plotlyLayouts[currentTheme]);
  return Plotly.react(id, data, l, config);
}

function PlotlyRelayout(id, data, layout){
  const l = getThemedLayout(layout, plotlyLayouts[currentTheme]);
  return Plotly.relayout(id, data, l);
}
    
    