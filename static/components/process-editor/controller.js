(() => {
    const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

    const loopMembers = (root) => [...root.querySelectorAll('.graph-node')].filter(node =>
      (root.loopNodeIds ? root.loopNodeIds.has(node.dataset.node) : !node.dataset.node?.startsWith('added-'))
      && !node.classList.contains('placement-ghost')
      && !['start', 'wait', 'end'].includes(node.dataset.node));
    function updateLoopBounds(root) {
      const nodes = loopMembers(root);
      const box = root.querySelector('.loop-box');
      if (!box || !nodes.length) return;
      const contentPadding = 14;
      const stage = box.querySelector('.loop-stage');
      const stageStyle = getComputedStyle(stage);
      const boxStyle = getComputedStyle(box);
      const topInset = parseFloat(stageStyle.top) + parseFloat(boxStyle.borderTopWidth);
      const bottomInset = parseFloat(stageStyle.bottom) + parseFloat(boxStyle.borderBottomWidth);
      const left = Math.min(...nodes.map(node => node.offsetLeft)) - 22;
      const top = Math.min(...nodes.map(node => node.offsetTop)) - topInset - contentPadding;
      const right = Math.max(...nodes.map(node => node.offsetLeft + node.offsetWidth)) + 22;
      const bottom = Math.max(...nodes.map(node => node.offsetTop + node.offsetHeight)) + bottomInset + contentPadding;
      Object.assign(box.style, { left: `${left}px`, top: `${top}px`, width: `${right-left}px`, height: `${bottom-top}px` });
    }

    const graphConnections = [
      ['start', 0, 'wait', 0],
      ['wait', 1, 'nav-grasp', 0],
      ['wait', 1, 'pose', 0],
      ['wait', 1, 'grasp', 0],
      ['nav-grasp', 1, 'human-1', 0],
      ['pose', 1, 'human-1', 0],
      ['human-1', 1, 'human-2', 0],
      ['human-2', 1, 'nav-place-1', 0],
      ['grasp', 1, 'scan', 0],
      ['scan', 1, 'condition', 0],
      ['condition', 1, 'nav-place-2', 0],
      ['nav-place-1', 1, 'place', 0],
      ['nav-place-2', 1, 'place', 0],
      ['place', 1, 'human-3', 0],
      ['place', 2, 'continue', 0],
      ['human-3', 1, 'end', 0],
      ['continue', 1, 'end', 0],
    ];

    function renderGraphEdges(root) {
      root.alignWorkflowPorts?.();
      root.querySelectorAll('.graph-node').forEach(node=>{
        const ports=node.querySelectorAll(':scope > .port');
        node.querySelectorAll('.node-hover-actions [data-port-index]').forEach(button=>{
          const port=ports[Number(button.dataset.portIndex)];
          if(!port)return;
          button.style.top=`${port.offsetTop+port.offsetHeight/2}px`;
          button.style.left=`${port.offsetLeft+port.offsetWidth/2}px`;
          button.style.right='auto';
          button.style.transform='translate(-50%, -50%)';
        });
      });
      root.querySelectorAll('.graph-node').forEach(node=>node.classList.toggle('flow-hidden',(root.hiddenFlows||[]).includes(node.dataset.flowId||'main')));
      root.querySelectorAll('.loop-box').forEach(box=>box.classList.toggle('flow-hidden',(root.hiddenFlows||[]).includes(box.dataset.flowId||'main')));
      updateLoopBounds(root);
      const layer = root.querySelector('.edge-layer');
      if (!layer) return;
      layer.querySelectorAll('.edge, .edge-interaction').forEach((edge) => edge.remove());

      const portPoint = (nodeName, portIndex) => {
        const node = root.querySelector(`.graph-node[data-node="${nodeName}"]`);
        const port = node?.querySelectorAll('.port')[portIndex];
        if (!node || !port || node.classList.contains('flow-hidden')) return null;
        const rect = port.getBoundingClientRect();
        const matrix=layer.getScreenCTM();
        if(matrix){
          const point=new DOMPoint(rect.left+rect.width/2,rect.top+rect.height/2).matrixTransform(matrix.inverse());
          return {x:point.x,y:point.y};
        }
        const sceneRect = node.closest('.scene').getBoundingClientRect();
        const scale = Number(node.closest('.canvas-stage').dataset.zoom || 1);
        return {
          x: (rect.left + rect.width / 2 - sceneRect.left) / scale,
          y: (rect.top + rect.height / 2 - sceneRect.top) / scale,
        };
      };

      let currentConnection;
      const appendPath = (d, withArrow = true) => {
        const insertionConnection=[...currentConnection];
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('class', withArrow ? 'edge' : 'edge edge--branch');
        path.setAttribute('d', d);
        layer.append(path);
        const ns = 'http://www.w3.org/2000/svg';
        const group = document.createElementNS(ns, 'g');
        group.setAttribute('class', 'edge-interaction');
        const hit = document.createElementNS(ns, 'path');
        hit.setAttribute('d', d); hit.setAttribute('class', 'edge-hit');
        const point = path.getPointAtLength(path.getTotalLength()/2);
        const add = document.createElementNS(ns, 'g');
        add.setAttribute('class', 'edge-add');
        add.setAttribute('transform', `translate(${point.x},${point.y})`);
        add.setAttribute('role','button'); add.setAttribute('aria-label','在连线中添加节点'); add.setAttribute('tabindex','0');
        add.innerHTML = '<circle r="9"/><path d="M-5 0H5M0-5V5"/>';
        group.append(hit,add);
        // Keep the visible path last for branch styling below.
        layer.insertBefore(group,path);
        group.addEventListener('pointerdown', event => event.stopPropagation());
        add.addEventListener('click', event => {
          event.stopPropagation();
          root.insertionConnection=insertionConnection;
          root.querySelector('[data-action="add"]')?.dispatchEvent(new CustomEvent('click', {
            detail: { anchor: add.getBoundingClientRect() }
          }));
        });
        add.addEventListener('keydown', event => { if(event.key==='Enter'||event.key===' '){event.preventDefault();add.dispatchEvent(new MouseEvent('click',{bubbles:true}));} });
      };

      // Route each connection independently so moving a node backwards remains valid.
      const connections = root.baseConnections ? [...root.baseConnections] : root.querySelector('process-flow-canvas[variant="basic"]')
        ? [['start', 0, 'split', 0], ['split', 1, 'sample', 0], ['sample', 1, 'review', 0], ['review', 1, 'accept', 0], ['accept', 1, 'condition', 0], ['condition', 1, 'internal', 0], ['internal', 1, 'end', 0], ['condition', 2, 'end', 0]] : [...graphConnections];
      connections.push(...(root.customConnections || []).filter(([source,,target]) =>
        root.querySelector(`[data-node="${source}"]`) && root.querySelector(`[data-node="${target}"]`)));
      if(root.querySelector('process-flow-canvas[variant="initial"]'))connections.unshift(['start',0,'end',0]);
      root.layoutConnections=connections.filter(item=>!(root.removedConnections||[]).some(removed=>JSON.stringify(item)===JSON.stringify(removed)));
      connections.forEach(([source, sourcePort, target, targetPort]) => {
        currentConnection=[source,sourcePort,target,targetPort];
        if((root.removedConnections||[]).some(item=>JSON.stringify(item)===JSON.stringify(currentConnection)))return;
        const from = portPoint(source, sourcePort), to = portPoint(target, targetPort);
        if (!from || !to) return;
        if(source==='save'&&target==='order'&&root.loopNodeIds){
          const area=root.querySelector('.loop-box');
          const matrix=layer.getScreenCTM();
          if(area&&matrix){
            const rect=area.getBoundingClientRect();
            const topLeft=new DOMPoint(rect.left,rect.top).matrixTransform(matrix.inverse());
            const bottomLeft=new DOMPoint(rect.left,rect.bottom).matrixTransform(matrix.inverse());
            to.x=topLeft.x;to.y=Math.max(topLeft.y+48,Math.min(bottomLeft.y-20,from.y));
            let port=area.querySelector('.loop-entry-port');
            if(!port){port=document.createElement('span');port.className='port loop-entry-port';area.append(port);}
            port.style.left='-4px';port.style.top=`${to.y-topLeft.y-4}px`;
          }
        }
        // Without arrowheads, connect directly to the input port center.
        if (root.routeWorkflowEdge) {
          appendPath(root.routeWorkflowEdge(from, to, currentConnection));
          return;
        }
        if (root.loopNodeIds && source === 'continue' && target === 'next') {
          const y = Math.min(...loopMembers(root).map(node => node.offsetTop)) - 12;
          appendPath(`M ${from.x} ${from.y} H ${from.x+20} V ${y} H ${to.x-16} V ${to.y} H ${to.x}`);
          return;
        }
        if (source === 'condition' && sourcePort === 2) {
          const bottom = Math.max(from.y, to.y) + 85;
          const middle=(from.x+to.x)/2;
          const bend=Math.max(24,Math.abs(to.x-from.x)*.28);
          appendPath(`M ${from.x} ${from.y}
            C ${from.x+bend} ${from.y}, ${middle-bend} ${bottom}, ${middle} ${bottom}
            C ${middle+bend} ${bottom}, ${to.x-bend} ${to.y}, ${to.x} ${to.y}`);
          layer.lastElementChild.style.strokeDasharray = '5 4';
          return;
        }
        const horizontalGap = to.x - from.x;
        if (horizontalGap > 0) {
          const bend=horizontalGap/2;
          appendPath(`M ${from.x} ${from.y} C ${from.x+bend} ${from.y}, ${to.x-bend} ${to.y}, ${to.x} ${to.y}`);
          return;
        }
        // Forward edges must keep their controls inside the available gap.
        // A fixed minimum bends short connections back on themselves.
        const bend = horizontalGap >= 0
          ? horizontalGap / 2
          : Math.max(32, Math.abs(horizontalGap) / 2);
        appendPath(`M ${from.x} ${from.y} C ${from.x+bend} ${from.y}, ${to.x-bend} ${to.y}, ${to.x} ${to.y}`);
      });
      root.querySelectorAll('.graph-node').forEach(node => {
        const connected = connections.some(([source,,target]) =>
          (source === node.dataset.node || target === node.dataset.node) &&
          root.querySelector(`.graph-node[data-node="${source}"]`) && root.querySelector(`.graph-node[data-node="${target}"]`));
        node.classList.toggle('has-connections', connected);
        node.querySelectorAll('.port').forEach((port,index)=>{
          if(!port.style.right)return;
          const used=root.layoutConnections.some(([source,sourcePort,target,targetPort])=>
            (source===node.dataset.node&&sourcePort===index || target===node.dataset.node&&targetPort===index) &&
            root.querySelector(`.graph-node[data-node="${source}"]`) && root.querySelector(`.graph-node[data-node="${target}"]`));
          port.style.visibility=used?'':'hidden';
        });
      });
      // SVG paints in DOM order: keep all interactive plus buttons above edges.
      layer.querySelectorAll('.edge-interaction').forEach(group => layer.append(group));
    }

    function updateCanvasTransform(canvas, zoomText) {
      const scale = Number(canvas.dataset.zoom || '1');
      const panX = Number(canvas.dataset.panX || '0');
      const panY = Number(canvas.dataset.panY || '0');
      canvas.style.setProperty('--scene-scale', scale.toFixed(3));
      canvas.style.setProperty('--scene-x', `${panX.toFixed(1)}px`);
      canvas.style.setProperty('--scene-y', `${panY.toFixed(1)}px`);
      if (zoomText) zoomText.textContent = `${Math.round(scale * 100)}%`;
    }

    function zoomCanvas(canvas, zoomText, nextScale, anchorX, anchorY) {
      const currentScale = Number(canvas.dataset.zoom || '1');
      const scale = clamp(nextScale, 0.35, 1.75);
      const rect = canvas.getBoundingClientRect();
      const localX = anchorX - rect.left;
      const localY = anchorY - rect.top;
      const panX = Number(canvas.dataset.panX || '0');
      const panY = Number(canvas.dataset.panY || '0');
      const worldX = (localX - panX) / currentScale;
      const worldY = (localY - panY) / currentScale;
      const nextPanX = localX - worldX * scale;
      const nextPanY = localY - worldY * scale;
      canvas.dataset.zoom = String(scale);
      canvas.dataset.panX = String(nextPanX);
      canvas.dataset.panY = String(nextPanY);
      updateCanvasTransform(canvas, zoomText);
    }

    function fitCanvas(canvas, zoomText, fixedScale) {
      const root = canvas.closest(".process-editor-components");
      const rect = canvas.getBoundingClientRect();
      updateLoopBounds(root);
      const items = [...canvas.querySelectorAll('.graph-node, .loop-box')];
      const left = Math.min(...items.map(node => node.offsetLeft));
      const top = Math.min(...items.map(node => node.offsetTop));
      const contentWidth = Math.max(...items.map(node => node.offsetLeft + node.offsetWidth)) - left;
      const contentHeight = Math.max(...items.map(node => node.offsetTop + node.offsetHeight)) - top;
      const scale = fixedScale ?? Math.min(1, (rect.width-48)/contentWidth, (rect.height-48)/contentHeight);
      const panX = (rect.width-contentWidth*scale)/2-left*scale;
      const panY = (rect.height-contentHeight*scale)/2-top*scale;
      canvas.dataset.zoom = String(scale);
      canvas.dataset.panX = String(panX);
      canvas.dataset.panY = String(panY);
      updateCanvasTransform(canvas, zoomText);
    }

    function initializeEditor(root) {
      root.addEventListener('flow-visibility-change',event=>{root.hiddenFlows=event.detail.hidden;renderGraphEdges(root);});
      const canvas = root.querySelector('.canvas-stage');
      const zoomText = root.querySelector('.zoom-text');
      const zoomMinus = root.querySelector('[data-action="zoom-out"]');
      const zoomPlus = root.querySelector('[data-action="zoom-in"]');
      const fitBtn = root.querySelector('[data-action="fit"]');
      const handBtn = root.querySelector('[data-action="hand"]');
      const selectBtn = root.querySelector('.tool-btn[title="选择"]');
      const toast = root.querySelector('.toast');
      const searchInput = root.querySelector('search-input');
      const undoBtn = root.querySelector('[data-action="undo"]');
      const redoBtn = root.querySelector('[data-action="redo"]');

      if (!canvas) return;

      document.addEventListener('pointerdown', event => {
        if (event.button !== 0 || event.target.closest('process-node-properties, .right-panel, .graph-node')) return;
        root.querySelectorAll('process-node-properties .right-panel').forEach(panel => {
          panel.style.display = 'none';
        });
      }, true);

      requestAnimationFrame(() => renderGraphEdges(root));

      let toastTimer;
      const notify = (message) => {
        if (!toast) return;
        toast.textContent = message;
        toast.classList.add('is-visible');
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => toast.classList.remove('is-visible'), 1800);
      };

      const snapshot = () => ({
        removedConnections:(root.removedConnections||[]).map(item=>[...item]),
        connections: (root.customConnections || []).map(connection => [...connection]),
        nodes: [...root.querySelectorAll('.graph-node:not(.placement-ghost)')].map(node => ({id: node.dataset.node, x: node.offsetLeft, y: node.offsetTop, html: node.outerHTML})),
      });
      const history = { past: [], future: [] };
      const record = () => {
        const current = snapshot();
        const previous = history.past[history.past.length - 1];
        if (previous && JSON.stringify(previous) === JSON.stringify(current)) return;
        history.past.push(current);
        history.future = [];
        updateHistoryButtons();
      };
      const restore = (state) => {
        root.removedConnections=(state.removedConnections||[]).map(item=>[...item]);
        root.customConnections = (state.connections || []).map(connection => [...connection]);
        root.querySelectorAll('.graph-node').forEach(node => { if (!state.nodes.some(saved => saved.id === node.dataset.node)) node.remove(); });
        state.nodes.forEach(saved => {
          let node = root.querySelector(`[data-node="${saved.id}"]`);
          if (!node) { canvas.querySelector('.scene').insertAdjacentHTML('beforeend', saved.html); node = root.querySelector(`[data-node="${saved.id}"]`); }
          node.style.left = `${saved.x}px`; node.style.top = `${saved.y}px`;
        });
        renderGraphEdges(root);
      };
      const updateHistoryButtons = () => {
        if (undoBtn) undoBtn.disabled = history.past.length < 2;
        if (redoBtn) redoBtn.disabled = history.future.length === 0;
      };
      root.querySelector('[data-action="arrange"]')?.addEventListener('click',()=>{
        if(root.arrangeWorkflow){root.arrangeWorkflow();renderGraphEdges(root);fitCanvas(canvas,zoomText);record();return;}
        const nodes=[...canvas.querySelectorAll('.graph-node:not(.placement-ghost)')];
        if(!nodes.length)return;
        const byId=new Map(nodes.map(node=>[node.dataset.node,node]));
        const outgoing=new Map(nodes.map(node=>[node.dataset.node,new Set()]));
        const indegree=new Map(nodes.map(node=>[node.dataset.node,0]));
        for(const [from,,to] of root.layoutConnections||[]){
          if(from===to||!byId.has(from)||!byId.has(to)||outgoing.get(from).has(to))continue;
          outgoing.get(from).add(to);indegree.set(to,indegree.get(to)+1);
        }
        const ranks=new Map(nodes.map(node=>[node.dataset.node,0]));
        const queue=[...indegree].filter(([,degree])=>!degree).map(([id])=>id),visited=new Set();
        while(queue.length){const id=queue.shift();visited.add(id);for(const next of outgoing.get(id)){ranks.set(next,Math.max(ranks.get(next),ranks.get(id)+1));indegree.set(next,indegree.get(next)-1);if(!indegree.get(next))queue.push(next);}}
        // Keep cyclic nodes together rather than iterating indefinitely.
        const cycleRank=Math.max(...ranks.values())+1;
        nodes.forEach(node=>{if(!visited.has(node.dataset.node))ranks.set(node.dataset.node,cycleRank);});
        const columns=new Map();
        nodes.forEach(node=>{const rank=ranks.get(node.dataset.node);if(!columns.has(rank))columns.set(rank,[]);columns.get(rank).push(node);});
        const left=Math.min(...nodes.map(node=>node.offsetLeft)),top=Math.min(...nodes.map(node=>node.offsetTop));
        let x=left;
        [...columns].sort(([a],[b])=>a-b).forEach(([,items])=>{
          items.sort((a,b)=>a.offsetTop-b.offsetTop);let y=top;
          items.forEach(node=>{node.style.left=`${x}px`;node.style.top=`${y}px`;y+=node.offsetHeight+40;});
          x+=Math.max(...items.map(node=>node.offsetWidth))+62;
        });
        renderGraphEdges(root);
        fitCanvas(canvas, zoomText);
        record();
      });

      canvas.dataset.zoom = '0.7';
      canvas.dataset.panX = '30';
      canvas.dataset.panY = '260';
      updateCanvasTransform(canvas, zoomText);
      fitCanvas(canvas, zoomText, root.querySelector('process-flow-canvas[variant="current"]') ? undefined : 1);
      history.past.push(snapshot());
      updateHistoryButtons();

      const state = {
        dragging: false,
        startX: 0,
        startY: 0,
        startPanX: 0,
        startPanY: 0,
        handMode: false,
        spaceMode: false,
      };

      handBtn?.classList.remove('active');
      canvas.style.cursor = 'default';
      if(handBtn){handBtn.title='按住空格或鼠标中键拖动画布';handBtn.dataset.tooltip=handBtn.title;}
      const isInteractiveTarget = (target) => Boolean(target.closest('.tool-btn, .zoom-btn, button, a, input, textarea, select, .right-panel'));

      let nodeDrag = null;
      const clearAlignmentGuides = () => canvas.querySelectorAll('.alignment-guide').forEach(line => line.remove());
      const snapNode = (node, x, y, disabled = false) => {
        clearAlignmentGuides();
        if (disabled) return {x,y};
        const threshold = 6 / Number(canvas.dataset.zoom || 1);
        const peers = [...canvas.querySelectorAll('.graph-node:not(.placement-ghost)')].filter(peer => peer !== node);
        const best = {};
        for (const peer of peers) {
          for (const axis of ['x','y']) {
            const position = axis === 'x' ? x : y;
            const size = axis === 'x' ? node.offsetWidth : node.offsetHeight;
            const otherPosition = axis === 'x' ? peer.offsetLeft : peer.offsetTop;
            const otherSize = axis === 'x' ? peer.offsetWidth : peer.offsetHeight;
            for (const fraction of [0,0.5,1]) {
              const coordinate = otherPosition + otherSize * fraction;
              const delta = coordinate - (position + size * fraction);
              if (Math.abs(delta) <= threshold && (!best[axis] || Math.abs(delta) < Math.abs(best[axis].delta))) {
                best[axis] = {delta,coordinate,peer};
              }
            }
          }
        }
        x += best.x?.delta || 0; y += best.y?.delta || 0;
        for (const axis of ['x','y']) {
          if (!best[axis]) continue;
          const {coordinate,peer} = best[axis];
          const line = document.createElement('div'); line.className='alignment-guide';
          const vertical = axis === 'x';
          const start = Math.min(vertical ? y : x, vertical ? peer.offsetTop : peer.offsetLeft)-20;
          const end = Math.max(vertical ? y+node.offsetHeight : x+node.offsetWidth, vertical ? peer.offsetTop+peer.offsetHeight : peer.offsetLeft+peer.offsetWidth)+20;
          Object.assign(line.style, {position:'absolute',pointerEvents:'none',background:'#4285ff',zIndex:'10',
            left:`${vertical?coordinate:start}px`, top:`${vertical?start:coordinate}px`,
            width:vertical?'1px':`${end-start}px`,height:vertical?`${end-start}px`:'1px'});
          canvas.querySelector('.scene').append(line);
        }
        return {x,y};
      };
      canvas.addEventListener('pointerdown', event => {
        if (pendingNode || pendingConnection || event.target.closest('.node-hover-actions')) return;
        const node = event.target.closest('.graph-node');
        const group = event.target.closest('.loop-title');
        if (event.button !== 0 || (!node && !group) || state.spaceMode) return;
        event.preventDefault(); event.stopPropagation();
        const targets = node ? [node] : loopMembers(root);
        root.querySelectorAll('.graph-node.selected').forEach(item => item.classList.remove('selected'));
        targets.forEach(item => item.classList.add('selected'));
        nodeDrag = { pointerId: event.pointerId, x: event.clientX, y: event.clientY, scale: Number(canvas.dataset.zoom), targets: targets.map(item => ({node:item, x:item.offsetLeft, y:item.offsetTop})) };
        canvas.setPointerCapture(event.pointerId);
      }, true);
      canvas.addEventListener('pointermove', event => {
        if (!nodeDrag || event.pointerId !== nodeDrag.pointerId) return;
        if(!nodeDrag.moved&&Math.hypot(event.clientX-nodeDrag.x,event.clientY-nodeDrag.y)<5)return;
        nodeDrag.moved=true;
        const dx = (event.clientX-nodeDrag.x)/nodeDrag.scale, dy = (event.clientY-nodeDrag.y)/nodeDrag.scale;
        nodeDrag.targets.forEach(({node,x,y}) => {
          const position = nodeDrag.targets.length === 1 ? snapNode(node,x+dx,y+dy,event.altKey) : {x:x+dx,y:y+dy};
          node.style.left=`${position.x}px`;node.style.top=`${position.y}px`;
        });
        renderGraphEdges(root);
      });
      const finishNodeDrag = event => {
        if (!nodeDrag || event.pointerId !== nodeDrag.pointerId) return;
        const finishedDrag=nodeDrag;
        nodeDrag=null;
        clearAlignmentGuides();
        if(canvas.hasPointerCapture(event.pointerId))canvas.releasePointerCapture(event.pointerId);
        if(finishedDrag.moved)record();
        if(event.type==='pointerup' && !finishedDrag.moved && finishedDrag.targets.length===1 && Math.hypot(event.clientX-finishedDrag.x,event.clientY-finishedDrag.y)<5){
          const node=finishedDrag.targets[0].node;
          const isCurrent=canvas.closest('process-flow-canvas')?.getAttribute('variant')==='current';
          const isInterrupt=isCurrent && !!node.querySelector('img[src$="human.svg"]');
          const isAutomation=[...node.querySelectorAll('img')].some(image=>new URL(image.src,document.baseURI).pathname.endsWith('/omini.svg'));
          const isCondition=!!node.querySelector('img[src$="condition-fix.svg"],img[src$="condition.svg"]');
          const isSampling=isCondition&&!isCurrent&&!!customElements.get('condition-panel');
          // Only node types with a properties component in the gallery open a panel.
          const workflowPanels={'start.svg':'start','end.svg':'end','condition-fix.svg':'workflow-condition','condition.svg':'workflow-condition','loop.svg':'workflow-loop','human.svg':'workflow-human','api.svg':'api-request','pose.svg':'workflow-pose','nav.svg':'workflow-navigation','omini.svg':'workflow-automation','variable.svg':'workflow-variable','variable-yellow.svg':'workflow-variable'};
          const workflowVariant=isCurrent?[...node.querySelectorAll('img')].map(image=>workflowPanels[new URL(image.src,document.baseURI).pathname.split('/').pop()]).find(Boolean):null;
          const hasPanel=isCurrent?!!workflowVariant:isSampling||isAutomation||!!node.querySelector('img[src$="human.svg"]');
          if(!hasPanel){
            const existing=root.querySelector('process-node-properties .right-panel');
            if(existing)existing.style.display='none';
            nodeDrag=null;
            clearAlignmentGuides();
            if(canvas.hasPointerCapture(event.pointerId))canvas.releasePointerCapture(event.pointerId);
            return;
          }
          const variant=workflowVariant||(isSampling?'condition-sampling':isCondition?'condition':isInterrupt?'workflow-human':isAutomation&&!isCurrent?'automation':isCurrent?'default':'basic');
          let properties=root.querySelector('process-node-properties');
          const humanStage=variant==='basic'&&['review','accept','internal'].includes(node.dataset.node)?node.dataset.node:'';
          if(properties && ((properties.getAttribute('variant')||'default')!==variant||(properties.getAttribute('human-stage')||'')!==humanStage)){
            const old=properties;
            const panelStyle=old.querySelector('.right-panel')?.style.cssText||'';
            properties=document.createElement('process-node-properties');properties.setAttribute('variant',variant);
            if(humanStage)properties.setAttribute('human-stage',humanStage);
            old.replaceWith(properties);
            properties.querySelector('.right-panel').style.cssText=panelStyle;
          }
          if(!properties){
            properties=document.createElement('process-node-properties');properties.setAttribute('variant',variant);
            if(humanStage)properties.setAttribute('human-stage',humanStage);
            canvas.append(properties);
            Object.assign(properties.querySelector('.right-panel').style,{position:'absolute',right:'0',top:'0',bottom:'0',zIndex:'30',maxWidth:'90%'});
          }
          const panel=properties.querySelector('.right-panel');
          if(panel){panel.hidden=false;panel.style.display='';}
          const title=node.querySelector('.graph-title')?.textContent.trim()||'节点';
          properties.dataset.nodeId=node.dataset.node;
          if(variant==='workflow-variable'){
            properties.querySelectorAll('workflow-field-collection').forEach(collection=>{collection.value=node._variableFields?.[collection.getAttribute('kind')]||[];});
            properties.querySelector('workflow-next-step').setAttribute('source-id',node.dataset.node);
            if(!properties._variableFieldsBound){
              properties._variableFieldsBound=true;
              properties.addEventListener('workflow-fields-change',event=>{
                const selected=[...canvas.querySelectorAll('[data-node]')].find(item=>item.dataset.node===properties.dataset.nodeId);
                if(!selected)return;
                selected._variableFields={...selected._variableFields,[event.detail.kind]:event.detail.value};
              });
            }
          }
          if(workflowVariant){
            const heading=properties.querySelector('.interrupt-heading h2');
            const description=properties.querySelector('.interrupt-heading p');
            if(heading)heading.textContent=title;
            if(description)description.textContent=node.querySelector('.graph-sub')?.textContent.trim()||'';
          }
          if(properties.syncBasicInput){
            properties.removeEventListener('input',properties.syncBasicInput);
            properties.removeEventListener('change',properties.syncBasicChange);
            properties.removeEventListener('node-properties-save',properties.syncBasicSave);
          }
          if(['basic','condition','condition-sampling','automation','human-interrupt'].includes(variant)){
            const syncBasic=()=>{
              const name=properties.querySelector('input[name="nodeName"],input[name="name"]')?.value??'';
              const description=properties.querySelector('textarea[name="description"]')?.value??'';
              const titleElement=node.querySelector('.graph-title');
              let subtitle=node.querySelector('.graph-sub');
              if(!subtitle&&titleElement){subtitle=document.createElement('div');subtitle.className='graph-sub';titleElement.after(subtitle);}
              if(titleElement)titleElement.textContent=name;
              if(subtitle)subtitle.textContent=description;
              node.title=name;
              const heading=properties.querySelector('h2');if(heading)heading.textContent=name;
            };
            properties.syncBasicInput=event=>{
              if(['nodeName','name','description'].includes(event.target.name||event.target.getAttribute?.('name')))syncBasic();
            };
            properties.syncBasicChange=event=>{
              if(['nodeName','name','description'].includes(event.target.name||event.target.getAttribute?.('name'))){syncBasic();record();}
            };
            properties.syncBasicSave=()=>{syncBasic();record();};
            properties.addEventListener('input',properties.syncBasicInput);
            properties.addEventListener('change',properties.syncBasicChange);
            properties.addEventListener('node-properties-save',properties.syncBasicSave);
          }
          const heading=properties.querySelector('h2');if(heading)heading.textContent=isInterrupt?'Human Interrupt':title;
          for(const [name,value] of [['nodeName',title],['nodeId',node.dataset.node],['description',node.querySelector('.graph-sub')?.textContent.trim()||title]]){
            const field=properties.querySelector(`[name="${name}"]`);if(field)field.value=value;
          }
          if(variant==='automation'){
            if(node.automationConfig){for(const [key,value] of Object.entries(node.automationConfig)){const field=properties.querySelector(`[name="${key}"]`);if(field&&key!=='processingRule')field.value=value;}properties.querySelectorAll('form-radio input').forEach(input=>input.checked=input.value===node.automationConfig.processingRule);}
            properties.onautomationSave && properties.removeEventListener('automation-node-save',properties.onautomationSave);
            properties.onautomationSave=event=>{node.automationConfig={...event.detail};node.querySelector('.graph-title').textContent=event.detail.nodeName;const sub=node.querySelector('.graph-sub');if(sub)sub.textContent=event.detail.description;record();};
            properties.addEventListener('automation-node-save',properties.onautomationSave);
            properties.onautomationDelete && properties.removeEventListener('automation-node-delete',properties.onautomationDelete);
            properties.onautomationDelete=()=>{node.remove();panel.style.display='none';renderGraphEdges(root);record();};
            properties.addEventListener('automation-node-delete',properties.onautomationDelete);
          }
          if(isSampling){
            const component=properties.querySelector('condition-panel');
            if(node.samplingComponent&&component!==node.samplingComponent){
              const savedStyle=component.querySelector('.right-panel').style.cssText;
              component.replaceWith(node.samplingComponent);
              node.samplingComponent.querySelector('.right-panel').style.cssText=savedStyle;
              node.samplingComponent.querySelector('.right-panel').style.display='';
            }
            const active=properties.querySelector('condition-panel');
            active.querySelector('input[name="name"]').value=title;
            active.querySelector('input[name="nodeId"]').value=node.dataset.node;
            active.querySelector('textarea[name="description"]').value=node.querySelector('.graph-sub')?.textContent.trim()||title;
            if(!node.samplingComponent){
              node.samplingComponent=active;
              active.addEventListener('node-properties-save',event=>{
                node.querySelector('.graph-title').textContent=event.detail.name;
                const sub=node.querySelector('.graph-sub');if(sub)sub.textContent=event.detail.description;
                const branch=node.querySelector('.basic-branch > span');if(branch&&event.detail.cases[0])branch.textContent=event.detail.cases[0].name;
                node.conditionConfig=event.detail;window.syncConditionNodePreview?.(node,event.detail);renderGraphEdges(root);record();
              });
            }
          }
          if(isCondition&&!isSampling&&variant==='condition'){
            const container=properties.querySelector('[data-condition-branches]');container.replaceChildren();
            const rows=[...node.querySelectorAll('.basic-branch,.branch-row')];
            rows.forEach((row,index)=>{
              const section=document.createElement('section');section.style.cssText='margin-bottom:16px;display:grid;gap:8px';
              const kind=row.querySelector('b')?.textContent||row.querySelector('.condition-case-label')?.lastElementChild?.textContent||row.textContent.split(' · ')[0];
              const label=document.createElement('label');label.textContent=kind;
              const field=document.createElement('input');field.name=`branch_${index}`;field.value=row.querySelector('.condition-expression span,.basic-branch > span')?.textContent||row.querySelector('span')?.textContent||row.textContent;
              if(kind==='ELSE'||kind==='ON ERROR')field.readOnly=true;
              label.append(field);section.append(label);
              const edge=(root.layoutConnections||[]).find(([from,port])=>from===node.dataset.node&&port===index+1);
              const hint=document.createElement('small');hint.textContent='下游：'+(edge?[...canvas.querySelectorAll('.graph-node')].find(item=>item.dataset.node===edge[2])?.querySelector('.graph-title')?.textContent||edge[2]:'未连接');section.append(hint);container.append(section);
            });
            if(properties.conditionSave)properties.removeEventListener('condition-properties-save',properties.conditionSave);
            properties.conditionSave=event=>{
              node.querySelector('.graph-title').textContent=event.detail.nodeName;node.title=event.detail.nodeName;
              const sub=node.querySelector('.graph-sub');if(sub)sub.textContent=event.detail.description;
              rows.forEach((row,index)=>{const text=row.querySelector('.basic-branch > span');if(text)text.textContent=event.detail[`branch_${index}`];});
              record();
            };
            properties.addEventListener('condition-properties-save',properties.conditionSave);
          }
          if(isInterrupt){
            const description=node.querySelector('.graph-sub')?.textContent.trim()||'';
            const transitions=(root.layoutConnections||[]).filter(([from])=>from===node.dataset.node).map(([, ,to])=>[...canvas.querySelectorAll('.graph-node')].find(item=>item.dataset.node===to)?.querySelector('.graph-title')?.textContent.trim()||to).join(', ');
            const values=node.interruptProperties||{name:title,description,transitions,timeout_s:description.match(/^(\d+(?:\.\d+)?)s\b/)?.[1]||'',reason:description.replace(/^\d+(?:\.\d+)?s\s*·\s*/, '')};
            for(const [name,value] of Object.entries(values)){
              const field=properties.querySelector(`[name="${name}"]`);if(field)field.value=value??'';
            }
            properties.onNodeSave && properties.removeEventListener('node-properties-save',properties.onNodeSave);
            properties.onNodeSave=event=>{
              node.interruptProperties={...event.detail};
              node.querySelector('.graph-title').textContent=event.detail.name;
              node.title=event.detail.name;
              record();
            };
            properties.addEventListener('node-properties-save',properties.onNodeSave);
          }
        }
      };
      canvas.addEventListener('pointerup', finishNodeDrag);
      canvas.addEventListener('pointercancel', finishNodeDrag);
      canvas.addEventListener('lostpointercapture',finishNodeDrag);

      canvas.addEventListener('pointerdown', (event) => {
        if (!(event.button === 1 || (event.button === 0 && state.spaceMode))) return;
        if (isInteractiveTarget(event.target)) return;
        event.preventDefault();
        state.dragging = true;
        state.startX = event.clientX;
        state.startY = event.clientY;
        state.startPanX = Number(canvas.dataset.panX || '0');
        state.startPanY = Number(canvas.dataset.panY || '0');
        canvas.classList.add('is-dragging');
        canvas.setPointerCapture(event.pointerId);
      });

      canvas.addEventListener('pointermove', (event) => {
        if (!state.dragging) return;
        const nextPanX = state.startPanX + (event.clientX - state.startX);
        const nextPanY = state.startPanY + (event.clientY - state.startY);
        canvas.dataset.panX = String(nextPanX);
        canvas.dataset.panY = String(nextPanY);
        updateCanvasTransform(canvas, zoomText);
      });

      const endDrag = (event) => {
        if (!state.dragging) return;
        state.dragging = false;
        canvas.classList.remove('is-dragging');
        if (event && canvas.hasPointerCapture && canvas.hasPointerCapture(event.pointerId)) {
          canvas.releasePointerCapture(event.pointerId);
        }
      };

      canvas.addEventListener('pointerup', endDrag);
      canvas.addEventListener('pointercancel', endDrag);
      canvas.addEventListener('auxclick',event=>{if(event.button===1)event.preventDefault();});
      canvas.addEventListener('pointerleave', endDrag);

      const isTypingTarget = (target) => target instanceof HTMLElement
        && (target.isContentEditable || Boolean(target.closest('input, textarea, select')));

      document.addEventListener('keydown', (event) => {
        if (event.composedPath().some(isTypingTarget) || event.isComposing) return;
        if ((event.key === 'Delete' || event.key === 'Backspace')
          && !event.metaKey && !event.ctrlKey && !event.altKey) {
          if (nodeDrag || state.dragging || pendingNode) return;
          const selectedNodes = canvas.querySelectorAll('.graph-node.selected:not(.placement-ghost)');
          if (!selectedNodes.length) return;
          event.preventDefault();
          selectedNodes.forEach(node => node.remove());
          renderGraphEdges(root);
          record();
          return;
        }
        if (!event.isComposing && !event.altKey && (event.metaKey || event.ctrlKey)) {
          const key = event.key.toLowerCase();
          const undo = key === 'z' && !event.shiftKey;
          const redo = (key === 'z' && event.shiftKey) || (key === 'y' && event.ctrlKey && !event.shiftKey);
          if (undo || redo) {
            event.preventDefault();
            if (!nodeDrag && !state.dragging) (undo ? undoBtn : redoBtn)?.click();
            return;
          }
        }
        if (event.code === 'Space') {
          event.preventDefault();
          state.spaceMode = true;
          canvas.classList.add('is-space-panning');
          return;
        }
        if (state.spaceMode && (event.key === 'ArrowLeft' || event.key === 'ArrowRight')) {
          event.preventDefault();
          const direction = event.key === 'ArrowLeft' ? 1 : -1;
          canvas.dataset.panX = String(Number(canvas.dataset.panX || '0') + direction * 120);
          updateCanvasTransform(canvas, zoomText);
        }
      });

      document.addEventListener('keyup', (event) => {
        if (event.code !== 'Space') return;
        state.spaceMode = false;
        canvas.classList.remove('is-space-panning');
        endDrag();
      });

      window.addEventListener('blur', () => {
        state.spaceMode = false;
        canvas.classList.remove('is-space-panning');
        endDrag();
      });

      canvas.addEventListener('wheel', (event) => {
        event.preventDefault();
        if (state.spaceMode) {
          const horizontalDelta = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? event.deltaX : event.deltaY;
          canvas.dataset.panX = String(Number(canvas.dataset.panX || '0') - horizontalDelta);
          updateCanvasTransform(canvas, zoomText);
          return;
        }
        const currentScale = Number(canvas.dataset.zoom || '1');
        const factor = event.deltaY < 0 ? 1.08 : 0.92;
        zoomCanvas(canvas, zoomText, currentScale * factor, event.clientX, event.clientY);
      }, { passive: false });

      zoomMinus?.addEventListener('click', (event) => {
        event.preventDefault();
        const rect = canvas.getBoundingClientRect();
        const next = (Math.ceil(Number(canvas.dataset.zoom || '1') * 10 - 1e-6) - 1) / 10;
        zoomCanvas(canvas, zoomText, next, rect.left + rect.width / 2, rect.top + rect.height / 2);
      });

      zoomPlus?.addEventListener('click', (event) => {
        event.preventDefault();
        const rect = canvas.getBoundingClientRect();
        const next = (Math.floor(Number(canvas.dataset.zoom || '1') * 10 + 1e-6) + 1) / 10;
        zoomCanvas(canvas, zoomText, next, rect.left + rect.width / 2, rect.top + rect.height / 2);
      });

      fitBtn?.addEventListener('click', (event) => {
        event.preventDefault();
        fitCanvas(canvas, zoomText);
      });

      handBtn?.addEventListener('click', (event) => {
        event.preventDefault();
        notify('按住空格 + 左键，或按住鼠标中键拖动画布');
      });
      selectBtn?.addEventListener('click', (event) => {
        event.preventDefault();
        state.handMode = false;
        handBtn?.classList.remove('active');
        selectBtn.classList.add('active');
        canvas.style.cursor = 'default';
        notify('已切换选择模式');
      });

      undoBtn?.setAttribute('data-action', 'undo');
      redoBtn?.setAttribute('data-action', 'redo');
      undoBtn?.setAttribute('title', '撤销（⌘/Ctrl+Z）');
      redoBtn?.setAttribute('title', '重做（⌘/Ctrl+Shift+Z）');
      undoBtn?.addEventListener('click', (event) => {
        event.preventDefault();
        if (history.past.length < 2) return;
        history.future.push(history.past.pop());
        restore(history.past[history.past.length - 1]);
        updateHistoryButtons();
        notify('已撤销');
      });
      redoBtn?.addEventListener('click', (event) => {
        event.preventDefault();
        const next = history.future.pop();
        if (!next) return;
        history.past.push(next);
        restore(next);
        updateHistoryButtons();
        notify('已重做');
      });

      root.querySelectorAll('.graph-node').forEach((node) => {
        node.addEventListener('click', (event) => {
          event.stopPropagation();
          root.querySelectorAll('.graph-node.selected').forEach((item) => item.classList.remove('selected'));
          node.classList.add('selected');
          const title = node.querySelector('.graph-title')?.textContent?.trim();
          const propTitle = root.querySelector('.prop-title h2');
          if (propTitle && title) propTitle.textContent = title;
          notify(`已选择：${title || '节点'}`);
        });
      });

      root.querySelectorAll('.rail-item').forEach((item) => {
        item.addEventListener('click', () => {
          root.querySelectorAll('.rail-item').forEach((entry) => entry.classList.toggle('active', entry === item));
          notify(`已切换至：${item.querySelector('span')?.textContent?.trim() || '平台'}`);
        });
      });

      root.querySelector('task-status-tabs')?.addEventListener('tab-change', event => {
          const name = event.detail.value;
          root.querySelectorAll('.panel-scroll[data-tab]').forEach((panel) => {
            panel.style.display = panel.dataset.tab === name ? 'block' : 'none';
          });
      });

      root.querySelectorAll('.group-head').forEach((head) => {
        head.addEventListener('click', () => head.closest('.palette-group')?.classList.toggle('is-collapsed'));
      });
      root.querySelectorAll('.flow-label').forEach((label) => {
        label.addEventListener('click', () => label.closest('.flow-section')?.classList.toggle('is-collapsed'));
      });

      searchInput?.addEventListener('search-change', () => {
        const query = searchInput.value.trim().toLowerCase();
        root.querySelectorAll('.palette-item').forEach((item) => {
          item.classList.toggle('is-hidden', query && !item.textContent.toLowerCase().includes(query));
        });
      });

      let pendingNode = null;
      let pendingConnection = null;
      const decorate = node => {
        if (node.querySelector('.node-hover-actions')) return;
        const actions = document.createElement('div'); actions.className='node-hover-actions';
        node.querySelectorAll(':scope > .port').forEach(port => {
          const button=document.createElement('button'); button.type='button';
          const left=port.style.left!=='';
          button.className=left?'node-add-before':'node-add-after';
          button.setAttribute('aria-label',left?'添加前置节点':'添加后置节点');
          button.dataset.portIndex = [...node.querySelectorAll(':scope > .port')].indexOf(port);
          button.style.top=node.dataset.node.startsWith('added-')&&!node.classList.contains('condition-cases') ? '50%' : `${port.offsetTop+port.offsetHeight/2}px`;
          if(left) button.style.left=`${port.offsetLeft+port.offsetWidth/2-9}px`;
          else {button.style.right='auto';button.style.left=`${port.offsetLeft+port.offsetWidth/2-9}px`;}
          actions.append(button);
        });
        actions.insertAdjacentHTML('beforeend','<button type="button" class="node-more" aria-label="更多节点操作">···</button>');
        for (const side of ['before','after']) {
          if (actions.querySelector(`.node-add-${side}`)) continue;
          const button = document.createElement('button'); button.type='button';
          button.className=`node-add-${side}`;
          const port=document.createElement('span');port.className='port';
          port.style[side==='before'?'left':'right']='-4px';port.style.top='calc(50% - 3.5px)';
          node.append(port);
          button.dataset.portIndex=[...node.querySelectorAll(':scope > .port')].indexOf(port);
          button.setAttribute('aria-label',side==='before'?'添加前置节点':'添加后置节点');
          button.style.top='50%';
          button.style.left=side==='before'?'-9px':`${node.offsetWidth-9}px`;
          button.style.right='auto'; actions.append(button);
        }
        node.append(actions);
      };
      canvas.querySelectorAll('.graph-node').forEach(decorate);
      const positionPending = (x, y) => {
        const rect = canvas.getBoundingClientRect();
        const scale = Number(canvas.dataset.zoom);
        pendingNode.style.left = `${(x-rect.left-Number(canvas.dataset.panX))/scale-64}px`;
        pendingNode.style.top = `${(y-rect.top-Number(canvas.dataset.panY))/scale-19}px`;
      };
      const pickNode = detail => {
        pendingNode?.remove();
        pendingNode = document.createElement('div');
        pendingNode.className = 'graph-node placement-ghost';
        pendingNode.dataset.node = `added-${Date.now()}-${Math.random().toString(36).slice(2,7)}`;
        const icon = document.createElement('span'); icon.className = detail.color.replace('node-icon', 'mini'); icon.innerHTML = detail.icon;
        const title = document.createElement('div'); title.className = 'graph-title'; title.textContent = detail.label;
        pendingNode.append(icon, title);
        pendingNode.insertAdjacentHTML('beforeend', '<span class="port" style="left:-4px;top:calc(50% - 3.5px)"></span><span class="port" style="right:-4px;top:calc(50% - 3.5px)"></span>');
        if(['Condition','condition','条件节点','条件分支'].includes(detail.label)){
          pendingNode.classList.add('condition-cases');
          Object.assign(pendingNode.style,{width:'300px',height:'168px',display:'block'});
          pendingNode.replaceChildren();
          const header=document.createElement('div');header.className='condition-case-header';
          Object.assign(header.style,{display:'flex',alignItems:'center',gap:'11px'});
          title.textContent='Condition';header.append(icon,title);pendingNode.append(header);
          pendingNode.insertAdjacentHTML('beforeend','<div class="branch-row" style="height:72px"><div class="condition-case-label"><span>CASE 1</span><span>IF</span></div><div class="condition-expression"><span>条件未设置</span></div></div><div class="branch-row condition-fallback" style="height:40px">ELSE</div><span class="port" style="left:-4px;top:88.5px"></span><span class="port" style="right:-4px;top:88.5px"></span><span class="port" style="right:-4px;top:144.5px"></span>');
        }
        if(['Variable Assignment','变量赋值'].includes(detail.label)){
          pendingNode.classList.add('variable-default');
          const text=document.createElement('div');text.className='node-text';title.replaceWith(text);text.append(title);
          text.insertAdjacentHTML('beforeend','<div class="variable-empty">未选择变量</div>');
        }
        if (['开始','开始节点', 'Start', 'start'].includes(detail.label)) {
          pendingNode.classList.add('start-main');
          const image = icon.querySelector('img');
          if (image) { image.style.width='23px'; image.style.height='23px'; image.style.flex='none'; icon.replaceWith(image); }
          const text = document.createElement('div'); text.className='node-text';
          title.textContent='开始'; title.replaceWith(text); text.append(title);
          pendingNode.querySelector('.port[style*="left"]')?.remove();
        }
        window.applyProcessNodeDefaultSummary(pendingNode,detail.label,canvas.closest('process-flow-canvas')?.getAttribute('variant')==='current');
        canvas.querySelector('.scene').append(pendingNode);
        if(root.insertionConnection){
          const connection=root.insertionConnection;root.insertionConnection=null;
          const [sourceId,sourcePort,targetId,targetPort]=connection;
          const source=canvas.querySelector(`[data-node="${sourceId}"]`),target=canvas.querySelector(`[data-node="${targetId}"]`);
          if(source&&target){
            const node=pendingNode;
            // Insertion requires both an input and an output, including terminal templates.
            if(!node.querySelector('.port[style*="left"]'))node.insertAdjacentHTML('beforeend','<span class="port" style="left:-4px;top:calc(50% - 3.5px)"></span>');
            const ports=[...node.querySelectorAll('.port')];
            const input=ports.findIndex(port=>port.style.left!==''),output=ports.findIndex(port=>port.style.right!=='');
            const x=source.offsetLeft+source.offsetWidth+62;
            const required=x+node.offsetWidth+62;
            const shift=Math.max(0,required-target.offsetLeft),oldTargetX=target.offsetLeft;
            canvas.querySelectorAll('.graph-node').forEach(item=>{if(item!==node&&item!==source&&item.offsetLeft>=oldTargetX)item.style.left=`${item.offsetLeft+shift}px`;});
            node.style.left=`${x}px`;node.style.top=`${source.offsetTop}px`;
            node.classList.remove('placement-ghost');decorate(node);pendingNode=null;
            root.removedConnections ||= [];root.removedConnections.push(connection);
            root.customConnections ||= [];root.customConnections.push([sourceId,sourcePort,node.dataset.node,input],[node.dataset.node,output,targetId,targetPort]);
            root.arrangeWorkflow?.();
            renderGraphEdges(root);record();return;
          }
        }
        const rect = canvas.getBoundingClientRect(); positionPending(rect.left+rect.width/2, rect.top+rect.height/2);
      };
      root.addEventListener('node-pick', event => pickNode(event.detail));
      root.addEventListener('click', event => {
        const item = event.target.closest('process-node-library .palette-item');
        if (item) pickNode({ label:item.textContent.trim(), icon:item.querySelector('.node-icon').innerHTML, color:item.querySelector('.node-icon').className });
      });
      canvas.addEventListener('pointermove', event => { if (pendingNode) positionPending(event.clientX, event.clientY); });
      canvas.addEventListener('pointerdown', event => {
        if (!pendingNode || event.button !== 0 || event.target.closest('button,.canvas-add-menu')) return;
        event.preventDefault(); event.stopImmediatePropagation();
        positionPending(event.clientX,event.clientY);
        const added=pendingNode;
        const loopArea=canvas.querySelector('.loop-box .loop-stage')?.getBoundingClientRect();
        const insideLoop=Boolean(loopArea&&event.clientX>=loopArea.left&&event.clientX<=loopArea.right&&event.clientY>=loopArea.top&&event.clientY<=loopArea.bottom);
        added.dataset.loopScope=insideLoop?'inside':'outside';
        added.classList.remove('placement-ghost'); decorate(added); pendingNode = null;
        // Keep free placement local: move only the new card out of occupied space.
        const peers=[...canvas.querySelectorAll('.graph-node:not(.placement-ghost)')].filter(n=>n!==added);
        let y=added.offsetTop;
        for(;;){
          const hit=peers.find(n=>added.offsetLeft<n.offsetLeft+n.offsetWidth+32&&added.offsetLeft+added.offsetWidth+32>n.offsetLeft&&y<n.offsetTop+n.offsetHeight+40&&y+added.offsetHeight+40>n.offsetTop);
          if(!hit)break;
          y=hit.offsetTop+hit.offsetHeight+40;
        }
        added.style.top=`${y}px`;
        if(root.loopNodeIds){
          if(insideLoop)root.loopNodeIds.add(added.dataset.node);
          else root.loopNodeIds.delete(added.dataset.node);
        }
        renderGraphEdges(root);record();
      }, true);
      document.addEventListener('keydown', event => { if (event.key === 'Escape') {
        if (pendingNode) { pendingNode.remove(); pendingNode=null; }
        pendingConnection=null; canvas.style.cursor='';
      } });
      let connectionDrag = null;
      let suppressConnectionClick = false;
      const clearConnectionDrag = () => {
        connectionDrag?.preview.remove(); connectionDrag = null;
        canvas.querySelectorAll('.connection-source').forEach(node => node.classList.remove('connection-source'));
        canvas.classList.remove('is-connecting');
      };
      canvas.addEventListener('pointerdown', event => {
        const button = event.target.closest('.node-add-before,.node-add-after');
        if (!button || event.button !== 0 || pendingNode) return;
        event.preventDefault(); event.stopImmediatePropagation();
        const rect = button.getBoundingClientRect();
        const preview = document.createElementNS('http://www.w3.org/2000/svg','path');
        preview.setAttribute('fill','none'); preview.setAttribute('stroke','#009bb5');
        preview.setAttribute('stroke-width','2'); preview.style.pointerEvents='none';
        canvas.querySelector('.edge-layer').append(preview);
        connectionDrag = {button, preview, x:rect.left+rect.width/2, y:rect.top+rect.height/2, moved:false};
        button.closest('.graph-node').classList.add('connection-source');
        pendingConnection=null;
        canvas.classList.add('is-connecting');
      }, true);
      document.addEventListener('pointermove', event => {
        if (!connectionDrag) return;
        const drag = connectionDrag;
        if (Math.hypot(event.clientX-drag.x,event.clientY-drag.y)>4) drag.moved=true;
        const rect=canvas.getBoundingClientRect(), scale=Number(canvas.dataset.zoom);
        const x=(drag.x-rect.left-Number(canvas.dataset.panX))/scale;
        const y=(drag.y-rect.top-Number(canvas.dataset.panY))/scale;
        const tx=(event.clientX-rect.left-Number(canvas.dataset.panX))/scale;
        const ty=(event.clientY-rect.top-Number(canvas.dataset.panY))/scale;
        drag.preview.setAttribute('d',`M${x} ${y} C${(x+tx)/2} ${y} ${(x+tx)/2} ${ty} ${tx} ${ty}`);
      });
      document.addEventListener('pointerup', event => {
        if (!connectionDrag) return;
        const {button,moved}=connectionDrag;
        let target=document.elementFromPoint(event.clientX,event.clientY)?.closest('.node-add-before,.node-add-after');
        // Hidden hover controls must not make a valid node impossible to connect.
        // Accept the node body or a small margin around its compatible port.
        if (!target) {
          const selector=button.classList.contains('node-add-before')?'.node-add-after':'.node-add-before';
          const source=button.closest('.graph-node');
          let closestDistance=Infinity;
          canvas.querySelectorAll('.graph-node:not(.placement-ghost)').forEach(node=>{
            if(node===source)return;
            const rect=node.getBoundingClientRect();
            const distance=Math.hypot(Math.max(rect.left-event.clientX,0,event.clientX-rect.right),Math.max(rect.top-event.clientY,0,event.clientY-rect.bottom));
            if(distance<=18 && distance<closestDistance){
              const candidate=node.querySelector(selector);
              if(candidate){target=candidate;closestDistance=distance;}
            }
          });
        }
        clearConnectionDrag();
        if (!moved) return;
        suppressConnectionClick=true;
        setTimeout(()=>{suppressConnectionClick=false;},0);
        if (!target || !canvas.contains(target) || target.closest('.graph-node')===button.closest('.graph-node')) return;
        const before=button.classList.contains('node-add-before');
        if (before===target.classList.contains('node-add-before')) return;
        const output=before?target:button, input=before?button:target;
        const outputIndex=Number(output.dataset.portIndex ?? -1), inputIndex=Number(input.dataset.portIndex ?? -1);
        if(outputIndex<0 || inputIndex<0) return;
        const connection=[output.closest('.graph-node').dataset.node,outputIndex,input.closest('.graph-node').dataset.node,inputIndex];
        root.removedConnections=(root.removedConnections||[]).filter(item=>JSON.stringify(item)!==JSON.stringify(connection));
        root.customConnections ||= [];
        if (!root.customConnections.some(item=>JSON.stringify(item)===JSON.stringify(connection))) {
          root.customConnections.push(connection);
        }
        renderGraphEdges(root); record();
      });
      document.addEventListener('pointercancel',clearConnectionDrag);
      document.addEventListener('keydown',event=>{if(event.key==='Escape')clearConnectionDrag();});
      canvas.addEventListener('click', event => {
        if(suppressConnectionClick){event.preventDefault();event.stopImmediatePropagation();return;}
        if (!pendingConnection) return;
        const target = event.target.closest('.graph-node');
        if (!target || target === pendingConnection.node || event.target.closest('.node-more')) return;
        event.preventDefault(); event.stopImmediatePropagation();
        const {node, before, portIndex} = pendingConnection;
        const source = before ? target : node;
        const destination = before ? node : target;
        const ports = [...source.querySelectorAll(':scope > .port')];
        const output = before ? ports.findIndex(port => port.style.right !== '') : portIndex;
        const inputs = [...destination.querySelectorAll(':scope > .port')];
        const input = before ? portIndex : inputs.findIndex(port => port.style.left !== '');
        if (output < 0 || input < 0) { notify('该节点没有对应的连接口'); return; }
        const connection = [source.dataset.node, output, destination.dataset.node, input];
        root.removedConnections=(root.removedConnections||[]).filter(item=>JSON.stringify(item)!==JSON.stringify(connection));
        root.customConnections ||= [];
        if (!root.customConnections.some(item => JSON.stringify(item) === JSON.stringify(connection))) {
          root.customConnections.push(connection);
        }
        renderGraphEdges(root); record();
        pendingConnection=null; canvas.style.cursor='';
      }, true);
      canvas.addEventListener('click', event => {
        const action = event.target.closest('.node-hover-actions button');
        if (!action) return;
        event.stopPropagation();
        if (!action.classList.contains('node-more')) {
          pendingConnection = {node:action.closest('.graph-node'), before:action.classList.contains('node-add-before'), portIndex:Number(action.dataset.portIndex ?? -1)};
          canvas.style.cursor='crosshair';
          notify('点击目标节点完成连接，Esc 取消'); return;
        }
        const node = action.closest('.graph-node');
        const old = node.querySelector('.node-context-menu');
        if (old) { old.remove(); return; }
        const menu = document.createElement('div'); menu.className='node-context-menu';
        const remove = document.createElement('button'); remove.type='button'; remove.textContent='删除节点';
        remove.onclick = e => { e.stopPropagation(); node.remove(); renderGraphEdges(root); record(); };
        menu.append(remove); node.querySelector('.node-hover-actions').append(menu);
      });

      root.querySelector('process-actions')?.addEventListener('process-action', event => {
        if(event.detail.action==='download'){
          notify('完整 YAML 导出功能尚未接入');
          return;
        }
        const labels = {parameters:'全局参数',save:'保存',publish:'发布',history:'历史'};
        notify(`${labels[event.detail.action]}操作已触发`);
      });
      root.querySelectorAll('.prop-tools button').forEach((button) => {
        button.addEventListener('click', () => {
          if (button.dataset.propertyAction === 'close') return;
          const label = button.textContent.trim() || button.getAttribute('aria-label') || '操作';
          if (button.classList.contains('primary')) notify('发布操作已触发');
          else notify(`${label}已触发`);
        });
      });

      window.addEventListener('resize', () => {
        fitCanvas(canvas, zoomText, Number(canvas.dataset.zoom || 1));
        renderGraphEdges(root);
      });
    }
    const initialize = () => document.querySelectorAll(".process-editor-components").forEach(initializeEditor);
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize, {once:true});
    else initialize();


})();
