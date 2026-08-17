/**
 * Perchance AI Studio — Pure Perchance Engine with Live WebSocket Streaming (ws:// / wss://)
 * Bespoke Custom Dropdowns & Responsive Neural Canvas
 */

document.addEventListener('DOMContentLoaded', () => {
  // Application State
  const state = {
    presets: { styles: [], enhancers: {}, prompts: [] },
    gallery: [],
    selectedStyle: null,
    selectedShape: 'square',
    guidanceScale: 7.0,
    isRandomSeed: true,
    customSeed: -1,
    batchCount: 1,
    isGenerating: false,
    timerInterval: null,
    activeModalItem: null,
    ws: null,
    wsConnected: false,
  };

  // DOM Elements
  const tabStudioBtn = document.getElementById('tabStudioBtn');
  const tabGalleryBtn = document.getElementById('tabGalleryBtn');
  const studioView = document.getElementById('studioView');
  const galleryView = document.getElementById('galleryView');
  const galleryCountBadge = document.getElementById('galleryCountBadge');
  const statusIndicator = document.getElementById('statusIndicator');
  const statusLabel = document.getElementById('statusLabel');

  const promptInput = document.getElementById('promptInput');
  const charCount = document.getElementById('charCount');
  const inspireBtn = document.getElementById('inspireBtn');
  const clearPromptBtn = document.getElementById('clearPromptBtn');

  const toggleEnhancersBtn = document.getElementById('toggleEnhancersBtn');
  const enhancersContent = document.getElementById('enhancersContent');
  const enhancersCategories = document.getElementById('enhancersCategories');

  // Bespoke Custom Dropdown Elements (Style, Shape, Advanced)
  const styleDropdown = document.getElementById('styleDropdown');
  const styleDropdownTrigger = document.getElementById('styleDropdownTrigger');
  const selectedStyleTitle = document.getElementById('selectedStyleTitle');
  const selectedStyleDesc = document.getElementById('selectedStyleDesc');
  const selectedStyleBadge = document.getElementById('selectedStyleBadge');
  const styleDropdownMenu = document.getElementById('styleDropdownMenu');
  const styleDropdownItems = document.getElementById('styleDropdownItems');
  const styleSearchInput = document.getElementById('styleSearchInput');

  const shapeDropdown = document.getElementById('shapeDropdown');
  const shapeDropdownTrigger = document.getElementById('shapeDropdownTrigger');
  const selectedShapeTitle = document.getElementById('selectedShapeTitle');
  const selectedShapeDesc = document.getElementById('selectedShapeDesc');
  const selectedShapeRes = document.getElementById('selectedShapeRes');
  const shapePreviewBox = document.getElementById('shapePreviewBox');
  const shapeDropdownMenu = document.getElementById('shapeDropdownMenu');

  const advancedDropdown = document.getElementById('advancedDropdown');
  const advancedDropdownTrigger = document.getElementById('advancedDropdownTrigger');
  const selectedAdvancedTitle = document.getElementById('selectedAdvancedTitle');
  const selectedAdvancedDesc = document.getElementById('selectedAdvancedDesc');
  const selectedAdvancedBadge = document.getElementById('selectedAdvancedBadge');
  const advancedDropdownMenu = document.getElementById('advancedDropdownMenu');

  const negativePromptInput = document.getElementById('negativePromptInput');
  const guidanceScaleInput = document.getElementById('guidanceScaleInput');
  const guidanceScaleVal = document.getElementById('guidanceScaleVal');
  const randomSeedToggle = document.getElementById('randomSeedToggle');
  const seedInput = document.getElementById('seedInput');
  const batchButtons = document.querySelectorAll('.batch-btn');

  const generateBtn = document.getElementById('generateBtn');
  const generatingState = document.getElementById('generatingState');
  const genStageTitle = document.getElementById('genStageTitle');
  const genStageDesc = document.getElementById('genStageDesc');
  const genTimer = document.getElementById('genTimer');
  const progressBarFill = document.getElementById('progressBarFill');
  const currentImagesGrid = document.getElementById('currentImagesGrid');
  const emptyCanvas = document.getElementById('emptyCanvas');
  const resultsHeader = document.getElementById('resultsHeader');
  const resultsMeta = document.getElementById('resultsMeta');
  const samplePromptChips = document.getElementById('samplePromptChips');

  const gallerySearchInput = document.getElementById('gallerySearchInput');
  const galleryStyleFilters = document.getElementById('galleryStyleFilters');
  const galleryGrid = document.getElementById('galleryGrid');
  const galleryEmptyState = document.getElementById('galleryEmptyState');

  const lightboxModal = document.getElementById('lightboxModal');
  const closeModalBtn = document.getElementById('closeModalBtn');
  const modalImage = document.getElementById('modalImage');
  const modalPromptText = document.getElementById('modalPromptText');
  const modalCopyPromptBtn = document.getElementById('modalCopyPromptBtn');
  const modalStyleVal = document.getElementById('modalStyleVal');
  const modalResolutionVal = document.getElementById('modalResolutionVal');
  const modalSeedVal = document.getElementById('modalSeedVal');
  const modalGuidanceVal = document.getElementById('modalGuidanceVal');
  const modalRemixBtn = document.getElementById('modalRemixBtn');
  const modalDownloadLink = document.getElementById('modalDownloadLink');
  const modalDeleteBtn = document.getElementById('modalDeleteBtn');
  const toastContainer = document.getElementById('toastContainer');

  // =========================================================================
  // Initialize Application
  // =========================================================================
  async function init() {
    setupEventListeners();
    setupCustomDropdowns();
    setupWebSocket();
    await fetchPresets();
    await fetchGallery();
    checkStatus();
  }

  // =========================================================================
  // WebSocket Live Streaming Connection (ws:// / wss://)
  // =========================================================================
  let currentWsResolve = null;
  let currentWsReject = null;
  let wsAccumulatedResults = [];

  function setupWebSocket() {
    try {
      const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${proto}//${location.host}/ws/generate`;
      state.ws = new WebSocket(wsUrl);

      state.ws.onopen = () => {
        state.wsConnected = true;
        console.log('[WebSocket] Live stream channel connected');
      };

      state.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          handleWebSocketMessage(msg);
        } catch (e) {
          console.error('[WebSocket] JSON parse error:', e);
        }
      };

      state.ws.onclose = () => {
        state.wsConnected = false;
        setTimeout(setupWebSocket, 3000);
      };

      state.ws.onerror = (err) => {
        console.warn('[WebSocket] Connection note:', err);
      };
    } catch (e) {
      console.warn('WebSocket setup skipped, HTTP fallback active');
    }
  }

  function handleWebSocketMessage(msg) {
    if (msg.type === 'status') {
      if (genStageTitle) genStageTitle.textContent = msg.stage || 'Processing...';
      if (genStageDesc) {
        if (msg.queue_position) {
          genStageDesc.textContent = `Queued request — Estimated wait: ~${msg.estimated_wait || 10}s`;
        } else if (msg.worker_id) {
          genStageDesc.textContent = `Worker #${msg.worker_id} synthesizing latents (${msg.progress || 0}%)`;
        } else {
          genStageDesc.textContent = `Streaming Perchance neural diffusion (${msg.progress || 0}%)`;
        }
      }
      if (progressBarFill && msg.progress) {
        progressBarFill.style.width = `${msg.progress}%`;
      }
    } else if (msg.type === 'image_ready') {
      if (msg.item) {
        wsAccumulatedResults.push(msg.item);
        appendResultLive(msg.item);
      }
    } else if (msg.type === 'complete') {
      if (currentWsResolve) {
        currentWsResolve(msg);
        currentWsResolve = null;
      }
    } else if (msg.type === 'error') {
      if (currentWsReject) {
        currentWsReject(new Error(msg.message || 'Generation failed'));
        currentWsReject = null;
      }
    }
  }

  function appendResultLive(item) {
    if (emptyCanvas) emptyCanvas.style.display = 'none';
    resultsHeader.style.display = 'flex';
    resultsMeta.textContent = `Generated ${wsAccumulatedResults.length} image(s)`;

    const card = createArtworkCard(item);
    currentImagesGrid.appendChild(card);
  }

  // =========================================================================
  // Presets & Data Fetching
  // =========================================================================
  async function fetchPresets() {
    try {
      const res = await fetch('/api/presets');
      if (!res.ok) throw new Error('Failed to load presets');
      state.presets = await res.json();
      renderCustomStyleDropdown(state.presets.styles || []);
      renderEnhancers(state.presets.enhancers || {});
      const sampleList = state.presets.sample_prompts || state.presets.prompts || [];
      renderSamplePrompts(sampleList);
    } catch (err) {
      console.error('Error fetching presets:', err);
      showToast('Could not load style presets', 'error');
    }
  }

  async function fetchGallery() {
    try {
      const res = await fetch('/api/gallery');
      if (!res.ok) throw new Error('Failed to load gallery');
      state.gallery = await res.json();
      updateGalleryCount();
      renderGallery();
      renderGalleryFilters();
    } catch (err) {
      console.error('Error fetching gallery:', err);
    }
  }

  async function checkStatus() {
    try {
      const res = await fetch('/api/status');
      if (res.ok) {
        const data = await res.json();
        const workerCountLabel = document.getElementById('workerCountLabel');
        const workerCapacityBadge = document.getElementById('workerCapacityBadge');

        if (workerCountLabel && data.total_workers) {
          const busy = data.busy_workers || 0;
          const total = data.total_workers || 1;
          const waiting = data.waiting_in_queue || 0;

          if (waiting > 0) {
            workerCountLabel.textContent = `${waiting} Queued (${busy}/${total} Busy)`;
            if (workerCapacityBadge) {
              workerCapacityBadge.style.borderColor = 'rgba(245, 158, 11, 0.4)';
              workerCapacityBadge.style.color = '#fde68a';
            }
          } else if (busy > 0) {
            workerCountLabel.textContent = `${total - busy}/${total} Workers Free`;
            if (workerCapacityBadge) {
              workerCapacityBadge.style.borderColor = 'rgba(59, 130, 246, 0.3)';
              workerCapacityBadge.style.color = '#93c5fd';
            }
          } else {
            workerCountLabel.textContent = `${total} Workers Ready`;
            if (workerCapacityBadge) {
              workerCapacityBadge.style.borderColor = 'rgba(16, 185, 129, 0.3)';
              workerCapacityBadge.style.color = '#6ee7b7';
            }
          }
        }

        if (data.busy_workers > 0) {
          statusIndicator.classList.add('busy');
          statusLabel.textContent = data.waiting_in_queue > 0 ? 'Queue Active' : 'Generating...';
        } else {
          statusIndicator.classList.remove('busy');
          statusLabel.textContent = 'Engine Ready';
        }
      }
    } catch (e) {
      statusLabel.textContent = 'Offline';
    }
  }

  // =========================================================================
  // Custom Dropdown Implementation
  // =========================================================================
  function renderCustomStyleDropdown(styles) {
    if (!styleDropdownItems) return;
    styleDropdownItems.innerHTML = '';

    // Group styles
    const categories = {};
    styles.forEach(s => {
      const cat = s.category || 'Curated Styles';
      if (!categories[cat]) categories[cat] = [];
      categories[cat].push(s);
    });

    Object.entries(categories).forEach(([catName, catStyles]) => {
      const catLabel = document.createElement('div');
      catLabel.className = 'dropdown-category-label';
      catLabel.textContent = catName;
      styleDropdownItems.appendChild(catLabel);

      catStyles.forEach((s, idx) => {
        const item = document.createElement('div');
        const isDefault = (s.id === 'none' || idx === 0 && !state.selectedStyle);
        item.className = `dropdown-item ${isDefault ? 'active' : ''}`;
        item.dataset.styleId = s.id;
        item.dataset.name = s.name;
        item.dataset.prompt = s.style_prompt || '';
        item.dataset.badge = s.badge || 'Style';
        item.dataset.desc = s.style_prompt ? `Applies: "${s.style_prompt.substring(0, 38)}..."` : 'Natural diffusion without constraint';

        item.innerHTML = `
          <div class="item-left">
            <div class="item-info">
              <span class="item-title">${escapeHtml(s.name)}</span>
              <span class="item-desc">${escapeHtml(item.dataset.desc)}</span>
            </div>
          </div>
          <div class="trigger-right">
            <span class="item-badge">${escapeHtml(s.badge)}</span>
            <span class="check-icon">✓</span>
          </div>
        `;

        item.addEventListener('click', () => selectCustomStyle(s, item));
        styleDropdownItems.appendChild(item);

        if (isDefault && !state.selectedStyle) {
          selectCustomStyle(s, item, false);
        }
      });
    });
  }

  function selectCustomStyle(styleObj, itemEl, closeMenu = true) {
    state.selectedStyle = styleObj;
    selectedStyleTitle.textContent = styleObj.name;
    selectedStyleDesc.textContent = styleObj.style_prompt ? `"${styleObj.style_prompt.substring(0, 36)}..."` : 'Natural diffusion without constraint';
    selectedStyleBadge.textContent = styleObj.badge || 'Style';

    if (styleDropdownItems) {
      styleDropdownItems.querySelectorAll('.dropdown-item').forEach(i => i.classList.remove('active'));
      if (itemEl) itemEl.classList.add('active');
    }

    if (closeMenu && styleDropdown) {
      styleDropdown.classList.remove('open');
      styleDropdownTrigger.setAttribute('aria-expanded', 'false');
    }
  }

  function setupCustomDropdowns() {
    // Style Dropdown Trigger
    if (styleDropdownTrigger) {
      styleDropdownTrigger.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = styleDropdown.classList.toggle('open');
        styleDropdownTrigger.setAttribute('aria-expanded', isOpen);
        if (shapeDropdown) shapeDropdown.classList.remove('open');
        if (isOpen && styleSearchInput) {
          setTimeout(() => styleSearchInput.focus(), 50);
        }
      });
    }

    // Style Search Input Filtering
    if (styleSearchInput) {
      styleSearchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        const items = styleDropdownItems.querySelectorAll('.dropdown-item');
        items.forEach(it => {
          const name = (it.dataset.name || '').toLowerCase();
          const badge = (it.dataset.badge || '').toLowerCase();
          const matches = name.includes(query) || badge.includes(query);
          it.style.display = matches ? 'flex' : 'none';
        });
      });
    }

    // Shape Dropdown Trigger
    if (shapeDropdownTrigger) {
      shapeDropdownTrigger.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = shapeDropdown.classList.toggle('open');
        shapeDropdownTrigger.setAttribute('aria-expanded', isOpen);
        if (styleDropdown) styleDropdown.classList.remove('open');
      });
    }

    // Shape Dropdown Items
    if (shapeDropdownMenu) {
      const shapeItems = shapeDropdownMenu.querySelectorAll('.dropdown-item');
      shapeItems.forEach(item => {
        item.addEventListener('click', () => {
          shapeItems.forEach(i => i.classList.remove('active'));
          item.classList.add('active');

          const shape = item.dataset.shape;
          const title = item.dataset.title;
          const res = item.dataset.res;
          const desc = item.dataset.desc;

          state.selectedShape = shape;
          selectedShapeTitle.textContent = title;
          selectedShapeDesc.textContent = desc;
          selectedShapeRes.textContent = res;

          shapePreviewBox.className = `aspect-preview-box ${shape}`;

          shapeDropdown.classList.remove('open');
          shapeDropdownTrigger.setAttribute('aria-expanded', 'false');
        });
      });
    }

    // Advanced Dropdown Trigger
    if (advancedDropdownTrigger) {
      advancedDropdownTrigger.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = advancedDropdown.classList.toggle('open');
        advancedDropdownTrigger.setAttribute('aria-expanded', isOpen);
        if (styleDropdown) styleDropdown.classList.remove('open');
        if (shapeDropdown) shapeDropdown.classList.remove('open');
      });
    }

    // Close on click outside
    document.addEventListener('click', (e) => {
      if (styleDropdown && !styleDropdown.contains(e.target)) {
        styleDropdown.classList.remove('open');
        if (styleDropdownTrigger) styleDropdownTrigger.setAttribute('aria-expanded', 'false');
      }
      if (shapeDropdown && !shapeDropdown.contains(e.target)) {
        shapeDropdown.classList.remove('open');
        if (shapeDropdownTrigger) shapeDropdownTrigger.setAttribute('aria-expanded', 'false');
      }
      if (advancedDropdown && !advancedDropdown.contains(e.target)) {
        advancedDropdown.classList.remove('open');
        if (advancedDropdownTrigger) advancedDropdownTrigger.setAttribute('aria-expanded', 'false');
      }
    });

    // Close on ESC
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        if (styleDropdown) styleDropdown.classList.remove('open');
        if (shapeDropdown) shapeDropdown.classList.remove('open');
        if (advancedDropdown) advancedDropdown.classList.remove('open');
      }
    });
  }

  function updateAdvancedSummary() {
    if (!selectedAdvancedDesc) return;
    const cfg = state.guidanceScale.toFixed(1);
    const seed = state.isRandomSeed ? 'Random Seed' : `Seed #${seedInput.value || 'Custom'}`;
    const batch = `Batch: ${state.batchCount}`;
    selectedAdvancedDesc.textContent = `CFG: ${cfg} • ${seed} • ${batch}`;
  }

  function renderEnhancers(enhancers) {
    if (!enhancersCategories) return;
    enhancersCategories.innerHTML = '';
    Object.entries(enhancers).forEach(([category, tags]) => {
      const catDiv = document.createElement('div');
      catDiv.className = 'enhancer-category';

      const title = document.createElement('div');
      title.className = 'enhancers-category-title';
      title.textContent = category.charAt(0).toUpperCase() + category.slice(1);
      catDiv.appendChild(title);

      const tagsRow = document.createElement('div');
      tagsRow.className = 'enhancer-tags-row';

      if (Array.isArray(tags)) {
        tags.forEach(item => {
          const tagName = typeof item === 'object' && item.name ? item.name : item;
          const tagValue = typeof item === 'object' && item.tag ? item.tag : (typeof item === 'object' && item.name ? item.name : item);

          const tagBtn = document.createElement('button');
          tagBtn.type = 'button';
          tagBtn.className = 'enhancer-tag';
          tagBtn.textContent = `+ ${tagName}`;
          tagBtn.title = `Add "${tagValue}"`;
          tagBtn.addEventListener('click', () => appendToPrompt(tagValue));
          tagsRow.appendChild(tagBtn);
        });
      }

      catDiv.appendChild(tagsRow);
      enhancersCategories.appendChild(catDiv);
    });
  }

  function renderSamplePrompts(prompts) {
    samplePromptChips.innerHTML = '';
    prompts.slice(0, 4).forEach(p => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'sample-chip';
      chip.innerHTML = `
        <span class="sample-chip-icon">✦</span>
        <span>${p}</span>
      `;
      chip.addEventListener('click', () => {
        promptInput.value = p;
        updateCharCount();
        promptInput.focus();
      });
      samplePromptChips.appendChild(chip);
    });
  }

  function appendToPrompt(phrase) {
    let current = promptInput.value.trim();
    if (!current) {
      promptInput.value = phrase;
    } else if (!current.toLowerCase().includes(phrase.toLowerCase())) {
      promptInput.value = `${current}, ${phrase}`;
    }
    updateCharCount();
    showToast(`Added "${phrase}" to prompt`, 'info');
  }

  function updateCharCount() {
    const len = promptInput.value.length;
    charCount.textContent = `${len} / 2000`;
  }

  function updateGalleryCount() {
    galleryCountBadge.textContent = state.gallery.length;
  }

  function renderGalleryFilters() {
    const styles = ['all', ...new Set(state.gallery.map(item => item.style || 'Default'))];
    galleryStyleFilters.innerHTML = '';
    styles.forEach(st => {
      const btn = document.createElement('button');
      btn.className = `filter-chip ${st === 'all' ? 'active' : ''}`;
      btn.dataset.style = st;
      btn.textContent = st === 'all' ? 'All Styles' : st;
      btn.addEventListener('click', () => {
        document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        renderGallery();
      });
      galleryStyleFilters.appendChild(btn);
    });
  }

  function renderGallery() {
    const query = gallerySearchInput.value.toLowerCase().trim();
    const activeFilterBtn = document.querySelector('.filter-chip.active');
    const selectedStyleFilter = activeFilterBtn ? activeFilterBtn.dataset.style : 'all';

    const filtered = state.gallery.filter(item => {
      const matchesSearch = !query || (item.prompt && item.prompt.toLowerCase().includes(query));
      const matchesStyle = selectedStyleFilter === 'all' || (item.style || 'Default') === selectedStyleFilter;
      return matchesSearch && matchesStyle;
    });

    galleryGrid.innerHTML = '';
    if (filtered.length === 0) {
      galleryEmptyState.style.display = 'block';
    } else {
      galleryEmptyState.style.display = 'none';
      filtered.forEach(item => {
        const card = createArtworkCard(item);
        galleryGrid.appendChild(card);
      });
    }
  }

  function createArtworkCard(item) {
    const card = document.createElement('div');
    const shapeClass = item.shape || 'square';
    card.className = `artwork-card ${shapeClass}`;
    card.dataset.id = item.id;

    card.innerHTML = `
      <div class="artwork-thumb-wrapper">
        <img class="artwork-img" src="${item.url}" alt="${escapeHtml(item.prompt)}" loading="lazy">
        <div class="artwork-overlay">
          <div class="overlay-top">
            <button type="button" class="overlay-btn btn-zoom" title="Inspect HD">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>
            </button>
            <a href="${item.download_link || `/api/download/${item.id}`}" class="overlay-btn" title="Download Image">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
            </a>
            <button type="button" class="overlay-btn btn-del" title="Delete Artwork">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
          <div class="overlay-bottom">
            <span class="tag-badge font-mono">Seed: ${item.seed}</span>
          </div>
        </div>
      </div>
      <div class="artwork-footer">
        <p class="artwork-prompt-snip" title="${escapeHtml(item.prompt)}">${escapeHtml(item.prompt)}</p>
        <div class="artwork-tags">
          <span class="tag-badge">${item.style || 'Default'}</span>
          <span>${item.resolution || '768x768'}</span>
        </div>
      </div>
    `;

    card.querySelector('.artwork-thumb-wrapper').addEventListener('click', (e) => {
      if (!e.target.closest('.overlay-btn')) {
        openLightbox(item);
      }
    });

    card.querySelector('.btn-zoom').addEventListener('click', () => openLightbox(item));
    card.querySelector('.btn-del').addEventListener('click', (e) => {
      e.stopPropagation();
      deleteArtwork(item.id);
    });

    return card;
  }

  // =========================================================================
  // Generation Process (WebSocket Streaming with HTTP Fallback)
  // =========================================================================
  async function triggerGeneration() {
    const prompt = promptInput.value.trim();
    if (!prompt) {
      showToast('Please enter a prompt description first', 'error');
      promptInput.focus();
      return;
    }

    if (state.isGenerating) return;

    state.isGenerating = true;
    wsAccumulatedResults = [];
    currentImagesGrid.innerHTML = '';
    updateGeneratingUI(true);

    const styleVal = state.selectedStyle ? state.selectedStyle.style_prompt : null;
    const seedVal = state.isRandomSeed ? -1 : parseInt(seedInput.value, 10) || -1;
    const negativeVal = negativePromptInput.value.trim();

    const payload = {
      prompt: prompt,
      style: styleVal,
      shape: state.selectedShape,
      negative_prompt: negativeVal,
      guidance_scale: state.guidanceScale,
      seed: seedVal,
      count: state.batchCount,
    };

    const startTime = Date.now();
    startProgressTimer();

    try {
      let generatedResults = [];

      // WebSocket live streaming
      if (state.wsConnected && state.ws && state.ws.readyState === WebSocket.OPEN) {
        const wsPromise = new Promise((resolve, reject) => {
          currentWsResolve = resolve;
          currentWsReject = reject;
          state.ws.send(JSON.stringify(payload));
        });

        const completeMsg = await wsPromise;
        generatedResults = completeMsg.results || wsAccumulatedResults;
      } else {
        // Fallback to HTTP REST
        const response = await fetch('/api/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || 'Generation request failed');
        }

        const data = await response.json();
        generatedResults = data.results || [];
      }

      await fetchGallery();
      renderCurrentResults(generatedResults);

      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      showToast(`Generated ${generatedResults.length} artwork(s) in ${elapsed}s!`, 'success');
    } catch (err) {
      console.error('Generation error:', err);
      showToast(`Generation error: ${err.message}`, 'error');
    } finally {
      state.isGenerating = false;
      stopProgressTimer();
      updateGeneratingUI(false);
      checkStatus();
    }
  }

  function renderCurrentResults(results) {
    if (emptyCanvas) emptyCanvas.style.display = 'none';
    resultsHeader.style.display = 'flex';
    resultsMeta.textContent = `Generated ${results.length} image(s)`;

    currentImagesGrid.innerHTML = '';
    results.forEach(item => {
      const card = createArtworkCard(item);
      currentImagesGrid.appendChild(card);
    });
  }

  function startProgressTimer() {
    const startTime = Date.now();
    genStageTitle.textContent = 'Initializing Perchance Neural Pipeline...';
    genStageDesc.textContent = 'Injecting prompts and synthesizing diffusion latents';

    state.timerInterval = setInterval(() => {
      const sec = Math.floor((Date.now() - startTime) / 1000);
      const m = String(Math.floor(sec / 60)).padStart(2, '0');
      const s = String(sec % 60).padStart(2, '0');
      genTimer.textContent = `Elapsed: ${m}:${s}`;
    }, 200);
  }

  function stopProgressTimer() {
    if (state.timerInterval) clearInterval(state.timerInterval);
  }

  function updateGeneratingUI(isGen) {
    if (isGen) {
      generateBtn.disabled = true;
      generateBtn.querySelector('.btn-content').style.display = 'none';
      generateBtn.querySelector('.btn-loader').style.display = 'flex';
      generatingState.style.display = 'block';
      statusIndicator.classList.add('busy');
      statusLabel.textContent = 'Streaming via WebSocket...';
    } else {
      generateBtn.disabled = false;
      generateBtn.querySelector('.btn-content').style.display = 'flex';
      generateBtn.querySelector('.btn-loader').style.display = 'none';
      generatingState.style.display = 'none';
      statusIndicator.classList.remove('busy');
      statusLabel.textContent = 'Engine Ready';
    }
  }

  // =========================================================================
  // Lightbox Modal & Actions
  // =========================================================================
  function openLightbox(item) {
    state.activeModalItem = item;
    modalImage.src = item.url;
    modalPromptText.textContent = item.prompt;
    modalStyleVal.textContent = item.style || 'Default';
    modalResolutionVal.textContent = item.resolution || '768x768';
    modalSeedVal.textContent = item.seed !== undefined ? item.seed : '-1';
    modalGuidanceVal.textContent = item.guidance_scale || '7.0';
    modalDownloadLink.href = item.download_link || `/api/download/${item.id}`;
    modalDownloadLink.download = `perchance_${item.id}.jpeg`;

    lightboxModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }

  function closeLightbox() {
    lightboxModal.style.display = 'none';
    document.body.style.overflow = '';
    state.activeModalItem = null;
  }

  async function deleteArtwork(id) {
    if (!confirm('Are you sure you want to delete this artwork?')) return;
    try {
      const res = await fetch(`/api/gallery/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Delete failed');

      state.gallery = state.gallery.filter(i => i.id !== id);
      updateGalleryCount();
      renderGallery();
      renderGalleryFilters();

      const curCard = currentImagesGrid.querySelector(`[data-id="${id}"]`);
      if (curCard) curCard.remove();

      if (state.activeModalItem && state.activeModalItem.id === id) {
        closeLightbox();
      }

      showToast('Artwork removed', 'info');
    } catch (e) {
      showToast('Failed to delete artwork', 'error');
    }
  }

  function remixArtwork(item) {
    promptInput.value = item.prompt || '';
    updateCharCount();

    if (item.style && state.presets.styles) {
      const match = state.presets.styles.find(
        s => s.style_prompt && s.style_prompt.toLowerCase() === item.style.toLowerCase()
      );
      if (match && styleDropdownItems) {
        const itemEl = styleDropdownItems.querySelector(`[data-style-id="${match.id}"]`);
        selectCustomStyle(match, itemEl, true);
      }
    }

    if (item.shape && shapeDropdownMenu) {
      const targetShapeItem = shapeDropdownMenu.querySelector(`[data-shape="${item.shape}"]`);
      if (targetShapeItem) targetShapeItem.click();
    }

    if (item.seed !== undefined && item.seed !== -1) {
      randomSeedToggle.checked = false;
      seedInput.disabled = false;
      seedInput.value = item.seed;
    }

    if (item.guidance_scale) {
      guidanceScaleInput.value = item.guidance_scale;
      guidanceScaleVal.textContent = parseFloat(item.guidance_scale).toFixed(1);
      state.guidanceScale = parseFloat(item.guidance_scale);
    }

    closeLightbox();
    switchToTab('studio');
    showToast('Settings loaded into Studio', 'success');
  }

  // =========================================================================
  // Toast Helper
  // =========================================================================
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = '✦';
    if (type === 'success') icon = '✓';
    if (type === 'error') icon = '✕';

    toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function switchToTab(tabName) {
    if (tabName === 'studio') {
      tabStudioBtn.classList.add('active');
      tabGalleryBtn.classList.remove('active');
      studioView.style.display = 'block';
      galleryView.style.display = 'none';
    } else {
      tabGalleryBtn.classList.add('active');
      tabStudioBtn.classList.remove('active');
      galleryView.style.display = 'block';
      studioView.style.display = 'none';
      renderGallery();
    }
  }

  // =========================================================================
  // Event Listeners
  // =========================================================================
  function setupEventListeners() {
    tabStudioBtn.addEventListener('click', () => switchToTab('studio'));
    tabGalleryBtn.addEventListener('click', () => switchToTab('gallery'));

    inspireBtn.addEventListener('click', () => {
      const sampleList = (state.presets && (state.presets.sample_prompts || state.presets.prompts)) || [
        "A majestic mechanical dragon with translucent crystal wings soaring over neon-lit futuristic Tokyo at midnight",
        "Cozy hidden library inside a giant ancient hollow redwood tree with warm fireflies and floating lanterns",
        "Serene Japanese garden in autumn with vibrant red maple leaves floating on a crystal koi pond, 8k",
        "A cute astronaut red panda discovering glowing alien flora on an unexplored purple moon",
        "Cyberpunk street noodle vendor in rainy Neo-Seoul with neon reflections on wet cobblestones",
        "An intricate steampunk mechanical pocket watch revealing a tiny floating miniature universe inside",
        "Ethereal ice palace on top of aurora borealis mountains under a starry cosmic sky, cinematic still",
        "A magical apothecary shop filled with glowing potions, herb bundles, and sleeping feline familiars",
      ];
      if (sampleList.length > 0) {
        const randomPrompt = sampleList[Math.floor(Math.random() * sampleList.length)];
        promptInput.value = randomPrompt;
        updateCharCount();
        promptInput.focus();
        showToast('Generated inspiring prompt! ✨', 'info');
      }
    });

    clearPromptBtn.addEventListener('click', () => {
      promptInput.value = '';
      updateCharCount();
      promptInput.focus();
    });

    toggleEnhancersBtn.addEventListener('click', () => {
      toggleEnhancersBtn.classList.toggle('open');
      enhancersContent.classList.toggle('open');
    });

    guidanceScaleInput.addEventListener('input', (e) => {
      const val = parseFloat(e.target.value).toFixed(1);
      guidanceScaleVal.textContent = val;
      state.guidanceScale = parseFloat(val);
      updateAdvancedSummary();
    });

    randomSeedToggle.addEventListener('change', (e) => {
      state.isRandomSeed = e.target.checked;
      seedInput.disabled = state.isRandomSeed;
      if (state.isRandomSeed) {
        seedInput.value = '';
      } else {
        seedInput.value = Math.floor(Math.random() * 999999);
        seedInput.focus();
      }
      updateAdvancedSummary();
    });

    if (seedInput) {
      seedInput.addEventListener('input', updateAdvancedSummary);
    }

    batchButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        batchButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.batchCount = parseInt(btn.dataset.count, 10);
        updateAdvancedSummary();
      });
    });

    generateBtn.addEventListener('click', triggerGeneration);

    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        triggerGeneration();
      }
      if (e.key === 'Escape' && lightboxModal.style.display === 'flex') {
        closeLightbox();
      }
    });

    gallerySearchInput.addEventListener('input', renderGallery);

    closeModalBtn.addEventListener('click', closeLightbox);
    lightboxModal.addEventListener('click', (e) => {
      if (e.target === lightboxModal) closeLightbox();
    });

    modalCopyPromptBtn.addEventListener('click', () => {
      if (state.activeModalItem) {
        navigator.clipboard.writeText(state.activeModalItem.prompt);
        showToast('Prompt copied to clipboard!', 'success');
      }
    });

    modalRemixBtn.addEventListener('click', () => {
      if (state.activeModalItem) remixArtwork(state.activeModalItem);
    });

    modalDeleteBtn.addEventListener('click', () => {
      if (state.activeModalItem) deleteArtwork(state.activeModalItem.id);
    });
  }

  // Run on start
  init();
});
