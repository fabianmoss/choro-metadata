(() => {
  "use strict";

  const DEFAULT_ROOT = "urn:uuid:persons/1168168328";
  const TREE_KINDS = new Set([
    "composer", "arranger", "librettist",
    "realises", "embodies", "exemplifies",
    "work part", "expression part", "manifestation part", "item part",
  ]);
  const TYPE_COLORS = {
    Person: "#8a5a44",
    Work: "#2f6f73",
    Expression: "#486f9c",
    Manifestation: "#76639b",
    Item: "#8f6b33",
    Institution: "#666666",
    Place: "#777777",
    Instrumentation: "#777777",
    Bibliography: "#777777",
    Venue: "#777777",
    PerformanceEvent: "#777777",
  };
  const PREFIXES = [
    ["rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"],
    ["rdfs", "http://www.w3.org/2000/01/rdf-schema#"],
    ["schema", "https://schema.org/"],
    ["melod", "https://lod.academy/melod/vocab/ontology#"],
    ["terms", "https://lod.academy/melod/vocab/terms#"],
    ["lrmoo", "http://iflastandards.info/ns/lrm/lrmoo/"],
    ["cidoc", "http://www.cidoc-crm.org/cidoc-crm/"],
    ["owl", "http://www.w3.org/2002/07/owl#"],
    ["skos", "http://www.w3.org/2004/02/skos/core#"],
    ["dct", "http://purl.org/dc/terms/"],
    ["mus", "http://data.doremus.org/ontology#"],
    ["xsd", "http://www.w3.org/2001/XMLSchema#"],
  ];

  const state = {
    nodes: new Map(),
    edges: [],
    outEdges: new Map(),
    inEdges: new Map(),
    childMap: new Map(),
    workOfExpression: new Map(),
    searchList: [],
    rootId: null,
    selectedId: null,
    expanded: new Set(),
    rootHierarchy: null,
    visible: new Map(),
    treeEdges: new Set(),
    transform: d3.zoomIdentity,
    detailsCache: new Map(),
    detailQuads: [],
    detailsRequest: 0,
    crossLinks: true,
  };

  const svg = d3.select("#graph");
  const viewport = d3.select("#viewport");
  const detailsPanel = document.getElementById("details");
  const searchInput = document.getElementById("search");
  const searchResults = document.getElementById("search-results");
  const statusBox = document.getElementById("status");
  const crossLinkToggle = document.getElementById("show-cross-links");

  const zoom = d3.zoom()
    .scaleExtent([0.025, 3])
    .on("zoom", (event) => {
      state.transform = event.transform;
      viewport.attr("transform", event.transform);
    });

  svg.call(zoom).on("dblclick.zoom", null);

  let clickTimer = null;

  init().catch((error) => {
    console.error(error);
    statusBox.textContent = `Could not load the viewer data: ${error.message}`;
    detailsPanel.innerHTML = `<div class="empty-details"><h2>Viewer could not start</h2>
      <p>${escapeHtml(error.message)}</p>
      <p>Generate the data with <code>python tools/viewer_data.py</code> and serve the repository over HTTP.</p></div>`;
  });

  async function init() {
    bindControls();
    statusBox.textContent = "Loading graph…";
    const [nodesText, edgesText] = await Promise.all([
      fetchText("data/nodes.jsonl"),
      fetchText("data/edges.jsonl"),
    ]);

    for (const line of nodesText.split("\n")) {
      if (!line.trim()) continue;
      const node = JSON.parse(line);
      state.nodes.set(node.id, node);
    }
    for (const line of edgesText.split("\n")) {
      if (!line.trim()) continue;
      state.edges.push(JSON.parse(line));
    }

    buildIndexes();
    state.searchList = [...state.nodes.values()]
      .sort((a, b) => a.label.localeCompare(b.label, "pt-BR"));

    const root = initialRoot();
    setRoot(root, { expandAll: true, updateHash: false, fit: true });
    wireHash();
  }

  async function fetchText(path) {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`${path}: ${response.status} ${response.statusText}`);
    }
    return response.text();
  }

  function buildIndexes() {
    for (const edge of state.edges) {
      if (!state.outEdges.has(edge.source)) state.outEdges.set(edge.source, []);
      if (!state.inEdges.has(edge.target)) state.inEdges.set(edge.target, []);
      state.outEdges.get(edge.source).push(edge);
      state.inEdges.get(edge.target).push(edge);
      if (edge.kind === "realises") {
        state.workOfExpression.set(edge.target, edge.source);
      }
    }

    const addChild = (parentId, childId, edge) => {
      if (!state.childMap.has(parentId)) state.childMap.set(parentId, []);
      const list = state.childMap.get(parentId);
      if (list.some((record) => record.id === childId)) return;
      list.push({ id: childId, edge });
    };

    const personComposer = new Map();
    const personOtherRole = new Map();
    const pushPerson = (map, personId, edge) => {
      if (!map.has(personId)) map.set(personId, []);
      map.get(personId).push(edge);
    };

    for (const edge of state.edges) {
      switch (edge.kind) {
        case "composer":
          pushPerson(personComposer, edge.target, edge);
          break;
        case "arranger":
        case "librettist":
          pushPerson(personOtherRole, edge.target, edge);
          break;
        case "realises":
          addChild(edge.source, edge.target, edge);
          break;
        case "embodies":
          addChild(edge.target, edge.source, edge);
          break;
        case "exemplifies":
          addChild(edge.target, edge.source, edge);
          break;
        case "work part":
        case "expression part":
        case "manifestation part":
        case "item part":
          addChild(edge.source, edge.target, edge);
          break;
        default:
          break;
      }
    }

    for (const [personId, composerEdges] of personComposer) {
      const composerWorkIds = new Set(composerEdges.map((edge) => edge.source));
      const otherEdges = (personOtherRole.get(personId) || []).filter((edge) => {
        // An arranger expression is already shown below the composed work when
        // the same person also composed that work.  Do not duplicate it as a
        // second branch of the person.
        const workId = state.workOfExpression.get(edge.source);
        return !workId || !composerWorkIds.has(workId);
      });
      for (const edge of [...composerEdges, ...otherEdges]) {
        addChild(personId, edge.source, edge);
      }
    }

    // A person may only have arranger/librettist links.
    for (const [personId, edges] of personOtherRole) {
      if (personComposer.has(personId)) continue;
      for (const edge of edges) addChild(personId, edge.source, edge);
    }

    for (const list of state.childMap.values()) {
      list.sort((a, b) => {
        const left = state.nodes.get(a.id);
        const right = state.nodes.get(b.id);
        return (left ? left.label : a.id).localeCompare(right ? right.label : b.id, "pt-BR");
      });
    }
  }

  function initialRoot() {
    const hashParams = new URLSearchParams(location.hash.replace(/^#/, ""));
    const queryParams = new URLSearchParams(location.search);
    for (const candidate of [hashParams.get("root"), queryParams.get("root")]) {
      if (candidate && state.nodes.has(candidate)) return candidate;
    }
    if (state.nodes.has(DEFAULT_ROOT)) return DEFAULT_ROOT;
    const firstPersonWithChildren = [...state.nodes.values()]
      .filter((node) => node.type === "Person" && (state.childMap.get(node.id) || []).length)
      .sort((a, b) => a.label.localeCompare(b.label, "pt-BR"))[0];
    if (firstPersonWithChildren) return firstPersonWithChildren.id;
    return state.searchList[0] ? state.searchList[0].id : null;
  }

  function setRoot(id, options = {}) {
    if (!id || !state.nodes.has(id)) return;
    const firstRoot = state.rootId === null;
    state.rootId = id;
    state.selectedId = id;
    state.expanded = options.expandAll ? reachable(id) : new Set([id]);
    if (options.updateHash !== false) {
      history.replaceState(null, "", `#root=${encodeURIComponent(id)}`);
    }
    render({ fit: options.fit || firstRoot });
    showDetails(id);
    searchInput.value = "";
    hideSearchResults();
  }

  function reachable(rootId) {
    const seen = new Set([rootId]);
    const stack = [rootId];
    while (stack.length) {
      const id = stack.pop();
      for (const child of state.childMap.get(id) || []) {
        if (seen.has(child.id)) continue;
        seen.add(child.id);
        stack.push(child.id);
      }
    }
    return seen;
  }

  function buildTree(id, claimed, edge = null) {
    const node = state.nodes.get(id);
    const records = (state.childMap.get(id) || [])
      .filter((record) => record.id !== id && !claimed.has(record.id));
    const children = [];
    if (state.expanded.has(id)) {
      for (const record of records) {
        claimed.add(record.id);
        state.treeEdges.add(record.edge);
        children.push(buildTree(record.id, claimed, record.edge));
      }
    }
    return {
      id,
      node,
      edge,
      childCount: records.length,
      children,
    };
  }

  function render(options = {}) {
    state.treeEdges = new Set();
    if (!state.rootId) return;

    const claimed = new Set([state.rootId]);
    const treeData = buildTree(state.rootId, claimed);
    const hierarchy = d3.hierarchy(treeData, (datum) => datum.children);
    d3.tree().nodeSize([34, 260])(hierarchy);
    state.rootHierarchy = hierarchy;
    state.visible = new Map();
    hierarchy.each((datum) => {
      datum.width = nodeWidth(datum.data.node, datum.data.id === state.rootId);
      state.visible.set(datum.data.id, datum);
    });

    viewport.selectAll("*").remove();

    const linkLayer = viewport.append("g").attr("class", "links");
    const crossLayer = viewport.append("g").attr("class", "cross-links");
    const nodeLayer = viewport.append("g").attr("class", "nodes");

    const links = linkLayer.selectAll("path")
      .data(hierarchy.links())
      .join("path")
      .attr("class", "tree-link")
      .attr("d", (link) => linkPath(link.source, link.target))
      .attr("marker-end", (link) => semanticArrow(link, "end"))
      .attr("marker-start", (link) => semanticArrow(link, "start"));

    links.append("title").text((link) => {
      const edge = link.target.data.edge || link.source.data.edge;
      return edge ? `${edge.label} (${edge.predicate})` : "";
    });

    const crossLinks = state.crossLinks
      ? state.edges.filter((edge) => {
          return edge !== null
            && state.visible.has(edge.source)
            && state.visible.has(edge.target)
            && !state.treeEdges.has(edge);
        })
      : [];

    crossLayer.selectAll("path")
      .data(crossLinks)
      .join("path")
      .attr("class", "cross-link")
      .attr("d", (edge) => crossLinkPath(edge))
      .attr("marker-end", "url(#arrow-cross)")
      .append("title")
      .text((edge) => `${edge.label} (${edge.predicate})`);

    const nodes = nodeLayer.selectAll("g")
      .data(hierarchy.descendants(), (datum) => datum.data.id)
      .join("g")
      .attr("class", (datum) => {
        const classes = ["node"];
        if (datum.data.id === state.rootId) classes.push("root");
        if (datum.data.id === state.selectedId) classes.push("selected");
        return classes.join(" ");
      })
      .attr("transform", (datum) => `translate(${datum.y},${datum.x})`)
      .on("click", (event, datum) => {
        clearTimeout(clickTimer);
        clickTimer = setTimeout(() => {
          state.selectedId = datum.data.id;
          nodeLayer.selectAll("g.node").classed("selected", (item) => item.data.id === state.selectedId);
          showDetails(datum.data.id);
        }, 230);
      })
      .on("dblclick", (event, datum) => {
        event.preventDefault();
        clearTimeout(clickTimer);
        toggle(datum.data.id);
      });

    nodes.call(
      d3.drag()
        .on("start", function (event, datum) {
          event.sourceEvent.stopPropagation();
          datum.dragStart = { x: datum.x, y: datum.y };
          d3.select(this).classed("dragging", true).raise();
        })
        .on("drag", function (event, datum) {
          const scale = state.transform.k || 1;
          datum.x = datum.dragStart.x + event.dy / scale;
          datum.y = datum.dragStart.y + event.dx / scale;
          updatePositions(nodeLayer, crossLayer);
        })
        .on("end", function () {
          d3.select(this).classed("dragging", false);
        })
    );

    nodes.append("rect")
      .attr("x", 0)
      .attr("y", -17)
      .attr("width", (datum) => datum.width)
      .attr("height", 34)
      .attr("rx", 7);

    nodes.append("rect")
      .attr("x", 0)
      .attr("y", -17)
      .attr("width", 3)
      .attr("height", 34)
      .attr("rx", 1.5)
      .attr("fill", (datum) => TYPE_COLORS[datum.data.node.type] || "#777")
      .attr("stroke", "none");

    nodes.append("text")
      .attr("class", "type")
      .attr("x", 10)
      .attr("y", -4)
      .text((datum) => datum.data.node.type);

    nodes.append("text")
      .attr("class", "label")
      .attr("x", 10)
      .attr("y", 10)
      .text((datum) => shorten(datum.data.node.label, 47));

    const toggleGroup = nodes.filter((datum) => datum.data.childCount > 0)
      .append("g")
      .attr("class", "toggle-group")
      .attr("transform", (datum) => `translate(${datum.width - 12},0)`)
      .on("click", (event, datum) => {
        event.stopPropagation();
        clearTimeout(clickTimer);
        toggle(datum.data.id);
      })
      .on("dblclick", (event) => event.stopPropagation());

    toggleGroup.append("circle")
      .attr("class", "toggle")
      .attr("r", 7)
      .attr("cx", 0)
      .attr("cy", 0);

    toggleGroup.append("text")
      .attr("class", "toggle-text")
      .attr("x", 0)
      .attr("y", 0)
      .text((datum) => state.expanded.has(datum.data.id) ? "−" : "+");

    nodes.append("title")
      .text((datum) => `${datum.data.node.type}: ${datum.data.node.label}\n${datum.data.id}`);

    const shown = hierarchy.descendants().length;
    statusBox.textContent = `${shown.toLocaleString("en-US")} nodes shown · ${crossLinks.length.toLocaleString("en-US")} cross-links · ${state.nodes.size.toLocaleString("en-US")} entities in the dataset`;
    document.title = `${state.nodes.get(state.rootId).label} · Choro acervo graph`;

    viewport.attr("transform", state.transform);
    if (options.fit) requestAnimationFrame(fit);
  }

  function updatePositions(nodeLayer, crossLayer) {
    nodeLayer.selectAll("g.node")
      .attr("transform", (datum) => `translate(${datum.y},${datum.x})`);
    const linkLayer = viewport.select("g.links");
    linkLayer.selectAll("path").attr("d", (link) => linkPath(link.source, link.target));
    crossLayer.selectAll("path").attr("d", (edge) => crossLinkPath(edge));
  }

  function toggle(id) {
    if (!state.expanded.has(id)) {
      state.expanded.add(id);
    } else {
      state.expanded.delete(id);
    }
    render({ fit: false });
  }

  function linkPath(source, target) {
    const sx = source.y + source.width;
    const sy = source.x;
    const tx = target.y;
    const ty = target.x;
    const bend = Math.max(34, (tx - sx) * 0.45);
    return `M${sx},${sy}C${sx + bend},${sy} ${tx - bend},${ty} ${tx},${ty}`;
  }

  function crossLinkPath(edge) {
    const source = state.visible.get(edge.source);
    const target = state.visible.get(edge.target);
    if (!source || !target) return "";
    const sx = source.y + source.width;
    const sy = source.x;
    const tx = target.y;
    const ty = target.x;
    const bend = Math.max(38, Math.abs(tx - sx) * 0.4);
    return `M${sx},${sy}C${sx + bend},${sy} ${tx - bend},${ty} ${tx},${ty}`;
  }

  function semanticArrow(link, position) {
    const edge = link.target.data.edge;
    if (!edge) return null;
    const parentId = link.source.data.id;
    const childId = link.target.data.id;
    const sourceIsParent = edge.source === parentId && edge.target === childId;
    const targetIsParent = edge.source === childId && edge.target === parentId;
    if (!sourceIsParent && !targetIsParent) return null;
    if (position === "end") {
      return sourceIsParent ? "url(#arrow-tree)" : null;
    }
    return targetIsParent ? "url(#arrow-tree)" : null;
  }

  function nodeWidth(node, isRoot) {
    const label = shorten(node && node.label ? node.label : "", 47);
    const width = Math.max(
      isRoot ? 155 : 125,
      Math.min(345, 25 + label.length * 6.9)
    );
    return width;
  }

  function shorten(text, limit) {
    if (!text) return "";
    return text.length > limit ? `${text.slice(0, limit - 1)}…` : text;
  }

  function fit() {
    if (!state.rootHierarchy) return;
    const nodes = state.rootHierarchy.descendants();
    if (!nodes.length) return;
    const x0 = d3.min(nodes, (node) => node.x - 22);
    const x1 = d3.max(nodes, (node) => node.x + 22);
    const y0 = d3.min(nodes, (node) => node.y);
    const y1 = d3.max(nodes, (node) => node.y + node.width);
    const element = svg.node();
    const width = element.clientWidth || 900;
    const height = element.clientHeight || 650;
    const scale = Math.min(
      0.92 * width / Math.max(1, y1 - y0),
      0.92 * height / Math.max(1, x1 - x0),
      1.6
    );
    const tx = width / 2 - scale * (y0 + y1) / 2;
    const ty = height / 2 - scale * (x0 + x1) / 2;
    svg.transition().duration(260)
      .call(zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale));
  }

  function bindControls() {
    document.getElementById("fit").addEventListener("click", fit);

    document.getElementById("expand-all").addEventListener("click", () => {
      if (!state.rootId) return;
      state.expanded = reachable(state.rootId);
      render({ fit: true });
    });

    document.getElementById("collapse-all").addEventListener("click", () => {
      if (!state.rootId) return;
      state.expanded = new Set([state.rootId]);
      render({ fit: true });
    });

    crossLinkToggle.addEventListener("change", () => {
      state.crossLinks = crossLinkToggle.checked;
      render({ fit: false });
    });

    searchInput.addEventListener("input", runSearch);
    searchInput.addEventListener("focus", () => {
      if (searchInput.value.trim()) runSearch();
    });
    searchInput.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        hideSearchResults();
        searchInput.blur();
      }
      if (event.key === "Enter") {
        const first = searchResults.querySelector(".search-result");
        if (first) {
          event.preventDefault();
          first.click();
        }
      }
    });

    document.addEventListener("click", (event) => {
      if (!searchResults.contains(event.target) && event.target !== searchInput) {
        hideSearchResults();
      }
    });
  }

  function runSearch() {
    const query = searchInput.value.trim().toLocaleLowerCase("pt-BR");
    searchResults.innerHTML = "";
    if (!query) {
      hideSearchResults();
      return;
    }

    const tokens = query.split(/\s+/).filter(Boolean);
    const matches = [];
    for (const node of state.searchList) {
      const label = node.label.toLocaleLowerCase("pt-BR");
      const id = node.id.toLocaleLowerCase("pt-BR");
      if (!tokens.every((token) => label.includes(token) || id.includes(token))) continue;
      matches.push({ node, score: searchScore(label, id, tokens) });
    }
    matches.sort((a, b) => a.score - b.score
      || a.node.label.localeCompare(b.node.label, "pt-BR"));
    const shown = matches.slice(0, 30).map((match) => match.node);

    if (!shown.length) {
      searchResults.hidden = false;
      searchResults.innerHTML = '<div class="search-result"><span></span><span>No matching entity.</span></div>';
      return;
    }

    for (const node of shown) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "search-result";
      button.innerHTML = `<span class="kind">${escapeHtml(node.type)}</span><span class="label">${escapeHtml(node.label)}</span>`;
      button.addEventListener("click", () => setRoot(node.id, { expandAll: true, fit: true }));
      searchResults.appendChild(button);
    }
    searchResults.hidden = false;
  }

  function searchScore(label, id, tokens) {
    const phrase = tokens.join(" ");
    if (label === phrase) return 0;
    if (label.startsWith(phrase)) return 1;
    if (label.split(/[\s,;:—-]+/).some((word) => word.startsWith(tokens[0]))) return 2;
    if (label.includes(phrase)) return 3;
    if (tokens.every((token) => label.includes(token))) return 4;
    return 5;
  }

  function hideSearchResults() {
    searchResults.hidden = true;
    searchResults.innerHTML = "";
  }

  function wireHash() {
    window.addEventListener("hashchange", () => {
      const params = new URLSearchParams(location.hash.replace(/^#/, ""));
      const id = params.get("root");
      if (id && id !== state.rootId && state.nodes.has(id)) {
        setRoot(id, { expandAll: true, updateHash: false, fit: true });
      }
    });
  }

  async function showDetails(id) {
    const node = state.nodes.get(id);
    if (!node) return;
    const requestId = ++state.detailsRequest;

    detailsPanel.innerHTML = `<div class="details-head">
        <div class="details-kicker">${escapeHtml(node.type)}</div>
        <h2>${escapeHtml(node.label)}</h2>
        <div class="iri">${escapeHtml(node.id)}</div>
      </div>
      <div class="details-body"><p class="value">Loading ${escapeHtml(node.path)}…</p></div>`;

    let documentData;
    try {
      documentData = await loadDocument(node.path);
    } catch (error) {
      if (requestId !== state.detailsRequest) return;
      detailsPanel.innerHTML += `<p class="details-error">${escapeHtml(error.message)}<br>
        Serve the repository over HTTP (for example <code>python3 -m http.server 8000</code>)
        instead of opening this file directly.</p>`;
      return;
    }
    if (requestId !== state.detailsRequest) return;

    state.detailQuads = documentData.quads;
    const body = document.createElement("div");
    body.className = "details-body";
    renderProperties(node.id, new Set(), 0, body);

    const raw = document.createElement("details");
    raw.className = "raw";
    const summary = document.createElement("summary");
    summary.textContent = "Raw Turtle";
    const pre = document.createElement("pre");
    pre.textContent = documentData.text;
    raw.append(summary, pre);
    body.appendChild(raw);

    detailsPanel.innerHTML = "";
    const head = document.createElement("div");
    head.className = "details-head";
    head.innerHTML = `<div class="details-kicker">${escapeHtml(node.type)}</div>
      <h2>${escapeHtml(node.label)}</h2>
      <div class="iri">${escapeHtml(node.id)}</div>`;

    const buttons = document.createElement("div");
    buttons.className = "details-buttons";

    const rootButton = document.createElement("button");
    rootButton.type = "button";
    rootButton.textContent = "Show as root";
    rootButton.addEventListener("click", () => setRoot(node.id, { expandAll: true, fit: true }));
    buttons.appendChild(rootButton);

    const copyButton = document.createElement("button");
    copyButton.type = "button";
    copyButton.textContent = "Copy IRI";
    copyButton.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(node.id);
        copyButton.textContent = "Copied";
        setTimeout(() => { copyButton.textContent = "Copy IRI"; }, 1200);
      } catch {
        copyButton.textContent = "Copy failed";
      }
    });
    buttons.appendChild(copyButton);

    const sourceLink = document.createElement("a");
    sourceLink.href = `../${node.path}`;
    sourceLink.target = "_blank";
    sourceLink.rel = "noopener";
    sourceLink.textContent = "Open Turtle";
    buttons.appendChild(sourceLink);

    head.appendChild(buttons);
    detailsPanel.append(head, body);

    body.querySelectorAll(".entity-link").forEach((link) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        setRoot(link.dataset.id, { expandAll: true, fit: true });
      });
    });
  }

  async function loadDocument(path) {
    if (state.detailsCache.has(path)) return state.detailsCache.get(path);
    const url = new URL(`../${path}`, location.href);
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`${path}: ${response.status} ${response.statusText}`);
    }
    const text = await response.text();
    const parser = new N3.Parser({ baseIRI: url.href });
    const quads = parser.parse(text);
    const result = { text, quads };
    state.detailsCache.set(path, result);
    return result;
  }

  function renderProperties(subject, seen, depth, container) {
    const groups = new Map();
    for (const quad of state.detailQuads) {
      if (quad.subject.value !== subject) continue;
      const key = quad.predicate.value;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(quad.object);
    }

    for (const [predicate, objects] of groups) {
      const property = document.createElement("div");
      property.className = "property";
      const name = document.createElement("div");
      name.className = "predicate";
      name.textContent = shortUri(predicate);
      name.title = predicate;
      const values = document.createElement("div");
      values.className = "values";

      for (const object of objects) {
        values.appendChild(renderValue(object, seen, depth));
      }

      property.append(name, values);
      container.appendChild(property);
    }
  }

  function renderValue(term, seen, depth) {
    if (term.termType === "NamedNode") {
      if (state.nodes.has(term.value)) {
        const link = document.createElement("a");
        link.className = "entity-link";
        link.href = `#root=${encodeURIComponent(term.value)}`;
        link.dataset.id = term.value;
        link.textContent = state.nodes.get(term.value).label;
        link.title = term.value;
        return wrapValue(link);
      }
      if (term.value.startsWith("urn:uuid:")) {
        return wrapValue(document.createTextNode(shortUri(term.value)));
      }
      const link = document.createElement("a");
      link.href = term.value;
      link.target = "_blank";
      link.rel = "noopener";
      link.textContent = shortUri(term.value);
      link.title = term.value;
      const wrapper = wrapValue(link);
      wrapper.classList.add("external");
      return wrapper;
    }

    if (term.termType === "BlankNode") {
      if (seen.has(term.value)) {
        return wrapValue(document.createTextNode("…"));
      }
      const nextSeen = new Set(seen);
      nextSeen.add(term.value);
      const details = document.createElement("details");
      details.className = "blank";
      if (depth === 0) details.open = true;
      const summary = document.createElement("summary");
      summary.textContent = "blank node";
      details.appendChild(summary);
      renderProperties(term.value, nextSeen, depth + 1, details);
      const wrapper = document.createElement("div");
      wrapper.appendChild(details);
      return wrapper;
    }

    const wrapper = wrapValue(document.createTextNode(term.value));
    if (term.language) {
      const meta = document.createElement("span");
      meta.className = "meta";
      meta.textContent = `@${term.language}`;
      wrapper.appendChild(meta);
    } else if (term.datatype && term.datatype.value !== "http://www.w3.org/2001/XMLSchema#string") {
      const meta = document.createElement("span");
      meta.className = "meta";
      meta.textContent = shortUri(term.datatype.value);
      wrapper.appendChild(meta);
    }
    return wrapper;
  }

  function wrapValue(child) {
    const wrapper = document.createElement("div");
    wrapper.className = "value";
    wrapper.appendChild(child);
    return wrapper;
  }

  function shortUri(uri) {
    for (const [prefix, namespace] of PREFIXES) {
      if (uri.startsWith(namespace)) return `${prefix}:${uri.slice(namespace.length)}`;
    }
    return uri;
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[character]));
  }
})();
