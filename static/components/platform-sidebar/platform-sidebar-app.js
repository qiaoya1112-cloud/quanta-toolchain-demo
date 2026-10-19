(() => {
  const scriptUrl = document.currentScript?.src || "";
  const assetBase = new URL("./assets/", scriptUrl).href;
  const COLLAPSED_WIDTH = 64;
  const EXPANDED_WIDTH = 200;
  const EXPANDED_THRESHOLD = 170;
  const pathPageMap = {
    "/data/instruction-management": "command-management",
    "/data/instruction-packages": "command-package-management",
    "/data/collection-plans/assigned": "collection-plans",
    "/data/collection-plans": "collection-plan-management",
    "/data/processing-tasks": "task-processing",
    "/data/allocations-v2": "assignment-management",
    "/data/allocations": "assignment-management",
    "/data/recordings": "data-management",
    "/data/workbench-v2": "action-annotation",
    "/data/workbench": "action-annotation",
    "/data/pipelines": "process-management",
    "/data/operators": "operator-management",
    "/data/rules": "rule-management",
    "/data/workbench-management": "workbench-management",
    "/data/projects": "project-management",
    "/data/user-groups": "user-group-management",
    "/data/suppliers": "supplier-management",
    "/data/permissions": "permission-management",
    "/model/data/query": "model-data-query",
    "/model/data/datasets": "model-datasets",
    "/model/data/raw": "model-raw-data",
    "/model/experiments": "model-training",
    "/model/checkpoints": "model-checkpoints",
    "/model/eval/tasks": "model-evaluations",
    "/model/eval/benchmarks": "model-evaluation-sets",
    "/model/eval/test-cases": "model-evaluation-cases",
    "/model/eval/catalog": "model-scenes",
    "/model/eval/criteria": "model-evaluation-criteria",
    "/model/eval/evaluate2": "model-device-demo",
    "/model/eval/tags": "model-tags",
    "/model/eval/prompts": "model-prompts",
    "/model/config/images": "model-images",
    "/model/resources": "model-resources",
    "/model/queues": "model-queues"
  };
  const currentPath = Object.keys(pathPageMap)
    .sort((a, b) => b.length - a.length)
    .find(path => location.pathname === path || location.pathname.startsWith(path + "/"));
  const currentPage = document.body?.dataset.pageId || pathPageMap[currentPath] || "";
  const pageRoutes = {
    "resource-library": "/data/operators",
    "command-package-management": "/data/instruction-packages",
    "collection-plan-management": "/data/collection-plans",
    "collection-plans": "/data/collection-plans/assigned",
    "command-management": "/data/instruction-management",
    "user-group-management": "/data/user-groups",
    "supplier-management": "/data/suppliers",
    "permission-management": "/data/permissions",
    "project-management": "/data/projects",
    "rule-management": "/data/rules",
    "workbench-management": "/data/workbench-management",
    "operator-management": "/data/operators",
    "assignment-management": "/data/allocations-v2",
    "data-management": "/data/recordings",
    "task-processing": "/data/processing-tasks",
    "action-annotation": "/data/workbench-v2",
    "process-management": "/data/pipelines"
  };
  const modelRoutes = {
    "model-data-query": "/model/data/query",
    "model-datasets": "/model/data/datasets",
    "model-raw-data": "/model/data/raw",
    "model-training": "/model/experiments",
    "model-checkpoints": "/model/checkpoints",
    "model-evaluations": "/model/eval/tasks",
    "model-evaluation-sets": "/model/eval/benchmarks",
    "model-evaluation-cases": "/model/eval/test-cases",
    "model-scenes": "/model/eval/catalog",
    "model-evaluation-criteria": "/model/eval/criteria",
    "model-device-demo": "/model/eval/evaluate2",
    "model-tags": "/model/eval/tags",
    "model-prompts": "/model/eval/prompts",
    "model-images": "/model/config/images",
    "model-resources": "/model/resources",
    "model-queues": "/model/queues"
  };
  const navGroups = [
    ["任务管理", [["任务处理", "icon-task-list.svg", "task-processing"], ["分配管理", "icon-assignment.svg", "assignment-management"], ["数据管理", "icon-data-management.svg", "data-management"]]],
    ["工作台", [["标注工作台", "icon-annotation.svg", "action-annotation"]]],
    ["工作流", [["流程管理", "icon-workflow.svg", "process-management"], ["资源库", "icon-project-folder.svg", "resource-library"], ["算子管理", "icon-operator.svg", "operator-management"]]],
    ["配置管理", [["规则管理", "icon-rules.svg", "rule-management"], ["工作台管理", "icon-workbench.svg", "workbench-management"]]],
    ["运营管理", [["项目管理", "icon-task-list.svg", "project-management"], ["用户组管理", "icon-users.svg", "user-group-management"], ["供应商管理", "icon-store.svg", "supplier-management"], ["权限管理", "icon-shield.svg", "permission-management"]]]
  ];

  const modelGroups = [
    ["数据", [["数据湖圈选", "icon-data-management.svg", "model-data-query"], ["数据集", "icon-task-list.svg", "model-datasets"], ["原始数据", "icon-operator-blocks.svg", "model-raw-data"]]],
    ["训练", [["训练任务", "icon-operator.svg", "model-training"], ["Checkpoint", "icon-operator-blocks.svg", "model-checkpoints"]]],
    ["评测", [["评测任务", "icon-operator.svg", "model-evaluations"], ["评测集", "icon-task-list.svg", "model-evaluation-sets"], ["评测用例", "icon-task-list.svg", "model-evaluation-cases"], ["场景库", "icon-task-list.svg", "model-scenes"], ["评价标准", "icon-rules.svg", "model-evaluation-criteria"], ["端侧示意", "icon-navigation.svg", "model-device-demo"]]],
    ["配置", [["标签管理", "icon-project-folder.svg", "model-tags"], ["任务提示词", "icon-annotation.svg", "model-prompts"], ["镜像管理", "icon-operator.svg", "model-images"]]],
    ["管理", [["资源管理", "icon-operator.svg", "model-resources"], ["队列管理", "icon-operator-blocks.svg", "model-queues"]]]
  ];

  class PlatformSidebar extends HTMLElement {
    connectedCallback() {
      if (this.dataset.rendered === "true") return;
      const componentCatalog = this.getAttribute('variant') === 'components' || this.getAttribute('catalog') === 'components';
      this.isModelPlatform = this.getAttribute('platform') === 'model';
      const groupsSource = this.isModelPlatform ? modelGroups : componentCatalog ? [
        ['基础组件', [['通用','icon-operator-blocks.svg','color-tokens'],['导航','icon-navigation.svg','platform-sidebar'],['按钮','icon-operator.svg','button'],['输入与表单','icon-rules.svg','input'],['表格配套','icon-task-list.svg','table-controls'],['表格示例','icon-task-list.svg','table-examples'],['新建详情示例','icon-operator-blocks.svg','create-examples'],['滚动条','icon-task-list.svg','scrollbar']]],
        ['业务组件', [['工作台','icon-workbench.svg','workbench'],['工作流','icon-workflow.svg','workflow']]]
      ] : navGroups;
      const groups = groupsSource.map(([label, items], index) => `
        <section class="platform-sidebar__group${this.isModelPlatform && index > 0 && !items.some(([, , id]) => id === currentPage) ? ' is-collapsed' : ''}">
          ${index ? '<span class="platform-sidebar__divider" aria-hidden="true"></span>' : ''}
          <button class="platform-sidebar__group-title" type="button" aria-expanded="${!(this.isModelPlatform && index > 0 && !items.some(([, , id]) => id === currentPage))}"><span>${label}</span><span class="platform-sidebar__group-chevron" aria-hidden="true"><img src="${assetBase}icon-sidebar-section-chevron.svg" alt="" /></span></button>
          <div class="platform-sidebar__group-items">${items.map(([itemLabel, icon, pageId]) => {
            const active = pageId === currentPage;
            return `
            <button class="platform-sidebar__item${active ? ' platform-sidebar__item--active' : ''}" type="button" title="${itemLabel}"${pageId ? ` data-page-id="${pageId}"` : ''}${active ? ' aria-current="page"' : ''}>
              <span class="platform-sidebar__icon"><img src="${assetBase}${icon}?v=native-icons-4" alt="" /></span><span class="platform-sidebar__label">${itemLabel}</span>
            </button>`;
          }).join('')}</div>
        </section>`).join('');

      this.innerHTML = `
        <aside class="platform-sidebar" data-component="platform-sidebar" data-expanded="true" aria-label="平台侧边导航">
          <div class="platform-sidebar__main">
            <div class="platform-sidebar__brand"><div class="platform-sidebar__logo"><img src="${assetBase}quanta-logo.png" alt="" /></div><div class="platform-sidebar__brand-copy"><img class="platform-sidebar__wordmark" src="${assetBase}spirit-ai-wordmark.svg" alt="Spirit AI" /><span class="platform-sidebar__brand-caption">${componentCatalog ? '设计规范' : 'Quanta平台'}</span></div></div>
            <button class="platform-sidebar__platform" type="button" aria-haspopup="listbox" aria-expanded="false" aria-controls="platform-switcher-menu"><span class="platform-sidebar__platform-icon"><img src="${assetBase}icon-data-platform.svg" alt="" /></span><span class="platform-sidebar__platform-short">数</span><span class="platform-sidebar__platform-name">数据平台</span><span class="platform-sidebar__chevron" aria-hidden="true"><img src="${assetBase}icon-platform-select-chevron.svg" alt="" /></span></button>
            <nav class="platform-sidebar__nav" aria-label="平台导航">${groups}</nav>
          </div>
          <div class="platform-sidebar__platform-menu" id="platform-switcher-menu" role="listbox" aria-label="切换平台" hidden>
            <button class="platform-sidebar__platform-option is-selected" type="button" role="option" aria-selected="true" data-platform="数据平台"><span><img src="${assetBase}icon-data-platform.svg" alt="" /></span><b>数据平台</b></button>
            <button class="platform-sidebar__platform-option" type="button" role="option" aria-selected="false" data-platform="模型平台"><span><img src="${assetBase}icon-model-platform.svg" alt="" /></span><b>模型平台</b></button>
            <button class="platform-sidebar__platform-option" type="button" role="option" aria-selected="false" data-platform="应用编排平台"><span><img src="${assetBase}icon-orchestrate-platform.svg" alt="" /></span><b>应用编排平台</b></button>
            <button class="platform-sidebar__platform-option" type="button" role="option" aria-selected="false" data-platform="设备管理平台"><span><img src="${assetBase}icon-device-platform.svg" alt="" /></span><b>设备管理平台</b></button>
          </div>
          <div class="platform-sidebar__footer"><span class="platform-sidebar__brand-decoration" aria-hidden="true"><img src="${assetBase}brand-decoration.svg" alt="" /></span><span class="platform-sidebar__footer-divider" aria-hidden="true"></span><div class="platform-sidebar__profile"><span class="platform-sidebar__avatar" aria-hidden="true"></span><span class="platform-sidebar__username">Aria.Pei</span></div><div class="platform-sidebar__version" role="group" aria-label="版本切换"><button type="button">新</button><button class="is-active" type="button">旧</button></div></div>
          <div class="platform-sidebar__resize-handle" role="separator" aria-label="调整侧边栏宽度" aria-orientation="vertical" aria-valuemin="64" aria-valuemax="200" tabindex="0"></div>
        </aside>`;
      this.dataset.rendered = "true";
      this.sidebar = this.querySelector('.platform-sidebar');
      this.resizeHandle = this.querySelector('.platform-sidebar__resize-handle');
      this.platformButton = this.querySelector('.platform-sidebar__platform');
      this.platformButton.querySelector('.platform-sidebar__chevron img').src = `${assetBase}icon-platform-switch.svg`;
      this.platformMenu = this.querySelector('.platform-sidebar__platform-menu');
      if (this.getAttribute('variant') === 'style-variant') {
        this.classList.add('platform-sidebar--compact-switch');
        this.platformButton.querySelector('.platform-sidebar__platform-name').textContent = '千寻数据平台';
        this.platformButton.title = '切换平台';
      }
      if (this.getAttribute('variant') === 'style-variant' && !componentCatalog && !this.isModelPlatform) {
        const nav = this.querySelector('.platform-sidebar__nav');
        const items = new Map([...nav.querySelectorAll('[data-page-id]')].map(item => [item.dataset.pageId, item]));
        nav.replaceChildren();
        items.get('task-processing').querySelector('.platform-sidebar__label').textContent = '处理任务';
        items.get('task-processing').title = '处理任务';
        const navIcons = {
          'task-processing': 'nav-tasks.svg',
          'assignment-management': 'nav-assignment.svg',
          'data-management': 'nav-database.svg',
          'action-annotation': 'nav-annotation.svg',
          'process-management': 'nav-workflow.svg',
          'operator-management': 'nav-operator.svg',
          'rule-management': 'nav-rules.svg',
          'workbench-management': 'nav-workbench.svg',
          'project-management': 'nav-project.svg',
          'user-group-management': 'nav-users.svg',
          'supplier-management': 'nav-supplier.svg',
          'permission-management': 'nav-permission.svg'
        };
        Object.entries(navIcons).forEach(([id, icon]) => {
          items.get(id).querySelector('.platform-sidebar__icon img').src = `${assetBase}${icon}`;
        });
        const sections = [
          ['数据采集', [
            ['指令管理', 'nav-command.svg', 'command-management'],
            ['指令包管理', 'nav-package.svg', 'command-package-management'],
            ['方案管理', 'nav-plan.svg', 'collection-plan-management'],
            ['采集方案', 'nav-collection.svg', 'collection-plans']
          ]],
          ['数据处理', ['task-processing', 'assignment-management', 'data-management']],
          ['工作台', ['action-annotation']],
          ['工作流', ['process-management', 'resource-library', 'operator-management']],
          ['配置管理', ['rule-management', 'workbench-management']],
          ['运营管理', ['project-management', 'user-group-management', 'supplier-management', 'permission-management']]
        ];
        if (!this.hasAttribute('demo') && performance.getEntriesByType('navigation')[0]?.type === 'reload') {
          try {
            sections.forEach(([label]) => sessionStorage.removeItem(`platform-sidebar-group:data:${label}`));
          } catch (_) {}
        }
        const groupIcons = ['nav-group-collection.svg', 'nav-group-processing.svg', 'nav-group-workbench.svg', 'nav-group-workflow.svg', 'nav-group-settings.svg', 'nav-group-operations.svg'];
        sections.forEach(([label, entries], index) => {
          const group = document.createElement('section');
          group.dataset.stateKey = `platform-sidebar-group:data:${label}`;
          let storedState = null;
          if (!this.hasAttribute('demo')) {
            try { storedState = sessionStorage.getItem(group.dataset.stateKey); } catch (_) {}
          }
          const collapsed = storedState ? storedState === 'collapsed' : index !== 0;
          group.className = 'platform-sidebar__group' + (collapsed ? ' is-collapsed' : '');
          group.innerHTML = `<button class="platform-sidebar__group-title" type="button" aria-expanded="${!collapsed}"><span class="platform-sidebar__icon" aria-hidden="true"><img src="${assetBase}${groupIcons[index]}" alt=""></span><span class="platform-sidebar__group-label">${label}</span><span class="platform-sidebar__group-chevron" aria-hidden="true"><img src="${assetBase}icon-sidebar-section-chevron.svg" alt=""></span></button><div class="platform-sidebar__group-items"></div>`;
          entries.forEach(entry => {
            const item = typeof entry === 'string' ? items.get(entry) : document.createElement('button');
            if (typeof entry !== 'string') {
              const [itemLabel, icon, pageId] = entry;
              item.className = 'platform-sidebar__item platform-sidebar__item--collection';
              item.type = 'button';
              item.title = itemLabel;
              if (pageId) {
                item.dataset.pageId = pageId;
                items.set(pageId, item);
                if (pageId === currentPage) {item.classList.add('platform-sidebar__item--active');item.setAttribute('aria-current','page');group.classList.remove('is-collapsed');group.querySelector('button').setAttribute('aria-expanded','true');}
              }
              item.innerHTML = `<span class="platform-sidebar__icon"><img src="${assetBase}${icon}" alt=""></span><span class="platform-sidebar__label">${itemLabel}</span>`;
            }
            group.lastElementChild.append(item);
          });
          if (group.querySelector('[aria-current="page"]')) {
            group.classList.remove('is-collapsed');
            group.querySelector('.platform-sidebar__group-title')?.setAttribute('aria-expanded', 'true');
          }
          nav.append(group);
        });
        const selectItem = item => {
          items.forEach(button => {
            button.classList.toggle('platform-sidebar__item--active', button === item);
            if (button === item) button.setAttribute('aria-current','page');
            else button.removeAttribute('aria-current');
          });
          nav.querySelectorAll('.platform-sidebar__group').forEach(group => group.classList.toggle('has-active-item', group.contains(item)));
        };
        if (this.hasAttribute('demo')) selectItem(items.get('task-processing'));
        nav.addEventListener('click', event => {
          const item = event.target.closest('.platform-sidebar__item[data-page-id]');
          if (item && nav.contains(item)) selectItem(item);
        });
      }
      if (this.isModelPlatform) {
        this.platformButton.querySelector('.platform-sidebar__platform-name').textContent = this.classList.contains('platform-sidebar--compact-switch') ? '千寻模型平台' : '模型平台';
        this.platformButton.querySelector('.platform-sidebar__platform-short').textContent = '模';
        this.platformButton.querySelector('.platform-sidebar__platform-icon img').src = `${assetBase}icon-model-platform.svg`;
        this.platformMenu.querySelectorAll('[data-platform]').forEach(option => {
          const selected = option.dataset.platform === '模型平台';
          option.classList.toggle('is-selected', selected);
          option.setAttribute('aria-selected', String(selected));
        });
        const badge = document.createElement('span');
        badge.className = 'platform-sidebar__saas-badge';
        badge.textContent = 'saas 专属';
        this.querySelector('[data-page-id="model-resources"]').append(badge);
        if (this.hasAttribute('demo')) {
          const updateModelPage = () => {
            const id = location.hash.slice(1);
            const item = this.querySelector(`[data-page-id="${CSS.escape(id)}"]`) || this.querySelector('[data-page-id="model-data-query"]');
            this.querySelectorAll('[data-page-id]').forEach(button => {
              const active = button === item;
              button.classList.toggle('platform-sidebar__item--active', active);
              if (active) button.setAttribute('aria-current', 'page');
              else button.removeAttribute('aria-current');
            });
            const title = document.querySelector('[data-model-title]');
            if (title) title.textContent = item.title;
            document.title = item.title + ' · 模型平台';
          };
          updateModelPage();
          window.addEventListener('hashchange', updateModelPage);
        }
      }
      if (this.getAttribute('variant') === 'style-variant') this.setupGroupNavigation();
      let initialWidth = this.hasAttribute('collapsed') ? COLLAPSED_WIDTH : EXPANDED_WIDTH;
      if (this.getAttribute('variant') === 'style-variant' && !this.hasAttribute('demo') && !this.hasAttribute('collapsed')) {
        initialWidth = EXPANDED_WIDTH;
        try { if (sessionStorage.getItem('platform-sidebar-pinned') === 'false') initialWidth = COLLAPSED_WIDTH; } catch (_) {}
      }
      this.setWidth(initialWidth);
      this.setupInteractions();
      requestAnimationFrame(() => requestAnimationFrame(() => document.documentElement.classList.add('platform-sidebar-ready')));
      if (componentCatalog) {
        this.querySelector('.platform-sidebar__brand-caption').textContent = '组件';
        this.platformButton.remove();
        this.platformMenu.remove();
        this.querySelector('.platform-sidebar__footer').hidden = true;
      }
    }

    setupGroupNavigation() {
      this.classList.add('platform-sidebar--group-navigation');
      const nav = this.querySelector('.platform-sidebar__nav');
      const icons = {
        '数据': 'nav-database.svg', '训练': 'nav-group-processing.svg',
        '评测': 'nav-tasks.svg', '配置': 'nav-group-settings.svg',
        '管理': 'nav-group-operations.svg', '基础组件': 'nav-operator.svg',
        '业务组件': 'nav-group-workbench.svg'
      };
      const scope = this.isModelPlatform ? 'model' : this.getAttribute('catalog') === 'components' ? 'components' : 'data';
      nav.querySelectorAll('.platform-sidebar__group').forEach((group, index) => {
        const heading = group.querySelector('.platform-sidebar__group-title');
        const label = heading.querySelector('.platform-sidebar__group-label') || heading.firstElementChild;
        label.classList.add('platform-sidebar__group-label');
        if (!heading.querySelector('.platform-sidebar__icon')) {
          const icon = document.createElement('span');
          icon.className = 'platform-sidebar__icon';
          icon.setAttribute('aria-hidden', 'true');
          icon.innerHTML = `<img src="${assetBase}${icons[label.textContent] || 'nav-project.svg'}" alt="">`;
          heading.prepend(icon);
        }
        if (!group.dataset.stateKey) {
          group.dataset.stateKey = `platform-sidebar-group:${scope}:${label.textContent}`;
          let storedState = null;
          if (!this.hasAttribute('demo')) {
            try {
              if (performance.getEntriesByType('navigation')[0]?.type === 'reload') sessionStorage.removeItem(group.dataset.stateKey);
              storedState = sessionStorage.getItem(group.dataset.stateKey);
            } catch (_) {}
          }
          const hasActiveItem = !!group.querySelector('[aria-current="page"]');
          const collapsed = hasActiveItem ? false : storedState ? storedState === 'collapsed' : index !== 0;
          group.classList.toggle('is-collapsed', collapsed);
          heading.setAttribute('aria-expanded', String(!collapsed));
        }
      });
      const flyout = document.createElement('div');
      flyout.className = 'platform-sidebar__group-flyout';
      flyout.setAttribute('role', 'group');
      flyout.hidden = true;
      this.sidebar.append(flyout);
      let flyoutGroup = null;
      let hideTimer;
      const hideFlyout = () => {
        clearTimeout(hideTimer);
        flyout.hidden = true;
        flyoutGroup = null;
      };
      const scheduleHide = () => {
        clearTimeout(hideTimer);
        hideTimer = setTimeout(hideFlyout, 150);
      };
      const showFlyout = group => {
        clearTimeout(hideTimer);
        if (this.sidebar.dataset.expanded !== 'false') return hideFlyout();
        this.setPlatformMenuOpen?.(false);
        const label = group.querySelector('.platform-sidebar__group-label').textContent;
        flyoutGroup = group;
        flyout.setAttribute('aria-label', `${label}菜单`);
        flyout.innerHTML = '<div class="platform-sidebar__group-flyout-items"></div>';
        [...group.querySelectorAll('.platform-sidebar__group-items > .platform-sidebar__item')].forEach((item, index) => {
          const option = document.createElement('button');
          option.className = 'platform-sidebar__group-flyout-item';
          if (item.getAttribute('aria-current') === 'page' || item.classList.contains('platform-sidebar__item--active')) {
            option.classList.add('is-selected');
            option.setAttribute('aria-current', 'page');
          }
          option.type = 'button';
          option.dataset.index = index;
          option.innerHTML = item.innerHTML;
          flyout.lastElementChild.append(option);
        });
        flyout.hidden = false;
        const heading = group.querySelector('.platform-sidebar__group-title').getBoundingClientRect();
        const sidebar = this.sidebar.getBoundingClientRect();
        flyout.style.left = `${Math.max(8, Math.min(sidebar.right + 8, window.innerWidth - flyout.offsetWidth - 8))}px`;
        flyout.style.top = `${Math.max(8, Math.min(heading.top, window.innerHeight - flyout.offsetHeight - 8))}px`;
      };
      nav.querySelectorAll('.platform-sidebar__group').forEach(group => {
        const heading = group.querySelector('.platform-sidebar__group-title');
        heading.setAttribute('aria-label', group.querySelector('.platform-sidebar__group-label').textContent);
        heading.addEventListener('pointerenter', () => showFlyout(group));
        heading.addEventListener('pointerleave', scheduleHide);
        heading.addEventListener('focusin', () => showFlyout(group));
        heading.addEventListener('focusout', scheduleHide);
      });
      this.showGroupFlyout = showFlyout;
      this.hideGroupFlyout = hideFlyout;
      flyout.addEventListener('pointerenter', () => clearTimeout(hideTimer));
      flyout.addEventListener('pointerleave', scheduleHide);
      flyout.addEventListener('focusin', () => clearTimeout(hideTimer));
      flyout.addEventListener('focusout', scheduleHide);
      flyout.addEventListener('click', event => {
        const option = event.target.closest('[data-index]');
        if (!option || !flyoutGroup) return;
        flyoutGroup.querySelectorAll('.platform-sidebar__group-items > .platform-sidebar__item')[Number(option.dataset.index)]?.click();
        hideFlyout();
      });
      flyout.addEventListener('keydown', event => {
        if (event.key !== 'Escape') return;
        flyoutGroup?.querySelector('.platform-sidebar__group-title').focus();
        hideFlyout();
      });
      this.querySelector('.platform-sidebar__main').addEventListener('scroll', hideFlyout);
      window.addEventListener('resize', hideFlyout);
    }

    setWidth(width) {
      this.hideGroupFlyout?.();
      this.setPlatformMenuOpen?.(false);
      const nextWidth = Math.max(COLLAPSED_WIDTH, Math.min(EXPANDED_WIDTH, Math.round(width)));
      const expanded = nextWidth >= EXPANDED_THRESHOLD;
      this.navWidth = nextWidth;
      if (this.pinButton) {
        this.pinButton.setAttribute('aria-pressed', String(expanded));
        this.pinButton.setAttribute('aria-label', expanded ? '取消固定导航' : '固定导航');
        this.pinButton.title = expanded ? '取消固定导航' : '固定导航';
      }
      this.classList.remove('is-hover-expanded');
      this.style.width = `${nextWidth}px`;
      this.sidebar.style.width = `${nextWidth}px`;
      this.sidebar.dataset.expanded = String(expanded);
      this.resizeHandle.setAttribute('aria-valuenow', String(nextWidth));
      document.documentElement.style.setProperty('--platform-sidebar-width', `${nextWidth}px`);
      this.dispatchEvent(new CustomEvent('platform-sidebar-resize', { bubbles: true, detail: { width: nextWidth, expanded } }));
    }

    setupInteractions() {
      if (this.getAttribute('variant') === 'style-variant') {
        this.pinButton = document.createElement('button');
        this.pinButton.type = 'button';
        this.pinButton.className = 'platform-sidebar__pin';
        this.pinButton.innerHTML = '<svg width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden="true"><rect x="2.5" y="2.5" width="15" height="15" rx="2.5" stroke="currentColor" stroke-width="1.5"/><path d="M8 2.5v15" stroke="currentColor" stroke-width="1.5"/></svg>';
        this.querySelector('.platform-sidebar__brand').append(this.pinButton);
        this.setWidth(this.navWidth);
        this.pinButton.addEventListener('click', () => {
          const pinned = this.navWidth < EXPANDED_THRESHOLD;
          this.setWidth(pinned ? EXPANDED_WIDTH : COLLAPSED_WIDTH);
          if (!this.hasAttribute('demo')) {
            try { sessionStorage.setItem('platform-sidebar-pinned', String(pinned)); } catch (_) {}
          }
          if (!pinned) this.pinButton.blur();
        });

      }
      const versionButtons = [...this.querySelectorAll('.platform-sidebar__version button')];
      const themeVariant = this.getAttribute('variant') === 'style-variant';
      if (themeVariant && !this.hasAttribute('demo')) {
        this.setAttribute('palette', 'dark');
      }
      versionButtons.forEach(button => {
        button.setAttribute('aria-pressed', String(button.classList.contains('is-active')));
        button.setAttribute('aria-label', button.textContent === '新' ? '新版（示例）' : '旧版（示例）');
        button.addEventListener('click', () => {
          versionButtons.forEach(item => {
            item.classList.toggle('is-active', item === button);
            item.setAttribute('aria-pressed', String(item === button));
          });

        });
      });
      let startX = 0;
      let startWidth = COLLAPSED_WIDTH;
      this.resizeHandle.addEventListener('pointerdown', (event) => {
        startX = event.clientX;
        startWidth = this.sidebar.getBoundingClientRect().width;
        document.body?.classList.add('is-resizing-platform-sidebar');
        this.classList.add('is-resizing-host');
        this.sidebar.classList.add('is-resizing');
        this.resizeHandle.setPointerCapture(event.pointerId);
      });
      this.resizeHandle.addEventListener('pointermove', (event) => {
        if (this.resizeHandle.hasPointerCapture(event.pointerId)) this.setWidth(startWidth + event.clientX - startX);
      });
      const finish = (event) => {
        if (this.resizeHandle.hasPointerCapture(event.pointerId)) this.resizeHandle.releasePointerCapture(event.pointerId);
        document.body?.classList.remove('is-resizing-platform-sidebar');
        this.classList.remove('is-resizing-host');
        this.sidebar.classList.remove('is-resizing');
      };
      this.resizeHandle.addEventListener('pointerup', finish);
      this.resizeHandle.addEventListener('pointercancel', finish);
      this.resizeHandle.addEventListener('dblclick', () => this.setWidth(this.sidebar.dataset.expanded === 'true' ? COLLAPSED_WIDTH : EXPANDED_WIDTH));
      this.resizeHandle.addEventListener('keydown', (event) => {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault();
        if (event.key === 'Home') return this.setWidth(COLLAPSED_WIDTH);
        if (event.key === 'End') return this.setWidth(EXPANDED_WIDTH);
        this.setWidth(this.sidebar.getBoundingClientRect().width + (event.key === 'ArrowRight' ? 10 : -10));
      });
      this.querySelectorAll('.platform-sidebar__group-title').forEach((button) => button.addEventListener('click', () => {
        const group = button.closest('.platform-sidebar__group');
        if (this.showGroupFlyout && this.sidebar.dataset.expanded === 'false') {
          this.showGroupFlyout(group);
          return;
        }
        const collapsed = group.classList.toggle('is-collapsed');
        button.setAttribute('aria-expanded', String(!collapsed));
        if (!collapsed && !this.isModelPlatform && !this.showGroupFlyout) {
          this.querySelectorAll('.platform-sidebar__group').forEach(otherGroup => {
            if (otherGroup === group || otherGroup.querySelector('[aria-current="page"]')) return;
            otherGroup.classList.add('is-collapsed');
            otherGroup.querySelector('.platform-sidebar__group-title')?.setAttribute('aria-expanded', 'false');
            if (otherGroup.dataset.stateKey && !this.hasAttribute('demo')) {
              try { sessionStorage.setItem(otherGroup.dataset.stateKey, 'collapsed'); } catch (_) {}
            }
          });
        }
        if (group.dataset.stateKey && !this.hasAttribute('demo')) {
          try { sessionStorage.setItem(group.dataset.stateKey, collapsed ? 'collapsed' : 'expanded'); } catch (_) {}
        }
      }));
      this.querySelectorAll('.platform-sidebar__item[data-page-id]').forEach((button) => {
        button.addEventListener('click', () => {
          if (this.getAttribute('variant') === 'components' || this.getAttribute('catalog') === 'components') {
            this.dispatchEvent(new CustomEvent('component-select', {bubbles:true,detail:{id:button.dataset.pageId,title:button.title}}));
            return;
          }
          if (this.isModelPlatform) {
            if (this.hasAttribute('demo')) location.hash = button.dataset.pageId;
            else {
              const route = modelRoutes[button.dataset.pageId];
              if (route && route !== location.pathname) window.location.assign(route);
            }
            return;
          }
          if (this.hasAttribute('demo')) return;
          const route = pageRoutes[button.dataset.pageId];
          if (route && button.dataset.pageId !== currentPage) window.location.assign(route);
        });
      });

      const setPlatformMenuOpen = (open) => {
        this.platformMenu.hidden = !open;
        if (open && this.classList.contains('platform-sidebar--compact-switch')) {
          this.hideGroupFlyout?.();
          const trigger = this.platformButton.getBoundingClientRect();
          const sidebar = this.sidebar.getBoundingClientRect();
          const collapsed = this.sidebar.dataset.expanded === 'false';
          this.platformMenu.style.width = `${collapsed ? 188 : sidebar.width - 24}px`;
          this.platformMenu.style.left = `${Math.max(8, Math.min(collapsed ? sidebar.right + 8 : sidebar.left + 12, window.innerWidth - this.platformMenu.offsetWidth - 8))}px`;
          this.platformMenu.style.top = `${Math.max(8, Math.min(collapsed ? trigger.top : trigger.bottom + 8, window.innerHeight - this.platformMenu.offsetHeight - 8))}px`;
        }
        this.platformButton.setAttribute('aria-expanded', String(open));
        this.sidebar.classList.toggle('is-platform-menu-open', open);
      };
      this.setPlatformMenuOpen = setPlatformMenuOpen;
      window.addEventListener('resize', () => setPlatformMenuOpen(false));
      this.querySelector('.platform-sidebar__main').addEventListener('scroll', () => setPlatformMenuOpen(false));
      this.platformButton.addEventListener('click', (event) => {
        event.stopPropagation();
        setPlatformMenuOpen(this.platformMenu.hidden);
      });
      this.platformMenu.addEventListener('click', (event) => {
        const option = event.target.closest('.platform-sidebar__platform-option');
        if (!option) return;
        if (!this.hasAttribute('demo') && option.dataset.platform === '模型平台' && !this.isModelPlatform) {
          window.location.assign('/model/data/query');
          return;
        }
        if (!this.hasAttribute('demo') && option.dataset.platform === '数据平台' && this.isModelPlatform) {
          window.location.assign(pageRoutes['task-processing']);
          return;
        }
        this.platformMenu.querySelectorAll('.platform-sidebar__platform-option').forEach((item) => {
          const selected = item === option;
          item.classList.toggle('is-selected', selected);
          item.setAttribute('aria-selected', String(selected));
        });
        this.platformButton.querySelector('.platform-sidebar__platform-short').textContent = option.dataset.platform.slice(0, 1);
        this.platformButton.querySelector('.platform-sidebar__platform-name').textContent = this.classList.contains('platform-sidebar--compact-switch') ? '千寻' + option.dataset.platform : option.dataset.platform;
        setPlatformMenuOpen(false);
      });
      document.addEventListener('click', (event) => {
        if (!this.contains(event.target)) setPlatformMenuOpen(false);
      });
      document.addEventListener('keydown', (event) => {
        if (event.key !== 'Escape' || this.platformMenu.hidden) return;
        setPlatformMenuOpen(false);
        this.platformButton.focus();
      });
    }
  }
  if (!customElements.get("platform-sidebar")) customElements.define("platform-sidebar", PlatformSidebar);
})();
