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