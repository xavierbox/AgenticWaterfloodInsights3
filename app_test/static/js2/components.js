
   class TabsComponent extends HTMLElement {
      constructor() {
        super();

        this.tabs = [];
        this.activeIndex = -1;

        this.buttonsContainer = null;
        this.pagesContainer = null;

        this._onButtonClick = this._onButtonClick.bind(this);
      }

      connectedCallback() {
        if (!this.buttonsContainer || !this.pagesContainer) {
          this.innerHTML = `
            <div class="tabs-component">
              <div class="tabs-buttons"></div>
              <div class="tabs-pages"></div>
            </div>
          `;

          this.buttonsContainer = this.querySelector(".tabs-buttons");
          this.pagesContainer = this.querySelector(".tabs-pages");
        }

        this.buttonsContainer.removeEventListener("click", this._onButtonClick);
        this.buttonsContainer.addEventListener("click", this._onButtonClick);
      }

      disconnectedCallback() {
        this.buttonsContainer?.removeEventListener("click", this._onButtonClick);
      }

      attributeChangedCallback(name, oldValue, newValue) {}

      _onButtonClick(event) {
        const closeButton = event.target.closest(".tabs-button-close");
        const button = event.target.closest(".tabs-button");

        if (!button || !this.buttonsContainer.contains(button)) return;

        const index = Array.from(this.buttonsContainer.children).indexOf(button);
        if (index === -1) return;

        if (closeButton) {
          this.deleteTab(index);
          return;
        }

        this.setActiveTab(index);

        const tab = this.tabs[index];

        this.dispatchEvent(new CustomEvent("tab-selected", {
          detail: {
            name: tab.name,
            index: index
          },
          bubbles: true,
          composed: true
        }));
      }

      _setButtonContent(button, name, icon = null) {
        button.replaceChildren();

        if (icon !== null && icon !== undefined) {
          const iconSpan = document.createElement("span");
          iconSpan.className = "tabs-button-icon";

          if (icon instanceof Node) {
            iconSpan.appendChild(icon);
          } else {
            iconSpan.textContent = String(icon);
          }

          button.appendChild(iconSpan);
        }

        const labelSpan = document.createElement("span");
        labelSpan.className = "tabs-button-label";
        labelSpan.textContent = name;

        const closeSpan = document.createElement("span");
        closeSpan.className = "tabs-button-close";
        closeSpan.textContent = "×";

        button.append(labelSpan, closeSpan);
      }

      addTab(name, icon = null) {
        if (!name) {
          console.warn("TabsComponent.addTab: name is required.");
          return false;
        }

        if (!this.buttonsContainer || !this.pagesContainer) {
          console.warn("TabsComponent.addTab: component is not connected.");
          return false;
        }

        if (this.tabs.some(t => t.name === name)) {
          console.warn(`TabsComponent.addTab: tab "${name}" already exists.`);
          return false;
        }

        const button = document.createElement("button");
        button.className = "tabs-button";
        this._setButtonContent(button, name, icon);

        const page = document.createElement("div");
        page.className = "tabs-page";

        this.buttonsContainer.appendChild(button);
        this.pagesContainer.appendChild(page);

        this.tabs.push({
          name: name,
          icon: icon,
          closeDisabled: false
        });

        if (this.activeIndex === -1) {
          this.setActiveTab(0);
        }

        return true;
      }

      addTabWithContent(name, content, icon = null) {
        const added = this.addTab(name, icon);
        if (!added) return false;

        this.setTabContent(name, content);
        return true;
      }

      deleteTab(nameOrIndex) {
        const index =
          typeof nameOrIndex === "number"
            ? nameOrIndex
            : this.tabs.findIndex(t => t.name === nameOrIndex);

        if (index < 0 || index >= this.tabs.length) return false;

        const wasActive = index === this.activeIndex;
        const wasBeforeActive = index < this.activeIndex;

        this.buttonsContainer.children[index].remove();
        this.pagesContainer.children[index].remove();
        this.tabs.splice(index, 1);

        if (this.tabs.length === 0) {
          this.activeIndex = -1;
          return true;
        }

        if (wasActive) {
          this.activeIndex = -1;
          this.setActiveTab(Math.min(index, this.tabs.length - 1));
        } else if (wasBeforeActive) {
          this.activeIndex -= 1;
        }

        return true;
      }

      setTabContent(nameOrIndex, content) {
        const index =
          typeof nameOrIndex === "number"
            ? nameOrIndex
            : this.tabs.findIndex(t => t.name === nameOrIndex);

        if (index < 0 || index >= this.tabs.length) return false;

        const page = this.pagesContainer.children[index];
        page.replaceChildren();

        if (content == null) return true;

        if (typeof content === "string") {
          page.textContent = content;
        } else if (content instanceof Node) {
          page.appendChild(content);
        } else if (Array.isArray(content) && content.every(x => x instanceof Node)) {
          page.append(...content);
        } else if (
          typeof content === "object" &&
          typeof content.trustedHtml === "string"
        ) {
          page.innerHTML = content.trustedHtml;
        } else {
          page.textContent = String(content);
        }

        return true;
      }
        _resizePlotlyChartsInPage(page) {
        if (!window.Plotly || !page) return;

        const charts = page.querySelectorAll(".js-plotly-plot");

        charts.forEach(function (chart) {
            Plotly.Plots.resize(chart);
        });
        }

      setActiveTab(index) {
        if (index < 0 || index >= this.tabs.length) return false;
        if (index === this.activeIndex) return true;

        const oldButton = this.buttonsContainer.children[this.activeIndex];
        const oldPage = this.pagesContainer.children[this.activeIndex];

        if (oldButton) oldButton.classList.remove("active");
        if (oldPage) oldPage.style.display = "none";

        const newButton = this.buttonsContainer.children[index];
        const newPage = this.pagesContainer.children[index];

        newButton.classList.add("active");
        newPage.style.display = "block";

        this.activeIndex = index;


        requestAnimationFrame(() => {
            this._resizePlotlyChartsInPage(newPage);
        });



        return true;
      }

      selectTab(nameOrIndex) {
        const index =
          typeof nameOrIndex === "number"
            ? nameOrIndex
            : this.tabs.findIndex(t => t.name === nameOrIndex);

        return this.setActiveTab(index);
      }

      hasTab(name) {
        return this.tabs.some(t => t.name === name);
      }

      getTabCount() {
        return this.tabs.length;
      }
/**
 * Returns the page container associated with a tab.
 *
 * @param {string|number} nameOrIndex - Tab name or tab index.
 * @returns {HTMLElement|null} The tab page div, or null if not found.
 */
        getTabPage(nameOrIndex) {
        const index =
            typeof nameOrIndex === "number"
            ? nameOrIndex
            : this.tabs.findIndex(t => t.name === nameOrIndex);

        if (index < 0 || index >= this.tabs.length) {
            return null;
        }

        return this.pagesContainer.children[index];
        }


      getActiveTab() {
        if (this.activeIndex < 0 || this.activeIndex >= this.tabs.length) {
          return null;
        }

        return {
          name: this.tabs[this.activeIndex].name,
          index: this.activeIndex,
          button: this.buttonsContainer.children[this.activeIndex],
          page: this.pagesContainer.children[this.activeIndex]
        };
      }

      clearTabs() {
        if (!this.buttonsContainer || !this.pagesContainer) return false;

        this.buttonsContainer.replaceChildren();
        this.pagesContainer.replaceChildren();

        this.tabs = [];
        this.activeIndex = -1;

        return true;
      }

      disableClose(nameOrIndex, disabled = true) {
        const index =
          typeof nameOrIndex === "number"
            ? nameOrIndex
            : this.tabs.findIndex(t => t.name === nameOrIndex);

        if (index < 0 || index >= this.tabs.length) return false;

        this.tabs[index].closeDisabled = disabled;

        const closeButton =
          this.buttonsContainer.children[index]?.querySelector(".tabs-button-close");

        if (closeButton) {
          closeButton.style.display = disabled ? "none" : "";
        }

        return true;
      }
    }

    if (!customElements.get("tabs-component")) {
  customElements.define("tabs-component", TabsComponent);
}



class QuickJS_DoubleRangeTrack extends HTMLElement {
    /*
    Example of use: 
    <body>
    <h3>Date slice</h3>
    <double-range-component id="double-track"></double-range-component>
    <br><div>Dates: <span id='date1'></span> → <span id='date2'></span></div>
    
    <script>
        document.getElementById('double-track').addEventListener('clicked', (e) => {
        //console.log('Handle 1:', e.detail.handle1, 'Handle 2:', e.detail.handle2);

            const dates = [];
            const start = new Date(1989, 11, 15); // months are 0-indexed
            const end = new Date(2026, 3, 24);

            for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
            const day = String(d.getDate()).padStart(2, '0');
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const year = d.getFullYear();
            dates.push(`${day}-${month}-${year}`);
            }


            let percent1 = e.detail.handle1;
            let percent2 = e.detail.handle2;

            const index1 = Math.round((percent1 / 100) * (dates.length - 1));
            const index2 = Math.round((percent2 / 100) * (dates.length - 1));
            console.log(index1,index2)

            const date1 = dates[Math.min(index1, index2)];
            const date2 = dates[Math.max(index1, index2)];
            console.log(`Selected range: ${date1} → ${date2}`);

            document.getElementById('date1').textContent = date1;
            document.getElementById('date2').textContent = date2;


        });
        </script>
    </body>
    */
    constructor() {
      super();

    
    }

    getTemplate(){

        return `
        <div class="double-range-track">
          <div class="double-range-ticks"></div>
          <div class="double-range-fill"></div>
          <div class="double-range-handle" id="handle1" style="left: 10%;"></div>
          <div class="double-range-handle" id="handle2" style="left: 20%;"></div>
        </div>
      `;

    }

    getValues(){
        const handle1 = this.querySelector('.handle1');
        const handle2 = this.querySelector('.handle2');
        const val1 = parseFloat(handle1.style.left);
        const val2 = parseFloat(handle2.style.left);
        return [val1,val2];//{handle1: parseFloat(handle1.style.left), handle2: parseFloat(handle2.style.left)};
    }

    connectedCallback() {

        this.innerHTML = `
        <div class="double-range-track">
          <div class="double-range-ticks"></div>
          <div class="double-range-fill"></div>
          <div class="double-range-handle handle1" style="left: 0%;"></div>
          <div class="double-range-handle handle2" style="left: 100%;"></div>
        </div>
      `;

      let this_object = this;
      const track = this.querySelector('.double-range-track');
      const handle1 = this.querySelector('.handle1');
      const handle2 = this.querySelector('.handle2');
      const fill = this.querySelector('.double-range-fill');

      let dragging = null;

      const updateFill = () => {
        const val1 = parseFloat(handle1.style.left);
        const val2 = parseFloat(handle2.style.left);
        const left = Math.min(val1, val2);
        const right = Math.max(val1, val2);
        fill.style.left = `${left}%`;
        fill.style.width = `${right - left}%`;

        this.dispatchEvent(new CustomEvent('clicked', {
          detail: {
            handle1: val1,
            handle2: val2
          },
          bubbles: true
        }));
      };

      const onMouseMove = (e) => {
        if (!dragging) return;

        const trackRect = track.getBoundingClientRect();
        const x = e.clientX - trackRect.left;
        const percent = Math.max(0, Math.min(100, (x / trackRect.width) * 100));
        dragging.style.left = `${percent}%`;
        updateFill();
      };

      const onMouseUp = () => {
        dragging = null;
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);

        
        this_object.dispatchEvent(new CustomEvent('mouse-up', {bubbles: true}));
          
      };

      const onMouseDown = (e, handle) => {
        dragging = handle;
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
      };

      handle1.addEventListener('mousedown', (e) => onMouseDown(e, handle1));
      handle2.addEventListener('mousedown', (e) => onMouseDown(e, handle2));

      updateFill(); // Initial setup

      const tickCount = 20;
      const ticksContainer = this.querySelector('.double-range-ticks');

      for (let i = 0; i <= tickCount; i++) {
        const tick = document.createElement('div');
        ticksContainer.appendChild(tick);
      }
    }

    setRanges(minPercent, maxPercent) {
        const handle1 = this.querySelector('.handle1');
        const handle2 = this.querySelector('.handle2');
        const fill = this.querySelector('.double-range-fill');
      
        // Clamp values between 0 and 100
        minPercent = Math.max(0, Math.min(100, minPercent));
        maxPercent = Math.max(0, Math.min(100, maxPercent));
      
        handle1.style.left = `${minPercent}%`;
        handle2.style.left = `${maxPercent}%`;
      
        // Update the fill bar and emit event
        const left = Math.min(minPercent, maxPercent);
        const right = Math.max(minPercent, maxPercent);
        fill.style.left = `${left}%`;
        fill.style.width = `${right - left}%`;
      
        this.dispatchEvent(new CustomEvent('clicked', {
          detail: {
            handle1: minPercent,
            handle2: maxPercent
          },
          bubbles: true
        }));
    }
}
customElements.define('double-range-component', QuickJS_DoubleRangeTrack);



class QuickJS_ComboBoxSelector extends HTMLElement {
    constructor() {
        super();
        this.componentId = this.getAttribute("id") || "";
  
    }
    connectedCallback() {
        this.render();
    }

    //defaultOption.disabled = true;  
    //defaultOption.selected = true;  
    //defaultOption.textContent = 'Select an option...';  
    render() {
        this.innerHTML = `
            <select class="form-select combobox">
                <option disabled selected>Select option</option>
            </select>
        `;
        this.selectElement = this.querySelector("select");
        this.selectElement.addEventListener("change", () => {
            this.dispatchEvent(new CustomEvent("clicked", {
                detail: { text: this.selectElement.value }
            }));
        });
    }

    setData(items) {
        this.selectElement.innerHTML = "";

        let option = document.createElement("option");
        option.setAttribute('disabled', true);
        option.setAttribute('selected', true);
        option.textContent = "Select option";
        //option.value = undefined;
        this.selectElement.appendChild(option);

        items.forEach(item => {
            const option = document.createElement("option");
            option.value = item;
            option.textContent = item;
            this.selectElement.appendChild(option);
        });
    }

    setValue(txt) {
        this.selectElement.value = txt;
        this.dispatchEvent(new CustomEvent("clicked", {
            detail: { text: this.selectElement.value }
        }));
        
    }

    getValue() {
        return this.querySelector('select').value;  

    }

    getOptions() {  
        const select = this.querySelector('select');  
        const options = [];  
        select.querySelectorAll('option').forEach((option) => {  
          if (!option.disabled) {  
            options.push(option.value);  
          }  
        });  
        return options;  
      }  

}
if (!customElements.get("combobox-component")) {
    customElements.define("combobox-component", QuickJS_ComboBoxSelector);
}


class QuickJS_Stringlist extends HTMLElement { 
      
      static observedAttributes = ["selection_mode","checkboxes", "title"];
  
      _selection_mode
      _checkboxes
      extra 
      connected 
  
      constructor( names, title,  checkboxes, selection_mode){
          super();
          this.extra = undefined;
          this._names = names; 
          this._title = title;  
          this._selection_mode = selection_mode != undefined ? selection_mode : 'single';
          this._checkboxes  = checkboxes != undefined ? Boolean(checkboxes) : false;
      }  
  
      set_rows( names ){
          let this_object = this;
          this_object._names=names;
          let table = this_object.getElementsByTagName('table')[0];
          let thead = table.getElementsByTagName('thead')[0];
          let tbody = table.getElementsByTagName('tbody')[0];
  
          function get_check_box(){
            let chk = document.createElement('input');//,{type:'checkbox'});
            chk.type = 'checkbox';
                          chk.style.marginLeft='10px'
                          chk.style.marginRight='10px'
                          chk.style.verticalAlign ='middle'
                          return chk;
          }
  
          let  rowCount = tbody.rows.length;
          for (let i = 0; i < rowCount; i++) {
          tbody.deleteRow(0);
          }
  
  
          names.forEach((name) => {      
          
          let row =  tbody.insertRow(-1);  //add a row at the end 
          row.classList.add('string-list-tr');

          let c1 = row.insertCell(0);      //add a cell at index = 0 to the row. 
          c1.classList.add('string-list-td');
          let newText = document.createTextNode( name );
          let chk = undefined;//get_check_box()
          //let chk = get_radio()
          
         let use_checks =  Boolean(this_object._checkboxes);
          if(this_object._selection_mode=='multiple'){
          if( use_checks) {
              chk = get_check_box()
              chk.classList.add('string-list-checkbox');
              c1.appendChild( chk );
          }}
          
          c1.appendChild( newText);
          
          });
          
      
      }
  
      getRow = function (index) {
          let this_object = this;
          let table = this_object.getElementsByTagName('table')[0];
          let thead = table.getElementsByTagName('thead')[0];
          let tbody = table.getElementsByTagName('tbody')[0];
  
          
          let s = []//Array.from(table_columns);
          for( let c of table.rows[0].cells) s.push( c.innerText )
          
          let data={}
          let row = tbody.rows[index];
          let cells = row.cells;                               //plus the header and the value of each cell for the headers
          for (let n = 0; n < s.length; n++) data[s[n]] = cells[n].innerText;
          
          return data 
          
          }
  
      unselect_all_rows(  e=-1 ){
          let this_object = this;
          let table = this_object.getElementsByTagName('table')[0];
          let tbody = table.getElementsByTagName('tbody')[0];
  
          let rows = tbody.rows;
          
      
          for (let k = 0; k < rows.length; k++) {
          
          if(k!=e){
          rows[k].classList.remove('selected');
          let chk = rows[k].children[0].getElementsByTagName('input')[0]
          if(chk) chk.removeAttribute('checked');//,false );
          }
          
          }
      }
      
      select_row( k ) {
          let this_object = this;
          let table = this_object.getElementsByTagName('table')[0];
          let tbody = table.getElementsByTagName('tbody')[0];
  
          let rows = tbody.rows;
          rows[k].classList.add('selected');
          let chk = rows[k].children[0].getElementsByTagName('input')[0]
          if(chk) chk.setAttribute('checked',true );
      }
      
      flip_row_selection( k ) {
  
          let this_object = this;
          let table = this_object.getElementsByTagName('table')[0];
          let tbody = table.getElementsByTagName('tbody')[0];
          let rows = tbody.rows;
  
          rows[k].classList.toggle('selected');
          
          let chk = rows[k].children[0].getElementsByTagName('input')[0];
          if(chk) 
          {	
              if(chk.hasAttribute('checked')==false)
              chk.setAttribute('checked',true );
          
              else chk.removeAttribute('checked');
              
          }
      }
          
      selected() {
          
      let this_object = this;
      let table = this_object.getElementsByTagName('table')[0];
      let tbody = table.getElementsByTagName('tbody')[0];
      
          let selected_rows  = []
          
          let rows = tbody.rows;
          for (let i = 0; i < rows.length; i++)      //for each row 
          {
          let row = rows[i];
          if( row.classList.contains('selected'))
              selected_rows.push( {row_index:i, cell_text:row.innerText} ) 
          }
          
  
          return selected_rows;      
      }
  
      
      connect_row_click_events() {
          
      let this_object = this;
      let table = this_object.getElementsByTagName('table')[0];
      let thead = table.getElementsByTagName('thead')[0];
      let tbody = table.getElementsByTagName('tbody')[0];
  
          let rows = tbody.rows;
          for (let i = 0; i < rows.length; i++)      //for each row 
          {
          let row = rows[i];
  
          row.addEventListener('click', (evt) =>   //add a click event 
          {
              if( table.disabled==true){;}
          
              else{
          
         if(this_object.selection_mode =='none'){
             return;
         }  
                  
          if(this_object.selection_mode ==undefined){
              this_object.selection_mode = 'single';
          }
                  
              if(this_object.selection_mode =='single'){
                  this_object.unselect_all_rows(i);
                  this_object.flip_row_selection(i);
              }
              
              if(this_object.selection_mode =='multiple'){
                  this_object.flip_row_selection(i);
              }
              
              //now the data 
              const cell = evt.target.closest('td');
              let data = undefined 
              
              let s = this_object.selected()
              
              
              // not clicked on a cell
          let row_data= this_object.getRow( i );
              if (!cell)  this_object.raise_click_event({'clicked':s, 'row_index': i, 'row_data':row_data });	 
              
              else
          this_object.raise_click_event({ 'clicked':s, 'row_index': i, 'row_data':row_data, 'cell_text': evt.target.innerText, 'cell_index': cell.cellIndex });	
              }
              
          });
          
          row.addEventListener('dblclick', (evt) =>   //add a click event 
          {
              if( table.disabled==true){;}
          
              else{
          
         if(this_object.selection_mode =='none'){
             return;
         }  
                  
          if(this_object.selection_mode ==undefined){
              this_object.selection_mode = 'single';
          }
                  
              if(this_object.selection_mode =='single'){
                  this_object.unselect_all_rows(i);
                  this_object.flip_row_selection(i);
              }
              
              if(this_object.selection_mode =='multiple'){
                  this_object.flip_row_selection(i);
              }
              
              //now the data 
              const cell = evt.target.closest('td');
              let data = undefined 
              
              let s = this_object.selected()
              console.log( 'selected', s )
              
              // not clicked on a cell
          let row_data= this_object.getRow( i );
              if (!cell)  this_object.raise_dclick_event({'dclicked':s, 'row_index': i, 'row_data':row_data });	 
              
              else
          this_object.raise_dclick_event({ 'dclicked':s, 'row_index': i, 'row_data':row_data, 'cell_text': evt.target.innerText, 'cell_index': cell.cellIndex });	
              }
              
          });

          }//rows
      }//function
      
      raise_click_event(data) {
          let this_object = this;
          let table = this_object.getElementsByTagName('table')[0];
          this_object.selected();
  
          
          let x = new CustomEvent("clicked", { bubbles: true, detail: data }); 
          this_object.dispatchEvent(x);
  
          //console.log('dispatching event, data ', data )
          }
  
          raise_dclick_event(data) {
            let this_object = this;
            let table = this_object.getElementsByTagName('table')[0];
            this_object.selected();
    
            
            let x = new CustomEvent("dclicked", { bubbles: true, detail: data }); 
            this_object.dispatchEvent(x);
    
            //console.log('dispatching event, data ', data )
            }

      setData = ( strings ) => {
        this.set_data(strings);
      }
      set_data = ( strings )=>{
          let this_object = this;
          let table = this_object.getElementsByTagName('table')[0];
          let thead = table.getElementsByTagName('thead')[0];
          let tbody = table.getElementsByTagName('tbody')[0];
  
  
          this_object.set_rows( strings );
          this_object.connect_row_click_events( );
          
      }
  
      has_body = ()=> {
          return this.innerHTML.replace(/ /g, '').length  > 0; 
      }
  
      attributeChangedCallback(name, oldValue, newValue) {
          
          //if( this.has_body() == false) return 
          //if(name=='names') this.names = newValue;
          if(name=='title') this.set_title( newValue );//  title = newValue;
          if(name=='selection_mode') this._selection_mode = newValue;
          if(name=='checkboxes')  this._checkboxes = Boolean(newValue);
      }
  
      connectedCallback() {
  
        let listDiv = document.createElement('div');
        listDiv.classList.add('string-list-container');

          let table  = document.createElement('table');
          let tbody  = document.createElement('tbody');
          let thead  = document.createElement('thead');
              
          table.classList.add('table')
          table.classList.add('string-list-table')
          
          thead.classList.add('thead')
          thead.classList.add('string-list-thead')
          
          tbody.classList.add('tbody')
          tbody.classList.add('string-list-tbody')

          table.appendChild( tbody );
          table.appendChild( thead );
          this.appendChild(table);
          //this.style.display = "block";
  
          let t_atts = this.getAttributeNames();
          //let selection_mode = t_atts['selection_mode'] != undefined? t_atts['selection_mode']:'single'
          //let checkboxes     = t_atts['checkboxes']     != undefined? t_atts['checkboxes'] : false;     
      
    
      
          this.connected = true; 
          if(this._names) this.set_data(this._names);
          if(this._title) this.set_title(this._title);
          
           
        listDiv.appendChild(table);
        this.appendChild(listDiv);
        this.classList.add('string-list') 


        //this.id = this.hasAttribute('id') ? this.getAttribute('id') : 'string-list'+Math.random().toString(36).substring(2,16);
        
         //if( t_atts['id']!= undefined ) 
         //this.id = t_atts['id'] 
         //else this.id = 'string-list-'+Math.random().toString(36).substring(2,16);
          
        //if (t_atts['class_name']!=undefined)
        //    {
        //        table.classList.add( t_atts['class_name']);
        //    }
          
         //this.appendChild(table);
         //this.style.display = 'block';
         //this.classList.add('scrollable');
    }
  
      set_title( title ){
  
        this._title = title;
        if( !this.connected) return; 

          let this_object = this;
          let table = this_object.getElementsByTagName('table')[0];
          let thead = table.getElementsByTagName('thead')[0];
  
              while (thead.firstChild) {
              thead.removeChild(thead.firstChild);
              }
          
              if(title==undefined) thead.style.display = 'none';
              let tr = document.createElement('tr')
              tr.classList.add('string-list-tr');
              thead.appendChild(tr);
              let th = document.createElement('th')
              th.classList.add('string-list-th');
              
              th.appendChild( document.createTextNode( title ));
              tr.appendChild(th);	
      }


        deleteRowIndex(rowIndex) {
            if (rowIndex >= 0 && rowIndex < this._names.length) {
                this._names.splice(rowIndex, 1);
                this.set_rows(this._names); // re-render rows
                this.connect_row_click_events(); // rebind events
            }
        }


        deleteItem(string) {
            const index = this._names.findIndex(name => name === string);
            if (index !== -1) {
                this._names.splice(index, 1);                  // 1. Remove from internal state
                this.set_rows(this._names);                    
                this.connect_row_click_events();               
            }
        }

  
};  
if( customElements.get('stringlist-component') == undefined){
customElements.define('stringlist-component', QuickJS_Stringlist);
}

class QuickJS_Table extends QuickJS_Stringlist { 
     
      constructor(names,selection_mode){
          super(   names, undefined,  undefined, selection_mode );
          if( names != undefined )
            this.set_data( names );
        }
          
      selected() {
          
      let this_object = this;
      let table = this_object.getElementsByTagName('table')[0];
      let tbody = table.getElementsByTagName('tbody')[0];
      
          let selected_rows  = []
          
          let rows = tbody.rows;
          for (let i = 0; i < rows.length; i++)      //for each row 
          {
          let row = rows[i];
          if( row.classList.contains('selected'))
              {
              let row_data = this_object.getRow(i);
              row_data['row_index'] = i   
              selected_rows.push( row_data );//{row_index:i, cell_text:row.innerText} ) 
              }
          }
          
  
          return selected_rows;      
      }
      
      setData = ( strings, column_order  ) => {
        /*table*/
        this.set_data(strings,column_order);
      }

      set_data = ( data, column_order ) => {
            /*table*/
            
          function get_check_box(){
                          let chk = document.createElement('input');//,{type:'checkbox'});
                          chk.type = 'checkbox';
                          chk.style.marginLeft='10px'
                          chk.style.marginRight='10px'
                          chk.style.verticalAlign ='middle'
                          return chk;
              }
  
            
          let this_object = this;
          let table = this_object.getElementsByTagName('table')[0];
          let thead = table.getElementsByTagName('thead')[0];
          let tbody = table.getElementsByTagName('tbody')[0];
      
      
          let  rowCount = table.rows.length;
          for (let i = 0; i < rowCount; i++) {
              table.deleteRow(0);
          }
  
          // #region the head
          let table_columns = new Set()
          data.forEach((element) => {Object.keys(element).forEach((one) => { table_columns.add(one); });});
      
            if (column_order !== undefined) {
                const ordered = column_order.filter((col) => table_columns.has(col));
                const remaining = [...table_columns].filter((col) => !ordered.includes(col));

                table_columns = [...ordered, ...remaining];
            } else {
                table_columns = [...table_columns];
            }
      
          let tr = document.createElement('tr')
          //tr.classList.add('string-list-tr');
          thead.appendChild(tr);
          table_columns.forEach((column) => {
            let th = document.createElement('th')//ui.addChildren(thead, document.createElement("th"))
            //th.classList.add('string-list-th');
            th.appendChild( document.createTextNode( column ));
            tr.appendChild(th);
          });
       
      
          // #region the rows
          let s = Array.from(table_columns);
          data.forEach((item) => {           //for each item in the json
          let counter = 0;
          let row =  tbody.insertRow(-1);  //table.insertRow(-1); //add a row at the end 
          //row.classList.add('string-list-tr');
          //ui.addAttributesTo(row,{class:'active'});
      
          s.forEach((key) => {               //for each column name   
            let value = item[key];           //fetch the value for the item (may be undefined)
            let c1 = row.insertCell(counter); //and add the cell to the row. 
            //c1.classList.add('string-list-td');
            /*if(counter==0){
                  if(this_object.checkboxes==true) {
                  let chk = get_check_box()
                  c1.appendChild( chk );
              }}*/
                          
      
            let innerText =''
            if (value != undefined) 
            innerText = value;                //dont add the string 'undefined' set it to empty 
      
            let newText = document.createTextNode( innerText);
            c1.appendChild( newText);
            counter = counter + 1;
            });
        });
        // #endregion
      
        this_object.connect_row_click_events()
        }
      
      set_title( title ){;}
   
      
};     
if( customElements.get('table-component') == undefined){
customElements.define('table-component', QuickJS_Table);
}


class QuickJS_ScrollableList extends HTMLElement {

                
        static observedAttributes = ["selection_mode","checkboxes"];
      
        selection_mode
        checkboxes
        connected 

      constructor() {
        super();
        this.listDiv = document.createElement('div');
        this.listDiv.classList.add('scrollable-list');
        this.table = document.createElement('table');
        this.table.classList.add('table')
        this.listDiv.appendChild(this.table);
        this.appendChild(this.listDiv);
      }

      set_data(items) {
        // Clear the current table
        this.table.innerHTML = '';
        // Populate with new items
        items.forEach(item => {
          const row = document.createElement('tr');
          const cell = document.createElement('td');
          cell.textContent = item;
          row.appendChild(cell);
          this.table.appendChild(row);
        });
      }

        
      set_title( title ){

        this.title = title;
        if( ! this.connected) return; 

        let this_object = this;
        let table = this_object.getElementsByTagName('table')[0];
        let thead = table.getElementsByTagName('thead')[0];

        while (thead.firstChild) {
        thead.removeChild(thead.firstChild);
        }

        if(title==undefined) thead.style.display = 'none';
        let tr = document.createElement('tr')
        thead.appendChild(tr);
        let th = document.createElement('th')
        th.appendChild( document.createTextNode( title ));
        tr.appendChild(th);	
        }


      connectedCallback() {
        const items = this.getAttribute('items') ? JSON.parse(this.getAttribute('items')) : [];
        this.set_data(items);

        this.connected = true; 
      }






}
if( customElements.get('scrollable-component') == undefined){
    customElements.define('scrollable-component', QuickJS_ScrollableList);
    console.log('Added custom element scrollable-component');
}


class QuickJS_TwoColumnMainLayout extends HTMLElement {
    constructor() {
        super();
    }

    getTemplate(){
        // Create the inner HTML structure
        return `
                        <div id="main-layout" class="container-fluid mt-1">
                            <div  class="row">
                                <div id='xxx' class="columns-container">
                                    <!-- Left Pane -->
                                    <div id="left-pane" class="col-2 column" style="position: relative;">
                                        <div id = 'left-top' class="pane flex-grow-2" style="overflow-y: scroll;max-height: 170%; flex-basis: 65%;"></div>
                                        <div id = 'left-middle' class="pane flex-grow-1" style="overflow-y: scroll;max-height: 0%; flex-basis: 0%;"></div>
                                        <div id = 'left-bottom' class="pane flex-grow-1" style="overflow-y: scroll;max-height: 70%; flex-basis: 35%;"></div>
                                    </div>

                                    <!-- Middle Pane -->
                                    <div id="middle-pane" class="col-5 column gx-5" style="position: relative;">
                                        <div id="left-separator" class="separator" style="left: 0;"></div>
                                        <div id = 'middle-top'  class="pane flex-grow-1" style="overflow-y: scroll;flex-basis: 150%;"></div>
                                        <div class="handler" style="flex-basis: 2%;"></div>
                                        <div id = 'middle-bottom' class="pane flex-grow-1" style="overflow-y: scroll;flex-basis: 150%;"></div>
                                    </div>

                                    <!-- Right Pane -->
                                    <div id="right-pane" class="col-5 column" style="position: relative;">
                                        <div  id = 'right-top' class="pane flex-grow-1" style="overflow-y: scroll;flex-basis: 30%;"></div>
                                        <div class="handler"></div>
                                        <div  id = 'right-bottom' class="pane flex-grow-1" style="overflow-y: scroll;flex-basis: 70%;">
                                            <p>I am the right aaaabbbbccccdddddeeeeefffffggggghhhhh</p>
                                        </div>
                                        <div id="right-separator" class="separator" style="left: 0;"></div>
                                    </div>
                                </div>
                            </div>
                               
                    
                        </div>

                    `;

                    /*<!--div class="row">
                    <!-- Draggable Separator Above Messages -->
                   <div id="messages-separator" class="xxseparator" style="cursor: ns-resize; height: 5px; background: gray;"></div>

                  <div style='padding:20px;overflow-y: scroll;' class="message-container acolumns-container mt-1" id="messages"></div>
               
               
                  </div-->*/

                

    }

    getStyle(){
        return  `

        .message-container{
        background-color: red;    height: 10vh;            
        }

        body {
                background-color: #f5f5f5; /* Smoke white */
            }

            .pane {
                background-color: white;
                border: 1px solid #ddd;
                padding-left: 10px;
                padding-right: 10px;
                padding-top: 10px;
                xxpadding-bottom: 10px;
                
            }

            #left-pane .pane:nth-child(1) {
                background-color: #ffcccc; /* Random light color */
            }

            #left-pane .pane:nth-child(2) {
                background-color: #ccffcc; /* Random light color */
            }

            #left-pane .pane:nth-child(3) {
                background-color: #ccccff; /* Random light color */
            }

            #middle-pane .pane:nth-child(1) {
                background-color: #ffffcc; /* Random light color */
            }

            #middle-pane .pane:nth-child(2) {
                background-color: #ccffff; /* Random light color */
            }

            #right-pane .pane:nth-child(1) {
                background-color: #ffccff; /* Random light color */
            }

            #right-pane .pane:nth-child(2) {
                background-color: #cce5ff; /* Random light color */
            }

            .columns-container {
                display: flex;
                height: 80vh;
                gap: 0;
            }

            .column {
                display: flex;
                flex-direction: column;
                gap: 10px; /* Small gap between rows */
                position: relative;
                height: 100%;
            }

            .separator {
                width: 8px;
                background-color: red;
                cursor: ew-resize;
                position: absolute;
                top: 0;
                bottom: 0;
                z-index: 1;
            }

            .separator:hover {
                background-color: darkred;
            }

            .handler:hover {
                background-color: darkred;
            }

            .handler {
                height: 10px;
                background-color: red;
            }
        `;

    }

    initResizableMessages(){
        return;
        const separator = this.querySelector("#messages-separator");
        const messages = this.querySelector("#messages");
        let xxisResizing = false;
        let xxstartY, xxstartHeight;


        function xxonMouseMove(e) {
            if (!xxisResizing) return;

            //console.log('moving!!!')

            let delta = (e.clientY - xxstartY)
            const newHeight = xxstartHeight - delta;
            messages.style.height = `${newHeight}px`;

            let leftSeparator = this.querySelector('#xxx');

            let h = leftSeparator.offsetHeight + 0.025*delta ;
            console.log( 'h', h, delta)

            leftSeparator.style.height = h.toString() +'px';

        }
    
        function xxonMouseUp() {
            xxisResizing = false;

            console.log('up!!!')
            document.removeEventListener("mousemove", xxonMouseMove);
            document.removeEventListener("mouseup", xxonMouseUp);
        }    
        
        separator.addEventListener("mousedown", (e) => {
            xxisResizing = true;
            xxstartY = e.clientY;
            xxstartHeight = messages.offsetHeight;
            document.addEventListener("mousemove",  xxonMouseMove);
            document.addEventListener("mouseup", xxonMouseUp);
            console.log('down!!!')
        });
    


    }


    connectedCallback() {
        this.innerHTML = this.getTemplate();
        this.initResizableColumns();
        this.initResizableRows();

        this.initResizableMessages();

        const style = document.createElement('style');
        style.textContent = this.getStyle();
        document.head.appendChild(style);


    }

    initResizableColumns() {
        const leftSeparator = this.querySelector('#left-separator');
        const rightSeparator = this.querySelector('#right-separator');
        const leftPane = this.querySelector('#left-pane');
        const middlePane = this.querySelector('#middle-pane');
        const rightPane = this.querySelector('#right-pane');


        let isResizingLeft = false;
let lastDownXLeft = 0;

leftSeparator.addEventListener('mousedown', (e) => {
    isResizingLeft = true;
    lastDownXLeft = e.clientX;
    document.body.style.cursor = 'ew-resize';
});

document.addEventListener('mousemove', (e) => {
    if (!isResizingLeft) return;

    let offset = e.clientX - lastDownXLeft;
    let newLeftWidth = leftPane.offsetWidth + offset;
    let newMiddleWidth = middlePane.offsetWidth - offset;

    if (newLeftWidth > 50 && newMiddleWidth > 50) {
        leftPane.style.width = `${newLeftWidth}px`;
        middlePane.style.width = `${newMiddleWidth}px`;

    
        //rightPane.style.margin= "5%";
        //rightPane.style.width = "100%";
    

    }

    lastDownXLeft = e.clientX;
});

document.addEventListener('mouseup', () => {
    if (isResizingLeft) {
            this.dispatchEvent(new CustomEvent('pane-resized', {
                detail: {
                    id: leftPane.id,
                    offsetWidth: leftPane.offsetWidth,
                    offsetHeight: leftPane.offsetHeight
                }
            }));

            this.dispatchEvent(new CustomEvent('pane-resized', {
                detail: {
                    id: middlePane.id,
                    offsetWidth: middlePane.offsetWidth,
                    offsetHeight: middlePane.offsetHeight
                }
            }));
        }
       

isResizingLeft = false;
    document.body.style.cursor = 'default';
});

// For the middle-right separator between middle-pane and right-pane

let isResizingRight = false;
let lastDownXRight = 0;

rightSeparator.addEventListener('mousedown', (e) => {
    isResizingRight = true;
    lastDownXRight = e.clientX;
    document.body.style.cursor = 'ew-resize';
});

document.addEventListener('mousemove', (e) => {
    if (!isResizingRight) return;

    let offset = e.clientX - lastDownXRight;
    let newRightWidth = rightPane.offsetWidth - offset;  // Decrease right-pane width on drag left
    let newMiddleWidth = middlePane.offsetWidth + offset;  // Increase middle-pane width on drag left

    if (newRightWidth > 50 && newMiddleWidth > 50) {
        middlePane.style.width = `${newMiddleWidth}px`;
        //rightPane.style.width = "96%";//`${newRightWidth}px`;
        let x = window.innerWidth -20 - (leftPane.offsetWidth + offset + newMiddleWidth);

        rightPane.style.width = `${x}px`;//"20%";//`${newRightWidth}px`;
        //rightPane.style.flex_basis = parseInt(100.0*newRightWidth/(newMiddleWidth + newRightWidth ));

    }

    lastDownXRight = e.clientX;
});

document.addEventListener('mouseup', () => {

    if (isResizingRight) {
            this.dispatchEvent(new CustomEvent('pane-resized', {
                detail: {
                    id: rightPane.id,
                    offsetWidth: middlePane.offsetWidth,
                    offsetHeight: middlePane.offsetHeight
                }
            }));

            this.dispatchEvent(new CustomEvent('pane-resized', {
                detail: {
                    id: middlePane.id,
                    offsetWidth: middlePane.offsetWidth,
                    offsetHeight: middlePane.offsetHeight
                }
            }));
        }

   
    isResizingRight = false;
    document.body.style.cursor = 'default';
});
    }

    initResizableRows() {
        this.querySelectorAll('.handler').forEach(handler => {
            let isDragging = false;

            const onDrag = (e) => {
             
                if (!isDragging) return;

                const parent = handler.parentNode;
                const prevRow = handler.previousElementSibling;
                const nextRow = handler.nextElementSibling;
                const parentRect = parent.getBoundingClientRect();

                const prevHeight = e.clientY - parentRect.top - prevRow.offsetTop;
                const nextHeight = parentRect.height - prevHeight - handler.offsetHeight;

                const minHeight = 30; // Minimum height in pixels
                if (prevHeight > minHeight && nextHeight > minHeight) {
                    prevRow.style.flexBasis = `${prevHeight}px`;
                    nextRow.style.flexBasis = `${nextHeight}px`;
                }
            };

            const stopDrag = () => {

                if (isDragging) {
                const prevRow = handler.previousElementSibling;
                const nextRow = handler.nextElementSibling;

                this.dispatchEvent(new CustomEvent('pane-resized', {
                    detail: {
                        id: prevRow.id,
                        newWidth: prevRow.offsetWidth,
                        newHeight: prevRow.offsetHeight
                    }
                }));

                this.dispatchEvent(new CustomEvent('pane-resized', {
                    detail: {
                        id: nextRow.id,
                        newWidth: nextRow.offsetWidth,
                        newHeight: nextRow.offsetHeight
                    }
                }));

            }


                isDragging = false;
                document.body.style.cursor = 'default';
                document.removeEventListener('mousemove', onDrag);
                document.removeEventListener('mouseup', stopDrag);
            };

            handler.addEventListener('mousedown', () => {
                isDragging = true;
                document.body.style.cursor = 'row-resize';
                document.addEventListener('mousemove', onDrag);
                document.addEventListener('mouseup', stopDrag);
            });
        });
    }


//api 
addMessage(text) {
    const messagesContainer = this.querySelector("#messages");

    const message = document.createElement("p");
    message.textContent = text;
    messagesContainer.appendChild(message);
    }
setMessage(text) {
    const messagesContainer = this.querySelector("#messages");
    messagesContainer.innerHTML = ""; 
    const message = document.createElement("p");
    message.textContent = text;
    messagesContainer.appendChild(message);
    }
clearMessage(text) {
    const messagesContainer = this.querySelector("#messages");
    messagesContainer.innerHTML = ""; 
    }

// Set content in the specified pane
set(where, content) {
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(where)) {
        const pane = this.querySelector(`#${where}`);
        
        if (typeof content === 'string') {
            pane.innerHTML = content;  // Set content as innerHTML if it's a string
        } else if (content instanceof HTMLElement) {
            pane.innerHTML = ''; // Clear existing content
            pane.appendChild(content);  // Append the HTML element
        } else {
            console.error('Content must be a string or an HTML element');
        }
    } else {
        console.error('Invalid pane ID');
    }
    
    
}
clear(where) {
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(where)) {
        const pane = this.querySelector(`#${where}`);
        pane.innerHTML = ''; // Clear existing content
    }
    
    
}
append(where, content) {
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(where)) {
        const pane = this.querySelector(`#${where}`);
        
        //if (typeof content === 'string') {
        //    pane.innerHTML = content;  // Set content as innerHTML if it's a string

        if (content instanceof HTMLElement) {
            //pane.innerHTML = ''; // Clear existing content
            pane.appendChild(content);  // Append the HTML element
        } else {
            console.error('Content must be a an HTML element');
        }
    } else {
        console.error('Invalid pane ID');
    }
    
    
}
get_pane( id ){
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(id)) {
        const pane = this.querySelector(`#${id}`);
        return pane; 
    }

}

}
customElements.define('two-column-layout-component', QuickJS_TwoColumnMainLayout);


class Bad_QuickJS_TabsComponent extends HTMLElement {
    constructor() {
        super();
        this.tabNames = [];
        this.tabContents = {};
        this.componentId = this.getAttribute("id") || "";
    }

    connectedCallback() {
        this.render();
    }

    render() {
        this.innerHTML = `
            <div class="tabs-container" id="tabs">
                <button class="add-tab-btn" id="add-tab">+</button>
            </div>
            <div id="contents"></div>
        `;

        this.tabsContainer = this.querySelector("#tabs");
        this.contentsContainer = this.querySelector("#contents");
        this.addTabButton = this.querySelector("#add-tab");
        this.addTabButton.onclick = () => this.addNewTab();
        this.updateTabs();
    }

    tabCount() {
        return this.tabNames.length;
    }

    updateTabs() {
        this.tabsContainer.innerHTML = "";
        
        this.tabNames.forEach((name, index) => {
            const tab = document.createElement("div");
            tab.classList.add("tab");
            tab.innerText = name;
            tab.onclick = () => this.showTab(index);
            this.dispatchEvent(new CustomEvent("clicked", { detail: { index, name } }));
            
            tab.oncontextmenu = (event) => {
                event.preventDefault();
                this.renameTab(index);
            };
            
            const deleteBtn = document.createElement("button");
            deleteBtn.innerText = "x";
            deleteBtn.classList.add("delete-btn");
            deleteBtn.onclick = (event) => {
                event.stopPropagation();
                this.removeTab(index);
            };
            tab.appendChild(deleteBtn);
            
            this.tabsContainer.appendChild(tab);
        });
        
        this.tabsContainer.appendChild(this.addTabButton);
        this.renderContents();
        if (this.tabNames.length > 0) this.showTab(this.tabNames.length - 1);
    }

    renderContents() {
        this.contentsContainer.innerHTML = "";
        this.tabNames.forEach((name, index) => {
            const content = this.tabContents[name];
            content.classList.add("tab-content");
            this.contentsContainer.appendChild(content);
        });
    }

    showTab(index) {
        this.querySelectorAll(".tab").forEach((tab, i) => {
            tab.classList.toggle("active", i === index);
        });
        this.querySelectorAll(".tab-content").forEach((content, i) => {
            content.classList.toggle("active", i === index);
        });
    }

    removeTab(index) {
        const removedTab = this.tabNames.splice(index, 1)[0];
        delete this.tabContents[removedTab];
        this.dispatchEvent(new CustomEvent("deleted", { detail: { index, name: removedTab } }));
        this.updateTabs();
    }

    addNewTab() {
        const name = `Tab-${this.tabNames.length}`;
        const content = document.createElement("div");
        const timeString = new Date().toLocaleTimeString();
        content.innerHTML = `<p>${timeString}</p>`;
        this.addTab(name, content);
    }

    addTab(name, content) {
        if (!name) return;
        const index = this.tabNames.length;
        this.tabNames.push(name);
        this.tabContents[name] = content;
        this.dispatchEvent(new CustomEvent("new_tab", { detail: { index, name } }));
        this.updateTabs();
        this.showTab(index);
    }

    renameTab(index) {
        const newName = prompt("Enter new tab name:", this.tabNames[index]);
        if (newName && !this.tabNames.includes(newName)) {
            const oldName = this.tabNames[index];
            this.tabNames[index] = newName;
            this.tabContents[newName] = this.tabContents[oldName];
            delete this.tabContents[oldName];
            this.dispatchEvent(new CustomEvent("renamed", { detail: { index, oldName, newName } }));
            this.updateTabs();
        }
    }

    getTabContents(tabName) {
        return this.tabContents[tabName] || null;
    }
}

/*if (!customElements.get("tabs-component")) {
    customElements.define("tabs-component", QuickJS_TabsComponent);
}*/

class QuickJS_TwoColumnCheckboxList extends HTMLElement {
    constructor() {
        super();
        this.data = [];
        this.componentId = this.getAttribute("id") || "";
    }

    connectedCallback() {
        this.render();
    }

    set_data(items) {
        this.data = items;
        this.render();
    }
    setItems(prefix, count) {
        this.data = Array.from({ length: count }, (_, i) => `${prefix} ${i + 1}`);
        this.render();
    }

    getCheckedItems() {
        return Array.from(this.querySelectorAll("input[type=checkbox]:checked"))
            .map(cb => cb.nextSibling.textContent.trim());
    }

    getAllItems() {
        return this.data;
    }

    render() {
        this.innerHTML = "";
        const container = document.createElement("div");
        container.classList.add("checkbox-rows-container","row", "g-3");

        const col1 = document.createElement("div");
        col1.classList.add("col-6","checkbox-col");
        const col2 = document.createElement("div");
        col2.classList.add("col-6","checkbox-col");

        this.data.forEach((item, index) => {
            const row = document.createElement("div");
            row.classList.add("form-check","checkbox-row");

            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            //checkbox.classList.add("xxform-check-input");
            checkbox.addEventListener("change", () => {
                this.dispatchEvent(new CustomEvent("clicked", {
                    detail: { text: item, checked: checkbox.checked }
                }));
            });

            const label = document.createElement("label");
            label.textContent = item;
            label.classList.add("form-check-label", "ms-2");//, "checkbox-label");
            row.addEventListener("click", () => {
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event("change"));
            });



            row.appendChild(checkbox);
            row.appendChild(label);

            if (index % 2 === 0) {
                col1.appendChild(row);
            } else {
                col2.appendChild(row);
            }
        });

        container.appendChild(col1);
        container.appendChild(col2);
        this.appendChild(container);
    }
}

if (!customElements.get("two-column-checkbox-list")) {
    customElements.define("two-column-checkbox-list", QuickJS_TwoColumnCheckboxList);
}


