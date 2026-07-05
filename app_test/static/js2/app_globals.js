


let selected_well_names = undefined;                   //user selected wells in a locations chart 

/*
window.get_server = function get_server(url, imethod, idata) {

  
        let iurl = getWebAppBackendUrl( url );

        return new Promise((resolve, reject) => {
            $.ajax({
                type: imethod,
                url: iurl,
                xhr: () => new window.XMLHttpRequest(),
                processData: false,
                contentType: 'application/json',
                data: idata,
                success: function (resp) {
                    resolve(resp);
                },
                error: async function (jqXHR, status, errorThrown) {
                    let errorMessage = 'Unknown error in the backend.';
                    const responseText = jqXHR.responseText;

                    // Try to extract JSON message from response
                    if (responseText) {
                        try {
                            const parsed = JSON.parse(responseText);
                            if (parsed && parsed.message) {
                                errorMessage = parsed.message;
                            } else {
                                errorMessage += `\nUnexpected JSON response:\n${responseText}`;
                            }
                        } catch (e) {
                            errorMessage += `\nNon-JSON response:\n${responseText}`;
                        }
                    } else {
                        errorMessage += `\nNo response from server.`;
                    }

                    // Append status info if available
                    errorMessage += `\nStatus: ${jqXHR.status || 'Unknown'}\nError: ${errorThrown || 'N/A'}`;
                    await Swal.fire({
                        title: "*Backend Error",
                        html: errorMessage.replace(/\n/g, "<br>"),
                        icon: "error"
                    });

                    reject(new Error(errorMessage));
                }
            });
        });
    }
*/

/*function selectTheme(themeName){
    currentTheme = themeName;
    document.documentElement.setAttribute("data-theme", themeName);
    applyPlotlyTheme(document, themeName.includes("dark"));
}*/

            
            


/*
const darkLayout = {
    paper_bgcolor:  'transparent', //#1e1e1e',
    plot_bgcolor: 'transparent',//'#1e1e1e',
    font: { color: '#FFFFFF' },
    xaxis: {
      color: '#FFFFFF',
      gridcolor: '#333333',
      zerolinecolor: '#666666'
    },
    yaxis: {
      color: '#FFFFFF',
      gridcolor: '#333333',
      zerolinecolor: '#666666'
    },
      newselection: {
    line: { color: '#00ffff', width: 2 },
    fillcolor: 'rgba(0, 255, 255, 0.15)'
  }
  };
const lightLayout = {
    paper_bgcolor: '#FFFFFF',
    plot_bgcolor: '#FFFFFF',
    font: { color: '#000000' },
    xaxis: {
      color: '#000000',
      gridcolor: '#DDDDDD',
      zerolinecolor: '#AAAAAA'
    },
    yaxis: {
      color: '#000000',
      gridcolor: '#DDDDDD',
      zerolinecolor: '#AAAAAA'
    },
  newselection: {
    line: { color: '#0000cc', width: 2 },
    fillcolor: 'rgba(0, 0, 255, 0.08)'
  }
  };


function applyPlotlyTheme(container, isDark) {
  const layoutUpdate = isDark ? darkLayout : lightLayout;

  try {
    const plotDivs = container.querySelectorAll('.js-plotly-plot');
    plotDivs.forEach(div => {
      // merge current layout with the theme overrides
      const newLayout = getThemedLayout(div.layout, isDark);
      Plotly.relayout(div, newLayout);
    });
  } catch(e) {
    console.log('Error in applying theme', e);
  }
}



function getThemedLayout(layout, isDark) {
  const theme = isDark ? darkLayout : lightLayout;
  //return layout;
  // Merge theme into layout (theme takes precedence)
  const newLayout = {
    ...layout,
    ...theme,
    xaxis: {
      ...layout.xaxis,
      ...theme.xaxis
    },
    yaxis: {
      ...layout.yaxis,
      ...theme.yaxis
    }
  };

  return newLayout;
}


function PlotlyNewPlot(id, data, layout, config ){
            
        let l = getThemedLayout(layout, isDark);
        return Plotly.newPlot(id, data, l, config);
}
function PlotlyReact(id, data, layout, config ){
            
            let l = getThemedLayout(layout, isDark);
            return Plotly.react(id, data, l, config);
    }
function PlotlyRelayout(id, data, layout ){
            
            let l = getThemedLayout(layout, isDark);
            return Plotly.relayout(id, data, l);
    }
*/



function isEmptyOrWhitespace(str) {
    return str.trim() === "";
}

function isValidDate(date1) {
    const date = new Date(date1);
    return !isNaN(date.getTime()); // Checks if it's a valid date
}

function addMonthsToDate(dateStr, step) {
    let [year, month, day] = dateStr.split('-').map(Number);
    month -= 1; // Convert to 0-based month

    // Add step months manually
    step = Number(step);
    let totalMonths = month + step;
    let newYear = year + Math.floor(totalMonths / 12);
    let newMonth = totalMonths % 12;
    if (newMonth < 0) {
        newMonth += 12;
        newYear -= 1;
    }

    // Get last day of the new month
    let lastDay = new Date(newYear, newMonth + 1, 0).getDate();
    let newDay = Math.min(day, lastDay);

    let resultDate = new Date(newYear, newMonth, newDay);
    return resultDate.toISOString().split('T')[0];
}

function moveDates(direction = 1){
    let [date1,date2,step] = [ Id('start-date').value,Id('end-date').value, Id('range-value').value];

    step = Number(step) * direction;
    date1 = addMonthsToDate(date1, step)
    date2 = addMonthsToDate(date2, step)
    console.log( date1,date2,step )

    Id('start-date').value  = date1;
    Id('end-date').value    = date2;

}

function valueToColor1(value) {
    // Clamp between 0 and 1
    const v = Math.max(0.05, Math.min(0.95, value));

    // Blue = (0, 0, 255), Red = (255, 0, 0)
    const r = Math.round(255 * v);
    const g = 0;
    const b = Math.round(255 * (1 - v));

    return `rgb(${r},${g},${b})`;
}

function valueToColor(value) {
    // Clamp value between 0 and 1
    const v = Math.max(0.05, Math.min(0.95, value));

    let r, g, b;

    if (v < 0.5) {
        // Blue (0,0,255) → Orange (255,165,0)
        const t = v / 0.5; // Normalize to 0–1
        r = Math.round(255 * t);
        g = Math.round(165 * t);
        b = Math.round(255 * (1 - t));
    } else {
        // Orange (255,165,0) → Red (255,0,0)
        const t = (v - 0.5) / 0.5; // Normalize to 0–1
        r = 255;
        g = Math.round(165 * (1 - t));
        b = 0;
    }

    return `rgb(${r},${g},${b})`;
}


