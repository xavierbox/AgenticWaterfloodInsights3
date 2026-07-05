

class QuickJS_ThreeColLayout extends HTMLElement {
  _renderedTabs;

  constructor() {
    super();
 
    this._savedWidths = null;
      
  }
    
  get_column(name){
    if(name === "left") return this.querySelector(".qsthree-col-layout-col1");
    if(name === "middle") return this.querySelector(".qsthree-col-layout-col2");
    if(name === "right") return this.querySelector(".qsthree-col-layout-col3");
    return null;
  }
    
  get_top_bar(){
      
      return this.querySelector(".layout-top-bar");
      
  }
    
  getTemplate() {
    return `
<div class="layout-top-bar" style="
  height:20px;
  background:transparent;
  display:flex;
  align-items:stretch;
  margin:0;
  padding:0;
  border-top:1px solid grey;
  border-bottom:1px solid grey;

">
  <button 
    class="layout-hide-left-button" 
    name="toggle-left"
    style="
      height:100%;
      width:20px;
      margin:0;
      padding:0;
      border:none;
      background:transparent;
      line-height:1;
      font-size:14px;
      display:flex;
      align-items:center;
      justify-content:center;
    "
  >◀</button>

</div>

      <div class="qsthree-col-layout-main">
        <!-- Column 1 -->
        <div style="overflow-y:hidden;" class="qsthree-col-layout-column qsthree-col-layout-col1" id="left">
          
          <div style="max-height:100%; flex:0 0 50%;" id="left-top">Left Top</div>
          <div class="qsthree-col-layout-horizontal-resizer" id="horizontalResizerTop"></div>

          <!-- middle panel here with its own resizer -->
          <div style="max-height:100%; flex:0 0 25%;" id="left-middle">Left Middle</div>
          <div class="qsthree-col-layout-horizontal-resizer" id="horizontalResizerBottom"></div>

          <div style="max-height:100%; flex:0 0 25%;" id="left-bottom">Left Bottom</div>
        </div>

        <div class="qsthree-col-layout-vertical-resizer" id="vResizer1"></div>

        <!-- Column 2 -->
        <div class="qsthree-col-layout-column qsthree-col-layout-col2" id="middle">
          <div class="qsthree-col-layout-content">Center</div>
        </div>

        <div class="qsthree-col-layout-vertical-resizer" id="vResizer2"></div>

        <!-- Column 3 -->
        <div class="qsthree-col-layout-column qsthree-col-layout-col3" id="right">
          <div class="qsthree-col-layout-content">Right</div>
        </div>
      </div>
    `;
  }

  connectedCallback() {
    this.render();
    this.setup();

    const threeSplit = false;
      if (!threeSplit) {
        // 1. Hide middle pane and its resizer
        this.querySelector('#left-middle')?.classList.add('hidden');
        this.querySelector('#horizontalResizerBottom')?.classList.add('hidden');

        // 2. Expand remaining panes to fill 100% of the space evenly
        this.querySelector('#left-top').style.flex = "0 0 68%";
        this.querySelector('#left-bottom').style.flex = "0 0 32%";

        // 3. Connect the top resizer directly between top and bottom panes
        this.setupHorizontalResizer(
          this.querySelector("#horizontalResizerTop"),
          this.querySelector("#left-top"),
          this.querySelector("#left-bottom")
        );
      } 
      
      
      
      
      
      
  }

  render() {
    this.innerHTML = this.getTemplate();
  }

  setupVerticalResizer(resizer, leftEl, rightEl) {
    let isDragging = false;

    resizer.addEventListener("mousedown", (e) => {
      isDragging = true;
      document.body.classList.add("qsthree-col-layout-resizing");

      const container = resizer.parentElement;
      const startX = e.clientX;
      const startLeftWidth = leftEl.getBoundingClientRect().width;
      const startRightWidth = rightEl.getBoundingClientRect().width;
      const containerWidth = container.clientWidth;

      function onMouseMove(e) {
        if (!isDragging) return;

        const dx = e.clientX - startX;
        let newLeftWidth = startLeftWidth + dx;
        let newRightWidth = startRightWidth - dx;

        if (newLeftWidth < 50 || newRightWidth < 50) return;

        const newLeftPercent = (newLeftWidth / containerWidth) * 100;
        const newRightPercent = (newRightWidth / containerWidth) * 100;

        leftEl.style.width = `${newLeftPercent}%`;
        rightEl.style.width = `${newRightPercent}%`;
      }

      function onMouseUp() {
        isDragging = false;
        document.body.classList.remove("qsthree-col-layout-resizing");
        window.removeEventListener("mousemove", onMouseMove);
        window.removeEventListener("mouseup", onMouseUp);

        [leftEl, rightEl].forEach((el) => {
          resizer.dispatchEvent(
            new CustomEvent("pane-resized", {
              detail: {
                id: el.id,
                offsetWidth: el.offsetWidth,
                offsetHeight: el.offsetHeight,
              },
              bubbles: true,
              composed: true,
            })
          );
        });
      }

      window.addEventListener("mousemove", onMouseMove);
      window.addEventListener("mouseup", onMouseUp);
    });
  }

  setupHorizontalResizer(resizer, topEl, bottomEl) {
    let isDragging = false;

    resizer.addEventListener("mousedown", (e) => {
      isDragging = true;
      document.body.classList.add("qsthree-col-layout-resizing");

      const container = topEl.parentElement;
      const startY = e.clientY;
      const startTopHeight = topEl.getBoundingClientRect().height;
      const startBottomHeight = bottomEl.getBoundingClientRect().height;
      const containerHeight = container.clientHeight;

      function onMouseMove(e) {
        if (!isDragging) return;

        const dy = e.clientY - startY;
        let newTopHeight = startTopHeight + dy;
        let newBottomHeight = startBottomHeight - dy;

        if (newTopHeight < 50 || newBottomHeight < 50) return;

        const newTopPercent = (newTopHeight / containerHeight) * 100;
        const newBottomPercent = (newBottomHeight / containerHeight) * 100;

        topEl.style.flex = `0 0 ${newTopPercent}%`;
        bottomEl.style.flex = `0 0 ${newBottomPercent}%`;
      }

      function onMouseUp() {
        isDragging = false;
        document.body.classList.remove("qsthree-col-layout-resizing");
        window.removeEventListener("mousemove", onMouseMove);
        window.removeEventListener("mouseup", onMouseUp);

        [topEl, bottomEl].forEach((el) => {
          resizer.dispatchEvent(
            new CustomEvent("pane-resized", {
              detail: {
                id: el.id,
                offsetWidth: el.offsetWidth,
                offsetHeight: el.offsetHeight,
              },
              bubbles: true,
              composed: true,
            })
          );
        });
      }

      window.addEventListener("mousemove", onMouseMove);
      window.addEventListener("mouseup", onMouseUp);
    });
  }

  setup() {
      this.querySelector(".layout-hide-left-button").addEventListener("click", () => {

  const left = this.get_column("left");
  const middle = this.get_column("middle");
  const right = this.get_column("right");

  const container = left.parentElement;
  const containerWidth = container.clientWidth;

  if (!left.classList.contains("hidden")) {

    // --- HIDE LEFT ---
    this.querySelector("#vResizer1").classList.add("hidden");

    const lw = left.offsetWidth;
    const mw = middle.offsetWidth;
    const rw = right.offsetWidth;

    this._savedWidths = { lw, mw, rw };

    const remaining = mw + rw;

    const middlePercent = (mw / remaining) * 100;
    const rightPercent = (rw / remaining) * 100;

    left.classList.add("hidden");

    middle.style.width = `${middlePercent}%`;
    right.style.width = `${rightPercent}%`;

  } else {

this.querySelector("#vResizer1").classList.remove("hidden");
    // --- SHOW LEFT ---
    left.classList.remove("hidden");

    if (this._savedWidths) {
      const { lw, mw, rw } = this._savedWidths;
      const total = lw + mw + rw;

      left.style.width = `${(lw / total) * 100}%`;
      middle.style.width = `${(mw / total) * 100}%`;
      right.style.width = `${(rw / total) * 100}%`;
    }
  }

  this.querySelector(".layout-hide-left-button").innerHTML =
    left.classList.contains("hidden") ? "▶" : "◀";

          
  // emit resize event
  [left, middle, right].forEach((el) => {
    el.dispatchEvent(
      new CustomEvent("pane-resized", {
        detail: {
          id: el.id,
          offsetWidth: el.offsetWidth,
          offsetHeight: el.offsetHeight,
        },
        bubbles: true,
        composed: true,
      })
    );
  });

          
          
          
});
      
   
      
      
      
    this.setupVerticalResizer(
      this.querySelector("#vResizer1"),
      this.querySelector(".qsthree-col-layout-col1"),
      this.querySelector("#middle")
    );

    this.setupVerticalResizer(
      this.querySelector("#vResizer2"),
      this.querySelector("#middle"),
      this.querySelector("#right")
    );

    this.setupHorizontalResizer(
      this.querySelector("#horizontalResizerTop"),
      this.querySelector("#left-top"),
      this.querySelector("#left-middle")
    );

    this.setupHorizontalResizer(
      this.querySelector("#horizontalResizerBottom"),
      this.querySelector("#left-middle"),
      this.querySelector("#left-bottom")
    );
  }

  set(where, content) {
    const validPanes = [
      "left-top",
      "left-middle",
      "left-bottom",
      "middle",
      "right",
      "middle-top",
      "middle-bottom",
      "right-top",
      "right-bottom",
    ];

    if (validPanes.includes(where)) {
      if (where === "middle-top") where = "middle";
      if (where === "right-top") where = "right";

      const pane = this.querySelector(`#${where}`);

      if (typeof content === "string") {
        pane.innerHTML = content;
      } else if (content instanceof HTMLElement) {
        pane.innerHTML = "";
        pane.appendChild(content);
      } else {
        console.error("Content must be a string or an HTML element");
      }
    } else {
      console.error("Invalid pane ID");
    }
  }

  clear(where) {
    const validPanes = [
      "left-top",
      "left-middle",
      "left-bottom",
      "middle",
      "right",
      "middle-top",
      "middle-bottom",
      "right-top",
      "right-bottom",
    ];

    if (validPanes.includes(where)) {
      if (where === "middle-top") where = "middle";
      if (where === "right-top") where = "right";

      this.querySelector(`#${where}`).innerHTML = "";
    }
  }

  append(where, content) {
    const validPanes = [
      "left-top",
      "left-middle",
      "left-bottom",
      "middle",
      "right",
      "middle-top",
      "middle-bottom",
      "right-top",
      "right-bottom",
    ];

    if (validPanes.includes(where)) {
      if (where === "middle-top") where = "middle";
      if (where === "right-top") where = "right";

      if (content instanceof HTMLElement) {
        this.querySelector(`#${where}`).appendChild(content);
      } else {
        console.error("Content must be an HTML element");
      }
    } else {
      console.error("Invalid pane ID");
    }
  }

  get_pane(id) {
    const validPanes = [
      "left-top",
      "left-middle",
      "left-bottom",
      "middle",
      "right",
      "middle-top",
      "middle-bottom",
      "right-top",
      "right-bottom",
    ];

    let where = id;

    if (validPanes.includes(id)) {
      if (where === "middle-top") where = "middle";
      if (where === "right-top") where = "right";

      return this.querySelector(`#${where}`);
    } else {
      console.error(
        `Invalid pane ID "${id}". Valid IDs are: ${validPanes.join(", ")}`
      );
      return null;
    }
  }
}

if(!customElements.get('new-three-column-main-layout')){
  customElements.define("new-three-column-main-layout", QuickJS_ThreeColLayout);
}

















class __OLD__QuickJS_ThreeColLayout extends HTMLElement{
    _renderedTabs
    constructor(){

      super();
      this._renderedTabs = new Set();
    }

    getTemplate(){
   
    return `
      <div class="qsthree-col-layout-main">
        <!-- Column 1 -->
        <div style='overflow-y:hidden;'  class="qsthree-col-layout-column qsthree-col-layout-col1" id="left">
          <div style= 'max-height: 100%;flex-basis: 75%;' id="left-top">Left Top</div>
          <div class="qsthree-col-layout-horizontal-resizer" id="horizontalResizer"></div>

          <! middle panel here with its own resizer -->
   



          <div style='max-height: 100%;flex-basis: 25%;'id="left-bottom">Left Bottom</div>
        </div>
        <div class="qsthree-col-layout-vertical-resizer" id="vResizer1"></div>

        <!-- Column 2 -->
        <div class="qsthree-col-layout-column qsthree-col-layout-col2" id="middle">
          <div class="qsthree-col-layout-content">Center</div>
        </div>
        <div class="qsthree-col-layout-vertical-resizer" id="vResizer2"></div>

        <!-- Column 3 -->
        <div class="qsthree-col-layout-column qsthree-col-layout-col3" id="right">
          <div class="qsthree-col-layout-content">Right</div>
        </div>
      </div>
      `;
    }

    connectedCallback(){

      this.render();

      this.setup();
    }

    render(){

      this.innerHTML = this.getTemplate();

    }

    setupVerticalResizer(resizer, leftEl, rightEl) {
      let isDragging = false;

      resizer.addEventListener('mousedown', (e) => {
        isDragging = true;
        document.body.classList.add('qsthree-col-layout-resizing');

        const container = resizer.parentElement;
        const startX = e.clientX;
        const startLeftWidth = leftEl.getBoundingClientRect().width;
        const startRightWidth = rightEl.getBoundingClientRect().width;
        const containerWidth = container.clientWidth;

        function onMouseMove(e) {
          if (!isDragging) return;

          const dx = e.clientX - startX;
          let newLeftWidth = startLeftWidth + dx;
          let newRightWidth = startRightWidth - dx;

          if (newLeftWidth < 50 || newRightWidth < 50) return;

          const newLeftPercent = (newLeftWidth / containerWidth) * 100;
          const newRightPercent = (newRightWidth / containerWidth) * 100;

          leftEl.style.width = `${newLeftPercent}%`;
          rightEl.style.width = `${newRightPercent}%`;
        }

        function onMouseUp() {
          isDragging = false;
          document.body.classList.remove('qsthree-col-layout-resizing');
          window.removeEventListener('mousemove', onMouseMove);
          window.removeEventListener('mouseup', onMouseUp);

          // Emit custom event
          const event = new CustomEvent('pane-resized', {
            detail: {
              id: leftEl.id,
              offsetWidth: leftEl.offsetWidth,
              offsetHeight: leftEl.offsetHeight
            },
            bubbles: true,
            composed: true
          });
          resizer.dispatchEvent(event);



          // Emit custom event
          const event2 = new CustomEvent('pane-resized', {
            detail: {
              id:  rightEl.id,
              offsetWidth: rightEl.offsetWidth,
              offsetHeight: rightEl.offsetHeight

            },
            bubbles: true,
            composed: true
          });
          resizer.dispatchEvent(event2);



        }

        window.addEventListener('mousemove', onMouseMove);
        window.addEventListener('mouseup', onMouseUp);




      });
    }

    setupHorizontalResizer(resizer, topEl, bottomEl) {
      let isDragging = false;

      resizer.addEventListener('mousedown', (e) => {
        isDragging = true;
        document.body.classList.add('qsthree-col-layout-resizing');

        const container = topEl.parentElement;
        const startY = e.clientY;
        const startTopHeight = topEl.getBoundingClientRect().height;
        const startBottomHeight = bottomEl.getBoundingClientRect().height;
        const containerHeight = container.clientHeight;

        function onMouseMove(e) {
          if (!isDragging) return;

          const dy = e.clientY - startY;
          let newTopHeight = startTopHeight + dy;
          let newBottomHeight = startBottomHeight - dy;

          if (newTopHeight < 50 || newBottomHeight < 50) return;

          const newTopPercent = (newTopHeight / containerHeight) * 100;
          const newBottomPercent = 100 - newTopPercent;

          topEl.style.flex = '0 0 ' + newTopPercent + '%';
          bottomEl.style.flex = '0 0 ' + newBottomPercent + '%';
        }

        function onMouseUp() {
          isDragging = false;
          document.body.classList.remove('qsthree-col-layout-resizing');
          window.removeEventListener('mousemove', onMouseMove);
          window.removeEventListener('mouseup', onMouseUp);

          // Emit custom event
          const event = new CustomEvent('pane-resized', {
            detail: {
              id: topEl.id,
              offsetWidth: topEl.offsetWidth,
              offsetHeight: topEl.offsetHeight
              
            },
            bubbles: true,
            composed: true
          });
          resizer.dispatchEvent(event);


          // Emit custom event
          const event2 = new CustomEvent('pane-resized', {
            detail: {
              id:   bottomEl.id,
              offsetWidth: bottomEl.offsetWidth,
              offsetHeight: bottomEl.offsetHeight
            },
            bubbles: true,
            composed: true
          });
          resizer.dispatchEvent(event2);
          

        }

        window.addEventListener('mousemove', onMouseMove);
        window.addEventListener('mouseup', onMouseUp);
      });
    }

    setup(){
    // Init vertical resizers
    this.setupVerticalResizer(
      this.querySelector('#vResizer1'),
      this.querySelector('.qsthree-col-layout-col1'),
      this.querySelector('#middle')
    );

    this.setupVerticalResizer(
      this.querySelector('#vResizer2'),
      this.querySelector('#middle'),
      this.querySelector('#right')
    );

    // Init horizontal resizer
    this.setupHorizontalResizer(
      this.querySelector('#horizontalResizer'),
      this.querySelector('#left-top'),
      this.querySelector('#left-bottom')
    );

    }
  
  
    set(where, content) {


        
 
        const validPanes = ['left-top', 'left-bottom','middle', 'right', 'middle-top', 'middle-bottom', 'right-top', 'right-bottom']; 


        // Check if 'where' is valid
        if (validPanes.includes(where)) {
          if( where == 'middle-top') where = 'middle';
            if( where == 'right-top') where = 'right';
            

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
      //const validPanes = ['left-top', 'left-bottom','middle', 'right'];
      const validPanes = ['left-top', 'left-bottom','middle', 'right', 'middle-top', 'middle-bottom', 'right-top', 'right-bottom']; 
  
        // Check if 'where' is valid
        if (validPanes.includes(where)) {
          if( where == 'middle-top') where = 'middle';
            if( where == 'right-top') where = 'right';
            


            const pane = this.querySelector(`#${where}`);
            pane.innerHTML = ''; // Clear existing content
        }


    }
    append(where, content) {
      //const validPanes = ['left-top', 'left-bottom','middle', 'right'];
      const validPanes = ['left-top', 'left-bottom','middle', 'right', 'middle-top', 'middle-bottom', 'right-top', 'right-bottom']; 
    
        // Check if 'where' is valid
        if (validPanes.includes(where)) {
          if( where == 'middle-top') where = 'middle';
            if( where == 'right-top') where = 'right';
            

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
    get_pane(id) {
       // const validPanes = ['left-top', 'left-bottom',
       //     'middle',  'right'
       // ];
        const validPanes = ['left-top', 'left-bottom','middle', 'right', 'middle-top', 'middle-bottom', 'right-top', 'right-bottom']; 
        let where = id; 
        // Check if 'where' is valid
        if (validPanes.includes(id)) {

            if( where == 'middle-top') where = 'middle';
            if( where == 'right-top') where = 'right';
            

            const pane = this.querySelector(`#${where}`);
            return pane;
        }else {
        console.error(`Invalid pane ID "${id}". Valid IDs are: ${validPanes.join(', ')}`);
        return null;
            }

    }


  }
  customElements.define("old-new-three-column-main-layout", __OLD__QuickJS_ThreeColLayout);


