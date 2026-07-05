/*
const GlobalState = {
  themes: ["blue-light", "light", "dark", "neon-light", "neon-dark"],
  currentTheme: "neon-dark"
};


function selectTheme(themeName){
               
    document.documentElement.setAttribute("data-theme", themeName);
    if (typeof currentTheme !== "undefined"){
                    currentTheme = themeName;
    }
    if (typeof applyPlotlyTheme === "function"){
                    const isDark = themeName.includes("dark");
                    applyPlotlyTheme(document, isDark);
    }
    console.log("Theme selected:", themeName);
}
*/
// Global State Definition
const GlobalState = {
  themes: ["blue-light", "light", "dark", "neon-light", "neon-dark"],
  currentTheme: "neon-dark"
};

// Expose selectTheme globally to the window object
function selectTheme(themeName) {
    if (!GlobalState.themes.includes(themeName)) {
        console.warn(`Theme "${themeName}" is not a recognized option.`);
    }

    // Apply attribute to root element
    document.documentElement.setAttribute("data-theme", themeName);
    
    // Synchronize state tracking object
    GlobalState.currentTheme = themeName;
    
    // Legacy support fallback compatibility check
    if (typeof currentTheme !== "undefined") {
        currentTheme = themeName;
    }
    
    // Execute Plotly external framework rendering updates
    if (typeof applyPlotlyTheme === "function") {
        const isDark = themeName.includes("dark");
        applyPlotlyTheme(document, isDark);
    }
    
    const selector = document.getElementById("themeSelector");
        if (selector) {selector.value = themeName;}
        
    console.log("Global State Theme set to:", GlobalState.currentTheme);
};

// Initialize the default theme on load
/*document.addEventListener("DOMContentLoaded", () => {
    window.selectTheme(GlobalState.currentTheme);
    
    // Sync UI selector state if element exists on page
    const selector = document.getElementById("themeSelector");
    if (selector) {
        selector.value = GlobalState.currentTheme;
    }
});*/

