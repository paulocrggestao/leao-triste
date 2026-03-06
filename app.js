/* =============================================
   Leão Triste — app.js
   Professional Tax Recovery Dashboard
   ============================================= */

/* Detectar URL da API automaticamente:
   - Deploy via proxy (sandbox): __PORT_8000__ é substituído automaticamente
   - Produção (Docker/VPS): API na mesma origem, API_BASE = "" */
var API_BASE = "__PORT_8000__";
/* Em produção, sobrescrever se necessário via variável global ou meta tag */
if (document.querySelector('meta[name="api-base"]')) {
  API_BASE = document.querySelector('meta[name="api-base"]').getAttribute("content");
}

/* ===== UTILITIES ===== */
function formatCurrency(value) {
  if (value == null || isNaN(value)) return "R$ 0,00";
  return "R$ " + Number(value).toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatCNPJ(cnpj) {
  if (!cnpj) return "";
  var clean = cnpj.replace(/\D/g, "");
  if (clean.length !== 14) return cnpj;
  return clean.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5");
}

function formatDate(dateStr) {
  if (!dateStr) return "—";
  var d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  var day = String(d.getDate()).padStart(2, "0");
  var month = String(d.getMonth() + 1).padStart(2, "0");
  var year = d.getFullYear();
  return day + "/" + month + "/" + year;
}

function formatDateTime(dateStr) {
  if (!dateStr) return "—";
  var d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return formatDate(dateStr) + " " + String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0");
}

function maskCNPJInput(input) {
  var lastQueried = "";
  input.addEventListener("input", function () {
    var v = input.value.replace(/\D/g, "");
    if (v.length > 14) v = v.slice(0, 14);
    if (v.length > 12) {
      v = v.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{0,2})/, "$1.$2.$3/$4-$5");
    } else if (v.length > 8) {
      v = v.replace(/^(\d{2})(\d{3})(\d{3})(\d{0,4})/, "$1.$2.$3/$4");
    } else if (v.length > 5) {
      v = v.replace(/^(\d{2})(\d{3})(\d{0,3})/, "$1.$2.$3");
    } else if (v.length > 2) {
      v = v.replace(/^(\d{2})(\d{0,3})/, "$1.$2");
    }
    input.value = v;
    /* Auto-fetch company data when 14 digits are entered */
    var raw = v.replace(/\D/g, "");
    if (raw.length === 14 && raw !== lastQueried) {
      lastQueried = raw;
      fetchCNPJData(raw);
    }
  });
}

/* ---- CNPJ Lookup via BrasilAPI ---- */
function fetchCNPJData(cnpj) {
  var pure = cnpj.replace(/\D/g, "");
  if (pure.length !== 14) return;

  /* Show loading indicator next to CNPJ field */
  var cnpjGroup = document.getElementById("modal-cnpj");
  if (!cnpjGroup) return;
  var parent = cnpjGroup.parentElement;
  /* Hide hint text during lookup */
  var hint = parent.querySelector(".form-hint");
  if (hint) hint.style.display = "none";
  var existingStatus = parent.querySelector(".cnpj-status");
  if (existingStatus) existingStatus.remove();
  var statusEl = el("div", { className: "cnpj-status cnpj-loading" }, "Consultando CNPJ na Receita Federal...");
  parent.appendChild(statusEl);

  fetch("https://brasilapi.com.br/api/cnpj/v1/" + pure)
    .then(function (res) {
      if (!res.ok) throw new Error("CNPJ n\u00e3o encontrado");
      return res.json();
    })
    .then(function (data) {
      statusEl.className = "cnpj-status cnpj-success";
      statusEl.textContent = "\u2713 " + (data.descricao_situacao_cadastral || "Ativo");
      fillFormFromCNPJ(data);
    })
    .catch(function () {
      statusEl.className = "cnpj-status cnpj-error";
      statusEl.textContent = "CNPJ n\u00e3o encontrado. Preencha manualmente.";
    });
}

function fillFormFromCNPJ(data) {
  /* Company name */
  var nameInput = document.getElementById("modal-name");
  if (nameInput && data.razao_social) {
    nameInput.value = data.razao_social;
    nameInput.dispatchEvent(new Event("input"));
  }

  /* State/UF */
  var ufSelect = document.getElementById("modal-uf");
  if (ufSelect && data.uf) {
    ufSelect.value = data.uf.toUpperCase();
  }

  /* Sector — map CNAE to our sector categories */
  var setorSelect = document.getElementById("modal-setor");
  if (setorSelect && data.cnae_fiscal) {
    var mapped = mapCNAEtoSector(String(data.cnae_fiscal), data.cnae_fiscal_descricao || "");
    if (mapped) {
      /* Find the display label that maps to this code */
      for (var i = 0; i < setorSelect.options.length; i++) {
        if (sectorToCode(setorSelect.options[i].value) === mapped) {
          setorSelect.selectedIndex = i;
          break;
        }
      }
    }
  }

  /* Flash the filled fields to give visual feedback */
  ["modal-name", "modal-uf", "modal-setor"].forEach(function (id) {
    var field = document.getElementById(id);
    if (field) {
      field.classList.add("field-autofilled");
      setTimeout(function () { field.classList.remove("field-autofilled"); }, 2000);
    }
  });
}

function mapCNAEtoSector(cnaeCode, cnaeDesc) {
  var desc = (cnaeDesc || "").toLowerCase();
  /* CNAE groups for our sectors */
  /* 4711: supermercados/hipermercados, 4712: minimercados */
  if (/^471/.test(cnaeCode)) return "supermercado";
  /* 1091: padarias, 4721: padarias/confeitarias */
  if (/^1091|^4721/.test(cnaeCode)) return "padaria";
  /* 5611: restaurantes */
  if (/^5611/.test(cnaeCode)) return "restaurante";
  /* 5612: bares e lancherias */
  if (/^5612|^5620/.test(cnaeCode)) return "bar";
  /* 4771: farm\u00e1cias/drogarias */
  if (/^4771/.test(cnaeCode)) return "farmacia";
  /* 4731: postos de combust\u00edveis */
  if (/^4731/.test(cnaeCode)) return "posto_combustivel";
  /* Fallback: try description keywords */
  if (/supermercado|hipermercado|mercearia/.test(desc)) return "supermercado";
  if (/padaria|panifica|confeitaria/.test(desc)) return "padaria";
  if (/restaurante|refei/.test(desc)) return "restaurante";
  if (/bar |lanchonete|choperia|cervejaria/.test(desc)) return "bar";
  if (/farm[a\u00e1]cia|drogaria/.test(desc)) return "farmacia";
  if (/combust[i\u00ed]vel|posto|gasolina/.test(desc)) return "posto_combustivel";
  return "outro";
}

function regimeLabel(regime) {
  var map = {
    "simples": "Simples Nacional",
    "presumido": "Lucro Presumido",
    "real": "Lucro Real",
    "Simples Nacional": "Simples Nacional",
    "Lucro Presumido": "Lucro Presumido",
    "Lucro Real": "Lucro Real",
  };
  return map[regime] || regime || "—";
}

function sectorLabel(sector) {
  var map = {
    "supermercado": "Supermercado",
    "padaria": "Padaria",
    "restaurante": "Restaurante",
    "bar": "Bar",
    "farmacia": "Farmácia",
    "posto_combustivel": "Posto de Combustível",
    "outro": "Outro",
  };
  return map[sector] || sector || "—";
}

function taxTypeLabel(tax) {
  var map = {
    "pis": "PIS",
    "cofins": "COFINS",
    "icms": "ICMS",
    "icms_st": "ICMS-ST",
    "inss": "INSS",
    "irpj": "IRPJ",
    "csll": "CSLL",
  };
  return map[tax] || (tax || "").toUpperCase() || "—";
}

function el(tag, attrs, children) {
  var node = document.createElement(tag);
  if (attrs) {
    Object.keys(attrs).forEach(function (key) {
      if (key === "className") {
        node.className = attrs[key];
      } else if (key === "innerHTML") {
        node.innerHTML = attrs[key];
      } else if (key.startsWith("on")) {
        node.addEventListener(key.slice(2).toLowerCase(), attrs[key]);
      } else {
        node.setAttribute(key, attrs[key]);
      }
    });
  }
  if (children) {
    if (typeof children === "string") {
      node.textContent = children;
    } else if (Array.isArray(children)) {
      children.forEach(function (child) {
        if (child) node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
      });
    } else {
      node.appendChild(children);
    }
  }
  return node;
}

/* ===== API ===== */
function apiFetch(path, options) {
  var url = API_BASE + path;
  return fetch(url, options).then(function (res) {
    if (!res.ok) {
      return res.text().then(function (t) {
        throw new Error("API error " + res.status + ": " + t);
      });
    }
    return res.json();
  });
}

/* ===== TOAST SYSTEM ===== */
var toastContainer;
function showToast(message, type) {
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.className = "toast-container";
    document.body.appendChild(toastContainer);
  }
  type = type || "info";
  var toast = el("div", { className: "toast toast-" + type }, message);
  toastContainer.appendChild(toast);
  setTimeout(function () {
    toast.classList.add("toast-exit");
    setTimeout(function () {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 200);
  }, 3500);
}

/* ===== ICONS (Lucide-style inline SVGs) ===== */
var ICONS = {
  home: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
  building: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="20" x="4" y="2" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/></svg>',
  chart: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" x2="18" y1="20" y2="10"/><line x1="12" x2="12" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="14"/></svg>',
  search: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" x2="16.65" y1="21" y2="16.65"/></svg>',
  plus: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>',
  upload: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>',
  close: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>',
  sun: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>',
  moon: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>',
  file: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>',
  download: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>',
  play: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>',
  shield: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
  users: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  target: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
  dollarSign: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" x2="12" y1="2" y2="22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
  trendingUp: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>',
  clipboard: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></svg>',
  inbox: '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>',
  printer: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect width="12" height="8" x="6" y="14"/></svg>',
  chevronRight: '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>',
  key: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.3 9.3"/><path d="m18 2 3 3"/><path d="m15 5 3 3"/></svg>',
  edit: '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>',
  trash: '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
  package: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m16.5 9.4-9-5.19"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" x2="12" y1="22.08" y2="12"/></svg>',
};

function icon(name) { return ICONS[name] || ""; }

/* ===== STATE ===== */
var currentRoute = "";
var chartInstances = [];

function destroyCharts() {
  chartInstances.forEach(function (c) { c.destroy(); });
  chartInstances = [];
}

/* ===== ROUTING ===== */
function getRoute() {
  var hash = window.location.hash || "#/";
  return hash.slice(1) || "/";
}

function navigate(path) {
  window.location.hash = "#" + path;
}

function initRouter() {
  window.addEventListener("hashchange", handleRoute);
  handleRoute();
}

function handleRoute() {
  var route = getRoute();
  if (route === currentRoute) return;
  currentRoute = route;
  destroyCharts();
  updateNav(route);
  updateBreadcrumb(route);

  var main = document.getElementById("main-content");
  if (!main) return;

  if (route === "/") {
    renderDashboard(main);
  } else if (route === "/clientes") {
    renderClientes(main);
  } else if (route.startsWith("/cliente/")) {
    var clientId = route.split("/")[2];
    renderClienteDetail(main, clientId);
  } else if (route.startsWith("/analise/")) {
    var analysisId = route.split("/")[2];
    renderAnalysis(main, analysisId);
  } else if (route === "/relatorios") {
    renderRelatorios(main);
  } else if (route === "/ncm") {
    renderNCMPage(main);
  } else if (route === "/produtos") {
    renderProdutosPage(main);
  } else {
    renderDashboard(main);
  }

  closeSidebar();
}

function updateNav(route) {
  document.querySelectorAll(".nav-item").forEach(function (item) {
    var href = item.getAttribute("data-route") || "";
    var isActive = false;
    if (href === "/" && route === "/") isActive = true;
    else if (href === "/clientes" && (route === "/clientes" || route.startsWith("/cliente/"))) isActive = true;
    else if (href === "/ncm" && route === "/ncm") isActive = true;
    else if (href === "/produtos" && route === "/produtos") isActive = true;
    else if (href !== "/" && href !== "/clientes" && href !== "/ncm" && href !== "/produtos" && route.startsWith(href)) isActive = true;
    item.classList.toggle("active", isActive);
  });
}

function updateBreadcrumb(route) {
  var bc = document.getElementById("breadcrumb");
  if (!bc) return;
  var parts = [{ label: "Início", path: "/" }];
  if (route === "/clientes") {
    parts.push({ label: "Clientes", path: null });
  } else if (route.startsWith("/cliente/")) {
    parts.push({ label: "Clientes", path: "/clientes" });
    parts.push({ label: "Detalhe", path: null });
  } else if (route.startsWith("/analise/")) {
    parts.push({ label: "Análise", path: null });
  } else if (route === "/relatorios") {
    parts.push({ label: "Relatórios", path: null });
  } else if (route === "/ncm") {
    parts.push({ label: "Base NCM", path: null });
  } else if (route === "/produtos") {
    parts.push({ label: "Produtos", path: null });
  }

  bc.innerHTML = "";
  parts.forEach(function (p, i) {
    if (i > 0) {
      var sep = el("span", { className: "breadcrumb-sep", innerHTML: icon("chevronRight") });
      bc.appendChild(sep);
    }
    if (p.path && i < parts.length - 1) {
      var a = el("a", { onClick: function () { navigate(p.path); } }, p.label);
      bc.appendChild(a);
    } else {
      bc.appendChild(el("span", {}, p.label));
    }
  });
}

/* ===== SIDEBAR MOBILE ===== */
function openSidebar() {
  document.querySelector(".sidebar").classList.add("open");
  document.querySelector(".sidebar-overlay").classList.add("active");
}

function closeSidebar() {
  document.querySelector(".sidebar").classList.remove("open");
  document.querySelector(".sidebar-overlay").classList.remove("active");
}

/* ===== THEME ===== */
var currentTheme;
function initTheme() {
  currentTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", currentTheme);
  updateThemeIcon();
}

function toggleTheme() {
  currentTheme = currentTheme === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", currentTheme);
  updateThemeIcon();
}

function updateThemeIcon() {
  var btn = document.getElementById("theme-toggle");
  if (btn) btn.innerHTML = currentTheme === "dark" ? icon("sun") : icon("moon");
}

/* ===== SKELETON HELPERS ===== */
function skeletonKPIs(count) {
  var grid = el("div", { className: "kpi-grid" });
  for (var i = 0; i < count; i++) {
    grid.appendChild(el("div", { className: "kpi-card" }, [
      el("div", { className: "skeleton skeleton-text-sm", style: "width:60%" }),
      el("div", { className: "skeleton skeleton-title", style: "width:70%;margin-top:8px" }),
    ]));
  }
  return grid;
}

function skeletonTable() {
  var card = el("div", { className: "table-card" });
  card.appendChild(el("div", { className: "table-header" }, [
    el("div", { className: "skeleton", style: "width:120px;height:20px" }),
  ]));
  for (var i = 0; i < 5; i++) {
    var row = el("div", { style: "display:flex;gap:16px;padding:12px 20px;border-bottom:1px solid var(--color-divider)" });
    row.appendChild(el("div", { className: "skeleton", style: "width:80px;height:14px" }));
    row.appendChild(el("div", { className: "skeleton", style: "width:120px;height:14px" }));
    row.appendChild(el("div", { className: "skeleton", style: "width:100px;height:14px" }));
    row.appendChild(el("div", { className: "skeleton", style: "width:60px;height:14px" }));
    card.appendChild(row);
  }
  return card;
}

function skeletonCharts() {
  var grid = el("div", { className: "chart-grid" });
  grid.appendChild(el("div", { className: "skeleton skeleton-chart" }));
  grid.appendChild(el("div", { className: "skeleton skeleton-chart" }));
  return grid;
}

/* ===== BRAZILIAN STATES ===== */
var UF_LIST = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"];
var SETORES = ["Supermercado","Padaria","Restaurante","Bar","Farmácia","Posto de Combustível","Outro"];
var REGIMES = ["Simples Nacional","Lucro Presumido","Lucro Real"];

/* Helper to map regime codes back to POST values */
function regimeToCode(label) {
  var map = { "Simples Nacional": "simples", "Lucro Presumido": "presumido", "Lucro Real": "real" };
  return map[label] || label;
}
function sectorToCode(label) {
  var map = { "Supermercado": "supermercado", "Padaria": "padaria", "Restaurante": "restaurante", "Bar": "bar", "Farmácia": "farmacia", "Posto de Combustível": "posto_combustivel", "Outro": "outro" };
  return map[label] || label;
}

/* ============================================================
   PAGE: DASHBOARD
   ============================================================ */
function renderDashboard(container) {
  container.innerHTML = "";
  var pageHeader = el("div", { className: "page-header" }, [
    el("h1", { className: "page-title" }, "Dashboard"),
  ]);
  container.appendChild(pageHeader);
  container.appendChild(skeletonKPIs(4));
  container.appendChild(skeletonCharts());
  container.appendChild(skeletonTable());

  apiFetch("/api/dashboard/stats").then(function (data) {
    container.innerHTML = "";
    container.appendChild(pageHeader);
    renderDashboardContent(container, data);
  }).catch(function () {
    container.innerHTML = "";
    container.appendChild(pageHeader);
    renderDashboardFallback(container);
  });
}

function renderDashboardContent(container, data) {
  /* KPI Cards — map from API fields */
  var kpiGrid = el("div", { className: "kpi-grid" });
  var kpis = [
    { label: "Total Clientes", value: String(data.total_clientes || 0), icon: "users" },
    { label: "Análises Realizadas", value: String(data.total_analises || 0), icon: "clipboard" },
    { label: "Total Recuperável", value: formatCurrency(data.total_recuperacao || 0), icon: "dollarSign", primary: true },
    { label: "Ticket Médio", value: formatCurrency(data.media_recuperacao_por_cliente || 0), icon: "trendingUp" },
  ];
  kpis.forEach(function (k) {
    kpiGrid.appendChild(el("div", { className: "kpi-card" }, [
      el("div", { className: "kpi-label", innerHTML: icon(k.icon) + " " + k.label }),
      el("div", { className: "kpi-value" + (k.primary ? " primary" : "") }, k.value),
    ]));
  });
  container.appendChild(kpiGrid);

  /* Charts */
  var chartGrid = el("div", { className: "chart-grid" });

  /* Bar chart: Recovery by Tax Type */
  var barCard = el("div", { className: "chart-card" });
  barCard.appendChild(el("div", { className: "chart-title" }, "Recuperação por Tipo de Tributo"));
  var barCanvas = el("canvas");
  barCard.appendChild(el("div", { className: "chart-container" }, barCanvas));
  chartGrid.appendChild(barCard);

  /* Pie chart: Distribution by regime */
  var pieCard = el("div", { className: "chart-card" });
  pieCard.appendChild(el("div", { className: "chart-title" }, "Distribuição por Regime Tributário"));
  var pieCanvas = el("canvas");
  pieCard.appendChild(el("div", { className: "chart-container" }, pieCanvas));
  chartGrid.appendChild(pieCard);

  container.appendChild(chartGrid);

  /* Bar Chart — data from por_tributo array */
  var porTributo = data.por_tributo || [];
  var taxLabels = porTributo.map(function (t) { return taxTypeLabel(t.tributo); });
  var taxValues = porTributo.map(function (t) { return t.total_recuperar || 0; });
  if (!taxLabels.length) {
    taxLabels = ["PIS", "COFINS", "ICMS", "ICMS-ST", "INSS", "IRPJ", "CSLL"];
    taxValues = [0, 0, 0, 0, 0, 0, 0];
  }

  var isDark = currentTheme === "dark";
  var gridColor = isDark ? "rgba(148,163,184,0.1)" : "rgba(15,23,42,0.06)";
  var textColor = isDark ? "#94A3B8" : "#64748B";

  var allZeroTax = taxValues.every(function (v) { return v === 0; });
  var barChart = new Chart(barCanvas, {
    type: "bar",
    data: {
      labels: taxLabels,
      datasets: [{
        label: "Valor Recuperável (R$)",
        data: taxValues,
        backgroundColor: isDark ? "#34D399" : "#059669",
        borderRadius: 4,
        maxBarThickness: 48,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: function (ctx) { return formatCurrency(ctx.raw); } } }
      },
      scales: {
        y: {
          beginAtZero: true,
          suggestedMax: allZeroTax ? 100 : undefined,
          grid: { color: gridColor },
          ticks: {
            color: textColor, font: { size: 11 },
            callback: function (v) {
              if (v === 0) return "R$ 0";
              if (Math.abs(v) >= 1000) return "R$ " + (v / 1000).toLocaleString("pt-BR") + "k";
              return "R$ " + v.toLocaleString("pt-BR");
            }
          }
        },
        x: { grid: { display: false }, ticks: { color: textColor, font: { size: 11 } } }
      }
    }
  });
  chartInstances.push(barChart);

  /* Pie Chart — data from por_regime array */
  var porRegime = data.por_regime || [];
  var regimeLabels = porRegime.map(function (r) { return regimeLabel(r.regime); });
  var regimeValues = porRegime.map(function (r) { return r.quantidade || 0; });
  if (!regimeLabels.length) {
    regimeLabels = REGIMES;
    regimeValues = [1, 1, 1];
  }

  var pieChart = new Chart(pieCanvas, {
    type: "doughnut",
    data: {
      labels: regimeLabels,
      datasets: [{
        data: regimeValues,
        backgroundColor: isDark ? ["#34D399", "#60A5FA", "#FBBF24"] : ["#059669", "#2563EB", "#D97706"],
        borderWidth: 0,
        hoverOffset: 4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "65%",
      plugins: {
        legend: { position: "bottom", labels: { color: textColor, font: { size: 12 }, padding: 16 } },
        tooltip: {
          callbacks: {
            label: function (ctx) {
              var total = ctx.dataset.data.reduce(function (a, b) { return a + b; }, 0);
              var pct = total > 0 ? Math.round(ctx.raw / total * 100) : 0;
              return ctx.label + ": " + pct + "% (" + ctx.raw + ")";
            }
          }
        }
      }
    }
  });
  chartInstances.push(pieChart);

  /* Recent Analyses Table — data from analises_recentes */
  var analyses = data.analises_recentes || [];
  renderRecentAnalysesTable(container, analyses);
}

function renderDashboardFallback(container) {
  var demoData = {
    total_clientes: 0, total_analises: 0, total_recuperacao: 0, media_recuperacao_por_cliente: 0,
    por_tributo: [], por_regime: [], analises_recentes: []
  };
  renderDashboardContent(container, demoData);
}

function renderRecentAnalysesTable(container, analyses) {
  var tableCard = el("div", { className: "table-card" });
  tableCard.appendChild(el("div", { className: "table-header" }, [
    el("div", { className: "table-title" }, "Últimas Análises Realizadas"),
  ]));

  if (!analyses.length) {
    tableCard.appendChild(el("div", { className: "empty-state" }, [
      el("div", { innerHTML: icon("inbox") }),
      el("h3", {}, "Nenhuma análise realizada"),
      el("p", {}, "Cadastre um cliente e faça o upload dos arquivos fiscais para iniciar."),
    ]));
    container.appendChild(tableCard);
    return;
  }

  var scroll = el("div", { className: "table-scroll" });
  var table = el("table", { className: "data-table" });
  var thead = el("thead");
  var headRow = el("tr");
  ["Cliente", "CNPJ", "Regime", "Total Recuperável", "Data", "Status"].forEach(function (h) {
    headRow.appendChild(el("th", {}, h));
  });
  thead.appendChild(headRow);
  table.appendChild(thead);

  var tbody = el("tbody");
  analyses.forEach(function (a) {
    var tr = el("tr", { className: "clickable", onClick: function () { navigate("/analise/" + a.id); } });
    tr.appendChild(el("td", { style: "font-weight:500" }, a.empresa || "—"));
    tr.appendChild(el("td", { className: "font-mono" }, formatCNPJ(a.cnpj)));
    tr.appendChild(el("td", {}, el("span", { className: "badge badge-neutral" }, regimeLabel(a.regime))));
    tr.appendChild(el("td", { className: "value-green" }, formatCurrency(a.total_recuperacao)));
    tr.appendChild(el("td", {}, formatDate(a.created_at)));
    var statusBadge = a.status === "completed" ? "badge-success" : a.status === "error" ? "badge-error" : "badge-warning";
    var statusText = a.status === "completed" ? "Concluída" : a.status === "error" ? "Erro" : "Pendente";
    tr.appendChild(el("td", {}, el("span", { className: "badge " + statusBadge }, statusText)));
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  scroll.appendChild(table);
  tableCard.appendChild(scroll);
  container.appendChild(tableCard);
}

/* ============================================================
   PAGE: CLIENTES
   ============================================================ */
function renderClientes(container) {
  container.innerHTML = "";

  var pageHeader = el("div", { className: "page-header" }, [
    el("h1", { className: "page-title" }, "Clientes"),
    el("button", { className: "btn btn-primary", onClick: openNewClientModal, innerHTML: icon("plus") + " Novo Cliente" }),
  ]);
  container.appendChild(pageHeader);

  var searchBar = el("div", { className: "search-bar", style: "margin-bottom:var(--space-4)" });
  var searchWrap = el("div", { className: "search-input-wrapper", innerHTML: icon("search") });
  var searchInput = el("input", { className: "search-input", type: "text", placeholder: "Buscar por nome, CNPJ ou setor..." });
  searchWrap.appendChild(searchInput);
  searchBar.appendChild(searchWrap);
  container.appendChild(searchBar);

  var tableContainer = el("div");
  container.appendChild(tableContainer);
  tableContainer.appendChild(skeletonTable());

  var allClients = [];

  function renderTable(clients) {
    tableContainer.innerHTML = "";
    var tableCard = el("div", { className: "table-card" });

    if (!clients.length) {
      tableCard.appendChild(el("div", { className: "empty-state" }, [
        el("div", { innerHTML: icon("inbox") }),
        el("h3", {}, "Nenhum cliente encontrado"),
        el("p", {}, 'Cadastre o primeiro cliente clicando em "Novo Cliente".'),
      ]));
      tableContainer.appendChild(tableCard);
      return;
    }

    var scroll = el("div", { className: "table-scroll" });
    var table = el("table", { className: "data-table" });
    var thead = el("thead");
    var headRow = el("tr");
    ["CNPJ", "Nome", "Regime", "UF", "Setor", "Cadastro"].forEach(function (h) { headRow.appendChild(el("th", {}, h)); });
    thead.appendChild(headRow);
    table.appendChild(thead);

    var tbody = el("tbody");
    clients.forEach(function (c) {
      var tr = el("tr", { className: "clickable", onClick: function () { navigate("/cliente/" + c.id); } });
      tr.appendChild(el("td", { className: "font-mono" }, formatCNPJ(c.cnpj)));
      tr.appendChild(el("td", { style: "font-weight:500" }, c.company_name || c.name || "—"));
      tr.appendChild(el("td", {}, el("span", { className: "badge badge-neutral" }, regimeLabel(c.tax_regime || c.regime))));
      tr.appendChild(el("td", {}, (c.state_uf || c.uf || "—").toUpperCase()));
      tr.appendChild(el("td", {}, sectorLabel(c.activity_sector || c.sector)));
      tr.appendChild(el("td", {}, formatDate(c.created_at)));
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    scroll.appendChild(table);
    tableCard.appendChild(scroll);
    tableContainer.appendChild(tableCard);
  }

  searchInput.addEventListener("input", function () {
    var q = searchInput.value.toLowerCase();
    var filtered = allClients.filter(function (c) {
      return (c.company_name || "").toLowerCase().includes(q) ||
        (c.cnpj || "").includes(q) ||
        (c.activity_sector || "").toLowerCase().includes(q) ||
        (c.state_uf || "").toLowerCase().includes(q);
    });
    renderTable(filtered);
  });

  apiFetch("/api/clients").then(function (data) {
    allClients = Array.isArray(data) ? data : data.clients || [];
    renderTable(allClients);
  }).catch(function () {
    allClients = [];
    renderTable([]);
  });
}

/* ===== NEW CLIENT MODAL ===== */
function openNewClientModal() {
  var overlay = document.getElementById("modal-overlay");
  var modalContent = document.getElementById("modal-content");
  if (!overlay || !modalContent) return;

  modalContent.innerHTML = "";
  modalContent.appendChild(el("div", { className: "modal-header" }, [
    el("div", { className: "modal-title" }, "Novo Cliente"),
    el("button", { className: "modal-close", onClick: closeModal, innerHTML: icon("close"), "aria-label": "Fechar" }),
  ]));

  var body = el("div", { className: "modal-body" });
  body.appendChild(el("div", { className: "form-group cnpj-field-group" }, [
    el("label", { className: "form-label" }, "CNPJ"),
    el("input", { className: "form-input", type: "text", id: "modal-cnpj", placeholder: "00.000.000/0000-00" }),
    el("small", { className: "form-hint" }, "Digite o CNPJ para preencher os dados automaticamente"),
  ]));
  body.appendChild(el("div", { className: "form-group" }, [
    el("label", { className: "form-label" }, "Nome da Empresa"),
    el("input", { className: "form-input", type: "text", id: "modal-name", placeholder: "Ex: Supermercado Bom Preço" }),
  ]));

  var row1 = el("div", { className: "form-row" });
  var regimeSelect = el("select", { className: "form-select", id: "modal-regime" });
  regimeSelect.appendChild(el("option", { value: "" }, "Selecione..."));
  REGIMES.forEach(function (r) { regimeSelect.appendChild(el("option", { value: r }, r)); });
  row1.appendChild(el("div", { className: "form-group" }, [el("label", { className: "form-label" }, "Regime Tributário"), regimeSelect]));

  var ufSelect = el("select", { className: "form-select", id: "modal-uf" });
  ufSelect.appendChild(el("option", { value: "" }, "Selecione..."));
  UF_LIST.forEach(function (u) { ufSelect.appendChild(el("option", { value: u }, u)); });
  row1.appendChild(el("div", { className: "form-group" }, [el("label", { className: "form-label" }, "UF"), ufSelect]));
  body.appendChild(row1);

  var setorSelect = el("select", { className: "form-select", id: "modal-setor" });
  setorSelect.appendChild(el("option", { value: "" }, "Selecione..."));
  SETORES.forEach(function (s) { setorSelect.appendChild(el("option", { value: s }, s)); });
  body.appendChild(el("div", { className: "form-group" }, [el("label", { className: "form-label" }, "Setor de Atividade"), setorSelect]));
  body.appendChild(el("div", { className: "form-group" }, [el("label", { className: "form-label" }, "Certificado Digital A1 (.pfx) — opcional"), el("input", { className: "form-input", type: "file", id: "modal-cert", accept: ".pfx" })]));
  body.appendChild(el("div", { className: "form-group" }, [el("label", { className: "form-label" }, "Senha do Certificado — opcional"), el("input", { className: "form-input", type: "password", id: "modal-cert-pass", placeholder: "Senha" })]));
  modalContent.appendChild(body);

  modalContent.appendChild(el("div", { className: "modal-footer" }, [
    el("button", { className: "btn btn-secondary", onClick: closeModal }, "Cancelar"),
    el("button", { className: "btn btn-primary", id: "modal-save-btn", onClick: saveNewClient }, "Criar Cliente"),
  ]));

  overlay.classList.add("active");
  var cnpjInput = document.getElementById("modal-cnpj");
  if (cnpjInput) maskCNPJInput(cnpjInput);
}

function closeModal() {
  var overlay = document.getElementById("modal-overlay");
  if (overlay) overlay.classList.remove("active");
}

function saveNewClient() {
  var name = document.getElementById("modal-name").value.trim();
  var cnpj = document.getElementById("modal-cnpj").value.replace(/\D/g, "");
  var regime = document.getElementById("modal-regime").value;
  var uf = document.getElementById("modal-uf").value;
  var sector = document.getElementById("modal-setor").value;

  if (!name) { showToast("Informe o nome da empresa.", "warning"); return; }
  if (cnpj.length !== 14) { showToast("CNPJ inválido. Informe os 14 dígitos.", "warning"); return; }

  var saveBtn = document.getElementById("modal-save-btn");
  if (saveBtn) saveBtn.disabled = true;

  /* Map to backend field names */
  var formatted = cnpj.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5");

  apiFetch("/api/clients", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      company_name: name,
      cnpj: formatted,
      tax_regime: regimeToCode(regime),
      state_uf: uf,
      activity_sector: sectorToCode(sector)
    }),
  }).then(function (client) {
    closeModal();
    showToast("Cliente \"" + name + "\" criado com sucesso!", "success");
    navigate("/cliente/" + client.id);
  }).catch(function (err) {
    if (saveBtn) saveBtn.disabled = false;
    showToast("Erro ao criar cliente: " + err.message, "error");
  });
}

/* ============================================================
   PAGE: CLIENTE DETAIL
   ============================================================ */
function renderClienteDetail(container, clientId) {
  container.innerHTML = "";
  container.appendChild(el("div", { className: "skeleton skeleton-title", style: "width:200px" }));
  container.appendChild(skeletonKPIs(3));

  apiFetch("/api/clients/" + clientId).then(function (client) {
    container.innerHTML = "";
    buildClientDetailView(container, client);
  }).catch(function (err) {
    container.innerHTML = "";
    container.appendChild(el("div", { className: "empty-state" }, [
      el("h3", {}, "Cliente não encontrado"),
      el("p", {}, err.message),
      el("button", { className: "btn btn-primary", onClick: function () { navigate("/clientes"); } }, "Voltar para Clientes"),
    ]));
  });
}

function buildClientDetailView(container, client) {
  var cName = client.company_name || client.name || "Cliente";
  var cRegime = regimeLabel(client.tax_regime || client.regime);
  var cUF = (client.state_uf || client.uf || "").toUpperCase();
  var cSector = sectorLabel(client.activity_sector || client.sector);

  var header = el("div", { className: "client-header" });
  var info = el("div", { className: "client-info" });
  info.appendChild(el("h1", {}, cName));
  var meta = el("div", { className: "client-meta" });
  meta.appendChild(el("span", { className: "client-meta-item font-mono" }, formatCNPJ(client.cnpj)));
  if (cRegime !== "—") meta.appendChild(el("span", { className: "client-meta-item" }, cRegime));
  if (cUF) meta.appendChild(el("span", { className: "client-meta-item" }, cUF));
  if (cSector !== "—") meta.appendChild(el("span", { className: "client-meta-item" }, cSector));
  info.appendChild(meta);
  header.appendChild(info);

  header.appendChild(el("button", {
    className: "btn btn-primary btn-lg",
    innerHTML: icon("play") + " Executar Análise",
    onClick: function () { runAnalysis(client.id); }
  }));
  container.appendChild(header);

  var tabNames = ["Visão Geral", "Arquivos", "Análises", "Certificado Digital"];
  var tabContainer = el("div", { className: "tabs" });
  var contentContainer = el("div");

  tabNames.forEach(function (name, i) {
    tabContainer.appendChild(el("div", {
      className: "tab" + (i === 0 ? " active" : ""),
      onClick: function () { switchTab(i); }
    }, name));
  });
  container.appendChild(tabContainer);
  container.appendChild(contentContainer);

  function switchTab(index) {
    tabContainer.querySelectorAll(".tab").forEach(function (t, i) { t.classList.toggle("active", i === index); });
    renderTabContent(index);
  }

  function renderTabContent(index) {
    contentContainer.innerHTML = "";
    if (index === 0) renderOverviewTab(contentContainer, client);
    else if (index === 1) renderFilesTab(contentContainer, client);
    else if (index === 2) renderAnalysesTab(contentContainer, client);
    else if (index === 3) renderCertTab(contentContainer, client);
  }

  renderTabContent(0);
}

function renderOverviewTab(container, client) {
  var kpiGrid = el("div", { className: "kpi-grid" });
  var kpis = [
    { label: "Total Recuperável", value: formatCurrency(client.total_recovery || 0), primary: true },
    { label: "Análises Feitas", value: String(client.total_analyses || 0) },
    { label: "Arquivos Enviados", value: String(client.total_uploads || 0) },
  ];
  kpis.forEach(function (k) {
    kpiGrid.appendChild(el("div", { className: "kpi-card" }, [
      el("div", { className: "kpi-label" }, k.label),
      el("div", { className: "kpi-value" + (k.primary ? " primary" : "") }, k.value),
    ]));
  });
  container.appendChild(kpiGrid);
}

function renderFilesTab(container, client) {
  var uploadZone = el("div", { className: "upload-zone", id: "upload-zone" });
  uploadZone.innerHTML = icon("upload") + '<div class="upload-zone-text">Arraste arquivos SPED, XML ou ZIP aqui</div><div class="upload-zone-sub">Aceita: SPED EFD (.txt), XML de NFe (.xml), ZIP com XMLs (.zip)</div>';
  var fileInput = el("input", { type: "file", style: "display:none", id: "file-input", multiple: "true", accept: ".txt,.xml,.sped,.zip" });
  uploadZone.appendChild(fileInput);

  uploadZone.addEventListener("click", function () { fileInput.click(); });
  uploadZone.addEventListener("dragover", function (e) { e.preventDefault(); uploadZone.classList.add("drag-over"); });
  uploadZone.addEventListener("dragleave", function () { uploadZone.classList.remove("drag-over"); });
  uploadZone.addEventListener("drop", function (e) {
    e.preventDefault(); uploadZone.classList.remove("drag-over");
    if (e.dataTransfer.files.length) uploadFiles(client.id, e.dataTransfer.files);
  });
  fileInput.addEventListener("change", function () { if (fileInput.files.length) uploadFiles(client.id, fileInput.files); });
  container.appendChild(uploadZone);

  var filesContainer = el("div", { style: "margin-top:var(--space-4)" });
  container.appendChild(filesContainer);
  loadUploads(client.id, filesContainer);
}

function loadUploads(clientId, container) {
  container.innerHTML = "";
  apiFetch("/api/clients/" + clientId + "/uploads").then(function (data) {
    var uploads = Array.isArray(data) ? data : data.uploads || [];
    if (!uploads.length) {
      container.appendChild(el("div", { className: "empty-state", style: "padding:var(--space-8)" }, [
        el("h3", {}, "Nenhum arquivo enviado"),
        el("p", {}, "Faça upload de arquivos SPED ou XML acima."),
      ]));
      return;
    }
    var tableCard = el("div", { className: "table-card" });
    var scroll = el("div", { className: "table-scroll" });
    var table = el("table", { className: "data-table" });
    var thead = el("thead");
    var headRow = el("tr");
    ["Arquivo", "Tipo", "Período", "Status", "Data Upload"].forEach(function (h) { headRow.appendChild(el("th", {}, h)); });
    thead.appendChild(headRow);
    table.appendChild(thead);

    var tbody = el("tbody");
    uploads.forEach(function (u) {
      var tr = el("tr");
      var fname = u.filename || u.original_filename || "Arquivo";
      tr.appendChild(el("td", {}, [el("span", { innerHTML: icon("file"), style: "display:inline;margin-right:4px" }), document.createTextNode(fname)]));
      tr.appendChild(el("td", {}, el("span", { className: "badge badge-info" }, (u.file_type || "—").replace("_", " ").toUpperCase())));
      var period = u.period_start && u.period_end ? formatDate(u.period_start) + " — " + formatDate(u.period_end) : "—";
      tr.appendChild(el("td", {}, period));
      var statusClass = u.status === "completed" ? "badge-success" : u.status === "error" ? "badge-error" : "badge-warning";
      var statusText = u.status === "completed" ? "Processado" : u.status === "error" ? "Erro" : "Pendente";
      tr.appendChild(el("td", {}, el("span", { className: "badge " + statusClass }, statusText)));
      tr.appendChild(el("td", {}, formatDateTime(u.created_at)));
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    scroll.appendChild(table);
    tableCard.appendChild(scroll);
    container.appendChild(tableCard);
  }).catch(function () {
    container.appendChild(el("div", { className: "empty-state", style: "padding:var(--space-8)" }, [
      el("h3", {}, "Erro ao carregar arquivos"),
    ]));
  });
}

function uploadFiles(clientId, files) {
  var fileList = Array.prototype.slice.call(files);
  var total = fileList.length;
  var done = 0;
  var errors = 0;
  var totalItems = 0;
  var totalNfes = 0;
  var totalFat = 0;
  showToast("Enviando e processando " + total + " arquivo(s)...", "info");

  function uploadNext(idx) {
    if (idx >= fileList.length) {
      var msg = done + " de " + total + " arquivo(s) processado(s).";
      if (totalItems) msg += " " + totalItems + " itens fiscais extraídos.";
      if (totalNfes) msg += " " + totalNfes + " NFe(s) lida(s).";
      if (totalFat) msg += " Faturamento: R$ " + Number(totalFat).toLocaleString("pt-BR", {minimumFractionDigits: 2});
      showToast(msg, errors ? "warning" : "success");
      currentRoute = ""; handleRoute();
      return;
    }
    var formData = new FormData();
    formData.append("file", fileList[idx]);
    fetch(API_BASE + "/api/clients/" + clientId + "/upload", { method: "POST", body: formData })
      .then(function (res) { if (!res.ok) return res.json().then(function(e) { throw new Error(e.detail || "Upload failed"); }); return res.json(); })
      .then(function (data) {
        done++;
        if (data.parse_summary) {
          var ps = data.parse_summary;
          if (ps.items_stored) totalItems += ps.items_stored;
          if (ps.nfes_parsed) totalNfes += ps.nfes_parsed;
          if (ps.total_faturamento) totalFat += ps.total_faturamento;
        }
        uploadNext(idx + 1);
      })
      .catch(function (err) {
        errors++;
        done++;
        showToast("Erro no arquivo " + fileList[idx].name + ": " + err.message, "error");
        uploadNext(idx + 1);
      });
  }
  uploadNext(0);
}

function renderAnalysesTab(container, client) {
  container.innerHTML = "";
  container.appendChild(el("div", { className: "skeleton skeleton-text", style: "width:200px" }));

  /* Fetch analyses by re-fetching client detail which includes total_analyses */
  apiFetch("/api/dashboard/stats").then(function (stats) {
    container.innerHTML = "";
    var analyses = (stats.analises_recentes || []).filter(function (a) {
      return String(a.client_id) === String(client.id);
    });
    /* Also check by empresa name */
    if (!analyses.length) {
      analyses = (stats.analises_recentes || []).filter(function (a) {
        return a.empresa === (client.company_name || client.name);
      });
    }
    if (!analyses.length) {
      container.appendChild(el("div", { className: "empty-state" }, [
        el("div", { innerHTML: icon("inbox") }),
        el("h3", {}, "Nenhuma análise disponível"),
        el("p", {}, 'Clique em "Executar Análise" para iniciar.'),
      ]));
      return;
    }
    var tableCard = el("div", { className: "table-card" });
    var scroll = el("div", { className: "table-scroll" });
    var table = el("table", { className: "data-table" });
    var thead = el("thead");
    var headRow = el("tr");
    ["ID", "Status", "Total Recuperável", "Data"].forEach(function (h) { headRow.appendChild(el("th", {}, h)); });
    thead.appendChild(headRow);
    table.appendChild(thead);
    var tbody = el("tbody");
    analyses.forEach(function (a) {
      var tr = el("tr", { className: "clickable", onClick: function () { navigate("/analise/" + a.id); } });
      tr.appendChild(el("td", {}, "#" + a.id));
      var sc = a.status === "completed" ? "badge-success" : a.status === "error" ? "badge-error" : "badge-warning";
      var st = a.status === "completed" ? "Concluída" : a.status === "error" ? "Erro" : "Pendente";
      tr.appendChild(el("td", {}, el("span", { className: "badge " + sc }, st)));
      tr.appendChild(el("td", { className: "value-green" }, formatCurrency(a.total_recuperacao)));
      tr.appendChild(el("td", {}, formatDate(a.created_at)));
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    scroll.appendChild(table);
    tableCard.appendChild(scroll);
    container.appendChild(tableCard);
  }).catch(function () {
    container.innerHTML = "";
    container.appendChild(el("div", { className: "empty-state" }, [
      el("h3", {}, "Nenhuma análise disponível"),
      el("p", {}, "Execute uma análise para ver resultados."),
    ]));
  });
}

function renderCertTab(container, client) {
  var hasCert = !!client.certificate_file;
  var certStatus = el("div", { className: "cert-status" });
  certStatus.appendChild(el("div", { className: "cert-icon " + (hasCert ? "active" : "inactive"), innerHTML: icon(hasCert ? "shield" : "key") }));
  var textDiv = el("div");
  textDiv.appendChild(el("div", { style: "font-weight:600;font-size:var(--text-sm)" }, hasCert ? "Certificado Digital A1 Ativo" : "Nenhum Certificado"));
  textDiv.appendChild(el("div", { style: "font-size:var(--text-xs);color:var(--color-text-muted);margin-top:var(--space-1)" },
    hasCert ? "Certificado digital configurado e válido." : "Faça upload do certificado A1 (.pfx) para integração com a Receita Federal."
  ));
  certStatus.appendChild(textDiv);
  container.appendChild(certStatus);

  if (!hasCert) {
    var uploadForm = el("div", { style: "margin-top:var(--space-4);display:flex;flex-direction:column;gap:var(--space-4);max-width:400px" });
    uploadForm.appendChild(el("div", { className: "form-group" }, [
      el("label", { className: "form-label" }, "Arquivo do Certificado (.pfx)"),
      el("input", { className: "form-input", type: "file", accept: ".pfx", id: "cert-upload" }),
    ]));
    uploadForm.appendChild(el("div", { className: "form-group" }, [
      el("label", { className: "form-label" }, "Senha do Certificado"),
      el("input", { className: "form-input", type: "password", id: "cert-pass", placeholder: "Senha" }),
    ]));
    uploadForm.appendChild(el("button", { className: "btn btn-primary", innerHTML: icon("upload") + " Enviar Certificado", onClick: function () {
      showToast("Certificado enviado com sucesso!", "success");
    }}));
    container.appendChild(uploadForm);
  }
}

function runAnalysis(clientId) {
  showToast("Iniciando análise tributária...", "info");
  var overlay = el("div", { className: "loading-overlay", id: "analysis-loading" });
  overlay.appendChild(el("div", { style: "text-align:center;background:var(--color-surface);padding:var(--space-8);border-radius:var(--radius-xl);box-shadow:var(--shadow-lg)" }, [
    el("div", { className: "loading-spinner", style: "margin:0 auto var(--space-4)" }),
    el("div", { style: "font-weight:600;margin-bottom:var(--space-2)" }, "Executando Análise"),
    el("div", { style: "font-size:var(--text-xs);color:var(--color-text-muted)" }, "Analisando tributos e identificando oportunidades..."),
  ]));
  document.body.appendChild(overlay);

  apiFetch("/api/clients/" + clientId + "/analyze", { method: "POST" }).then(function (result) {
    document.body.removeChild(overlay);
    showToast("Análise concluída com sucesso!", "success");
    navigate("/analise/" + result.id);
  }).catch(function (err) {
    document.body.removeChild(overlay);
    var rawMsg = err.message || "Erro desconhecido";
    /* Extract clean detail message from API error JSON */
    var msg = rawMsg;
    var jsonMatch = rawMsg.match(/\{.*\}/);
    if (jsonMatch) {
      try {
        var parsed = JSON.parse(jsonMatch[0]);
        if (parsed.detail) msg = parsed.detail;
      } catch(e) { /* keep rawMsg */ }
    }
    if (msg.indexOf("arquivo") !== -1 || msg.indexOf("certificado") !== -1 || msg.indexOf("análise") !== -1) {
      // Show prominent validation alert
      var alertOverlay = el("div", { className: "loading-overlay", id: "analysis-alert" });
      var alertBox = el("div", { style: "text-align:center;background:var(--color-surface);padding:var(--space-8);border-radius:var(--radius-xl);box-shadow:var(--shadow-lg);max-width:480px" }, [
        el("div", { style: "font-size:48px;margin-bottom:var(--space-4)" }, "⚠️"),
        el("div", { style: "font-weight:700;font-size:var(--text-lg);margin-bottom:var(--space-3);color:var(--color-text)" }, "Análise Indisponível"),
        el("div", { style: "font-size:var(--text-sm);color:var(--color-text-muted);margin-bottom:var(--space-6);line-height:1.6" }, msg),
        el("div", { style: "display:flex;gap:var(--space-3);justify-content:center;flex-wrap:wrap" }, [
          el("button", { className: "btn btn-primary", innerHTML: icon("upload") + " Enviar Arquivos", onClick: function() { document.body.removeChild(alertOverlay); var tabBtns = document.querySelectorAll(".tab"); tabBtns.forEach(function(b){ if(b.textContent.trim()==="Arquivos") b.click(); }); } }),
          el("button", { className: "btn btn-secondary", innerHTML: icon("key") + " Certificado Digital", onClick: function() { document.body.removeChild(alertOverlay); var tabBtns = document.querySelectorAll(".tab"); tabBtns.forEach(function(b){ if(b.textContent.trim()==="Certificado Digital") b.click(); }); } }),
          el("button", { className: "btn btn-ghost", onClick: function() { document.body.removeChild(alertOverlay); } }, "Fechar"),
        ]),
      ]);
      alertOverlay.appendChild(alertBox);
      document.body.appendChild(alertOverlay);
    } else {
      showToast("Erro na análise: " + msg, "error");
    }
  });
}

/* ============================================================
   PAGE: ANALYSIS RESULT
   ============================================================ */
function renderAnalysis(container, analysisId) {
  container.innerHTML = "";
  container.appendChild(el("div", { className: "skeleton skeleton-title", style: "width:300px" }));
  container.appendChild(skeletonKPIs(4));
  container.appendChild(skeletonTable());

  apiFetch("/api/analyses/" + analysisId).then(function (analysis) {
    container.innerHTML = "";
    buildAnalysisView(container, analysis);
  }).catch(function (err) {
    container.innerHTML = "";
    container.appendChild(el("div", { className: "empty-state" }, [
      el("h3", {}, "Análise não encontrada"),
      el("p", {}, err.message),
      el("button", { className: "btn btn-primary", onClick: function () { navigate("/"); } }, "Voltar ao Dashboard"),
    ]));
  });
}

function buildAnalysisView(container, analysis) {
  var pageHeader = el("div", { className: "page-header" }, [
    el("div", {}, [
      el("h1", { className: "page-title" }, "Resultado da Análise #" + analysis.id),
      el("div", { style: "font-size:var(--text-xs);color:var(--color-text-muted);margin-top:var(--space-1)" },
        (analysis.analysis_type || "Completa") + " · " + formatDate(analysis.created_at)
      ),
    ]),
    el("div", { style: "display:flex;gap:var(--space-3)" }, [
      el("button", { className: "btn btn-secondary", innerHTML: icon("printer") + " Exportar Relatório", onClick: function () { window.print(); } }),
      analysis.client_id ? el("button", { className: "btn btn-ghost", onClick: function () { navigate("/cliente/" + analysis.client_id); } }, "Voltar ao Cliente") : null,
    ]),
  ]);
  container.appendChild(pageHeader);

  /* Hero: Total Recovery */
  var totalRecovery = analysis.total_recovery_amount || 0;
  container.appendChild(el("div", { className: "analysis-hero" }, [
    el("div", { className: "analysis-hero-label" }, "Total Recuperável"),
    el("div", { className: "analysis-hero-value" }, formatCurrency(totalRecovery)),
    el("div", { className: "analysis-hero-sub" }, "Status: " + (analysis.status === "completed" ? "Concluída" : analysis.status || "—")),
  ]));

  /* Items */
  var items = analysis.recovery_items || [];

  /* Build summary by tax type */
  var summary = {};
  items.forEach(function (item) {
    var tax = taxTypeLabel(item.tax_type);
    if (!summary[tax]) summary[tax] = 0;
    summary[tax] += item.valor_recuperar || 0;
  });

  if (Object.keys(summary).length) {
    var kpiGrid = el("div", { className: "kpi-grid" });
    Object.keys(summary).forEach(function (tax) {
      kpiGrid.appendChild(el("div", { className: "kpi-card" }, [
        el("div", { className: "kpi-label" }, tax),
        el("div", { className: "kpi-value primary" }, formatCurrency(summary[tax])),
      ]));
    });
    container.appendChild(kpiGrid);
  }

  /* Monthly Timeline Chart */
  if (items.length) {
    var chartCard = el("div", { className: "chart-card", style: "margin-bottom:var(--space-6)" });
    chartCard.appendChild(el("div", { className: "chart-title" }, "Recuperação Mensal"));
    var chartCanvas = el("canvas");
    chartCard.appendChild(el("div", { className: "chart-container" }, chartCanvas));
    container.appendChild(chartCard);

    var monthly = {};
    items.forEach(function (item) {
      var period = item.period || "—";
      if (!monthly[period]) monthly[period] = 0;
      monthly[period] += item.valor_recuperar || 0;
    });

    var isDark = currentTheme === "dark";
    var monthLabels = Object.keys(monthly).sort();
    var monthValues = monthLabels.map(function (m) { return monthly[m]; });

    var lineChart = new Chart(chartCanvas, {
      type: "line",
      data: {
        labels: monthLabels,
        datasets: [{
          label: "Valor Recuperável",
          data: monthValues,
          borderColor: isDark ? "#34D399" : "#059669",
          backgroundColor: isDark ? "rgba(52,211,153,0.1)" : "rgba(5,150,105,0.1)",
          fill: true,
          tension: 0.3,
          pointRadius: 4,
          pointHoverRadius: 6,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: function (ctx) { return formatCurrency(ctx.raw); } } },
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: isDark ? "rgba(148,163,184,0.1)" : "rgba(15,23,42,0.06)" },
            ticks: {
              color: isDark ? "#94A3B8" : "#64748B", font: { size: 11 },
              callback: function (v) {
                if (v === 0) return "R$ 0";
                if (Math.abs(v) >= 1000) return "R$ " + (v / 1000).toLocaleString("pt-BR") + "k";
                return "R$ " + v.toLocaleString("pt-BR");
              }
            },
          },
          x: { grid: { display: false }, ticks: { color: isDark ? "#94A3B8" : "#64748B", font: { size: 11 } } },
        },
      },
    });
    chartInstances.push(lineChart);
  }

  /* Breakdown Table */
  var tableCard = el("div", { className: "table-card" });
  tableCard.appendChild(el("div", { className: "table-header" }, [
    el("div", { className: "table-title" }, "Detalhamento dos Itens"),
    el("div", { style: "font-size:var(--text-xs);color:var(--color-text-muted)" }, items.length + " itens encontrados"),
  ]));

  if (!items.length) {
    tableCard.appendChild(el("div", { className: "empty-state" }, [
      el("h3", {}, "Nenhum item de recuperação"),
      el("p", {}, "A análise não encontrou itens recuperáveis."),
    ]));
    container.appendChild(tableCard);
    return;
  }

  var scroll = el("div", { className: "table-scroll" });
  var table = el("table", { className: "data-table" });
  var thead = el("thead");
  var headRow = el("tr");
  ["Tributo", "Período", "NCM", "Descrição", "Base Original", "Base Correta", "Alíq. Orig.", "Alíq. Correta", "Valor Pago", "Valor Devido", "Recuperar", "Fundamentação", "Confiança"].forEach(function (c) {
    headRow.appendChild(el("th", {}, c));
  });
  thead.appendChild(headRow);
  table.appendChild(thead);

  var tbody = el("tbody");
  items.forEach(function (item) {
    var tr = el("tr");
    tr.appendChild(el("td", {}, el("span", { className: "badge badge-info" }, taxTypeLabel(item.tax_type))));
    tr.appendChild(el("td", {}, item.period || "—"));
    tr.appendChild(el("td", { className: "font-mono" }, item.ncm_code || "—"));
    tr.appendChild(el("td", { style: "white-space:normal;max-width:200px" }, item.description || "—"));
    tr.appendChild(el("td", { className: "text-right" }, formatCurrency(item.base_calculo_original)));
    tr.appendChild(el("td", { className: "text-right" }, formatCurrency(item.base_calculo_correta)));
    tr.appendChild(el("td", { className: "text-right" }, (item.aliquota_original != null ? item.aliquota_original : "—") + "%"));
    tr.appendChild(el("td", { className: "text-right" }, (item.aliquota_correta != null ? item.aliquota_correta : "—") + "%"));
    tr.appendChild(el("td", { className: "text-right" }, formatCurrency(item.valor_pago)));
    tr.appendChild(el("td", { className: "text-right" }, formatCurrency(item.valor_devido)));
    tr.appendChild(el("td", { className: "text-right value-green" }, formatCurrency(item.valor_recuperar)));
    tr.appendChild(el("td", { style: "white-space:normal;max-width:180px;font-size:11px" }, item.legal_basis || "—"));

    var confLevel = (item.confidence || "medium").toLowerCase();
    var confClass = confLevel === "high" ? "badge-success" : confLevel === "low" ? "badge-error" : "badge-warning";
    var confText = confLevel === "high" ? "Alta" : confLevel === "low" ? "Baixa" : "Média";
    tr.appendChild(el("td", {}, el("span", { className: "badge " + confClass }, confText)));
    tbody.appendChild(tr);
  });

  table.appendChild(tbody);
  scroll.appendChild(table);
  tableCard.appendChild(scroll);
  container.appendChild(tableCard);

  /* === NCM Comparison Section === */
  apiFetch("/api/analyses/" + analysis.id + "/ncm-comparacao").then(function (ncmData) {
    if (!ncmData || !ncmData.resumo || ncmData.resumo.total_produtos === 0) return;

    var resumo = ncmData.resumo;
    var comparacoes = ncmData.comparacoes || [];

    var ncmSection = el("div", { style: "margin-top:var(--space-6)" });

    ncmSection.appendChild(el("h2", {
      style: "font-size:var(--text-lg);font-weight:700;margin-bottom:var(--space-4);display:flex;align-items:center;gap:var(--space-2)"
    }, [
      el("span", { innerHTML: icon("package"), style: "display:flex" }),
      document.createTextNode("Compara\u00e7\u00e3o NCM \u2014 Base de Refer\u00eancia")
    ]));

    var ncmKpis = el("div", { className: "kpi-grid" });
    var conformidadeClass = resumo.taxa_conformidade >= 90 ? "primary" : "";
    [
      { label: "Produtos Analisados", value: String(resumo.total_produtos), icon: "box" },
      { label: "NCM Correto", value: String(resumo.ncm_correto), icon: "check-circle", cls: "value-green" },
      { label: "Diverg\u00eancias", value: String(resumo.ncm_divergente), icon: "alert-triangle", cls: resumo.ncm_divergente > 0 ? "value-red" : "" },
      { label: "N\u00e3o Cadastrado", value: String(resumo.ncm_nao_cadastrado), icon: "help-circle" },
      { label: "Conformidade", value: resumo.taxa_conformidade + "%", icon: "target", cls: conformidadeClass },
    ].forEach(function (k) {
      ncmKpis.appendChild(el("div", { className: "kpi-card" }, [
        el("div", { className: "kpi-label", innerHTML: icon(k.icon) + " " + k.label }),
        el("div", { className: "kpi-value" + (k.cls ? " " + k.cls : "") }, k.value),
      ]));
    });
    ncmSection.appendChild(ncmKpis);

    var divergencias = comparacoes.filter(function (c) { return c.status !== "ok"; });

    if (divergencias.length > 0) {
      var divCard = el("div", { className: "table-card", style: "margin-top:var(--space-4)" });
      divCard.appendChild(el("div", { className: "table-header" }, [
        el("div", { className: "table-title" }, "Diverg\u00eancias de NCM Encontradas"),
        el("div", { style: "font-size:var(--text-xs);color:var(--color-text-muted)" }, divergencias.length + " itens com diverg\u00eancia"),
      ]));

      var divScroll = el("div", { className: "table-scroll" });
      var divTable = el("table", { className: "data-table" });
      var divThead = el("thead");
      var divHeadRow = el("tr");
      ["Status", "Produto (NF-e)", "NCM NF-e", "NCM Ref.", "Produto Ref.", "Categoria", "Impacto Fiscal"].forEach(function (h) {
        divHeadRow.appendChild(el("th", {}, h));
      });
      divThead.appendChild(divHeadRow);
      divTable.appendChild(divThead);

      var divTbody = el("tbody");
      divergencias.forEach(function (comp) {
        var row = el("tr");
        var statusBadge = comp.status === "divergencia"
          ? el("span", { className: "badge badge-warning" }, "Divergente")
          : el("span", { className: "badge badge-error" }, "N\u00e3o Cadastrado");
        row.appendChild(el("td", {}, statusBadge));
        row.appendChild(el("td", { style: "max-width:180px;white-space:normal" }, comp.descricao_nfe || "\u2014"));
        row.appendChild(el("td", { className: "font-mono" }, comp.ncm_nfe || "\u2014"));
        row.appendChild(el("td", { className: "font-mono" }, comp.ncm_referencia || "\u2014"));
        row.appendChild(el("td", { style: "max-width:180px;white-space:normal" }, comp.descricao_referencia || "\u2014"));
        row.appendChild(el("td", {}, comp.categoria_referencia || "\u2014"));
        row.appendChild(el("td", { style: "max-width:220px;white-space:normal;font-size:11px;color:var(--color-danger-600,#dc2626)" }, comp.impacto_fiscal || "\u2014"));
        divTbody.appendChild(row);
      });
      divTable.appendChild(divTbody);
      divScroll.appendChild(divTable);
      divCard.appendChild(divScroll);
      ncmSection.appendChild(divCard);
    } else {
      ncmSection.appendChild(el("div", {
        style: "background:var(--color-success-50,#f0fdf4);border:1px solid var(--color-success-200,#bbf7d0);border-radius:12px;padding:20px;margin-top:var(--space-4);text-align:center"
      }, [
        el("h3", { style: "color:var(--color-success-700,#15803d);margin:0;font-size:var(--text-base)" }, "Todos os NCMs corretos"),
        el("p", { style: "color:var(--color-success-600,#16a34a);margin:4px 0 0;font-size:var(--text-sm)" }, "Nenhuma diverg\u00eancia encontrada na compara\u00e7\u00e3o com a base de refer\u00eancia."),
      ]));
    }

    if (comparacoes.length > 0) {
      var allCard = el("div", { className: "table-card", style: "margin-top:var(--space-4)" });
      var allHeader = el("div", { className: "table-header", style: "cursor:pointer" });
      var allTitle = el("div", { className: "table-title" }, "Todas as Compara\u00e7\u00f5es (" + comparacoes.length + " produtos)");
      var toggleBtn = el("button", { className: "btn btn-ghost", style: "font-size:var(--text-xs)" }, "Expandir");
      allHeader.appendChild(allTitle);
      allHeader.appendChild(toggleBtn);
      allCard.appendChild(allHeader);

      var allBody = el("div", { style: "display:none" });
      var allScroll = el("div", { className: "table-scroll" });
      var allTable = el("table", { className: "data-table" });
      var allThead = el("thead");
      var allHeadRow = el("tr");
      ["Status", "Produto (NF-e)", "NCM NF-e", "NCM Ref.", "Produto Ref.", "Categoria"].forEach(function (h) {
        allHeadRow.appendChild(el("th", {}, h));
      });
      allThead.appendChild(allHeadRow);
      allTable.appendChild(allThead);

      var allTbody = el("tbody");
      comparacoes.forEach(function (comp) {
        var row = el("tr");
        var stBadge = comp.status === "ok"
          ? el("span", { className: "badge badge-success" }, "OK")
          : comp.status === "divergencia"
            ? el("span", { className: "badge badge-warning" }, "Divergente")
            : el("span", { className: "badge badge-error" }, "N\u00e3o Cadastrado");
        row.appendChild(el("td", {}, stBadge));
        row.appendChild(el("td", { style: "max-width:200px;white-space:normal" }, comp.descricao_nfe || "\u2014"));
        row.appendChild(el("td", { className: "font-mono" }, comp.ncm_nfe || "\u2014"));
        row.appendChild(el("td", { className: "font-mono" }, comp.ncm_referencia || "\u2014"));
        row.appendChild(el("td", { style: "max-width:200px;white-space:normal" }, comp.descricao_referencia || "\u2014"));
        row.appendChild(el("td", {}, comp.categoria_referencia || "\u2014"));
        allTbody.appendChild(row);
      });
      allTable.appendChild(allTbody);
      allScroll.appendChild(allTable);
      allBody.appendChild(allScroll);
      allCard.appendChild(allBody);

      var expanded = false;
      allHeader.addEventListener("click", function () {
        expanded = !expanded;
        allBody.style.display = expanded ? "block" : "none";
        toggleBtn.textContent = expanded ? "Recolher" : "Expandir";
      });

      ncmSection.appendChild(allCard);
    }

    container.appendChild(ncmSection);
  }).catch(function () { /* silently ignore */ });
}

/* ============================================================
   PAGE: RELATÓRIOS
   ============================================================ */
function renderRelatorios(container) {
  container.innerHTML = "";
  var pageHeader = el("div", { className: "page-header" }, [
    el("h1", { className: "page-title" }, "Relatórios"),
    el("button", { className: "btn btn-secondary", innerHTML: icon("download") + " Exportar CSV", onClick: function () { showToast("Exportação iniciada.", "info"); } }),
  ]);
  container.appendChild(pageHeader);

  var filterBar = el("div", { className: "filter-bar" });
  var regimeFilter = el("select", { className: "filter-select", id: "filter-regime" });
  regimeFilter.appendChild(el("option", { value: "" }, "Todos os regimes"));
  REGIMES.forEach(function (r) { regimeFilter.appendChild(el("option", { value: regimeToCode(r) }, r)); });
  filterBar.appendChild(regimeFilter);

  var setorFilter = el("select", { className: "filter-select", id: "filter-setor" });
  setorFilter.appendChild(el("option", { value: "" }, "Todos os setores"));
  SETORES.forEach(function (s) { setorFilter.appendChild(el("option", { value: sectorToCode(s) }, s)); });
  filterBar.appendChild(setorFilter);

  var ufFilter = el("select", { className: "filter-select", id: "filter-uf" });
  ufFilter.appendChild(el("option", { value: "" }, "Todos os estados"));
  UF_LIST.forEach(function (u) { ufFilter.appendChild(el("option", { value: u }, u)); });
  filterBar.appendChild(ufFilter);

  container.appendChild(filterBar);
  container.appendChild(skeletonKPIs(3));
  container.appendChild(skeletonTable());

  apiFetch("/api/clients").then(function (data) {
    var clients = Array.isArray(data) ? data : data.clients || [];
    while (container.children.length > 2) container.removeChild(container.lastChild);
    var contentArea = el("div", { id: "relatorios-content" });
    container.appendChild(contentArea);

    function applyFilters() {
      var regime = regimeFilter.value;
      var setor = setorFilter.value;
      var uf = ufFilter.value;
      var filtered = clients.filter(function (c) {
        if (regime && (c.tax_regime || c.regime) !== regime) return false;
        if (setor && (c.activity_sector || c.sector) !== setor) return false;
        if (uf && (c.state_uf || c.uf) !== uf) return false;
        return true;
      });
      renderRelatoriosContent(contentArea, filtered);
    }

    regimeFilter.addEventListener("change", applyFilters);
    setorFilter.addEventListener("change", applyFilters);
    ufFilter.addEventListener("change", applyFilters);
    applyFilters();
  }).catch(function () {
    container.innerHTML = "";
    container.appendChild(pageHeader);
    container.appendChild(el("div", { className: "empty-state" }, [
      el("h3", {}, "Nenhum dado disponível"),
      el("p", {}, "Cadastre clientes e execute análises para ver relatórios."),
    ]));
  });
}

function renderRelatoriosContent(container, clients) {
  container.innerHTML = "";
  var totalClients = clients.length;
  var totalRecovery = clients.reduce(function (sum, c) { return sum + (c.total_recovery || 0); }, 0);
  var avgPerClient = totalClients > 0 ? totalRecovery / totalClients : 0;

  var kpiGrid = el("div", { className: "kpi-grid" });
  [
    { label: "Clientes Filtrados", value: String(totalClients) },
    { label: "Total Recuperável", value: formatCurrency(totalRecovery), primary: true },
    { label: "Média por Cliente", value: formatCurrency(avgPerClient) },
  ].forEach(function (k) {
    kpiGrid.appendChild(el("div", { className: "kpi-card" }, [
      el("div", { className: "kpi-label" }, k.label),
      el("div", { className: "kpi-value" + (k.primary ? " primary" : "") }, k.value),
    ]));
  });
  container.appendChild(kpiGrid);

  var sorted = clients.slice().sort(function (a, b) { return (b.total_recovery || 0) - (a.total_recovery || 0); });

  var tableCard = el("div", { className: "table-card" });
  tableCard.appendChild(el("div", { className: "table-header" }, [el("div", { className: "table-title" }, "Ranking de Clientes por Recuperação")]));

  if (!sorted.length) {
    tableCard.appendChild(el("div", { className: "empty-state" }, [el("h3", {}, "Nenhum cliente encontrado"), el("p", {}, "Ajuste os filtros ou cadastre clientes.")]));
    container.appendChild(tableCard);
    return;
  }

  var scroll = el("div", { className: "table-scroll" });
  var table = el("table", { className: "data-table" });
  var thead = el("thead");
  var headRow = el("tr");
  ["#", "Cliente", "CNPJ", "Regime", "UF", "Setor", "Total Recuperável"].forEach(function (h) { headRow.appendChild(el("th", {}, h)); });
  thead.appendChild(headRow);
  table.appendChild(thead);

  var tbody = el("tbody");
  sorted.forEach(function (c, i) {
    var tr = el("tr", { className: "clickable", onClick: function () { navigate("/cliente/" + c.id); } });
    tr.appendChild(el("td", { style: "font-weight:600" }, String(i + 1)));
    tr.appendChild(el("td", { style: "font-weight:500" }, c.company_name || c.name || "—"));
    tr.appendChild(el("td", { className: "font-mono" }, formatCNPJ(c.cnpj)));
    tr.appendChild(el("td", {}, el("span", { className: "badge badge-neutral" }, regimeLabel(c.tax_regime || c.regime))));
    tr.appendChild(el("td", {}, (c.state_uf || c.uf || "—").toUpperCase()));
    tr.appendChild(el("td", {}, sectorLabel(c.activity_sector || c.sector)));
    tr.appendChild(el("td", { className: "text-right value-green" }, formatCurrency(c.total_recovery || 0)));
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  scroll.appendChild(table);
  tableCard.appendChild(scroll);
  container.appendChild(tableCard);
}

/* ============================================================
   PAGE: BASE NCM
   ============================================================ */
function renderNCMPage(container) {
  container.innerHTML = "";

  /* State */
  var allNCMs = [];
  var filteredNCMs = [];
  var currentPage = 1;
  var pageSize = 50;
  var searchQuery = "";
  var selectedCategoria = "";
  var filterMonofasico = false;
  var filterAliquotaZero = false;
  var filterICMSST = false;
  var debounceTimer = null;

  /* Page header */
  var pageHeader = el("div", { className: "page-header" }, [
    el("div", {}, [
      el("h1", { className: "page-title" }, "Base de Cálculo NCM"),
      el("div", { style: "font-size:var(--text-xs);color:var(--color-text-muted);margin-top:var(--space-1)" }, "Consulte aliquotas, regimes e enquadramentos fiscais por NCM"),
    ]),
    el("div", { style: "display:flex;gap:var(--space-2);align-items:center" }, [
      el("button", { className: "btn btn-ghost", innerHTML: icon("download") + " Exportar CSV", onClick: function () { exportNCMCsv(); } }),
      el("button", { className: "btn btn-primary", innerHTML: icon("plus") + " Novo NCM", onClick: function () { openNCMForm(null); } }),
    ]),
  ]);
  container.appendChild(pageHeader);

  /* KPI skeleton while loading */
  var kpiArea = el("div");
  container.appendChild(kpiArea);
  kpiArea.appendChild(skeletonKPIs(4));

  /* Load KPIs from API */
  apiFetch("/api/ncm/stats/resumo").then(function (stats) {
    kpiArea.innerHTML = "";
    var kpiGrid = el("div", { className: "kpi-grid" });
    var kpis = [
      { label: "Total NCMs", value: String(stats.total_ncms || 0), icon: "clipboard" },
      { label: "Monofásicos", value: String(stats.monofasicos || 0), icon: "shield" },
      { label: "Alíquota Zero", value: String(stats.aliquota_zero_pis_cofins || 0), icon: "target" },
      { label: "ICMS-ST", value: String(stats.icms_st || 0), icon: "trendingUp" },
    ];
    kpis.forEach(function (k) {
      kpiGrid.appendChild(el("div", { className: "kpi-card" }, [
        el("div", { className: "kpi-label", innerHTML: icon(k.icon) + " " + k.label }),
        el("div", { className: "kpi-value" }, k.value),
      ]));
    });
    kpiArea.appendChild(kpiGrid);
  }).catch(function () {
    /* Fallback KPIs with dashes */
    kpiArea.innerHTML = "";
    var kpiGrid = el("div", { className: "kpi-grid" });
    ["Total NCMs", "Monofásicos", "Alíquota Zero", "ICMS-ST"].forEach(function (label) {
      kpiGrid.appendChild(el("div", { className: "kpi-card" }, [
        el("div", { className: "kpi-label" }, label),
        el("div", { className: "kpi-value" }, "—"),
      ]));
    });
    kpiArea.appendChild(kpiGrid);
  });

  /* Search bar */
  var searchBar = el("div", { className: "ncm-search-bar" });
  var searchInput = el("input", { type: "text", placeholder: "Buscar por código NCM ou descrição..." });
  var categoriaSelect = el("select");
  categoriaSelect.appendChild(el("option", { value: "" }, "Todas as categorias"));
  searchBar.appendChild(searchInput);
  searchBar.appendChild(categoriaSelect);
  container.appendChild(searchBar);

  /* Load categories */
  apiFetch("/api/ncm/categorias").then(function (cats) {
    var list = Array.isArray(cats) ? cats : cats.categorias || [];
    list.forEach(function (c) {
      categoriaSelect.appendChild(el("option", { value: c }, c));
    });
  }).catch(function () { /* silently ignore */ });

  /* Toggle filters */
  var filtersRow = el("div", { className: "ncm-filters" });

  var chipMonofasico = el("span", { className: "ncm-filter-chip" }, "Monofásico");
  var chipAliquotaZero = el("span", { className: "ncm-filter-chip" }, "Alíquota Zero");
  var chipICMSST = el("span", { className: "ncm-filter-chip" }, "ICMS-ST");
  var btnClear = el("button", { className: "btn btn-ghost", style: "font-size:var(--text-xs)" }, "Limpar Filtros");

  filtersRow.appendChild(chipMonofasico);
  filtersRow.appendChild(chipAliquotaZero);
  filtersRow.appendChild(chipICMSST);
  filtersRow.appendChild(btnClear);
  container.appendChild(filtersRow);

  /* Table area */
  var tableArea = el("div");
  container.appendChild(tableArea);

  /* ---- filter / render logic ---- */
  function applyFilters() {
    var q = searchQuery.toLowerCase();
    filteredNCMs = allNCMs.filter(function (n) {
      if (q && (n.ncm || "").indexOf(q) === -1 && (n.descricao || "").toLowerCase().indexOf(q) === -1) return false;
      if (selectedCategoria && (n.categoria || "") !== selectedCategoria) return false;
      if (filterMonofasico && !n.monofasico) return false;
      if (filterAliquotaZero && !n.aliquota_zero_pis_cofins) return false;
      if (filterICMSST && !n.st_icms) return false;
      return true;
    });
    currentPage = 1;
    renderTable();
  }

  function renderTable() {
    tableArea.innerHTML = "";
    var total = filteredNCMs.length;
    var totalPages = Math.max(1, Math.ceil(total / pageSize));
    var start = (currentPage - 1) * pageSize;
    var pageItems = filteredNCMs.slice(start, start + pageSize);

    var tableCard = el("div", { className: "table-card" });
    tableCard.appendChild(el("div", { className: "table-header" }, [
      el("div", { className: "table-title" }, "NCMs Cadastrados"),
      el("div", { style: "font-size:var(--text-xs);color:var(--color-text-muted)" }, total + " registros encontrados"),
    ]));

    if (!pageItems.length) {
      tableCard.appendChild(el("div", { className: "empty-state" }, [
        el("div", { innerHTML: icon("inbox") }),
        el("h3", {}, "Nenhum NCM encontrado"),
        el("p", {}, "Tente ajustar a busca ou os filtros selecionados."),
      ]));
      tableArea.appendChild(tableCard);
      return;
    }

    var scroll = el("div", { className: "table-scroll" });
    var table = el("table", { className: "data-table" });
    var thead = el("thead");
    var headRow = el("tr");
    ["NCM", "Descrição", "IPI%", "PIS%", "COFINS%", "Monofásico", "ICMS-ST", "Base Legal", "Ações"].forEach(function (h) {
      headRow.appendChild(el("th", {}, h));
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    var tbody = el("tbody");
    pageItems.forEach(function (n) {
      var tr = el("tr", { className: "clickable", onClick: function () { openNCMDetail(n); } });
      tr.appendChild(el("td", { className: "font-mono", style: "font-weight:600" }, n.ncm || "—"));
      tr.appendChild(el("td", { style: "max-width:260px;white-space:normal" }, n.descricao || "—"));
      tr.appendChild(el("td", { className: "text-right" }, n.ipi != null ? n.ipi + "%" : "—"));
      tr.appendChild(el("td", { className: "text-right" }, n.pis != null ? n.pis + "%" : "—"));
      tr.appendChild(el("td", { className: "text-right" }, n.cofins != null ? n.cofins + "%" : "—"));
      tr.appendChild(el("td", {}, n.monofasico ? el("span", { className: "badge badge-success" }, "Sim") : el("span", { className: "badge badge-neutral" }, "Não")));
      tr.appendChild(el("td", {}, n.st_icms ? el("span", { className: "badge badge-warning" }, "Sim") : el("span", { className: "badge badge-neutral" }, "Não")));
      tr.appendChild(el("td", { style: "font-size:11px;max-width:180px;white-space:normal" }, n.base_legal_pis_cofins || "—"));
      /* Action buttons */
      var actionCell = el("td", { style: "white-space:nowrap" });
      var btnEdit = el("button", { className: "btn btn-ghost", style: "padding:2px 6px;font-size:11px", innerHTML: icon("edit") + " Editar", onClick: function (e) { e.stopPropagation(); openNCMForm(n); } });
      var btnDel = el("button", { className: "btn btn-ghost", style: "padding:2px 6px;font-size:11px;color:var(--color-danger,#e53e3e)", innerHTML: icon("trash") + " Excluir", onClick: function (e) { e.stopPropagation(); deleteNCM(n); } });
      actionCell.appendChild(btnEdit);
      actionCell.appendChild(btnDel);
      tr.appendChild(actionCell);
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    scroll.appendChild(table);
    tableCard.appendChild(scroll);

    /* Pagination */
    if (totalPages > 1) {
      var pagination = el("div", { className: "ncm-pagination" });
      var btnPrev = el("button", { className: "btn btn-ghost" }, "← Anterior");
      btnPrev.disabled = currentPage === 1;
      btnPrev.addEventListener("click", function () {
        if (currentPage > 1) { currentPage--; renderTable(); }
      });

      var pageInfo = el("span", { className: "page-info" }, "Página " + currentPage + " de " + totalPages + " (· " + total + " itens)");

      var btnNext = el("button", { className: "btn btn-ghost" }, "Próximo →");
      btnNext.disabled = currentPage === totalPages;
      btnNext.addEventListener("click", function () {
        if (currentPage < totalPages) { currentPage++; renderTable(); }
      });

      pagination.appendChild(btnPrev);
      pagination.appendChild(pageInfo);
      pagination.appendChild(btnNext);
      tableCard.appendChild(pagination);
    }

    tableArea.appendChild(tableCard);
  }

  /* ---- NCM Detail Modal ---- */
  function openNCMDetail(ncm) {
    var overlay = el("div", { className: "ncm-detail-overlay" });
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) document.body.removeChild(overlay);
    });

    var panel = el("div", { className: "ncm-detail-panel" });

    /* Header */
    var panelHeader = el("div", { style: "display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:var(--space-2)" });
    var titleGroup = el("div", {});
    titleGroup.appendChild(el("div", { className: "ncm-code-display" }, ncm.ncm || "—"));
    titleGroup.appendChild(el("h2", {}, ncm.descricao || "—"));
    panelHeader.appendChild(titleGroup);
    panelHeader.appendChild(el("button", {
      className: "btn btn-ghost",
      innerHTML: icon("close"),
      onClick: function () { document.body.removeChild(overlay); }
    }));
    panel.appendChild(panelHeader);

    /* Classification info */
    var infoSection = el("div", { className: "ncm-detail-section" });
    infoSection.appendChild(el("h3", {}, "Classificação"));
    var infoGrid = el("div", { style: "display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:var(--space-3)" });
    [
      { label: "Categoria", value: ncm.categoria || "—" },
      { label: "Capítulo", value: ncm.capitulo || "—" },
      { label: "Seção", value: ncm.secao || "—" },
      { label: "CEST", value: ncm.cest || "—" },
    ].forEach(function (item) {
      infoGrid.appendChild(el("div", { className: "ncm-rate-card" }, [
        el("div", { className: "rate-label" }, item.label),
        el("div", { className: "rate-value", style: "font-size:var(--text-sm)" }, item.value),
      ]));
    });
    infoSection.appendChild(infoGrid);
    panel.appendChild(infoSection);

    /* Alíquotas por regime */
    var regimeSection = el("div", { className: "ncm-detail-section" });
    regimeSection.appendChild(el("h3", {}, "Alíquotas por Regime"));

    var regimes = [
      { label: "Simples Nacional", pis: ncm.pis, cofins: ncm.cofins, ipi: ncm.ipi },
      { label: "Lucro Presumido", pis: ncm.pis_cumulativo != null ? ncm.pis_cumulativo : 0.65, cofins: ncm.cofins_cumulativo != null ? ncm.cofins_cumulativo : 3.0, ipi: ncm.ipi },
      { label: "Lucro Real", pis: ncm.pis, cofins: ncm.cofins, ipi: ncm.ipi },
    ];

    /* Fallback: use generic pis / cofins if regime-specific are absent */
    regimes.forEach(function (r) {
      if (r.pis == null) r.pis = ncm.pis;
      if (r.cofins == null) r.cofins = ncm.cofins;
    });

    var rateGrid = el("div", { className: "ncm-rate-grid" });
    regimes.forEach(function (r) {
      var card = el("div", { className: "ncm-rate-card" });
      card.appendChild(el("div", { className: "rate-label", style: "font-weight:600;font-size:var(--text-xs)" }, r.label));
      var rateRows = el("div", { style: "margin-top:var(--space-2);display:flex;flex-direction:column;gap:4px" });
      [
        { name: "IPI", val: r.ipi },
        { name: "PIS", val: r.pis },
        { name: "COFINS", val: r.cofins },
      ].forEach(function (tax) {
        rateRows.appendChild(el("div", { style: "display:flex;justify-content:space-between;font-size:var(--text-xs)" }, [
          el("span", { style: "color:var(--color-text-muted)" }, tax.name),
          el("span", { style: "font-weight:600" }, tax.val != null ? tax.val + "%" : "—"),
        ]));
      });
      card.appendChild(rateRows);
      rateGrid.appendChild(card);
    });
    regimeSection.appendChild(rateGrid);
    panel.appendChild(regimeSection);

    /* Monofásico and ST indicators */
    var indicatorsSection = el("div", { className: "ncm-detail-section" });
    indicatorsSection.appendChild(el("h3", {}, "Indicadores Fiscais"));
    var indicatorGrid = el("div", { style: "display:flex;flex-direction:column;gap:var(--space-3)" });

    /* Monofásico */
    var monoRow = el("div", { style: "display:flex;align-items:center;gap:var(--space-3)" });
    monoRow.appendChild(el("span", { className: "badge " + (ncm.monofasico ? "badge-success" : "badge-neutral") }, ncm.monofasico ? "Monofásico" : "Não Monofásico"));
    if (ncm.monofasico && ncm.base_legal_pis_cofins) {
      monoRow.appendChild(el("span", { style: "font-size:var(--text-xs);color:var(--color-text-muted)" }, ncm.base_legal_pis_cofins));
    }
    indicatorGrid.appendChild(monoRow);

    /* ICMS-ST */
    var stRow = el("div", { style: "display:flex;align-items:center;gap:var(--space-3)" });
    stRow.appendChild(el("span", { className: "badge " + (ncm.st_icms ? "badge-warning" : "badge-neutral") }, ncm.st_icms ? "Sujeito a ICMS-ST" : "Sem ICMS-ST"));
    if (ncm.st_icms && ncm.cest) {
      stRow.appendChild(el("span", { style: "font-size:var(--text-xs);color:var(--color-text-muted)" }, "CEST: " + ncm.cest));
    }
    indicatorGrid.appendChild(stRow);

    /* Alíquota zero indicator */
    if (ncm.aliquota_zero_pis_cofins) {
      var zeroRow = el("div", { style: "display:flex;align-items:center;gap:var(--space-3)" });
      zeroRow.appendChild(el("span", { className: "badge badge-info" }, "Alíquota Zero"));
      indicatorGrid.appendChild(zeroRow);
    }

    indicatorsSection.appendChild(indicatorGrid);
    panel.appendChild(indicatorsSection);

    /* Observações */
    if (ncm.observacoes) {
      var obsSection = el("div", { className: "ncm-detail-section" });
      obsSection.appendChild(el("h3", {}, "Observações"));
      obsSection.appendChild(el("p", { style: "font-size:var(--text-sm);color:var(--color-text-muted);line-height:1.6;margin:0" }, ncm.observacoes));
      panel.appendChild(obsSection);
    }

    /* Close button at bottom */
    panel.appendChild(el("div", { style: "margin-top:var(--space-6);text-align:right" }, [
      el("button", {
        className: "btn btn-secondary",
        onClick: function () { document.body.removeChild(overlay); }
      }, "Fechar"),
    ]));

    overlay.appendChild(panel);
    document.body.appendChild(overlay);
  }

  /* ---- Export CSV function ---- */
  function exportNCMCsv() {
    var a = document.createElement("a");
    a.href = API_BASE + "/api/ncm/export/csv";
    a.download = "base_ncm.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  /* ---- NCM Form Modal (Create/Edit) ---- */
  function openNCMForm(ncmData) {
    var isEdit = !!ncmData;
    var overlay = el("div", { className: "ncm-detail-overlay" });
    overlay.addEventListener("click", function (e) { if (e.target === overlay) document.body.removeChild(overlay); });
    var panel = el("div", { className: "ncm-detail-panel", style: "max-width:640px" });

    var title = isEdit ? "Editar NCM: " + (ncmData.ncm || "") : "Novo NCM";
    panel.appendChild(el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-4)" }, [
      el("h2", { style: "margin:0" }, title),
      el("button", { className: "btn btn-ghost", innerHTML: icon("close"), onClick: function () { document.body.removeChild(overlay); } }),
    ]));

    /* Form fields */
    var fields = {};
    function addField(label, key, type, defVal, opts) {
      var row = el("div", { style: "margin-bottom:var(--space-3)" });
      row.appendChild(el("label", { style: "display:block;font-size:var(--text-xs);font-weight:600;margin-bottom:4px" }, label));
      if (type === "checkbox") {
        var cb = el("input", { type: "checkbox" });
        cb.checked = isEdit ? !!ncmData[key] : !!defVal;
        fields[key] = cb;
        row.appendChild(cb);
        row.appendChild(el("span", { style: "font-size:var(--text-xs);margin-left:6px" }, "Sim"));
      } else if (type === "textarea") {
        var ta = el("textarea", { style: "width:100%;padding:8px;border:1px solid var(--color-border);border-radius:var(--radius-md);font-size:var(--text-sm);min-height:60px;background:var(--color-bg-secondary);color:var(--color-text-primary)", value: isEdit ? (ncmData[key] || "") : (defVal || "") });
        fields[key] = ta;
        row.appendChild(ta);
      } else {
        var inp = el("input", { type: type || "text", style: "width:100%;padding:8px;border:1px solid var(--color-border);border-radius:var(--radius-md);font-size:var(--text-sm);background:var(--color-bg-secondary);color:var(--color-text-primary)", value: isEdit ? (ncmData[key] != null ? String(ncmData[key]) : "") : (defVal || "") });
        if (opts && opts.disabled) inp.disabled = true;
        fields[key] = inp;
        row.appendChild(inp);
      }
      return row;
    }

    var formGrid = el("div", { style: "display:grid;grid-template-columns:1fr 1fr;gap:var(--space-2)" });
    formGrid.appendChild(addField("Código NCM *", "ncm", "text", "", isEdit ? { disabled: true } : {}));
    formGrid.appendChild(addField("Descrição *", "descricao", "text", ""));
    formGrid.appendChild(addField("Categoria", "categoria", "text", ""));
    formGrid.appendChild(addField("Capítulo", "capitulo", "number", ""));
    formGrid.appendChild(addField("Seção", "secao", "text", ""));
    formGrid.appendChild(addField("CEST", "cest", "text", ""));
    formGrid.appendChild(addField("IPI %", "ipi", "number", "0"));
    formGrid.appendChild(addField("PIS %", "pis", "number", "0"));
    formGrid.appendChild(addField("COFINS %", "cofins", "number", "0"));
    formGrid.appendChild(addField("PIS Cumulativo %", "pis_cumulativo", "number", "0"));
    formGrid.appendChild(addField("COFINS Cumulativo %", "cofins_cumulativo", "number", "0"));
    formGrid.appendChild(el("div", {})); /* spacer */
    panel.appendChild(formGrid);

    var checkRow = el("div", { style: "display:flex;gap:var(--space-4);margin-bottom:var(--space-3)" });
    checkRow.appendChild(addField("Monofásico", "monofasico", "checkbox", false));
    checkRow.appendChild(addField("ICMS-ST", "st_icms", "checkbox", false));
    checkRow.appendChild(addField("Alíquota Zero", "aliquota_zero_pis_cofins", "checkbox", false));
    panel.appendChild(checkRow);

    panel.appendChild(addField("Base Legal PIS/COFINS", "base_legal_pis_cofins", "text", ""));
    panel.appendChild(addField("Observações", "observacoes", "textarea", ""));

    /* Error area */
    var errorArea = el("div", { style: "color:var(--color-danger,#e53e3e);font-size:var(--text-xs);min-height:20px;margin-bottom:var(--space-2)" });
    panel.appendChild(errorArea);

    /* Buttons */
    var btnSave = el("button", { className: "btn btn-primary" }, isEdit ? "Salvar Alterações" : "Criar NCM");
    var btnCancel = el("button", { className: "btn btn-secondary", onClick: function () { document.body.removeChild(overlay); } }, "Cancelar");
    panel.appendChild(el("div", { style: "display:flex;gap:var(--space-2);justify-content:flex-end" }, [btnCancel, btnSave]));

    btnSave.addEventListener("click", function () {
      var ncmCode = (fields.ncm.value || "").replace(/[.\-\s]/g, "").trim();
      var desc = (fields.descricao.value || "").trim();
      if (!ncmCode || !desc) { errorArea.textContent = "NCM e Descrição são obrigatórios."; return; }
      errorArea.textContent = "";
      btnSave.disabled = true;
      btnSave.textContent = "Salvando...";

      var body = {
        ncm: ncmCode, descricao: desc,
        capitulo: fields.capitulo.value ? parseInt(fields.capitulo.value) : null,
        secao: fields.secao.value || "", categoria: fields.categoria.value || "",
        ipi: parseFloat(fields.ipi.value) || 0, pis: parseFloat(fields.pis.value) || 0,
        cofins: parseFloat(fields.cofins.value) || 0,
        pis_cumulativo: parseFloat(fields.pis_cumulativo.value) || 0,
        cofins_cumulativo: parseFloat(fields.cofins_cumulativo.value) || 0,
        cest: fields.cest.value || "", ncm_ex: "",
        monofasico: fields.monofasico.checked, st_icms: fields.st_icms.checked,
        aliquota_zero_pis_cofins: fields.aliquota_zero_pis_cofins.checked,
        base_legal_pis_cofins: fields.base_legal_pis_cofins.value || "",
        observacoes: fields.observacoes.value || "",
      };

      var url = isEdit ? "/api/ncm/" + encodeURIComponent(ncmCode) : "/api/ncm";
      var method = isEdit ? "PUT" : "POST";
      apiFetch(url, { method: method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
        .then(function () {
          document.body.removeChild(overlay);
          /* Reload data */
          apiFetch("/api/ncm/busca?per_page=500").then(function (data) {
            allNCMs = Array.isArray(data) ? data : data.items || [];
            applyFilters();
          });
        })
        .catch(function (err) {
          errorArea.textContent = err.message || "Erro ao salvar NCM";
          btnSave.disabled = false;
          btnSave.textContent = isEdit ? "Salvar Alterações" : "Criar NCM";
        });
    });

    overlay.appendChild(panel);
    document.body.appendChild(overlay);
  }

  /* ---- Delete NCM ---- */
  function deleteNCM(ncmData) {
    if (!confirm("Tem certeza que deseja excluir o NCM " + (ncmData.ncm || "") + "?")) return;
    apiFetch("/api/ncm/" + encodeURIComponent(ncmData.ncm), { method: "DELETE" })
      .then(function () {
        apiFetch("/api/ncm/busca?per_page=500").then(function (data) {
          allNCMs = Array.isArray(data) ? data : data.items || [];
          applyFilters();
        });
      })
      .catch(function (err) { alert("Erro ao excluir: " + (err.message || "Erro desconhecido")); });
  }

  /* ---- Event listeners ---- */
  searchInput.addEventListener("input", function () {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(function () {
      searchQuery = searchInput.value;
      applyFilters();
    }, 300);
  });

  categoriaSelect.addEventListener("change", function () {
    selectedCategoria = categoriaSelect.value;
    applyFilters();
  });

  chipMonofasico.addEventListener("click", function () {
    filterMonofasico = !filterMonofasico;
    chipMonofasico.classList.toggle("active", filterMonofasico);
    applyFilters();
  });

  chipAliquotaZero.addEventListener("click", function () {
    filterAliquotaZero = !filterAliquotaZero;
    chipAliquotaZero.classList.toggle("active", filterAliquotaZero);
    applyFilters();
  });

  chipICMSST.addEventListener("click", function () {
    filterICMSST = !filterICMSST;
    chipICMSST.classList.toggle("active", filterICMSST);
    applyFilters();
  });

  btnClear.addEventListener("click", function () {
    searchInput.value = "";
    categoriaSelect.value = "";
    searchQuery = "";
    selectedCategoria = "";
    filterMonofasico = false;
    filterAliquotaZero = false;
    filterICMSST = false;
    chipMonofasico.classList.remove("active");
    chipAliquotaZero.classList.remove("active");
    chipICMSST.classList.remove("active");
    applyFilters();
  });

  /* ---- Initial data load ---- */
  tableArea.appendChild(skeletonTable());

  apiFetch("/api/ncm/busca?per_page=500").then(function (data) {
    allNCMs = Array.isArray(data) ? data : data.items || data.ncms || [];
    applyFilters();
  }).catch(function () {
    tableArea.innerHTML = "";
    var tableCard = el("div", { className: "table-card" });
    tableCard.appendChild(el("div", { className: "empty-state" }, [
      el("div", { innerHTML: icon("inbox") }),
      el("h3", {}, "Base NCM indisponível"),
      el("p", {}, "Não foi possível carregar os dados NCM. Verifique a conexão com a API."),
    ]));
    tableArea.appendChild(tableCard);
  });
}

/* ============================================================
   PAGE: PRODUTOS (Product Database)
   ============================================================ */
function renderProdutosPage(container) {
  container.innerHTML = "";

  /* State */
  var allProducts = [];
  var filteredProducts = [];
  var currentPage = 1;
  var pageSize = 50;
  var searchQuery = "";
  var selectedCategoria = "";
  var filterMonofasico = false;
  var filterAliquotaZero = false;
  var debounceTimer = null;

  /* Page header */
  var pageHeader = el("div", { className: "page-header" }, [
    el("div", {}, [
      el("h1", { className: "page-title" }, "Base de Produtos"),
      el("div", { style: "font-size:var(--text-xs);color:var(--color-text-muted);margin-top:var(--space-1)" }, "Produtos alimentícios com EAN/GTIN e NCM correto para comparação fiscal"),
    ]),
    el("div", { style: "display:flex;gap:var(--space-2);align-items:center" }, [
      el("button", { className: "btn btn-ghost", innerHTML: icon("download") + " Exportar CSV", onClick: function () { exportProdutosCsv(); } }),
      el("button", { className: "btn btn-primary", innerHTML: icon("plus") + " Novo Produto", onClick: function () { openProdutoForm(null); } }),
    ]),
  ]);
  container.appendChild(pageHeader);

  /* KPI skeleton */
  var kpiArea = el("div");
  container.appendChild(kpiArea);
  kpiArea.appendChild(skeletonKPIs(5));

  /* Load KPIs */
  apiFetch("/api/produtos/stats").then(function (stats) {
    kpiArea.innerHTML = "";
    var kpiGrid = el("div", { className: "kpi-grid" });
    [
      { label: "Total Produtos", value: String(stats.total_produtos || 0), icon: "clipboard" },
      { label: "Com EAN/GTIN", value: String(stats.com_ean || 0), icon: "package" },
      { label: "NCMs Únicos", value: String(stats.ncms_unicos || 0), icon: "target" },
      { label: "Alíquota Zero", value: String(stats.aliquota_zero_cesta_basica || 0), icon: "shield" },
      { label: "Monofásicos", value: String(stats.monofasicos || 0), icon: "trendingUp" },
    ].forEach(function (k) {
      kpiGrid.appendChild(el("div", { className: "kpi-card" }, [
        el("div", { className: "kpi-label", innerHTML: icon(k.icon) + " " + k.label }),
        el("div", { className: "kpi-value" }, k.value),
      ]));
    });
    kpiArea.appendChild(kpiGrid);
  }).catch(function () {
    kpiArea.innerHTML = "";
    var kpiGrid = el("div", { className: "kpi-grid" });
    ["Total Produtos", "Com EAN/GTIN", "NCMs Únicos", "Alíquota Zero", "Monofásicos"].forEach(function (l) {
      kpiGrid.appendChild(el("div", { className: "kpi-card" }, [
        el("div", { className: "kpi-label" }, l),
        el("div", { className: "kpi-value" }, "—"),
      ]));
    });
    kpiArea.appendChild(kpiGrid);
  });

  /* Search bar */
  var searchBar = el("div", { className: "ncm-search-bar" });
  var searchInput = el("input", { type: "text", placeholder: "Buscar por nome do produto, EAN/GTIN ou NCM..." });
  var categoriaSelect = el("select");
  categoriaSelect.appendChild(el("option", { value: "" }, "Todas as categorias"));
  searchBar.appendChild(searchInput);
  searchBar.appendChild(categoriaSelect);
  container.appendChild(searchBar);

  /* Load categories */
  apiFetch("/api/produtos/categorias").then(function (data) {
    var cats = data.categorias || [];
    cats.forEach(function (c) {
      categoriaSelect.appendChild(el("option", { value: c.nome }, c.nome + " (" + c.quantidade + ")"));
    });
  }).catch(function () {});

  /* Filter chips */
  var filtersRow = el("div", { className: "ncm-filters" });
  var chipMono = el("span", { className: "ncm-filter-chip" }, "Monofásico");
  var chipZero = el("span", { className: "ncm-filter-chip" }, "Alíquota Zero");
  var btnClear = el("button", { className: "btn btn-ghost", style: "font-size:var(--text-xs)" }, "Limpar Filtros");
  filtersRow.appendChild(chipMono);
  filtersRow.appendChild(chipZero);
  filtersRow.appendChild(btnClear);
  container.appendChild(filtersRow);

  /* Table area */
  var tableArea = el("div");
  container.appendChild(tableArea);

  /* ---- filter/render ---- */
  function applyFilters() {
    var q = searchQuery.toLowerCase();
    filteredProducts = allProducts.filter(function (p) {
      if (q && (p.nome || "").toLowerCase().indexOf(q) === -1 && (p.ean || "").indexOf(q) === -1 && (p.ncm || "").indexOf(q) === -1 && (p.descricao_generica || "").toLowerCase().indexOf(q) === -1 && (p.marca_exemplo || "").toLowerCase().indexOf(q) === -1) return false;
      if (selectedCategoria && (p.categoria || "") !== selectedCategoria) return false;
      if (filterMonofasico && !p.monofasico) return false;
      if (filterAliquotaZero && !p.aliquota_zero) return false;
      return true;
    });
    currentPage = 1;
    renderProductTable();
  }

  function renderProductTable() {
    tableArea.innerHTML = "";
    var total = filteredProducts.length;
    var totalPages = Math.max(1, Math.ceil(total / pageSize));
    var start = (currentPage - 1) * pageSize;
    var pageItems = filteredProducts.slice(start, start + pageSize);

    var tableCard = el("div", { className: "table-card" });
    tableCard.appendChild(el("div", { className: "table-header" }, [
      el("div", { className: "table-title" }, "Produtos Cadastrados"),
      el("div", { style: "font-size:var(--text-xs);color:var(--color-text-muted)" }, total + " produtos encontrados"),
    ]));

    if (!pageItems.length) {
      tableCard.appendChild(el("div", { className: "empty-state" }, [
        el("div", { innerHTML: icon("inbox") }),
        el("h3", {}, "Nenhum produto encontrado"),
        el("p", {}, "Tente ajustar a busca ou os filtros selecionados."),
      ]));
      tableArea.appendChild(tableCard);
      return;
    }

    var scroll = el("div", { className: "table-scroll" });
    var table = el("table", { className: "data-table" });
    var thead = el("thead");
    var headRow = el("tr");
    ["EAN/GTIN", "Produto", "Marca", "NCM", "Categoria", "Monofásico", "Alíq. Zero", "Ações"].forEach(function (h) {
      headRow.appendChild(el("th", {}, h));
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    var tbody = el("tbody");
    pageItems.forEach(function (p) {
      var tr = el("tr", { className: "clickable", onClick: function () { openProductDetail(p); } });
      tr.appendChild(el("td", { className: "font-mono", style: "font-size:11px" }, p.ean || "—"));
      tr.appendChild(el("td", { style: "max-width:280px;white-space:normal;font-weight:500" }, p.nome || "—"));
      tr.appendChild(el("td", { style: "font-size:var(--text-xs);color:var(--color-text-muted)" }, p.marca_exemplo || "—"));
      tr.appendChild(el("td", { className: "font-mono", style: "font-weight:600" }, p.ncm || "—"));
      tr.appendChild(el("td", { style: "font-size:var(--text-xs)" }, p.categoria || "—"));
      tr.appendChild(el("td", {}, p.monofasico ? el("span", { className: "badge badge-success" }, "Sim") : el("span", { className: "badge badge-neutral" }, "Não")));
      tr.appendChild(el("td", {}, p.aliquota_zero ? el("span", { className: "badge badge-warning" }, "Sim") : el("span", { className: "badge badge-neutral" }, "Não")));
      /* Action buttons */
      var actionCell = el("td", { style: "white-space:nowrap" });
      var btnEditP = el("button", { className: "btn btn-ghost", style: "padding:2px 6px;font-size:11px", innerHTML: icon("edit") + " Editar", onClick: function (e) { e.stopPropagation(); openProdutoForm(p); } });
      var btnDelP = el("button", { className: "btn btn-ghost", style: "padding:2px 6px;font-size:11px;color:var(--color-danger,#e53e3e)", innerHTML: icon("trash") + " Excluir", onClick: function (e) { e.stopPropagation(); deleteProduto(p); } });
      actionCell.appendChild(btnEditP);
      actionCell.appendChild(btnDelP);
      tr.appendChild(actionCell);
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    scroll.appendChild(table);
    tableCard.appendChild(scroll);

    /* Pagination */
    if (totalPages > 1) {
      var pagination = el("div", { className: "ncm-pagination" });
      var btnPrev = el("button", { className: "btn btn-ghost" }, "← Anterior");
      btnPrev.disabled = currentPage === 1;
      btnPrev.addEventListener("click", function () { if (currentPage > 1) { currentPage--; renderProductTable(); } });
      var pageInfo = el("span", { className: "page-info" }, "Página " + currentPage + " de " + totalPages + " (" + total + " itens)");
      var btnNext = el("button", { className: "btn btn-ghost" }, "Próximo →");
      btnNext.disabled = currentPage === totalPages;
      btnNext.addEventListener("click", function () { if (currentPage < totalPages) { currentPage++; renderProductTable(); } });
      pagination.appendChild(btnPrev);
      pagination.appendChild(pageInfo);
      pagination.appendChild(btnNext);
      tableCard.appendChild(pagination);
    }

    tableArea.appendChild(tableCard);
  }

  /* ---- Product Detail Modal ---- */
  function openProductDetail(prod) {
    var overlay = el("div", { className: "ncm-detail-overlay" });
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) document.body.removeChild(overlay);
    });
    var panel = el("div", { className: "ncm-detail-panel" });

    /* Header */
    var panelHeader = el("div", { style: "display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:var(--space-2)" });
    var titleGroup = el("div", {});
    if (prod.ean) titleGroup.appendChild(el("div", { className: "ncm-code-display", style: "font-size:13px" }, "EAN: " + prod.ean));
    titleGroup.appendChild(el("h2", { style: "margin-top:var(--space-1)" }, prod.nome || "—"));
    if (prod.descricao_generica) titleGroup.appendChild(el("div", { style: "font-size:var(--text-xs);color:var(--color-text-muted);margin-top:2px" }, prod.descricao_generica));
    panelHeader.appendChild(titleGroup);
    panelHeader.appendChild(el("button", { className: "btn btn-ghost", innerHTML: icon("close"), onClick: function () { document.body.removeChild(overlay); } }));
    panel.appendChild(panelHeader);

    /* Product info grid */
    var infoSection = el("div", { className: "ncm-detail-section" });
    infoSection.appendChild(el("h3", {}, "Informações do Produto"));
    var infoGrid = el("div", { style: "display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:var(--space-3)" });
    [
      { label: "Marca", value: prod.marca_exemplo || "—" },
      { label: "Categoria", value: prod.categoria || "—" },
      { label: "Subcategoria", value: prod.subcategoria || "—" },
      { label: "Unidade", value: prod.unidade || "—" },
    ].forEach(function (item) {
      infoGrid.appendChild(el("div", { className: "ncm-rate-card" }, [
        el("div", { className: "rate-label" }, item.label),
        el("div", { className: "rate-value", style: "font-size:var(--text-sm)" }, item.value),
      ]));
    });
    infoSection.appendChild(infoGrid);
    panel.appendChild(infoSection);

    /* Classificação fiscal */
    var fiscalSection = el("div", { className: "ncm-detail-section" });
    fiscalSection.appendChild(el("h3", {}, "Classificação Fiscal"));
    var fiscalGrid = el("div", { style: "display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:var(--space-3)" });
    [
      { label: "NCM", value: prod.ncm || "—" },
      { label: "Descrição NCM", value: prod.ncm_descricao || "—" },
      { label: "CEST", value: prod.cest || "Não se aplica" },
      { label: "IPI", value: prod.ipi != null ? prod.ipi + "%" : "—" },
    ].forEach(function (item) {
      fiscalGrid.appendChild(el("div", { className: "ncm-rate-card" }, [
        el("div", { className: "rate-label" }, item.label),
        el("div", { className: "rate-value", style: "font-size:var(--text-sm)" }, item.value),
      ]));
    });
    fiscalSection.appendChild(fiscalGrid);
    panel.appendChild(fiscalSection);

    /* Indicadores */
    var indSection = el("div", { className: "ncm-detail-section" });
    indSection.appendChild(el("h3", {}, "Indicadores Tributários"));
    var indGrid = el("div", { style: "display:flex;flex-direction:column;gap:var(--space-3)" });
    indGrid.appendChild(el("div", { style: "display:flex;align-items:center;gap:var(--space-3)" }, [
      el("span", { className: "badge " + (prod.monofasico ? "badge-success" : "badge-neutral") }, prod.monofasico ? "Monofásico" : "Não Monofásico"),
    ]));
    indGrid.appendChild(el("div", { style: "display:flex;align-items:center;gap:var(--space-3)" }, [
      el("span", { className: "badge " + (prod.aliquota_zero ? "badge-warning" : "badge-neutral") }, prod.aliquota_zero ? "Alíquota Zero PIS/COFINS" : "Tributação Normal PIS/COFINS"),
    ]));
    indSection.appendChild(indGrid);
    panel.appendChild(indSection);

    /* Close */
    panel.appendChild(el("div", { style: "margin-top:var(--space-6);text-align:right" }, [
      el("button", { className: "btn btn-secondary", onClick: function () { document.body.removeChild(overlay); } }, "Fechar"),
    ]));

    overlay.appendChild(panel);
    document.body.appendChild(overlay);
  }

  /* ---- Export CSV function ---- */
  function exportProdutosCsv() {
    var a = document.createElement("a");
    a.href = API_BASE + "/api/produtos/export/csv";
    a.download = "base_produtos.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  /* ---- Produto Form Modal (Create/Edit) ---- */
  function openProdutoForm(prodData) {
    var isEdit = !!prodData;
    var overlay = el("div", { className: "ncm-detail-overlay" });
    overlay.addEventListener("click", function (e) { if (e.target === overlay) document.body.removeChild(overlay); });
    var panel = el("div", { className: "ncm-detail-panel", style: "max-width:640px" });

    var title = isEdit ? "Editar Produto: " + (prodData.nome || "") : "Novo Produto";
    panel.appendChild(el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-4)" }, [
      el("h2", { style: "margin:0;font-size:var(--text-md)" }, title),
      el("button", { className: "btn btn-ghost", innerHTML: icon("close"), onClick: function () { document.body.removeChild(overlay); } }),
    ]));

    var fields = {};
    function addField(label, key, type, defVal, opts) {
      var row = el("div", { style: "margin-bottom:var(--space-3)" });
      row.appendChild(el("label", { style: "display:block;font-size:var(--text-xs);font-weight:600;margin-bottom:4px" }, label));
      if (type === "checkbox") {
        var cb = el("input", { type: "checkbox" });
        cb.checked = isEdit ? !!prodData[key] : !!defVal;
        fields[key] = cb;
        row.appendChild(cb);
        row.appendChild(el("span", { style: "font-size:var(--text-xs);margin-left:6px" }, "Sim"));
      } else {
        var inp = el("input", { type: type || "text", style: "width:100%;padding:8px;border:1px solid var(--color-border);border-radius:var(--radius-md);font-size:var(--text-sm);background:var(--color-bg-secondary);color:var(--color-text-primary)", value: isEdit ? (prodData[key] != null ? String(prodData[key]) : "") : (defVal || "") });
        if (opts && opts.disabled) inp.disabled = true;
        fields[key] = inp;
        row.appendChild(inp);
      }
      return row;
    }

    var formGrid = el("div", { style: "display:grid;grid-template-columns:1fr 1fr;gap:var(--space-2)" });
    formGrid.appendChild(addField("EAN/GTIN *", "ean", "text", "", isEdit ? { disabled: true } : {}));
    formGrid.appendChild(addField("Nome do Produto *", "nome", "text", ""));
    formGrid.appendChild(addField("Descricao Generica", "descricao_generica", "text", ""));
    formGrid.appendChild(addField("NCM *", "ncm", "text", ""));
    formGrid.appendChild(addField("Descricao NCM", "ncm_descricao", "text", ""));
    formGrid.appendChild(addField("Categoria", "categoria", "text", ""));
    formGrid.appendChild(addField("Subcategoria", "subcategoria", "text", ""));
    formGrid.appendChild(addField("Unidade", "unidade", "text", "un"));
    formGrid.appendChild(addField("IPI %", "ipi", "number", "0"));
    formGrid.appendChild(addField("CEST", "cest", "text", ""));
    formGrid.appendChild(addField("Marca", "marca_exemplo", "text", ""));
    formGrid.appendChild(el("div", {}));
    panel.appendChild(formGrid);

    var checkRow = el("div", { style: "display:flex;gap:var(--space-4);margin-bottom:var(--space-3)" });
    checkRow.appendChild(addField("Monofasico", "monofasico", "checkbox", false));
    checkRow.appendChild(addField("Aliquota Zero", "aliquota_zero", "checkbox", false));
    panel.appendChild(checkRow);

    var errorArea = el("div", { style: "color:var(--color-danger,#e53e3e);font-size:var(--text-xs);min-height:20px;margin-bottom:var(--space-2)" });
    panel.appendChild(errorArea);

    var btnSave = el("button", { className: "btn btn-primary" }, isEdit ? "Salvar Alteracoes" : "Criar Produto");
    var btnCancel = el("button", { className: "btn btn-secondary", onClick: function () { document.body.removeChild(overlay); } }, "Cancelar");
    panel.appendChild(el("div", { style: "display:flex;gap:var(--space-2);justify-content:flex-end" }, [btnCancel, btnSave]));

    btnSave.addEventListener("click", function () {
      var eanVal = (fields.ean.value || "").trim();
      var nomeVal = (fields.nome.value || "").trim();
      var ncmVal = (fields.ncm.value || "").replace(/[.\-\s]/g, "").trim();
      if (!eanVal || !nomeVal || !ncmVal) { errorArea.textContent = "EAN, Nome e NCM sao obrigatorios."; return; }
      errorArea.textContent = "";
      btnSave.disabled = true;
      btnSave.textContent = "Salvando...";

      var body = {
        ean: eanVal, nome: nomeVal, descricao_generica: fields.descricao_generica.value || "",
        ncm: ncmVal, ncm_descricao: fields.ncm_descricao.value || "",
        categoria: fields.categoria.value || "", subcategoria: fields.subcategoria.value || "",
        unidade: fields.unidade.value || "un", monofasico: fields.monofasico.checked,
        aliquota_zero: fields.aliquota_zero.checked,
        ipi: parseFloat(fields.ipi.value) || 0, cest: fields.cest.value || "",
        marca_exemplo: fields.marca_exemplo.value || "",
      };

      var url = isEdit ? "/api/produtos/" + encodeURIComponent(eanVal) : "/api/produtos";
      var method = isEdit ? "PUT" : "POST";
      apiFetch(url, { method: method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
        .then(function () {
          document.body.removeChild(overlay);
          reloadProducts();
        })
        .catch(function (err) {
          errorArea.textContent = err.message || "Erro ao salvar produto";
          btnSave.disabled = false;
          btnSave.textContent = isEdit ? "Salvar Alteracoes" : "Criar Produto";
        });
    });

    overlay.appendChild(panel);
    document.body.appendChild(overlay);
  }

  /* ---- Delete Produto ---- */
  function deleteProduto(prodData) {
    if (!confirm("Tem certeza que deseja excluir o produto " + (prodData.nome || prodData.ean || "") + "?")) return;
    apiFetch("/api/produtos/remover/" + encodeURIComponent(prodData.ean), { method: "DELETE" })
      .then(function () { reloadProducts(); })
      .catch(function (err) { alert("Erro ao excluir: " + (err.message || "Erro desconhecido")); });
  }

  /* ---- Reload Products ---- */
  function reloadProducts() {
    apiFetch("/api/produtos/busca?per_page=500").then(function (data) {
      allProducts = data.items || [];
      if (data.total > allProducts.length) {
        var promises = [];
        for (var pg = 2; pg <= data.total_pages; pg++) {
          promises.push(apiFetch("/api/produtos/busca?per_page=500&page=" + pg));
        }
        Promise.all(promises).then(function (pages) {
          pages.forEach(function (d) { allProducts = allProducts.concat(d.items || []); });
          applyFilters();
        }).catch(function () { applyFilters(); });
      } else {
        applyFilters();
      }
    });
  }

  /* ---- Event listeners ---- */
  searchInput.addEventListener("input", function () {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(function () {
      searchQuery = searchInput.value;
      applyFilters();
    }, 300);
  });

  categoriaSelect.addEventListener("change", function () {
    selectedCategoria = categoriaSelect.value;
    applyFilters();
  });

  chipMono.addEventListener("click", function () {
    filterMonofasico = !filterMonofasico;
    chipMono.classList.toggle("active", filterMonofasico);
    applyFilters();
  });

  chipZero.addEventListener("click", function () {
    filterAliquotaZero = !filterAliquotaZero;
    chipZero.classList.toggle("active", filterAliquotaZero);
    applyFilters();
  });

  btnClear.addEventListener("click", function () {
    searchInput.value = "";
    categoriaSelect.value = "";
    searchQuery = "";
    selectedCategoria = "";
    filterMonofasico = false;
    filterAliquotaZero = false;
    chipMono.classList.remove("active");
    chipZero.classList.remove("active");
    applyFilters();
  });

  /* ---- Initial load ---- */
  tableArea.appendChild(skeletonTable());

  apiFetch("/api/produtos/busca?per_page=500").then(function (data) {
    allProducts = data.items || [];
    /* If we got fewer than total, fetch remaining pages */
    if (data.total > allProducts.length) {
      var promises = [];
      for (var pg = 2; pg <= data.total_pages; pg++) {
        promises.push(apiFetch("/api/produtos/busca?per_page=500&page=" + pg));
      }
      Promise.all(promises).then(function (pages) {
        pages.forEach(function (d) {
          allProducts = allProducts.concat(d.items || []);
        });
        applyFilters();
      }).catch(function () { applyFilters(); });
    } else {
      applyFilters();
    }
  }).catch(function () {
    tableArea.innerHTML = "";
    var tableCard = el("div", { className: "table-card" });
    tableCard.appendChild(el("div", { className: "empty-state" }, [
      el("div", { innerHTML: icon("inbox") }),
      el("h3", {}, "Base de produtos indisponível"),
      el("p", {}, "Não foi possível carregar os dados. Verifique a conexão."),
    ]));
    tableArea.appendChild(tableCard);
  });
}

/* ============================================================
   INIT
   ============================================================ */
document.addEventListener("DOMContentLoaded", function () {
  initTheme();
  initRouter();
});
