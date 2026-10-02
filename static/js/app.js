/* ==========================================================================
   Estaciona - Controle por ticket - Frontend JS
   Consome a API Flask (/api/...) e controla toda a interatividade da SPA.
   ========================================================================== */

const API_BASE = "/api";

let abaAtual = "patio";
let cacheVeiculosPatio = [];
let cacheConfiguracoes = {};

// ---------------------- UTILITARIOS ----------------------

function formatarMoeda(valor) {
  if (valor === null || valor === undefined) return "R$ 0,00";
  return "R$ " + Number(valor).toFixed(2).replace(".", ",");
}

// Formata datas para exibicao (dd/mm/aaaa hh:mm), convertendo ISO com fuso
// para o horario local e removendo segundos. Aceita "AAAA-MM-DD" (so data),
// ISO 8601, "DD/MM/AAAA HH:MM:SS" e retorna o valor original como fallback.
function formatarDataHora(valor) {
  if (valor === null || valor === undefined || valor === "") return "—";
  const texto = String(valor);

  if (/^\d{2}\/\d{2}\/\d{4}(\s|$)/.test(texto)) return texto.slice(0, 16);

  if (/^\d{4}-\d{2}-\d{2}$/.test(texto)) {
    const [aa, mm, dd] = texto.split("-");
    return `${dd}/${mm}/${aa}`;
  }

  const data = new Date(texto);
  if (!isNaN(data)) {
    const dd = String(data.getDate()).padStart(2, "0");
    const mm = String(data.getMonth() + 1).padStart(2, "0");
    const aa = data.getFullYear();
    const hh = String(data.getHours()).padStart(2, "0");
    const mi = String(data.getMinutes()).padStart(2, "0");
    return `${dd}/${mm}/${aa} ${hh}:${mi}`;
  }
  return texto;
}

// Converte codigos internos (ex.: "cartao_credito", "aberta") em rotulo legivel
function rotuloStatus(texto) {
  if (texto === null || texto === undefined || texto === "") return "—";
  const limpo = String(texto).replace(/_/g, " ");
  return limpo.charAt(0).toUpperCase() + limpo.slice(1);
}

function mostrarToast(mensagem, tipo = "success") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast toast-${tipo === "success" ? "success" : "error"}`;
  toast.textContent = mensagem;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

async function chamarApi(endpoint, options = {}) {
  const resposta = await fetch(API_BASE + endpoint, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const dados = await resposta.json().catch(() => ({}));
  if (!resposta.ok) {
    const erro = new Error(dados.erro || "Erro inesperado.");
    erro.payload = dados;
    throw erro;
  }
  return dados;
}

function iconeVeiculo(tipo) {
  if (tipo === "Moto") {
    return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="5.5" cy="17.5" r="2.5" stroke="currentColor" stroke-width="1.8"/><circle cx="18.5" cy="17.5" r="2.5" stroke="currentColor" stroke-width="1.8"/><path d="M8 17.5h6l3-6h2M14 11.5l-2-4H8l-1.5 3M14 17.5l-3-6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  }
  if (tipo === "Caminhonete") {
    return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 13l1-5a2 2 0 0 1 2-1.5h5V13" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><rect x="11" y="9" width="9" height="4" rx="1" stroke="currentColor" stroke-width="1.8"/><rect x="2" y="13" width="19" height="4" rx="1" stroke="currentColor" stroke-width="1.8"/><circle cx="7" cy="19" r="1.6" fill="currentColor"/><circle cx="17" cy="19" r="1.6" fill="currentColor"/></svg>`;
  }
  return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M5 11l1.5-4.5A2 2 0 0 1 8.4 5h7.2a2 2 0 0 1 1.9 1.5L19 11" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><rect x="3" y="11" width="18" height="6" rx="2" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><circle cx="7.5" cy="17" r="1.4" fill="currentColor"/><circle cx="16.5" cy="17" r="1.4" fill="currentColor"/></svg>`;
}

const ICON_CLOCK = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2"/><path d="M12 7v5l3.5 2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
const ICON_PRINT = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M6 9V3h12v6M6 18H4a1 1 0 0 1-1-1v-5a1 1 0 0 1 1-1h16a1 1 0 0 1 1 1v5a1 1 0 0 1-1 1h-2" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><rect x="6" y="14" width="12" height="7" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>`;
const ICON_EXIT = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M9 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h4M15 17l5-5-5-5M20 12H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

// ---------------------- HEADER: DATA E CONTAGEM ----------------------

function atualizarDataHeader() {
  const agora = new Date();
  const texto = agora.toLocaleDateString("pt-BR", {
    weekday: "long",
    day: "2-digit",
    month: "long",
  });
  document.getElementById("header-data").textContent = texto;
}

// ---------------------- NAVEGACAO ENTRE VIEWS ----------------------

function mostrarView(viewId) {
  // Visao Geral e sempre permitida para todos os usuarios autenticados
  if (viewId && viewId !== "view-visao-geral" && perfilUsuarioAtual && perfilUsuarioAtual !== "admin") {
    const modulo = MENU_PERMISSAO[viewId];
    if (modulo) {
      const permitido = (permissoesMatriz && permissoesMatriz[modulo] && permissoesMatriz[modulo][perfilUsuarioAtual] || []).includes("ver");
      if (!permitido) {
        mostrarToast("Você não possui permissão para acessar este módulo.", "error");
        mostrarView("view-visao-geral");
        return;
      }
    }
  }

  // Persiste a view atual para restaurar ao recarregar a pagina (F5)
  localStorage.setItem("estaciona_view", viewId);

  document.querySelectorAll(".view").forEach((view) => view.classList.remove("view-active"));
  const view = document.getElementById(viewId);
  if (view) view.classList.add("view-active");

  document.querySelectorAll(".menu-item").forEach((item) => item.classList.remove("active"));
  const menuItem = document.querySelector(`.menu-item[data-view="${viewId}"]`);
  if (menuItem) menuItem.classList.add("active");

  // Abre o grupo de menu pai quando um subitem e selecionado
  if (menuItem) {
    const grupo = menuItem.closest(".menu-group");
    if (grupo) grupo.classList.add("open");
  }

  // Fecha sidebar em mobile apos selecao
  const sidebar = document.getElementById("app-sidebar");
  if (sidebar) sidebar.classList.remove("open");
  const sidebarBackdrop = document.getElementById("sidebar-backdrop");
  if (sidebarBackdrop) sidebarBackdrop.classList.remove("open");

  if (viewId === "view-visao-geral") {
    carregarDashboard();
    if (abaAtual === "patio") carregarPatio();
    else if (abaAtual === "historico") carregarHistorico();
    else if (abaAtual === "consultar") consultar("");
  } else if (viewId === "view-empresas") {
    carregarEmpresas();
  } else if (viewId === "view-usuarios") {
    carregarUsuarios();
  } else if (viewId === "view-clientes") {
    carregarClientes();
  } else if (viewId === "view-configuracoes") {
    carregarConfiguracoes();
  } else if (viewId === "view-financeiro") {
    carregarFinanceiro();
  } else if (viewId === "view-relatorios") {
    const tabAtiva = document.querySelector(".relatorio-tabs .tab.active")?.dataset.relatorioTab || "geral";
    if (tabAtiva === "pagamentos") {
      carregarFormasPagamentoRelatorio();
      carregarRelatorioPagamentos();
    } else {
      carregarRelatoriosFinanceiros();
    }
  } else if (viewId === "view-caixa") {
    carregarCaixa();
  } else if (viewId === "view-pagamentos") {
    carregarPagamentos();
  } else if (viewId === "view-formas-pagamento") {
    carregarFormasPagamento();
  } else if (viewId === "view-mensalistas") {
    carregarMensalistas();
  } else if (viewId === "view-convenios") {
    carregarConvenios();
  } else if (viewId === "view-contas-receber") {
    carregarContasReceber();
  } else if (viewId === "view-descontos") {
    carregarDescontos();
  } else if (viewId === "view-cortesias") {
    carregarCortesias();
  } else if (viewId === "view-dashboard-financeiro") {
    carregarDashboardFinanceiro();
  } else if (viewId === "view-nfse") {
    carregarNFSE();
  } else if (viewId === "view-lista-negra") {
    carregarListaNegra();
  } else if (viewId === "view-reservas") {
    carregarReservas();
  } else if (viewId === "view-ocorrencias") {
    carregarOcorrencias();
  } else if (viewId === "view-notificacoes") {
    carregarAvisos();
  } else if (viewId === "view-auditoria") {
    carregarAuditoria();
  } else if (viewId === "view-permissoes") {
    carregarPerfis();
  }
}

document.querySelectorAll(".menu-item").forEach((item) => {
  item.addEventListener("click", (evento) => {
    evento.preventDefault();
    mostrarView(item.dataset.view);
  });
});

// Logo/nome do sistema no topo do sidebar volta para a Visao Geral
document.getElementById("sidebar-brand-home").addEventListener("click", () => {
  mostrarView("view-visao-geral");
});

// Toggle dos grupos de menu (submenus expansiveis)
document.querySelectorAll(".menu-group-toggle").forEach((toggle) => {
  toggle.addEventListener("click", () => {
    const grupo = toggle.closest(".menu-group");
    if (grupo) grupo.classList.toggle("open");
  });
});

// Pesquisa do menu: filtra itens (respeitando permissoes do perfil)
const inputPesquisaMenu = document.getElementById("sidebar-input-pesquisa");
if (inputPesquisaMenu) {
  inputPesquisaMenu.addEventListener("input", () => {
    const termo = inputPesquisaMenu.value.trim().toLowerCase();
    document.querySelectorAll(".menu-item").forEach((item) => {
      if (item.dataset.permissaoOculto === "1") {
        item.style.display = "none";
        return;
      }
      const texto = item.textContent.toLowerCase();
      const visivel = !termo || texto.includes(termo);
      item.style.display = visivel ? "flex" : "none";
    });

    // Oculta grupos sem itens correspondentes e expande os que tem resultado
    document.querySelectorAll(".menu-group").forEach((grupo) => {
      const itens = grupo.querySelectorAll(".menu-item");
      const algumVisivel = Array.from(itens).some(
        (item) => item.style.display !== "none" && item.dataset.permissaoOculto !== "1"
      );
      grupo.style.display = algumVisivel ? "" : "none";
      if (termo && algumVisivel) {
        grupo.classList.add("open");
      }
    });
  });
}

// Toggle mobile
const sidebarToggle = document.getElementById("sidebar-toggle");
const appSidebar = document.getElementById("app-sidebar");
const sidebarBackdrop = document.getElementById("sidebar-backdrop");

if (sidebarToggle) {
  sidebarToggle.addEventListener("click", () => {
    appSidebar.classList.toggle("open");
    sidebarBackdrop.classList.toggle("open");
  });
}

if (sidebarBackdrop) {
  sidebarBackdrop.addEventListener("click", () => {
    appSidebar.classList.remove("open");
    sidebarBackdrop.classList.remove("open");
  });
}

// ---------------------- CARDS DE RESUMO (DASHBOARD) ----------------------

async function carregarDashboard() {
  try {
    const dados = await chamarApi("/dashboard");
    document.getElementById("card-no-patio").textContent = dados.no_patio_agora;
    document.getElementById("card-faturamento").textContent = formatarMoeda(dados.faturamento_hoje);
    document.getElementById("card-saidas").textContent = dados.saidas_hoje;
    document.getElementById("card-permanencia").textContent = dados.permanencia_media_texto;
    document.getElementById("header-contagem").textContent = `${dados.no_patio_agora} veículo(s) no pátio`;
    document.getElementById("tab-count-patio").textContent = dados.no_patio_agora;

    // Card "Vagas disponíveis": mostra o total de vagas livres e fica vermelho quando lotado
    const cardVagas = document.getElementById("card-vagas-disponiveis");
    const valorVagas = document.getElementById("card-vagas-disponiveis-valor");
    valorVagas.textContent = dados.vagas_disponiveis;
    cardVagas.classList.toggle("card-cheio", dados.vagas_disponiveis <= 0);

    // Banner Hero de Ocupacao (Gauge Operacional)
    const totalVagas = (dados.no_patio_agora || 0) + (dados.vagas_disponiveis || 0);
    const pctOcupacao = totalVagas > 0 ? Math.min(100, Math.round((dados.no_patio_agora / totalVagas) * 100)) : 0;
    const barFill = document.getElementById("ocupacao-bar-fill");
    const pctBadge = document.getElementById("ocupacao-percent-badge");
    const statsText = document.getElementById("ocupacao-stats-text");
    const tagStatus = document.getElementById("ocupacao-tag-status");

    if (barFill) {
      barFill.style.width = `${pctOcupacao}%`;
      if (dados.vagas_disponiveis <= 0) {
        barFill.style.background = "linear-gradient(90deg, #ef4444 0%, #b91c1c 100%)";
      } else if (pctOcupacao >= 85) {
        barFill.style.background = "linear-gradient(90deg, #f59e0b 0%, #d97706 100%)";
      } else {
        barFill.style.background = "linear-gradient(90deg, #10b981 0%, #059669 100%)";
      }
    }
    if (pctBadge) pctBadge.textContent = `${pctOcupacao}% ocupado`;
    if (statsText) statsText.textContent = `${dados.no_patio_agora} de ${totalVagas} vagas ocupadas (${dados.vagas_disponiveis} disponíveis)`;
    if (tagStatus) {
      if (dados.vagas_disponiveis <= 0) {
        tagStatus.textContent = "Pátio Lotado";
        tagStatus.style.color = "#dc2626";
      } else if (pctOcupacao >= 85) {
        tagStatus.textContent = "Pátio Quase Lotado";
        tagStatus.style.color = "#d97706";
      } else {
        tagStatus.textContent = "Operação Normal";
        tagStatus.style.color = "#059669";
      }
    }
    // Atualiza estado do caixa na tela inicial
    caixaAberto = dados.caixa_aberto || null;
    atualizarEstadoCaixaNaEntrada(caixaAberto);
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
}

// ---------------------- CONTROLE DE CAIXA NA NOVA ENTRADA ----------------------

function atualizarEstadoCaixaNaEntrada(caixa) {
  const alerta = document.getElementById("alerta-caixa-fechado-entrada");
  const btnEmitir = document.getElementById("btn-emitir-ticket");
  const inputPlaca = document.getElementById("input-placa");

  if (!caixa) {
    if (alerta) alerta.hidden = false;
    if (btnEmitir) {
      btnEmitir.disabled = true;
      btnEmitir.classList.add("btn-desabilitado-caixa");
      btnEmitir.innerHTML = '⚠️ Caixa Fechado (Abra o caixa para emitir)';
      btnEmitir.title = "Abertura de caixa obrigatória antes de emitir tickets";
    }
    if (inputPlaca) {
      inputPlaca.placeholder = "Caixa Fechado";
    }
  } else {
    if (alerta) alerta.hidden = true;
    if (btnEmitir) {
      btnEmitir.disabled = false;
      btnEmitir.classList.remove("btn-desabilitado-caixa");
      btnEmitir.innerHTML = '<span class="btn-plus">+</span> Emitir Ticket (Enter ↵)';
      btnEmitir.title = "Emitir novo ticket";
    }
    if (inputPlaca && inputPlaca.placeholder === "Caixa Fechado") {
      inputPlaca.placeholder = "ABC1D23";
    }
  }
}

// Botao no alerta para abrir o caixa diretamente
document.getElementById("btn-alerta-abrir-caixa")?.addEventListener("click", () => {
  abrirModalAbrirCaixa();
});

// ---------------------- NOVA ENTRADA ----------------------

// Auto-uppercase na placa
const inputPlacaEl = document.getElementById("input-placa");
if (inputPlacaEl) {
  inputPlacaEl.addEventListener("input", (e) => {
    e.target.value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 8);
  });
}

// Modelos de veiculos estritamente separados por categoria
const MODELOS_POR_CATEGORIA = {
  Carro: [
    "Civic", "Corolla", "Onix", "Onix Plus", "Gol", "HB20", "HB20S", "Polo", "Argo", "Mobi",
    "Kwid", "Cruze", "City", "Fit", "Yaris", "Cronos", "Virtus", "Ka", "Fiesta", "Focus",
    "Sandero", "Logan", "Celta", "Prisma", "Corsa", "Classic", "Astra", "Vectra", "Palio",
    "Siena", "Uno", "Punto", "Fox", "Voyage", "Up!", "Golf", "Jetta", "Fusca", "208", "C3",
    "Sentra", "Versa", "Etios", "Cobalt", "Spin", "Compass", "Renegade", "Creta", "Tracker",
    "T-Cross", "Nivus", "Taos", "Kicks", "HR-V", "WR-V", "Corolla Cross", "Duster", "Pulse",
    "Fastback", "EcoSport"
  ],
  Caminhonete: [
    "Hilux", "S10", "Ranger", "Amarok", "Toro", "Strada", "Saveiro", "L200 Triton", "Frontier",
    "Montana", "Oroch", "Fiorino", "SW4", "Commander", "Rampage", "Ram 1500", "Ram 2500",
    "Master", "Ducato", "Transit", "HR", "Bongo"
  ],
  Moto: [
    "CG 160", "Biz 125", "Bros 160", "Pop 110i", "XRE 300", "XRE 190", "CB 300F", "Twister",
    "Fazer 250", "Fazer 150", "Factor 150", "Crosser 150", "Lander 250", "PCX 160", "NMax 160",
    "Elite 125"
  ]
};

function atualizarSugestoesModelos() {
  const inputObs = document.getElementById("input-observacoes");
  const datalist = document.getElementById("lista-modelos-carros");
  if (!inputObs || !datalist) return;

  const texto = inputObs.value.trim();
  const tipo = document.getElementById("input-tipo")?.value || "Carro";

  // Só exibe as sugestões de modelos após iniciar a digitação no campo
  if (texto.length > 0) {
    const modelos = MODELOS_POR_CATEGORIA[tipo] || MODELOS_POR_CATEGORIA["Carro"];
    datalist.innerHTML = modelos.map((m) => `<option value="${m}"></option>`).join("\n");
    if (inputObs.getAttribute("list") !== "lista-modelos-carros") {
      inputObs.setAttribute("list", "lista-modelos-carros");
    }
  } else {
    // Campo vazio: remove o datalist para não exibir sugestões ao focar ou clicar
    datalist.innerHTML = "";
    if (inputObs.hasAttribute("list")) {
      inputObs.removeAttribute("list");
    }
  }
}

function atualizarModelosPorCategoria(tipo) {
  const inputObs = document.getElementById("input-observacoes");
  const categoria = tipo || document.getElementById("input-tipo")?.value || "Carro";

  // Ajusta o placeholder dinamicamente para orientar o operador
  if (inputObs) {
    if (categoria === "Moto") {
      inputObs.placeholder = "Modelo da moto, cor ou detalhes (ex.: CG 160, preta)...";
    } else if (categoria === "Caminhonete") {
      inputObs.placeholder = "Modelo da camionete, cor ou detalhes (ex.: Hilux, branca)...";
    } else {
      inputObs.placeholder = "Modelo do carro, cor ou detalhes (ex.: Civic, prata)...";
    }
  }

  // Atualiza as opções apenas se já houver digitação ativa
  atualizarSugestoesModelos();
}

// Selecao rapida de categoria (Pills)
document.querySelectorAll("#quick-types-selector .btn-quick-type").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#quick-types-selector .btn-quick-type").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    const tipo = btn.dataset.tipo;
    const sel = document.getElementById("input-tipo");
    if (sel) sel.value = tipo;
    atualizarModelosPorCategoria(tipo);
  });
});

document.getElementById("input-tipo")?.addEventListener("change", (e) => {
  atualizarModelosPorCategoria(e.target.value);
});

// Controle de visibilidade dos atalhos rápidos (só aparecem ao iniciar a digitação)
const inputObsEl = document.getElementById("input-observacoes");
const quickChipsObsEl = document.getElementById("quick-chips-obs");

function atualizarVisibilidadeChipsObs() {
  if (!inputObsEl || !quickChipsObsEl) return;
  const temTexto = inputObsEl.value.trim().length > 0;
  quickChipsObsEl.classList.toggle("visible", temTexto);
}

// Inicializa estado limpo (sem sugestões e sem atalhos visíveis enquanto vazio)
atualizarVisibilidadeChipsObs();
atualizarSugestoesModelos();

// Chips de observacoes rapidas
document.querySelectorAll(".quick-chips-row .chip-obs").forEach((chip) => {
  chip.addEventListener("click", () => {
    const obsInput = document.getElementById("input-observacoes");
    if (!obsInput) return;
    const val = chip.dataset.chip;
    if (obsInput.value.trim().length > 0) {
      if (!obsInput.value.includes(val)) {
        obsInput.value = `${obsInput.value.trim()}, ${val}`;
      }
    } else {
      obsInput.value = val;
    }
    atualizarVisibilidadeChipsObs();
    atualizarSugestoesModelos();
    obsInput.focus();
  });
});

// Auto-seleção de categoria pelo modelo digitado/selecionado
const MOTOS_COMUNS = ["CG 160", "Biz", "Bros", "Pop 110", "XRE", "CB 300", "Fazer", "PCX", "Titan", "Fan", "Factor", "Crosser", "Lander", "NMax"];
const CAMIONETES_COMUNS = ["Hilux", "S10", "Ranger", "Amarok", "L200", "Frontier", "Toro", "Montana", "Oroch", "Fiorino", "Saveiro", "Strada", "Rampage", "Ram"];

document.getElementById("input-observacoes")?.addEventListener("input", (e) => {
  atualizarVisibilidadeChipsObs();
  atualizarSugestoesModelos();
  const texto = e.target.value.trim();
  if (!texto) return;
  const tipoSelect = document.getElementById("input-tipo");
  if (!tipoSelect) return;

  if (MOTOS_COMUNS.some(m => texto.toLowerCase().includes(m.toLowerCase()))) {
    if (tipoSelect.value !== "Moto") {
      tipoSelect.value = "Moto";
      document.querySelectorAll(".btn-quick-type").forEach(b => b.classList.toggle("active", b.dataset.tipo === "Moto"));
      atualizarModelosPorCategoria("Moto");
    }
  } else if (CAMIONETES_COMUNS.some(c => texto.toLowerCase().includes(c.toLowerCase()))) {
    if (tipoSelect.value !== "Caminhonete") {
      tipoSelect.value = "Caminhonete";
      document.querySelectorAll(".btn-quick-type").forEach(b => b.classList.toggle("active", b.dataset.tipo === "Caminhonete"));
      atualizarModelosPorCategoria("Caminhonete");
    }
  }
});

document.getElementById("form-entrada").addEventListener("submit", async (evento) => {
  evento.preventDefault();

  // Validacao estrita: Bloquear emissao sem caixa aberto
  if (!caixaAberto) {
    mostrarToast("Não é permitido emitir ticket com o caixa fechado! Abra o caixa para operar.", "warning");
    abrirModalAbrirCaixa();
    return;
  }

  const placaInput = document.getElementById("input-placa");
  const tipoInput = document.getElementById("input-tipo");
  const obsInput = document.getElementById("input-observacoes");
  const botao = document.getElementById("btn-emitir-ticket") || evento.target.querySelector(".btn-emitir");

  const placa = placaInput.value.trim().toUpperCase();
  if (!placa) return;

  botao.disabled = true;
  try {
    const dados = await chamarApi("/entrada", {
      method: "POST",
      body: JSON.stringify({
        placa,
        tipo_veiculo: tipoInput.value,
        observacoes: obsInput.value.trim(),
      }),
    });
    mostrarToast(dados.mensagem, "success");
    placaInput.value = "";
    obsInput.value = "";
    atualizarVisibilidadeChipsObs();
    tipoInput.value = "Carro";

    // Reseta pills de tipo para Carro
    document.querySelectorAll("#quick-types-selector .btn-quick-type").forEach((b) => {
      b.classList.toggle("active", b.dataset.tipo === "Carro");
    });
    atualizarModelosPorCategoria("Carro");

    await carregarDashboard();
    if (abaAtual === "patio") await carregarPatio();

    // Exibe o modelo do ticket emitido para impressao
    mostrarTicket(dados.ticket);
  } catch (erro) {
    mostrarToast(erro.message, "error");
  } finally {
    if (caixaAberto && botao) botao.disabled = false;
  }
});

// ---------------------- TICKET (IMPRESSAO) ----------------------

function desenharCodigoBarrasSVG(numero) {
  const svg = document.getElementById("ticket-barcode");
  if (!svg) return;
  svg.innerHTML = "";

  const digitos = String(numero).padStart(6, "0").split("").map(Number);
  const larguraTotal = 260;
  const altura = 50;
  const larguraBarra = larguraTotal / (digitos.length * 7 + 10);
  let x = 5;

  svg.setAttribute("viewBox", `0 0 ${larguraTotal} ${altura}`);

  // Padrao simples de barras baseado nos digitos (code39-like visual)
  digitos.forEach((d) => {
    const bin = (d ^ (d >> 1)).toString(2).padStart(4, "0");
    for (let i = 0; i < bin.length; i++) {
      if (bin[i] === "1") {
        const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        rect.setAttribute("x", x);
        rect.setAttribute("y", 0);
        rect.setAttribute("width", Math.max(1, larguraBarra));
        rect.setAttribute("height", altura);
        rect.setAttribute("fill", "#000");
        svg.appendChild(rect);
      }
      x += larguraBarra * 1.4;
    }
    x += larguraBarra * 1.5;
  });
}

function mostrarTicket(ticket) {
  if (!ticket) return;

  // Cabecalho com dados do estacionamento
  const config = cacheConfiguracoes || {};
  document.getElementById("ticket-nome-estacionamento").textContent =
    config.nome_estacionamento || "Estaciona Parking";
  document.getElementById("ticket-cnpj").textContent = config.cnpj || "";
  document.getElementById("ticket-endereco").textContent = config.endereco || "";

  const cidadeUf = [config.cidade, config.estado].filter(Boolean).join(" - ");
  document.getElementById("ticket-cidade-uf").textContent = cidadeUf;
  document.getElementById("ticket-telefone").textContent = config.telefone || "";

  const cabecalhoCustom = document.getElementById("ticket-cabecalho-custom");
  cabecalhoCustom.textContent = config.cabecalho_ticket || "";
  cabecalhoCustom.style.display = config.cabecalho_ticket ? "block" : "none";

  // Dados do veiculo
  document.getElementById("ticket-numero").textContent = String(ticket.numero).padStart(6, "0");
  document.getElementById("ticket-placa").textContent = ticket.placa || "—";
  document.getElementById("ticket-tipo").textContent = ticket.tipo_veiculo || "—";
  document.getElementById("ticket-vaga").textContent = ticket.vaga != null ? ticket.vaga : "—";

  // Entrada / saida / tempo
  const entradaFormatada =
    ticket.entrada_data && ticket.entrada_hora
      ? `${ticket.entrada_data} ${ticket.entrada_hora}`
      : (ticket.entrada || "—");
  document.getElementById("ticket-entrada").textContent = entradaFormatada;

  const saidaRow = document.getElementById("ticket-saida-row");
  const saidaEl = document.getElementById("ticket-saida");
  if (ticket.saida) {
    const saidaFormatada =
      ticket.saida_data && ticket.saida_hora
        ? `${ticket.saida_data} ${ticket.saida_hora}`
        : ticket.saida;
    saidaEl.textContent = saidaFormatada;
    saidaRow.hidden = false;
  } else {
    saidaRow.hidden = true;
  }

  document.getElementById("ticket-tempo").textContent =
    ticket.tempo_estacionado || "—";

  // Observacoes
  const obsRow = document.getElementById("ticket-obs-row");
  const obsValor = document.getElementById("ticket-obs");
  if (ticket.observacoes) {
    obsValor.textContent = ticket.observacoes;
    obsRow.hidden = false;
  } else {
    obsRow.hidden = true;
  }

  // Valor e forma de pagamento (somente se fechado)
  const valorDivider = document.getElementById("ticket-valor-divider");
  const valorRow = document.getElementById("ticket-valor-row");
  const formaPagamentoRow = document.getElementById("ticket-forma-pagamento-row");

  if (ticket.status === "FECHADO" && ticket.valor != null) {
    document.getElementById("ticket-valor").textContent = formatarMoeda(ticket.valor);
    valorDivider.hidden = false;
    valorRow.hidden = false;
  } else {
    valorDivider.hidden = true;
    valorRow.hidden = true;
  }

  if (ticket.forma_pagamento) {
    document.getElementById("ticket-forma-pagamento").textContent =
      ticket.forma_pagamento;
    formaPagamentoRow.hidden = false;
  } else {
    formaPagamentoRow.hidden = true;
  }

  // Codigo de barras
  desenharCodigoBarrasSVG(ticket.numero);
  document.getElementById("ticket-codigo-numero").textContent =
    String(ticket.numero).padStart(6, "0");

  // Rodape
  const rodapeCustom = document.getElementById("ticket-rodape-custom");
  rodapeCustom.textContent = config.rodape_ticket || "";
  rodapeCustom.style.display = config.rodape_ticket ? "block" : "none";

  const agora = new Date();
  document.getElementById("ticket-data-emissao").textContent =
    `Documento emitido em ${agora.toLocaleDateString()} ${agora.toLocaleTimeString()}`;

  document.getElementById("ticket-modal").hidden = false;
}

function fecharTicket() {
  document.getElementById("ticket-modal").hidden = true;
}

document.getElementById("ticket-modal-fechar").addEventListener("click", fecharTicket);
document.getElementById("ticket-modal-imprimir").addEventListener("click", () => window.print());

document.getElementById("ticket-modal").addEventListener("click", (evento) => {
  if (evento.target === evento.currentTarget) fecharTicket();
});

document.addEventListener("keydown", (evento) => {
  if (evento.key === "Escape" && !document.getElementById("ticket-modal").hidden) fecharTicket();
  if (evento.key === "Escape" && !document.getElementById("modal-recibo-saida").hidden) fecharReciboSaida();
});

// ---------------------- RECIBO DE SAÍDA / COMPROVANTE DO CLIENTE ----------------------

let ticketReciboAtual = null;

function mostrarReciboSaida(ticket, infoExtra = {}) {
  if (!ticket) return;
  ticketReciboAtual = ticket;

  const config = cacheConfiguracoes || {};
  document.getElementById("recibo-nome-estacionamento").textContent =
    config.nome_estacionamento || "Estaciona Parking";
  document.getElementById("recibo-cnpj").textContent = config.cnpj ? `CNPJ: ${config.cnpj}` : "";
  document.getElementById("recibo-endereco").textContent = config.endereco || "";

  const cidadeUf = [config.cidade, config.estado].filter(Boolean).join(" - ");
  document.getElementById("recibo-cidade-uf").textContent = cidadeUf;
  document.getElementById("recibo-telefone").textContent = config.telefone ? `Tel: ${config.telefone}` : "";

  // Dados do veiculo
  document.getElementById("recibo-numero").textContent = `#${String(ticket.numero).padStart(6, "0")}`;
  document.getElementById("recibo-placa").textContent = ticket.placa || "—";
  document.getElementById("recibo-tipo").textContent = ticket.tipo_veiculo || "Carro";

  const vagaRow = document.getElementById("recibo-vaga-row");
  const vagaEl = document.getElementById("recibo-vaga");
  if (ticket.vaga != null) {
    vagaEl.textContent = `Vaga ${ticket.vaga}`;
    vagaRow.hidden = false;
  } else {
    vagaRow.hidden = true;
  }

  // Horários e permanência
  const entradaFormatada =
    ticket.entrada_data && ticket.entrada_hora
      ? `${ticket.entrada_data} ${ticket.entrada_hora}`
      : (ticket.entrada || "—");
  document.getElementById("recibo-entrada").textContent = entradaFormatada;

  const saidaFormatada =
    ticket.saida_data && ticket.saida_hora
      ? `${ticket.saida_data} ${ticket.saida_hora}`
      : (ticket.saida || "—");
  document.getElementById("recibo-saida").textContent = saidaFormatada;

  document.getElementById("recibo-tempo").textContent = ticket.tempo_estacionado || "—";

  // Financeiro
  const valor = Number(ticket.valor) || 0;
  document.getElementById("recibo-valor").textContent = formatarMoeda(valor);

  const formasMap = {
    dinheiro: "Dinheiro",
    pix: "PIX",
    cartao_credito: "Cartão de Crédito",
    cartao_debito: "Cartão de Débito",
    cortesia: "Cortesia",
    mensalista: "Mensalista (Isento)",
  };
  const formaNome = formasMap[ticket.forma_pagamento] || ticket.forma_pagamento || "Não informado";
  document.getElementById("recibo-forma-pagamento").textContent = formaNome;

  const trocoRow = document.getElementById("recibo-troco-row");
  if (infoExtra.troco && infoExtra.troco > 0) {
    document.getElementById("recibo-troco").textContent = formatarMoeda(infoExtra.troco);
    trocoRow.hidden = false;
  } else {
    trocoRow.hidden = true;
  }

  // Atendente e data/hora
  const usuarioLogado = document.getElementById("header-usuario-nome")?.textContent || "Operador";
  document.getElementById("recibo-operador").textContent = usuarioLogado;

  const agora = new Date();
  document.getElementById("recibo-data-emissao").textContent =
    `${agora.toLocaleDateString()} às ${agora.toLocaleTimeString().slice(0, 5)}`;

  document.getElementById("modal-recibo-saida").hidden = false;
}

function fecharReciboSaida() {
  const modal = document.getElementById("modal-recibo-saida");
  if (modal) modal.hidden = true;
}

function compartilharReciboWhatsApp(ticket) {
  if (!ticket) ticket = ticketReciboAtual;
  if (!ticket) return;

  const config = cacheConfiguracoes || {};
  const nomeEst = config.nome_estacionamento || "Estacionamento";
  const valorFmt = formatarMoeda(ticket.valor || 0);
  const formasMap = {
    dinheiro: "Dinheiro",
    pix: "PIX",
    cartao_credito: "Cartão de Crédito",
    cartao_debito: "Cartão de Débito",
    cortesia: "Cortesia",
    mensalista: "Mensalista (Isento)",
  };
  const formaNome = formasMap[ticket.forma_pagamento] || ticket.forma_pagamento || "Dinheiro";

  const texto =
`🧾 *RECIBO DE PAGAMENTO*
📍 *${nomeEst}*
--------------------------------
🚗 *Veículo:* ${ticket.placa || '—'} (${ticket.tipo_veiculo || 'Carro'})
🎫 *Ticket:* #${String(ticket.numero).padStart(6, '0')}
⏱️ *Permanência:* ${ticket.tempo_estacionado || '—'}
🕒 *Entrada:* ${ticket.entrada || '—'}
🏁 *Saída:* ${ticket.saida || '—'}
--------------------------------
💰 *TOTAL PAGO:* ${valorFmt}
💳 *Forma:* ${formaNome}
✅ *Status:* QUITADO
--------------------------------
_Agradecemos a preferência! Volte sempre._`;

  const url = `https://api.whatsapp.com/send?text=${encodeURIComponent(texto)}`;
  window.open(url, "_blank");
}

document.getElementById("recibo-modal-fechar")?.addEventListener("click", fecharReciboSaida);
document.getElementById("recibo-modal-imprimir")?.addEventListener("click", () => window.print());
document.getElementById("recibo-modal-whatsapp")?.addEventListener("click", () => compartilharReciboWhatsApp(ticketReciboAtual));
document.getElementById("modal-recibo-saida")?.addEventListener("click", (evento) => {
  if (evento.target === evento.currentTarget) fecharReciboSaida();
});

// ---------------------- SAIDA ----------------------

let saidaPendente = null; // identificador aguardando escolha da forma de pagamento

// ---------------------- CHECKOUT DE SAÍDA & PAGAMENTO ----------------------

let checkoutDadosAtuais = null;
let formaPagamentoCheckout = "dinheiro";

function calcularTrocoCheckout() {
  const inputRecebido = document.getElementById("input-checkout-recebido");
  const trocoVal = document.getElementById("checkout-troco-val");
  if (!inputRecebido || !trocoVal || !checkoutDadosAtuais) return;

  const total = Number(checkoutDadosAtuais.valor) || 0;
  const recebido = parseFloat(inputRecebido.value) || 0;

  if (recebido > total) {
    trocoVal.textContent = formatarMoeda(recebido - total);
    trocoVal.style.color = "#059669";
  } else {
    trocoVal.textContent = "R$ 0,00";
    trocoVal.style.color = "#64748b";
  }
}

async function registrarSaida(identificador) {
  saidaPendente = identificador;

  try {
    const dadosCalculo = await chamarApi(`/saida/calcular?identificador=${encodeURIComponent(identificador)}`);
    checkoutDadosAtuais = dadosCalculo;

    const t = dadosCalculo.ticket || {};
    document.getElementById("checkout-placa").textContent = t.placa || identificador;
    document.getElementById("checkout-tipo").textContent = t.tipo_veiculo || "Carro";
    document.getElementById("checkout-vaga").textContent = t.vaga ? `Vaga ${t.vaga}` : "Sem vaga fixa";
    document.getElementById("checkout-numero-ticket").textContent = `Ticket #${String(t.numero).padStart(6, '0')}`;

    const horaEntrada = t.entrada ? (t.entrada.split(" ")[1] || t.entrada).slice(0, 5) : "--:--";
    document.getElementById("checkout-entrada").textContent = horaEntrada;
    document.getElementById("checkout-tempo").textContent = dadosCalculo.tempo_permanencia || t.tempo_estacionado || "--";

    const badgeMensalista = document.getElementById("checkout-badge-mensalista");
    const valorTotalEl = document.getElementById("checkout-valor-total");

    if (dadosCalculo.eh_mensalista) {
      if (badgeMensalista) {
        badgeMensalista.hidden = false;
        badgeMensalista.textContent = `👤 Mensalista Ativo (${dadosCalculo.mensalista_nome || 'Identificado'}) • Isento de cobrança avulsa`;
      }
      valorTotalEl.textContent = "R$ 0,00";
      valorTotalEl.style.color = "#7c3aed";
      formaPagamentoCheckout = "mensalista";
    } else {
      if (badgeMensalista) badgeMensalista.hidden = true;
      valorTotalEl.textContent = formatarMoeda(dadosCalculo.valor);
      valorTotalEl.style.color = "#15803d";
      formaPagamentoCheckout = "dinheiro";
    }

    // Marca o botão inicial de forma de pagamento
    document.querySelectorAll("#forma-opcoes .forma-opcao").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.forma === formaPagamentoCheckout);
    });

    // Controla painel de troco
    const boxTroco = document.getElementById("checkout-troco-box");
    if (boxTroco) {
      boxTroco.style.display = (!dadosCalculo.eh_mensalista && formaPagamentoCheckout === "dinheiro") ? "flex" : "none";
    }
    const inputRecebido = document.getElementById("input-checkout-recebido");
    if (inputRecebido) inputRecebido.value = "";
    calcularTrocoCheckout();

    document.getElementById("modal-forma-saida").hidden = false;
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
}

async function confirmarSaida(identificador, formaPagamento) {
  try {
    const dados = await chamarApi("/saida", {
      method: "POST",
      body: JSON.stringify({ identificador, forma_pagamento: formaPagamento }),
    });
    mostrarToast(dados.mensagem, "success");
    if (dados.aviso) mostrarToast(dados.aviso, "warning");

    fecharModalForma();
    await carregarDashboard();
    await recarregarAbaAtual();

    // Emite o recibo de saída / pagamento para disponibilizar ao cliente
    if (dados.ticket) {
      let trocoValor = 0;
      const inputRecebido = document.getElementById("input-checkout-recebido");
      if (inputRecebido && formaPagamento === "dinheiro") {
        const recebido = parseFloat(inputRecebido.value) || 0;
        const total = Number(dados.ticket.valor) || 0;
        if (recebido > total) trocoValor = recebido - total;
      }
      mostrarReciboSaida(dados.ticket, { troco: trocoValor });
    }
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
}

function fecharModalForma() {
  document.getElementById("modal-forma-saida").hidden = true;
  saidaPendente = null;
  checkoutDadosAtuais = null;
}

document.getElementById("modal-forma-fechar").addEventListener("click", fecharModalForma);
document.getElementById("btn-forma-cancelar").addEventListener("click", fecharModalForma);
document.getElementById("modal-forma-saida").addEventListener("click", (evento) => {
  if (evento.target === evento.currentTarget) fecharModalForma();
});

// Seleção de forma de pagamento no modal
document.getElementById("forma-opcoes").addEventListener("click", (evento) => {
  const botao = evento.target.closest(".forma-opcao");
  if (!botao) return;
  document.querySelectorAll("#forma-opcoes .forma-opcao").forEach((b) => b.classList.remove("active"));
  botao.classList.add("active");
  formaPagamentoCheckout = botao.dataset.forma;

  const boxTroco = document.getElementById("checkout-troco-box");
  if (boxTroco) {
    const ehMensalista = checkoutDadosAtuais && checkoutDadosAtuais.eh_mensalista;
    boxTroco.style.display = (!ehMensalista && formaPagamentoCheckout === "dinheiro") ? "flex" : "none";
  }
});

document.getElementById("input-checkout-recebido")?.addEventListener("input", calcularTrocoCheckout);

// Botão Confirmar Saída
document.getElementById("btn-confirmar-checkout")?.addEventListener("click", () => {
  if (!saidaPendente) return;
  confirmarSaida(saidaPendente, formaPagamentoCheckout);
});

// ---------------------- RENDER LISTA DE VEICULOS ----------------------

function renderListaVeiculos(veiculos, { permitirSaida }) {
  const lista = document.getElementById("vehicle-list");
  const empty = document.getElementById("lista-empty");

  lista.innerHTML = "";

  if (!veiculos || veiculos.length === 0) {
    empty.hidden = false;
    return;
  }
  empty.hidden = true;

  veiculos.forEach((ticket) => {
    const item = document.createElement("div");
    item.className = "vehicle-item";

    const dataEntrada = ticket.entrada ? ticket.entrada.split(" ")[0].slice(0, 5) : "";
    const horaEntrada = ticket.entrada && ticket.entrada.split(" ")[1] ? ticket.entrada.split(" ")[1].slice(0, 5) : "";

    const ehMensalista = (ticket.observacoes || "").toLowerCase().includes("mensalista") || ticket.forma_pagamento === "mensalista";
    const badgeMensalistaHtml = ehMensalista ? `<span class="badge-mensalista-patio">👤 Mensalista</span>` : "";

    const obsHtml = ticket.observacoes
      ? `<span class="vehicle-obs">${ticket.observacoes}</span>`
      : "";

    const statusHtml = !permitirSaida
      ? `<span class="vehicle-status status-fechado">Saiu ${ticket.saida ? ticket.saida.split(" ")[1].slice(0,5) : ""}</span>`
      : "";

    const acoesHtml = permitirSaida
      ? `
        <button class="btn-print" title="Imprimir ticket" data-acao="imprimir" data-numero="${ticket.numero}">${ICON_PRINT}</button>
        <button class="btn-saida" data-acao="saida" data-identificador="${ticket.numero}">${ICON_EXIT} Saída</button>
      `
      : `<button class="btn-print" title="Imprimir ticket" data-acao="imprimir" data-numero="${ticket.numero}">${ICON_PRINT}</button>`;

    const valorNum = ticket.valor != null ? ticket.valor : (ticket.valor_estimado != null ? ticket.valor_estimado : 0);
    const valorTexto = ehMensalista ? "Isento" : formatarMoeda(valorNum);
    const classeValor = !ticket.saida ? "vehicle-val-estimado" : "";

    item.innerHTML = `
      <div class="vehicle-icon">${iconeVeiculo(ticket.tipo_veiculo)}</div>
      <div class="vehicle-main">
        <div class="vehicle-plate-row">
          <span class="vehicle-plate">${ticket.placa}</span>
          <span class="vehicle-type">${ticket.tipo_veiculo}</span>
          ${badgeMensalistaHtml}
        </div>
        <div class="vehicle-meta">
          ${ICON_CLOCK} ${ticket.tempo_estacionado || "0min"} &middot; ${dataEntrada}, ${horaEntrada}
        </div>
        ${obsHtml}
      </div>
      <div class="vehicle-right">
        ${statusHtml}
        <span class="vehicle-value ${classeValor}" title="${!ticket.saida ? 'Valor acumulado até o momento' : 'Valor final pago'}">${valorTexto}</span>
        ${acoesHtml}
      </div>
    `;

    lista.appendChild(item);
  });
}

// ---------------------- ABA: NO PATIO ----------------------

async function carregarPatio() {
  try {
    const dados = await chamarApi("/vagas");
    cacheVeiculosPatio = dados.veiculos;
    renderListaVeiculos(dados.veiculos, { permitirSaida: true });
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
}

// ---------------------- ABA: HISTORICO ----------------------

async function carregarHistorico() {
  try {
    const dados = await chamarApi("/historico");
    renderListaVeiculos(dados.veiculos, { permitirSaida: false });
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
}

// ---------------------- ABA: CONSULTAR (BUSCA GERAL) ----------------------

async function consultar(termo) {
  try {
    const query = termo ? `?q=${encodeURIComponent(termo)}` : "";
    const dados = await chamarApi(`/buscar${query}`);
    renderListaVeiculos(
      dados.veiculos,
      { permitirSaida: false }
    );
    // Permite saida apenas nos itens que ainda estao abertos
    document.querySelectorAll("#vehicle-list .vehicle-item").forEach((item, indice) => {
      const ticket = dados.veiculos[indice];
      if (ticket && ticket.status === "ABERTO") {
        const acoesArea = item.querySelector(".vehicle-right");
        if (!acoesArea.querySelector(".btn-saida")) {
          const botaoSaida = document.createElement("button");
          botaoSaida.className = "btn-saida";
          botaoSaida.dataset.acao = "saida";
          botaoSaida.dataset.identificador = ticket.numero;
          botaoSaida.innerHTML = `${ICON_EXIT} Saída`;
          acoesArea.appendChild(botaoSaida);
        }
      }
    });
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
}

// ---------------------- BUSCA & FILTROS OPERACIONAIS (PATIO) ----------------------

const inputBusca = document.getElementById("input-busca");
let filtroTipoVeiculoAtivo = "todos";

// Botoes de filtro por categoria no patio
document.querySelectorAll("#filtro-tipo-veiculos .btn-filtro-tipo").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#filtro-tipo-veiculos .btn-filtro-tipo").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    filtroTipoVeiculoAtivo = btn.dataset.filtroTipo || "todos";
    executarBuscaAtual();
  });
});

async function executarBuscaAtual() {
  const termo = inputBusca ? inputBusca.value.trim().toUpperCase() : "";

  if (abaAtual === "patio") {
    let filtrados = cacheVeiculosPatio || [];
    if (filtroTipoVeiculoAtivo && filtroTipoVeiculoAtivo !== "todos") {
      filtrados = filtrados.filter((t) => (t.tipo_veiculo || "").toLowerCase() === filtroTipoVeiculoAtivo.toLowerCase());
    }
    if (termo) {
      filtrados = filtrados.filter((t) =>
        (t.placa || "").toUpperCase().includes(termo) || String(t.numero).includes(termo)
      );
    }
    renderListaVeiculos(filtrados, { permitirSaida: true });
  } else if (abaAtual === "historico") {
    const dados = await chamarApi(`/historico`);
    let filtrados = dados.veiculos || [];
    if (filtroTipoVeiculoAtivo && filtroTipoVeiculoAtivo !== "todos") {
      filtrados = filtrados.filter((t) => (t.tipo_veiculo || "").toLowerCase() === filtroTipoVeiculoAtivo.toLowerCase());
    }
    if (termo) {
      filtrados = filtrados.filter((t) =>
        (t.placa || "").toUpperCase().includes(termo) || String(t.numero).includes(termo)
      );
    }
    renderListaVeiculos(filtrados, { permitirSaida: false });
  } else if (abaAtual === "consultar") {
    await consultar(termo);
  }
}

let debounceBusca = null;
if (inputBusca) {
  inputBusca.addEventListener("input", () => {
    clearTimeout(debounceBusca);
    debounceBusca = setTimeout(executarBuscaAtual, 200);
  });
}

// ---------------------- ACOES NA LISTA (delegacao de evento) ----------------------

document.getElementById("vehicle-list").addEventListener("click", (evento) => {
  const botao = evento.target.closest("button[data-acao]");
  if (!botao) return;

  const acao = botao.dataset.acao;
  if (acao === "saida") {
    registrarSaida(botao.dataset.identificador);
  } else if (acao === "imprimir") {
    imprimirTicket(botao.dataset.numero);
  }
});

async function imprimirTicket(numero) {
  const numeroNum = Number(numero);

  // Procura no cache do patio (tickets abertos)
  let ticket = cacheVeiculosPatio.find((t) => Number(t.numero) === numeroNum);

  // Se nao achou, busca no historico
  if (!ticket) {
    try {
      const dados = await chamarApi("/historico");
      ticket = dados.veiculos.find((t) => Number(t.numero) === numeroNum);
    } catch (erro) {
      mostrarToast(erro.message, "error");
      return;
    }
  }

  if (!ticket) {
    mostrarToast("Ticket não encontrado.", "error");
    return;
  }

  if (ticket.status === "FECHADO") {
    mostrarReciboSaida(ticket);
  } else {
    mostrarTicket(ticket);
  }
}

// ---------------------- TABS ----------------------

async function recarregarAbaAtual() {
  inputBusca.value = "";
  if (abaAtual === "patio") await carregarPatio();
  else if (abaAtual === "historico") await carregarHistorico();
  else if (abaAtual === "consultar") await consultar("");
}

document.querySelectorAll(".tab").forEach((botaoTab) => {
  botaoTab.addEventListener("click", async () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    botaoTab.classList.add("active");
    abaAtual = botaoTab.dataset.tab;
    // Persiste a aba atual para restaurar ao recarregar a pagina (F5)
    localStorage.setItem("estaciona_aba", abaAtual);

    const placeholders = {
      patio: "Buscar por placa ou ticket...",
      consultar: "Buscar por placa ou ticket...",
      historico: "Buscar por placa ou ticket...",
    };
    inputBusca.placeholder = placeholders[abaAtual];
    inputBusca.value = "";

    if (abaAtual === "patio") await carregarPatio();
    else if (abaAtual === "historico") await carregarHistorico();
    else if (abaAtual === "consultar") await consultar("");
  });
});

// ---------------------- FINANCEIRO ----------------------

const FORMAS_LABEL = {
  dinheiro: "Dinheiro",
  pix: "Pix",
  cartao_credito: "Cartão de crédito",
  cartao_debito: "Cartão de débito",
};

let financeiroPeriodo = "diario";

async function carregarFinanceiro() {
  const corpo = document.getElementById("tabela-financeiro");
  const empty = document.getElementById("financeiro-empty");
  corpo.innerHTML = "";

  let dados;
  try {
    dados = await chamarApi(`/financeiro?periodo=${financeiroPeriodo}`);
  } catch (erro) {
    mostrarToast(erro.message, "error");
    corpo.innerHTML = '<tr><td colspan="6" class="table-empty">Erro ao carregar lançamentos.</td></tr>';
    return;
  }

  const lancamentos = dados.lancamentos || [];
  if (!lancamentos.length) {
    corpo.innerHTML = "";
    empty.hidden = false;
  } else {
    empty.hidden = true;
  }

  // Permissoes de acao para o perfil atual (modulo financeiro)
  const podeEditarLancamento = temPermissaoModulo("financeiro", "editar");
  const podeExcluirLancamento = temPermissaoModulo("financeiro", "excluir");
  const podeCriarLancamento = temPermissaoModulo("financeiro", "criar");
  const temAcoes = podeEditarLancamento || podeExcluirLancamento;

  // Oculta o botao "Novo lancamento" caso o perfil nao possa criar
  const btnNovoLancamento = document.getElementById("btn-novo-lancamento");
  if (btnNovoLancamento) btnNovoLancamento.style.display = podeCriarLancamento ? "" : "none";

  // Oculta a coluna/header de acoes se nao houver nenhuma acao disponivel
  const headerAcoes = document.getElementById("th-financeiro-acoes");
  if (headerAcoes) headerAcoes.style.display = temAcoes ? "" : "none";

  lancamentos.forEach((lancamento) => {
    const linha = document.createElement("tr");
    const tipoEntrada = lancamento.tipo === "entrada";
    const forma = FORMAS_LABEL[lancamento.forma_pagamento] || lancamento.forma_pagamento;
    const origem = lancamento.origem === "ticket" ? " (ticket)" : "";

    const acoesHtml = temAcoes ? `
      <td class="col-acoes">
        ${podeEditarLancamento ? `
        <button type="button" class="btn-acao" data-acao-lancamento="editar" data-id="${lancamento.id}" title="Editar">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>` : ""}
        ${podeExcluirLancamento ? `
        <button type="button" class="btn-acao btn-acao-danger" data-acao-lancamento="excluir" data-id="${lancamento.id}" title="Excluir">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M10 11v6M14 11v6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
        </button>` : ""}
      </td>` : "";

    linha.innerHTML = `
      <td>${formatarDataHora(lancamento.data)}</td>
      <td class="cell-nome">${lancamento.descricao}${origem}</td>
      <td>
        <span class="badge ${tipoEntrada ? "badge-ativo" : "badge-inativo"}">${tipoEntrada ? "Entrada" : "Saída"}</span>
      </td>
      <td><span class="badge">${forma}</span></td>
      <td class="${tipoEntrada ? "valor-entrada" : "valor-saida"}">${tipoEntrada ? "+" : "−"} ${formatarMoeda(lancamento.valor)}</td>
      ${acoesHtml}
    `;
    corpo.appendChild(linha);
  });

  // Resumo do periodo
  try {
    const resumo = await chamarApi(`/financeiro/resumo?periodo=${financeiroPeriodo}`);
    document.getElementById("fin-total-entradas").textContent = formatarMoeda(resumo.resumo.total_entradas);
    document.getElementById("fin-total-saidas").textContent = formatarMoeda(resumo.resumo.total_saidas);
    document.getElementById("fin-saldo").textContent = formatarMoeda(resumo.resumo.saldo);
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
}

document.getElementById("filtro-financeiro-periodo").addEventListener("change", (evento) => {
  financeiroPeriodo = evento.target.value;
  carregarFinanceiro();
});

// ----- Modal de lancamento -----

function abrirModalLancamento(lancamento = null) {
  const overlay = document.getElementById("modal-lancamento");
  document.getElementById("input-lancamento-id").value = lancamento ? lancamento.id : "";
  document.getElementById("input-lancamento-tipo").value = lancamento ? lancamento.tipo : "entrada";
  document.getElementById("input-lancamento-descricao").value = lancamento ? lancamento.descricao : "";
  document.getElementById("input-lancamento-valor").value = lancamento ? lancamento.valor : "";
  document.getElementById("input-lancamento-forma").value = lancamento ? lancamento.forma_pagamento : "dinheiro";
  document.getElementById("input-lancamento-data").value = lancamento ? lancamento.data : "";
  document.getElementById("modal-lancamento-titulo").textContent = lancamento ? "Editar lançamento" : "Novo lançamento";
  overlay.hidden = false;
  setTimeout(() => document.getElementById("input-lancamento-descricao").focus(), 50);
}

function fecharModalLancamento() {
  document.getElementById("modal-lancamento").hidden = true;
  document.getElementById("form-lancamento").reset();
  document.getElementById("input-lancamento-id").value = "";
}

document.getElementById("btn-novo-lancamento").addEventListener("click", () => abrirModalLancamento());
document.getElementById("modal-lancamento-fechar").addEventListener("click", fecharModalLancamento);
document.getElementById("btn-lancamento-cancelar").addEventListener("click", fecharModalLancamento);
document.getElementById("modal-lancamento").addEventListener("click", (evento) => {
  if (evento.target === evento.currentTarget) fecharModalLancamento();
});
document.addEventListener("keydown", (evento) => {
  if (evento.key === "Escape" && !document.getElementById("modal-lancamento").hidden) fecharModalLancamento();
});

document.getElementById("form-lancamento").addEventListener("submit", async (evento) => {
  evento.preventDefault();

  const id = document.getElementById("input-lancamento-id").value;
  const tipo = document.getElementById("input-lancamento-tipo").value;
  const descricao = document.getElementById("input-lancamento-descricao").value.trim();
  const valor = Number(document.getElementById("input-lancamento-valor").value);
  const formaPagamento = document.getElementById("input-lancamento-forma").value;
  const data = document.getElementById("input-lancamento-data").value.trim();

  if (!descricao || isNaN(valor)) return;

  const botaoSalvar = document.getElementById("btn-lancamento-salvar");
  botaoSalvar.disabled = true;
  try {
    const payload = { tipo, descricao, valor, forma_pagamento: formaPagamento };
    if (data) payload.data = data;

    if (id) {
      const dados = await chamarApi(`/financeiro/${id}`, { method: "PUT", body: JSON.stringify(payload) });
      mostrarToast(dados.mensagem, "success");
    } else {
      const dados = await chamarApi("/financeiro", { method: "POST", body: JSON.stringify(payload) });
      mostrarToast(dados.mensagem, "success");
    }
    fecharModalLancamento();
    await carregarFinanceiro();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  } finally {
    botaoSalvar.disabled = false;
  }
});

document.getElementById("tabela-financeiro").addEventListener("click", async (evento) => {
  const botao = evento.target.closest("button[data-acao-lancamento]");
  if (!botao) return;

  const id = Number(botao.dataset.id);
  const acao = botao.dataset.acaoLancamento;

  if (acao === "editar") {
    try {
      const dados = await chamarApi(`/financeiro/${id}`);
      abrirModalLancamento(dados.lancamento);
    } catch (erro) {
      mostrarToast(erro.message, "error");
    }
    return;
  }

  if (acao === "excluir") {
    const confirmacao = confirm("Excluir este lançamento?");
    if (!confirmacao) return;
    try {
      const dados = await chamarApi(`/financeiro/${id}`, { method: "DELETE" });
      mostrarToast(dados.mensagem, "success");
      await carregarFinanceiro();
    } catch (erro) {
      mostrarToast(erro.message, "error");
    }
  }
});

// ---------------------- USUARIOS ----------------------

async function carregarUsuarios() {
  const corpo = document.getElementById("tabela-usuarios");
  const empty = document.getElementById("usuarios-empty");
  corpo.innerHTML = "";

  let usuarios;
  try {
    const dados = await chamarApi("/usuarios");
    usuarios = dados.usuarios || [];
  } catch (erro) {
    if (erro.payload && erro.payload.erro && erro.payload.erro.includes("permissao")) {
      corpo.innerHTML = '<tr><td colspan="7" class="table-empty">Acesso restrito ao módulo de usuários.</td></tr>';
      return;
    }
    mostrarToast(erro.message, "error");
    corpo.innerHTML = '<tr><td colspan="7" class="table-empty">Erro ao carregar usuários.</td></tr>';
    return;
  }

  if (!usuarios.length) {
    corpo.innerHTML = "";
    empty.hidden = false;
    return;
  }
  empty.hidden = true;

  usuarios.forEach((usuario) => {
    const linha = document.createElement("tr");

    const perfil = nomePerfil(usuario.perfil);
    const statusAtivo = usuario.ativo;
    const dataCadastro = formatarDataHora(usuario.data_cadastro);
    const nomeEmpresa = usuario.master
      ? '<span class="badge badge-master">Master</span>'
      : (cacheEmpresas.find((e) => e.id === usuario.empresa_id)?.nome_fantasia || "—");

    linha.innerHTML = `
      <td class="cell-nome">${usuario.nome}${usuario.master ? '<span class="badge-master">Master</span>' : ""}</td>
      <td>${usuario.email}</td>
      <td>
        <span class="badge ${statusAtivo ? "badge-perfil-admin" : ""}">${perfil}</span>
      </td>
      <td>${nomeEmpresa}</td>
      <td>
        <span class="badge ${statusAtivo ? "badge-ativo" : "badge-inativo"}">${statusAtivo ? "Ativo" : "Inativo"}</span>
      </td>
      <td>${dataCadastro}</td>
      <td class="col-acoes">
        <button type="button" class="btn-acao" data-acao-usuario="editar" data-id="${usuario.id}" title="Editar">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <button type="button" class="btn-acao btn-acao-danger" data-acao-usuario="excluir" data-id="${usuario.id}" data-nome="${usuario.nome}" data-ativo="${statusAtivo}" title="${statusAtivo ? "Desativar" : "Ativar"}">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M10 11v6M14 11v6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
        </button>
      </td>
    `;

    corpo.appendChild(linha);
  });
}

function abrirModalUsuario(usuario = null) {
  const overlay = document.getElementById("modal-usuario");
  document.getElementById("input-usuario-id").value = usuario ? usuario.id : "";
  document.getElementById("input-usuario-nome").value = usuario ? usuario.nome : "";
  document.getElementById("input-usuario-email").value = usuario ? usuario.email : "";
  document.getElementById("input-usuario-senha").value = "";
  document.getElementById("input-usuario-senha").placeholder = usuario ? "Deixe em branco para manter a senha atual" : "Defina uma senha de acesso";
  document.getElementById("input-usuario-trocar-senha").checked = usuario ? !!usuario.trocar_senha_no_proximo_acesso : false;
  document.getElementById("input-usuario-perfil").value = usuario ? usuario.perfil : "operador";
  document.getElementById("input-usuario-ativo").value = usuario ? String(usuario.ativo) : "true";

  // Master + empresa
  const master = usuario ? !!usuario.master : false;
  document.getElementById("input-usuario-master").checked = master;
  document.getElementById("campo-usuario-empresa-label").style.display = master ? "none" : "";
  document.getElementById("input-usuario-empresa").style.display = master ? "none" : "";
  atualizarSelectEmpresas();
  document.getElementById("input-usuario-empresa").value = usuario && usuario.empresa_id != null ? String(usuario.empresa_id) : "";

  document.getElementById("modal-usuario-titulo").textContent = usuario ? "Editar usuário" : "Novo usuário";
  overlay.hidden = false;
  const campoNome = document.getElementById("input-usuario-nome");
  setTimeout(() => campoNome.focus(), 50);
}

function fecharModalUsuario() {
  document.getElementById("modal-usuario").hidden = true;
  document.getElementById("form-usuario").reset();
  document.getElementById("input-usuario-id").value = "";
}

document.getElementById("btn-novo-usuario").addEventListener("click", () => abrirModalUsuario());

document.getElementById("modal-usuario-fechar").addEventListener("click", fecharModalUsuario);
document.getElementById("btn-usuario-cancelar").addEventListener("click", fecharModalUsuario);

document.getElementById("modal-usuario").addEventListener("click", (evento) => {
  if (evento.target === evento.currentTarget) fecharModalUsuario();
});

document.addEventListener("keydown", (evento) => {
  if (evento.key === "Escape" && !document.getElementById("modal-usuario").hidden) fecharModalUsuario();
});

document.getElementById("form-usuario").addEventListener("submit", async (evento) => {
  evento.preventDefault();

  const id = document.getElementById("input-usuario-id").value;
  const nome = document.getElementById("input-usuario-nome").value.trim();
  const email = document.getElementById("input-usuario-email").value.trim();
  const senha = document.getElementById("input-usuario-senha").value;
  const perfil = document.getElementById("input-usuario-perfil").value;
  const ativo = document.getElementById("input-usuario-ativo").value === "true";
  const trocarSenha = document.getElementById("input-usuario-trocar-senha").checked;
  const master = document.getElementById("input-usuario-master").checked;
  const empresaId = document.getElementById("input-usuario-empresa").value;

  if (!nome || !email) return;

  const botaoSalvar = document.getElementById("btn-usuario-salvar");
  botaoSalvar.disabled = true;
  try {
    if (id) {
      const corpo = { nome, email, perfil, ativo, trocar_senha_no_proximo_acesso: trocarSenha, master };
      if (senha) corpo.senha = senha;
      if (!master) corpo.empresa_id = empresaId ? Number(empresaId) : null;
      const dados = await chamarApi(`/usuarios/${id}`, {
        method: "PUT",
        body: JSON.stringify(corpo),
      });
      mostrarToast(dados.mensagem, "success");
    } else {
      if (!senha) {
        mostrarToast("Informe uma senha para o novo usuário.", "error");
        botaoSalvar.disabled = false;
        return;
      }
      const corpo = { nome, email, perfil, ativo, senha, trocar_senha_no_proximo_acesso: trocarSenha, master };
      if (!master) corpo.empresa_id = empresaId ? Number(empresaId) : null;
      const dados = await chamarApi("/usuarios", {
        method: "POST",
        body: JSON.stringify(corpo),
      });
      mostrarToast(dados.mensagem, "success");
    }
    fecharModalUsuario();
    await carregarUsuarios();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  } finally {
    botaoSalvar.disabled = false;
  }
});

document.getElementById("tabela-usuarios").addEventListener("click", async (evento) => {
  const botao = evento.target.closest("button[data-acao-usuario]");
  if (!botao) return;

  const id = Number(botao.dataset.id);
  const acao = botao.dataset.acaoUsuario;

  if (acao === "editar") {
    try {
      const dados = await chamarApi(`/usuarios/${id}`);
      abrirModalUsuario(dados.usuario);
    } catch (erro) {
      mostrarToast(erro.message, "error");
    }
    return;
  }

  if (acao === "excluir") {
    const nome = botao.dataset.nome || "";
    const statusAtual = botao.dataset.ativo === "true";
    const acaoTexto = statusAtual ? "Desativar" : "Ativar";
    const confirmacao = confirm(`${acaoTexto} o usuário "${nome}"?`);
    if (!confirmacao) return;

    try {
      // Alterna o status ativo/inativo (PUT) em vez de excluir de fato
      const dados = await chamarApi(`/usuarios/${id}`, {
        method: "PUT",
        body: JSON.stringify({ ativo: !statusAtual }),
      });
      mostrarToast(dados.mensagem, "success");
      await carregarUsuarios();
    } catch (erro) {
      mostrarToast(erro.message, "error");
    }
  }
});

// ---------------------- EMPRESAS (MULTI-CNPJ) ----------------------

let cacheEmpresas = [];

function formatarCNPJ(cnpj) {
  if (!cnpj) return "—";
  const d = String(cnpj).replace(/\D/g, "");
  if (d.length !== 14) return cnpj;
  return `${d.slice(0,2)}.${d.slice(2,5)}.${d.slice(5,8)}/${d.slice(8,12)}-${d.slice(12)}`;
}

async function carregarEmpresas() {
  const corpo = document.getElementById("empresas-tbody");
  if (!corpo) return;
  corpo.innerHTML = '<tr><td colspan="7" class="empty-state">Carregando empresas...</td></tr>';

  try {
    const dados = await chamarApi("/empresas");
    cacheEmpresas = dados.empresas || [];
  } catch (erro) {
    corpo.innerHTML = `<tr><td colspan="7" class="empty-state">Erro ao carregar empresas.</td></tr>`;
    return;
  }

  if (!cacheEmpresas.length) {
    corpo.innerHTML = '<tr><td colspan="7" class="empty-state">Nenhuma empresa cadastrada.</td></tr>';
    return;
  }

  corpo.innerHTML = "";
  cacheEmpresas.forEach((empresa) => {
    const linha = document.createElement("tr");
    const cidadeUf = [empresa.cidade, empresa.estado].filter(Boolean).join(" - ");
    linha.innerHTML = `
      <td class="cell-nome"><strong>${empresa.nome_fantasia || "—"}</strong></td>
      <td>${formatarCNPJ(empresa.cnpj)}</td>
      <td>${empresa.razao_social || "—"}</td>
      <td>${cidadeUf || "—"}</td>
      <td>${empresa.usuarios ?? 0}</td>
      <td>
        <span class="badge ${empresa.ativo ? "badge-ativo" : "badge-inativo"}">${empresa.ativo ? "Ativa" : "Inativa"}</span>
      </td>
      <td class="col-acoes">
        <button type="button" class="btn-acao" data-acao-empresa="editar" data-id="${empresa.id}" title="Editar">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <button type="button" class="btn-acao btn-acao-danger" data-acao-empresa="inativar" data-id="${empresa.id}" data-nome="${empresa.nome_fantasia}" data-ativo="${empresa.ativo}" title="${empresa.ativo ? "Inativar" : "Ativar"}">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M10 11v6M14 11v6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
        </button>
      </td>
    `;
    corpo.appendChild(linha);
  });
}

function abrirModalEmpresa(empresa = null) {
  const overlay = document.getElementById("modal-empresa");
  document.getElementById("input-empresa-id").value = empresa ? empresa.id : "";
  document.getElementById("input-empresa-cnpj").value = empresa ? empresa.cnpj : "";
  document.getElementById("input-empresa-nome-fantasia").value = empresa ? empresa.nome_fantasia : "";
  document.getElementById("input-empresa-razao-social").value = empresa ? empresa.razao_social : "";
  document.getElementById("input-empresa-telefone").value = empresa ? empresa.telefone : "";
  document.getElementById("input-empresa-email").value = empresa ? empresa.email : "";
  document.getElementById("input-empresa-endereco").value = empresa ? empresa.endereco : "";
  document.getElementById("input-empresa-cidade").value = empresa ? empresa.cidade : "";
  document.getElementById("input-empresa-estado").value = empresa ? empresa.estado : "";
  document.getElementById("input-empresa-cep").value = empresa ? empresa.cep : "";
  document.getElementById("input-empresa-ativo").value = empresa ? String(empresa.ativo) : "true";
  document.getElementById("modal-empresa-titulo").textContent = empresa ? "Editar empresa" : "Nova empresa";
  overlay.hidden = false;
  setTimeout(() => document.getElementById("input-empresa-cnpj").focus(), 50);
}

function fecharModalEmpresa() {
  document.getElementById("modal-empresa").hidden = true;
  document.getElementById("form-empresa").reset();
  document.getElementById("input-empresa-id").value = "";
}

document.getElementById("btn-nova-empresa").addEventListener("click", () => abrirModalEmpresa());
document.getElementById("modal-empresa-fechar").addEventListener("click", fecharModalEmpresa);
document.getElementById("btn-empresa-cancelar").addEventListener("click", fecharModalEmpresa);
document.getElementById("modal-empresa").addEventListener("click", (evento) => {
  if (evento.target === evento.currentTarget) fecharModalEmpresa();
});
document.addEventListener("keydown", (evento) => {
  if (evento.key === "Escape" && !document.getElementById("modal-empresa").hidden) fecharModalEmpresa();
});

document.getElementById("form-empresa").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const id = document.getElementById("input-empresa-id").value;
  const corpo = {
    cnpj: document.getElementById("input-empresa-cnpj").value.trim(),
    nome_fantasia: document.getElementById("input-empresa-nome-fantasia").value.trim(),
    razao_social: document.getElementById("input-empresa-razao-social").value.trim(),
    telefone: document.getElementById("input-empresa-telefone").value.trim(),
    email: document.getElementById("input-empresa-email").value.trim(),
    endereco: document.getElementById("input-empresa-endereco").value.trim(),
    cidade: document.getElementById("input-empresa-cidade").value.trim(),
    estado: document.getElementById("input-empresa-estado").value.trim(),
    cep: document.getElementById("input-empresa-cep").value.trim(),
    ativo: document.getElementById("input-empresa-ativo").value === "true",
  };
  if (!corpo.cnpj || !corpo.nome_fantasia || !corpo.razao_social) return;

  const botaoSalvar = document.getElementById("btn-empresa-salvar");
  botaoSalvar.disabled = true;
  try {
    if (id) {
      const dados = await chamarApi(`/empresas/${id}`, { method: "PUT", body: JSON.stringify(corpo) });
      mostrarToast(dados.mensagem, "success");
    } else {
      const dados = await chamarApi("/empresas", { method: "POST", body: JSON.stringify(corpo) });
      mostrarToast(dados.mensagem, "success");
    }
    fecharModalEmpresa();
    await carregarEmpresas();
    atualizarSelectEmpresas();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  } finally {
    botaoSalvar.disabled = false;
  }
});

document.getElementById("empresas-tbody").addEventListener("click", async (evento) => {
  const botao = evento.target.closest("button[data-acao-empresa]");
  if (!botao) return;
  const id = Number(botao.dataset.id);
  const acao = botao.dataset.acaoEmpresa;

  if (acao === "editar") {
    const empresa = cacheEmpresas.find((e) => e.id === id);
    if (empresa) abrirModalEmpresa(empresa);
    return;
  }

  if (acao === "inativar") {
    const nome = botao.dataset.nome || "";
    const ativo = botao.dataset.ativo === "true";
    const texto = ativo ? "Inativar" : "Ativar";
    if (!confirm(`${texto} a empresa "${nome}"?`)) return;
    try {
      if (ativo) {
        const dados = await chamarApi(`/empresas/${id}/inativar`, { method: "POST" });
        mostrarToast(dados.mensagem, "success");
      } else {
        const dados = await chamarApi(`/empresas/${id}`, {
          method: "PUT",
          body: JSON.stringify({ ativo: true }),
        });
        mostrarToast(dados.mensagem, "success");
      }
      await carregarEmpresas();
      atualizarSelectEmpresas();
    } catch (erro) {
      mostrarToast(erro.message, "error");
    }
  }
});

// Preenche o select de empresas no cadastro de usuario
function atualizarSelectEmpresas() {
  const select = document.getElementById("input-usuario-empresa");
  if (!select) return;
  const atual = select.value;
  select.innerHTML = cacheEmpresas
    .filter((e) => e.ativo)
    .map((e) => `<option value="${e.id}">${e.nome_fantasia} - ${formatarCNPJ(e.cnpj)}</option>`)
    .join("");
  if (atual && cacheEmpresas.some((e) => String(e.id) === atual)) select.value = atual;
}

// Controle do checkbox master no modal de usuario
document.getElementById("input-usuario-master").addEventListener("change", () => {
  const master = document.getElementById("input-usuario-master").checked;
  document.getElementById("campo-usuario-empresa-label").style.display = master ? "none" : "";
  document.getElementById("input-usuario-empresa").style.display = master ? "none" : "";
});

// Trocar empresa (master)
async function abrirModalTrocarEmpresa() {
  const lista = document.getElementById("trocar-empresa-lista");
  const overlay = document.getElementById("modal-trocar-empresa");
  lista.innerHTML = '<p class="modal-hint">Carregando empresas...</p>';
  overlay.hidden = false;

  let empresas = [];
  try {
    const dados = await chamarApi("/empresas");
    empresas = (dados.empresas || []).filter((e) => e.ativo);
  } catch (erro) {
    lista.innerHTML = `<p class="modal-hint">Erro ao carregar empresas.</p>`;
    return;
  }

  const atual = sessionEmpresaId;
  lista.innerHTML = empresas.map((e) => `
    <div class="trocar-empresa-item ${atual === e.id ? "active" : ""}" data-trocar-empresa="${e.id}">
      <div class="trocar-empresa-info">
        <span class="trocar-empresa-nome">${e.nome_fantasia}</span>
        <span class="trocar-empresa-cnpj">${formatarCNPJ(e.cnpj)}</span>
      </div>
      ${atual === e.id ? '<span class="trocar-empresa-check">ATUAL</span>' : ""}
    </div>
  `).join("");

  lista.querySelectorAll("[data-trocar-empresa]").forEach((item) => {
    item.addEventListener("click", async () => {
      const id = Number(item.dataset.trocarEmpresa);
      try {
        const dados = await chamarApi("/empresa/trocar", {
          method: "POST",
          body: JSON.stringify({ empresa_id: id }),
        });
        mostrarToast(dados.mensagem, "success");
        sessionEmpresaId = id;
        overlay.hidden = true;
        if (dados.empresa) {
          const nomeNovo = dados.empresa.nome_fantasia || dados.empresa.razao_social;
          if (nomeNovo) aplicarNomeSistema(nomeNovo);
        }
        await carregarSessao();
        await carregarEmpresas();
        await carregarDashboard();
        await carregarPatio();
        if (document.querySelector(".view-active#view-usuarios")) {
          await carregarUsuarios();
        }
        await carregarConfiguracoes();
        recarregarAbaAtual();
      } catch (erro) {
        mostrarToast(erro.message, "error");
      }
    });
  });
}

document.getElementById("btn-trocar-empresa")?.addEventListener("click", abrirModalTrocarEmpresa);
document.getElementById("modal-trocar-empresa-fechar")?.addEventListener("click", () => {
  document.getElementById("modal-trocar-empresa").hidden = true;
});
document.getElementById("btn-trocar-empresa-cancelar")?.addEventListener("click", () => {
  document.getElementById("modal-trocar-empresa").hidden = true;
});
document.getElementById("modal-trocar-empresa")?.addEventListener("click", (evento) => {
  if (evento.target === evento.currentTarget) {
    document.getElementById("modal-trocar-empresa").hidden = true;
  }
});

// ---------------------- CLIENTES (MENSALISTAS) ----------------------

const CATEGORIAS_CLIENTE = {
  carro_pequeno: "Carro pequeno",
  carro_grande: "Carro grande",
  moto: "Moto",
  caminhonete: "Caminhonete",
};

async function carregarClientes() {
  const corpo = document.getElementById("tabela-clientes");
  const empty = document.getElementById("clientes-empty");
  corpo.innerHTML = "";

  let clientes;
  try {
    const dados = await chamarApi("/clientes");
    clientes = dados.clientes || [];
  } catch (erro) {
    mostrarToast(erro.message, "error");
    corpo.innerHTML = '<tr><td colspan="7" class="table-empty">Erro ao carregar clientes.</td></tr>';
    return;
  }

  if (!clientes.length) {
    corpo.innerHTML = "";
    empty.hidden = false;
    return;
  }
  empty.hidden = true;

  clientes.forEach((cliente) => {
    const linha = document.createElement("tr");

    const categoria = CATEGORIAS_CLIENTE[cliente.categoria] || cliente.categoria;
    const ativo = cliente.ativo;
    const vigencia = cliente.data_inicio && cliente.data_fim
      ? `${cliente.data_inicio} - ${cliente.data_fim}`
      : "-";

    linha.innerHTML = `
      <td class="cell-nome">${cliente.nome}</td>
      <td>${cliente.telefone}</td>
      <td><span class="vehicle-plate">${cliente.placa}</span></td>
      <td><span class="badge">${categoria}</span></td>
      <td>${vigencia}</td>
      <td>
        <span class="badge ${ativo ? "badge-ativo" : "badge-inativo"}">${ativo ? "Ativo" : "Inativo"}</span>
      </td>
      <td class="col-acoes">
        <button type="button" class="btn-acao" data-acao-cliente="editar" data-id="${cliente.id}" title="Editar">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <button type="button" class="btn-acao btn-acao-danger" data-acao-cliente="excluir" data-id="${cliente.id}" data-nome="${cliente.nome}" data-ativo="${ativo}" title="${ativo ? "Desativar" : "Ativar"}">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M10 11v6M14 11v6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
        </button>
      </td>
    `;

    corpo.appendChild(linha);
  });
}

function abrirModalCliente(cliente = null) {
  const overlay = document.getElementById("modal-cliente");
  document.getElementById("input-cliente-id").value = cliente ? cliente.id : "";
  document.getElementById("input-cliente-nome").value = cliente ? cliente.nome : "";
  document.getElementById("input-cliente-telefone").value = cliente ? cliente.telefone : "";
  document.getElementById("input-cliente-placa").value = cliente ? cliente.placa : "";
  document.getElementById("input-cliente-categoria").value = cliente ? cliente.categoria : "carro_pequeno";
  document.getElementById("input-cliente-data-inicio").value = cliente ? cliente.data_inicio : "";
  document.getElementById("input-cliente-data-fim").value = cliente ? cliente.data_fim : "";
  document.getElementById("modal-cliente-titulo").textContent = cliente ? "Editar cliente" : "Novo cliente";
  overlay.hidden = false;
  setTimeout(() => document.getElementById("input-cliente-nome").focus(), 50);
}

function fecharModalCliente() {
  document.getElementById("modal-cliente").hidden = true;
  document.getElementById("form-cliente").reset();
  document.getElementById("input-cliente-id").value = "";
}

document.getElementById("btn-novo-cliente").addEventListener("click", () => abrirModalCliente());

// Preenche automaticamente a data de fim da vigencia (+30 dias)
// quando o usuario informa a data de inicio (apenas em novo cadastro).
document.getElementById("input-cliente-data-inicio").addEventListener("change", () => {
  const inicioInput = document.getElementById("input-cliente-data-inicio");
  const fimInput = document.getElementById("input-cliente-data-fim");
  const idCliente = document.getElementById("input-cliente-id").value;

  // Soh preenche automaticamente em novo cadastro e se o fim estiver vazio
  if (!idCliente && !fimInput.value.trim()) {
    const partes = inicioInput.value.trim().split("/");
    if (partes.length === 3 && partes[0] && partes[1] && partes[2]) {
      const dia = parseInt(partes[0], 10);
      const mes = parseInt(partes[1], 10) - 1;
      const ano = parseInt(partes[2], 10);
      const inicio = new Date(ano, mes, dia);
      if (!isNaN(inicio.getTime())) {
        const fim = new Date(inicio);
        fim.setDate(fim.getDate() + 30);
        fimInput.value = String(fim.getDate()).padStart(2, "0") + "/" +
          String(fim.getMonth() + 1).padStart(2, "0") + "/" + fim.getFullYear();
      }
    }
  }
});

document.getElementById("modal-cliente-fechar").addEventListener("click", fecharModalCliente);
document.getElementById("btn-cliente-cancelar").addEventListener("click", fecharModalCliente);

document.getElementById("modal-cliente").addEventListener("click", (evento) => {
  if (evento.target === evento.currentTarget) fecharModalCliente();
});

document.addEventListener("keydown", (evento) => {
  if (evento.key === "Escape" && !document.getElementById("modal-cliente").hidden) fecharModalCliente();
});

document.getElementById("form-cliente").addEventListener("submit", async (evento) => {
  evento.preventDefault();

  const id = document.getElementById("input-cliente-id").value;
  const nome = document.getElementById("input-cliente-nome").value.trim();
  const telefone = document.getElementById("input-cliente-telefone").value.trim();
  const placa = document.getElementById("input-cliente-placa").value.trim();
  const categoria = document.getElementById("input-cliente-categoria").value;
  const dataInicio = document.getElementById("input-cliente-data-inicio").value.trim();
  const dataFim = document.getElementById("input-cliente-data-fim").value.trim();

  if (!nome || !telefone || !placa || !dataInicio || !dataFim) return;

  const botaoSalvar = document.getElementById("btn-cliente-salvar");
  botaoSalvar.disabled = true;
  try {
    const payload = { nome, telefone, placa, categoria, data_inicio: dataInicio, data_fim: dataFim };
    if (id) {
      const dados = await chamarApi(`/clientes/${id}`, { method: "PUT", body: JSON.stringify(payload) });
      mostrarToast(dados.mensagem, "success");
    } else {
      const dados = await chamarApi("/clientes", { method: "POST", body: JSON.stringify(payload) });
      mostrarToast(dados.mensagem, "success");
    }
    fecharModalCliente();
    await carregarClientes();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  } finally {
    botaoSalvar.disabled = false;
  }
});

document.getElementById("tabela-clientes").addEventListener("click", async (evento) => {
  const botao = evento.target.closest("button[data-acao-cliente]");
  if (!botao) return;

  const id = Number(botao.dataset.id);
  const acao = botao.dataset.acaoCliente;

  if (acao === "editar") {
    try {
      const dados = await chamarApi(`/clientes/${id}`);
      abrirModalCliente(dados.cliente);
    } catch (erro) {
      mostrarToast(erro.message, "error");
    }
    return;
  }

  if (acao === "excluir") {
    const nome = botao.dataset.nome || "";
    const statusAtual = botao.dataset.ativo === "true";
    const acaoTexto = statusAtual ? "Desativar" : "Ativar";
    const confirmacao = confirm(`${acaoTexto} o cliente "${nome}"?`);
    if (!confirmacao) return;

    try {
      // Alterna o status ativo/inativo (PUT) em vez de excluir de fato
      const dados = await chamarApi(`/clientes/${id}`, {
        method: "PUT",
        body: JSON.stringify({ ativo: !statusAtual }),
      });
      mostrarToast(dados.mensagem, "success");
      await carregarClientes();
    } catch (erro) {
      mostrarToast(erro.message, "error");
    }
  }
});

// ---------------------- CONFIGURACOES & PREFERENCIAS ----------------------

function aplicarNomeSistema(nome) {
  const nomeFinal = (nome || "").trim() || "Estaciona Parking";
  const elSidebar = document.getElementById("nome-sistema");
  const elRodape = document.getElementById("nome-sistema-rodape");
  const elTitulo = document.getElementById("titulo-sistema");
  if (elSidebar) elSidebar.textContent = nomeFinal;
  if (elRodape) elRodape.textContent = nomeFinal;
  if (elTitulo) elTitulo.textContent = `${nomeFinal} - Controle por ticket`;
}

// Mascaras de entrada
function mascararCNPJ(valor) {
  const digits = String(valor || "").replace(/\D/g, "").slice(0, 14);
  return digits
    .replace(/^(\d{2})(\d)/, "$1.$2")
    .replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3")
    .replace(/\.(\d{3})(\d)/, ".$1/$2")
    .replace(/(\d{4})(\d)/, "$1-$2");
}

function mascararTelefone(valor) {
  const digits = String(valor || "").replace(/\D/g, "").slice(0, 11);
  if (digits.length <= 10) {
    return digits
      .replace(/^(\d{2})(\d)/, "($1) $2")
      .replace(/(\d{4})(\d)/, "$1-$2");
  }
  return digits
    .replace(/^(\d{2})(\d)/, "($1) $2")
    .replace(/(\d{5})(\d)/, "$1-$2");
}

function mascararCEP(valor) {
  const digits = String(valor || "").replace(/\D/g, "").slice(0, 8);
  return digits.replace(/^(\d{5})(\d)/, "$1-$2");
}

function atualizarAlertaVagas() {
  const total = Number(document.getElementById("input-config-total-vagas")?.value || 0);
  const carro = Number(document.getElementById("input-config-vagas-carro")?.value || 0);
  const moto = Number(document.getElementById("input-config-vagas-moto")?.value || 0);
  const cg = Number(document.getElementById("input-config-vagas-carro-grande")?.value || 0);
  const cam = Number(document.getElementById("input-config-vagas-caminhonete")?.value || 0);

  const soma = carro + moto + cg + cam;
  const elAlerta = document.getElementById("alerta-soma-vagas");
  const elTexto = document.getElementById("texto-soma-vagas");
  if (!elAlerta || !elTexto) return;

  if (soma > total && total > 0) {
    elAlerta.classList.add("alerta-aviso");
    elTexto.innerHTML = `⚠️ <strong>Atenção:</strong> A soma das categorias reservadas (${soma} vagas) excede a capacidade total do pátio (${total} vagas)!`;
  } else if (soma > 0) {
    elAlerta.classList.remove("alerta-aviso");
    elTexto.innerHTML = `✓ Capacidade total: <strong>${total}</strong> vagas (Categorias reservadas: <strong>${soma}</strong> / Livres para rotativo comum: <strong>${Math.max(0, total - soma)}</strong>)`;
  } else {
    elAlerta.classList.remove("alerta-aviso");
    elTexto.innerHTML = `✓ Capacidade total: <strong>${total}</strong> vagas (nenhuma restrição por categoria cadastrada)`;
  }
}

async function atualizarDiagnosticoSistema(dados) {
  const totalVagas = dados?.total_vagas ?? (cacheConfiguracoes?.total_vagas || 0);
  const elTotal = document.getElementById("diag-vagas-total");
  const elOcupadas = document.getElementById("diag-vagas-ocupadas");
  const elLivres = document.getElementById("diag-vagas-livres");

  if (elTotal) elTotal.textContent = `${totalVagas} vagas`;
  try {
    const dash = await chamarApi("/dashboard/resumo");
    if (dash) {
      const ocup = dash.no_patio_agora ?? 0;
      if (elOcupadas) elOcupadas.textContent = `${ocup} veículos`;
      if (elLivres) elLivres.textContent = `${Math.max(0, totalVagas - ocup)} livres`;
    }
  } catch (e) {
    // Silencioso se nao carregar dashboard
  }
}

function desenharBarcodePreview() {
  const svg = document.getElementById("ticket-preview-barcode");
  if (!svg) return;
  svg.innerHTML = `
    <rect x="2" y="0" width="3" height="40" fill="#111" />
    <rect x="7" y="0" width="2" height="40" fill="#111" />
    <rect x="11" y="0" width="4" height="40" fill="#111" />
    <rect x="17" y="0" width="1" height="40" fill="#111" />
    <rect x="20" y="0" width="3" height="40" fill="#111" />
    <rect x="25" y="0" width="5" height="40" fill="#111" />
    <rect x="32" y="0" width="2" height="40" fill="#111" />
    <rect x="36" y="0" width="4" height="40" fill="#111" />
    <rect x="42" y="0" width="2" height="40" fill="#111" />
    <rect x="46" y="0" width="6" height="40" fill="#111" />
    <rect x="54" y="0" width="2" height="40" fill="#111" />
    <rect x="58" y="0" width="3" height="40" fill="#111" />
    <rect x="63" y="0" width="5" height="40" fill="#111" />
    <rect x="70" y="0" width="2" height="40" fill="#111" />
    <rect x="74" y="0" width="4" height="40" fill="#111" />
    <rect x="80" y="0" width="3" height="40" fill="#111" />
    <rect x="85" y="0" width="2" height="40" fill="#111" />
    <rect x="89" y="0" width="5" height="40" fill="#111" />
    <rect x="96" y="0" width="3" height="40" fill="#111" />
    <rect x="101" y="0" width="2" height="40" fill="#111" />
  `;
  svg.setAttribute("viewBox", "0 0 106 40");
}

function atualizarPreviewTicket() {
  const nome = document.getElementById("input-config-nome")?.value.trim() || "Estaciona Parking";
  const cnpj = document.getElementById("input-config-cnpj")?.value.trim() || "";
  const endereco = document.getElementById("input-config-endereco")?.value.trim() || "";
  const telefone = document.getElementById("input-config-telefone")?.value.trim() || "";
  const cabecalho = document.getElementById("input-config-cabecalho-ticket")?.value.trim() || "";
  const rodape = document.getElementById("input-config-rodape-ticket")?.value.trim() || "";

  const formato = document.getElementById("input-config-ticket-formato")?.value || "80mm";
  const exibirCnpj = document.getElementById("input-config-ticket-cnpj")?.checked !== false;
  const exibirContato = document.getElementById("input-config-ticket-contato")?.checked !== false;
  const exibirBarcode = document.getElementById("input-config-ticket-barcode")?.checked !== false;

  const elPreview = document.getElementById("ticket-preview");
  if (elPreview) {
    elPreview.classList.remove("papel-58mm", "papel-a4");
    if (formato === "58mm") elPreview.classList.add("papel-58mm");
    else if (formato === "A4") elPreview.classList.add("papel-a4");
  }

  const elNome = document.getElementById("ticket-preview-nome");
  if (elNome) elNome.textContent = nome;

  const elCnpj = document.getElementById("ticket-preview-cnpj");
  if (elCnpj) {
    elCnpj.textContent = cnpj ? `CNPJ: ${cnpj}` : "";
    elCnpj.style.display = (exibirCnpj && cnpj) ? "block" : "none";
  }

  const elEndereco = document.getElementById("ticket-preview-endereco");
  if (elEndereco) {
    elEndereco.textContent = endereco;
    elEndereco.style.display = (exibirContato && endereco) ? "block" : "none";
  }

  const elTelefone = document.getElementById("ticket-preview-telefone");
  if (elTelefone) {
    elTelefone.textContent = telefone ? `Tel: ${telefone}` : "";
    elTelefone.style.display = (exibirContato && telefone) ? "block" : "none";
  }

  const barcodeBox = document.getElementById("ticket-preview-barcode-box");
  if (barcodeBox) {
    barcodeBox.style.display = exibirBarcode ? "block" : "none";
    if (exibirBarcode) desenharBarcodePreview();
  }

  const headerEl = document.querySelector(".ticket-preview-header");
  if (headerEl) {
    const cabecalhoExistente = headerEl.querySelector(".ticket-preview-custom-header");
    if (cabecalhoExistente) cabecalhoExistente.remove();
    if (cabecalho) {
      const div = document.createElement("div");
      div.className = "ticket-preview-custom-header";
      div.style.whiteSpace = "pre-line";
      div.style.marginTop = "6px";
      div.style.lineHeight = "1.4";
      div.textContent = cabecalho;
      headerEl.appendChild(div);
    }
  }

  const elRodape = document.getElementById("ticket-preview-rodape");
  if (elRodape) elRodape.textContent = rodape;
}

async function carregarConfiguracoes() {
  try {
    const dados = await chamarApi("/configuracoes");
    cacheConfiguracoes = dados;
    carregarTiposVeiculo();

    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.value = val ?? "";
    };
    const setChk = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.checked = !!val;
    };

    // 1. Identificacao & Empresa
    setVal("input-config-nome", dados.nome_estacionamento);
    setVal("input-config-cnpj", dados.cnpj);
    setVal("input-config-telefone", dados.telefone);
    setVal("input-config-endereco", dados.endereco);
    setVal("input-config-cidade", dados.cidade);
    setVal("input-config-estado", dados.estado);
    setVal("input-config-cep", dados.cep);

    // 2. Horarios de funcionamento
    setVal("input-config-horario-abertura", dados.horario_abertura);
    setVal("input-config-horario-fechamento", dados.horario_fechamento);

    // 3. Vagas & Patio
    setVal("input-config-total-vagas", dados.total_vagas);
    setVal("input-config-vagas-carro", dados.vagas_carro ?? 0);
    setVal("input-config-vagas-moto", dados.vagas_moto ?? 0);
    setVal("input-config-vagas-carro-grande", dados.vagas_carro_grande ?? 0);
    setVal("input-config-vagas-caminhonete", dados.vagas_caminhonete ?? 0);
    setChk("input-config-bloquear-sem-vaga", dados.bloquear_sem_vaga);
    setChk("input-config-exigir-observacao", dados.exigir_observacao !== false);

    // 4. Recebimentos PIX
    setVal("input-config-pix-tipo", dados.pix_tipo);
    setVal("input-config-pix-chave", dados.pix_chave);

    // 5. Cupom & Impressao
    setVal("input-config-cabecalho-ticket", dados.cabecalho_ticket);
    setVal("input-config-rodape-ticket", dados.rodape_ticket);
    setVal("input-config-ticket-formato", dados.ticket_formato_papel || "80mm");
    setChk("input-config-ticket-cnpj", dados.ticket_exibir_cnpj !== false);
    setChk("input-config-ticket-contato", dados.ticket_exibir_contato !== false);
    setChk("input-config-ticket-barcode", dados.ticket_exibir_codigo_barras !== false);

    aplicarNomeSistema(dados.nome_estacionamento);
    atualizarAlertaVagas();
    atualizarPreviewTicket();
    atualizarDiagnosticoSistema(dados);
  } catch (erro) {
    console.warn("Nao foi possivel carregar configuracoes:", erro.message);
  }

  // Carrega a tabela de precos (regras avancadas e sincronizacao)
  try {
    const dadosTabela = await chamarApi("/tabela-precos");
    const tp = dadosTabela.tabela_precos || {};
    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.value = val ?? "";
    };

    setVal("input-config-tp-fracionamento", tp.fracionamento_minutos ?? 60);
    setVal("input-config-tp-tarifa-minima", tp.tarifa_minima);
    setVal("input-config-tp-meia-min", tp.meia_estadia_minutos);
    setVal("input-config-tp-meia-valor", tp.meia_estadia_valor);
    setVal("input-config-tp-tolerancia", tp.tolerancia_minutos);
    setVal("input-config-tp-noturno", tp.valor_noturno);
    setVal("input-config-tp-fim-semana", tp.fim_semana);
    setVal("input-config-tp-feriados", tp.feriados);
    setVal("input-config-tp-ticket-perdido", tp.valor_ticket_perdido);
    setVal("input-config-tp-pernoite", tp.pernoite_valor);
    setVal("input-config-tp-pernoite-horas", tp.pernoite_a_partir_horas);

    // Carro (valores sincronizados com fallback da configuracao)
    setVal("input-config-tp-carro-primeira", tp.primeira_hora ?? cacheConfiguracoes?.valor_primeira_hora ?? "");
    setVal("input-config-tp-carro-adicional", tp.hora_adicional ?? cacheConfiguracoes?.valor_hora_adicional ?? "");
    setVal("input-config-tp-carro-diaria", tp.diaria);
    setVal("input-config-tp-carro-minuto", tp.valor_minuto);
    setVal("input-config-tp-carro-max", tp.valor_maximo_diario);
    setVal("input-config-tp-carro-mensal", tp.mensal ?? cacheConfiguracoes?.valor_mensal ?? "");

    // Moto
    setVal("input-config-tp-moto-primeira", tp.moto_primeira_hora);
    setVal("input-config-tp-moto-adicional", tp.moto_hora_adicional);
    setVal("input-config-tp-moto-diaria", tp.moto_diaria);
    setVal("input-config-tp-moto-minuto", tp.moto_valor_minuto);
    setVal("input-config-tp-moto-max", tp.moto_valor_maximo_diario);
    setVal("input-config-tp-moto-mensal", tp.moto_mensal);

    // Carro Grande
    setVal("input-config-tp-cg-primeira", tp.carro_grande_primeira_hora);
    setVal("input-config-tp-cg-adicional", tp.carro_grande_hora_adicional);
    setVal("input-config-tp-cg-diaria", tp.carro_grande_diaria);
    setVal("input-config-tp-cg-minuto", tp.carro_grande_valor_minuto);
    setVal("input-config-tp-cg-max", tp.carro_grande_valor_maximo_diario);
    setVal("input-config-tp-cg-mensal", tp.carro_grande_mensal);

    // Caminhonete
    setVal("input-config-tp-cam-primeira", tp.caminhonete_primeira_hora);
    setVal("input-config-tp-cam-adicional", tp.caminhonete_hora_adicional);
    setVal("input-config-tp-cam-diaria", tp.caminhonete_diaria);
    setVal("input-config-tp-cam-minuto", tp.caminhonete_valor_minuto);
    setVal("input-config-tp-cam-max", tp.caminhonete_valor_maximo_diario);
    setVal("input-config-tp-cam-mensal", tp.caminhonete_mensal);
  } catch (erro) {
    // tabela de precos pode nao existir ainda; ignora silenciosamente
  }
}

// Atualiza preview do ticket e alertas ao digitar
const inputCnpjCfg = document.getElementById("input-config-cnpj");
if (inputCnpjCfg) {
  inputCnpjCfg.addEventListener("input", (e) => {
    e.target.value = mascararCNPJ(e.target.value);
    atualizarPreviewTicket();
  });
}
const inputTelefoneCfg = document.getElementById("input-config-telefone");
if (inputTelefoneCfg) {
  inputTelefoneCfg.addEventListener("input", (e) => {
    e.target.value = mascararTelefone(e.target.value);
    atualizarPreviewTicket();
  });
}
const inputCepCfg = document.getElementById("input-config-cep");
if (inputCepCfg) {
  inputCepCfg.addEventListener("input", (e) => {
    e.target.value = mascararCEP(e.target.value);
  });
}
const inputEstadoCfg = document.getElementById("input-config-estado");
if (inputEstadoCfg) {
  inputEstadoCfg.addEventListener("input", (e) => {
    e.target.value = (e.target.value || "").toUpperCase().slice(0, 2);
  });
}

// Alerta dinâmico de vagas
["input-config-total-vagas", "input-config-vagas-carro", "input-config-vagas-moto",
 "input-config-vagas-carro-grande", "input-config-vagas-caminhonete"].forEach((id) => {
  const el = document.getElementById(id);
  if (el) el.addEventListener("input", atualizarAlertaVagas);
});

// Atualizacao da preview de ticket
["input-config-nome", "input-config-endereco", "input-config-cabecalho-ticket",
 "input-config-rodape-ticket", "input-config-ticket-formato", "input-config-ticket-cnpj",
 "input-config-ticket-contato", "input-config-ticket-barcode"].forEach((id) => {
  const el = document.getElementById(id);
  if (el) {
    el.addEventListener("input", atualizarPreviewTicket);
    el.addEventListener("change", atualizarPreviewTicket);
  }
});

// Botao de backup na aba de sistema
const btnSistemaBackup = document.getElementById("btn-sistema-backup");
if (btnSistemaBackup) {
  btnSistemaBackup.addEventListener("click", () => {
    window.open("/api/backup", "_blank");
  });
}

document.getElementById("form-configuracoes").addEventListener("submit", async (evento) => {
  evento.preventDefault();

  const botaoSalvar = evento.target.querySelector(".btn-salvar-config");
  if (botaoSalvar) botaoSalvar.disabled = true;

  const valorPrimeira = Number(document.getElementById("input-config-tp-carro-primeira")?.value || 0);
  const valorAdicional = Number(document.getElementById("input-config-tp-carro-adicional")?.value || 0);
  const valorMensal = Number(document.getElementById("input-config-tp-carro-mensal")?.value || 0);

  const payload = {
    nome_estacionamento: document.getElementById("input-config-nome")?.value.trim() || "",
    cnpj: document.getElementById("input-config-cnpj")?.value.trim() || "",
    telefone: document.getElementById("input-config-telefone")?.value.trim() || "",
    endereco: document.getElementById("input-config-endereco")?.value.trim() || "",
    cidade: document.getElementById("input-config-cidade")?.value.trim() || "",
    estado: (document.getElementById("input-config-estado")?.value || "").trim().toUpperCase(),
    cep: document.getElementById("input-config-cep")?.value.trim() || "",
    horario_abertura: document.getElementById("input-config-horario-abertura")?.value.trim() || "",
    horario_fechamento: document.getElementById("input-config-horario-fechamento")?.value.trim() || "",
    total_vagas: Number(document.getElementById("input-config-total-vagas")?.value || 1),
    vagas_carro: Number(document.getElementById("input-config-vagas-carro")?.value || 0),
    vagas_moto: Number(document.getElementById("input-config-vagas-moto")?.value || 0),
    vagas_carro_grande: Number(document.getElementById("input-config-vagas-carro-grande")?.value || 0),
    vagas_caminhonete: Number(document.getElementById("input-config-vagas-caminhonete")?.value || 0),
    valor_primeira_hora: valorPrimeira,
    valor_hora_adicional: valorAdicional,
    valor_mensal: valorMensal,
    cabecalho_ticket: document.getElementById("input-config-cabecalho-ticket")?.value.trim() || "",
    rodape_ticket: document.getElementById("input-config-rodape-ticket")?.value.trim() || "",
    ticket_formato_papel: document.getElementById("input-config-ticket-formato")?.value || "80mm",
    ticket_exibir_cnpj: document.getElementById("input-config-ticket-cnpj")?.checked !== false,
    ticket_exibir_contato: document.getElementById("input-config-ticket-contato")?.checked !== false,
    ticket_exibir_codigo_barras: document.getElementById("input-config-ticket-barcode")?.checked !== false,
    bloquear_sem_vaga: !!document.getElementById("input-config-bloquear-sem-vaga")?.checked,
    exigir_observacao: !!document.getElementById("input-config-exigir-observacao")?.checked,
    pix_tipo: document.getElementById("input-config-pix-tipo")?.value.trim() || "",
    pix_chave: document.getElementById("input-config-pix-chave")?.value.trim() || "",
  };

  try {
    const dados = await chamarApi("/configuracoes", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    await salvarTabelaPrecos();
    mostrarToast(dados.mensagem, "success");
    await carregarConfiguracoes();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  } finally {
    if (botaoSalvar) botaoSalvar.disabled = false;
  }
});

// Salva a tabela de precos (regras avancadas) quando houver valores preenchidos
async function salvarTabelaPrecos() {
  const campos = {
    fracionamento_minutos: "input-config-tp-fracionamento",
    tarifa_minima: "input-config-tp-tarifa-minima",
    meia_estadia_minutos: "input-config-tp-meia-min",
    meia_estadia_valor: "input-config-tp-meia-valor",
    tolerancia_minutos: "input-config-tp-tolerancia",
    valor_noturno: "input-config-tp-noturno",
    fim_semana: "input-config-tp-fim-semana",
    feriados: "input-config-tp-feriados",
    valor_ticket_perdido: "input-config-tp-ticket-perdido",
    pernoite_valor: "input-config-tp-pernoite",
    pernoite_a_partir_horas: "input-config-tp-pernoite-horas",
    // Carro (campos padrao)
    primeira_hora: "input-config-tp-carro-primeira",
    hora_adicional: "input-config-tp-carro-adicional",
    diaria: "input-config-tp-carro-diaria",
    valor_minuto: "input-config-tp-carro-minuto",
    valor_maximo_diario: "input-config-tp-carro-max",
    mensal: "input-config-tp-carro-mensal",
    // Moto
    moto_primeira_hora: "input-config-tp-moto-primeira",
    moto_hora_adicional: "input-config-tp-moto-adicional",
    moto_diaria: "input-config-tp-moto-diaria",
    moto_valor_minuto: "input-config-tp-moto-minuto",
    moto_valor_maximo_diario: "input-config-tp-moto-max",
    moto_mensal: "input-config-tp-moto-mensal",
    // Carro grande
    carro_grande_primeira_hora: "input-config-tp-cg-primeira",
    carro_grande_hora_adicional: "input-config-tp-cg-adicional",
    carro_grande_diaria: "input-config-tp-cg-diaria",
    carro_grande_valor_minuto: "input-config-tp-cg-minuto",
    carro_grande_valor_maximo_diario: "input-config-tp-cg-max",
    carro_grande_mensal: "input-config-tp-cg-mensal",
    // Caminhonete
    caminhonete_primeira_hora: "input-config-tp-cam-primeira",
    caminhonete_hora_adicional: "input-config-tp-cam-adicional",
    caminhonete_diaria: "input-config-tp-cam-diaria",
    caminhonete_valor_minuto: "input-config-tp-cam-minuto",
    caminhonete_valor_maximo_diario: "input-config-tp-cam-max",
    caminhonete_mensal: "input-config-tp-cam-mensal",
  };
  const payload = {};
  let temValor = false;
  for (const [chave, idCampo] of Object.entries(campos)) {
    const el = document.getElementById(idCampo);
    if (el && el.value !== "") {
      payload[chave] = Number(el.value);
      temValor = true;
    }
  }
  if (!temValor) return;
  try {
    const dados = await chamarApi("/tabela-precos");
    const tp = dados.tabela_precos || {};
    if (tp.id) {
      await chamarApi(`/tabela-precos/${tp.id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    }
  } catch (erro) {
    // tabela de precos pode nao existir; ignora silenciosamente
  }
}

// Tabs de tipo de veiculo na tabela de precos
document.querySelectorAll("#tp-tipo-tabs .tp-tipo-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll("#tp-tipo-tabs .tp-tipo-tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    const tipo = tab.dataset.tpTipo;
    document.querySelectorAll(".tp-tipo-pane").forEach((pane) => {
      pane.hidden = pane.dataset.tpPane !== tipo;
    });
  });
});

// Tabs das configuracoes
document.querySelectorAll("#tabs-config .tab").forEach((botaoTab) => {
  botaoTab.addEventListener("click", () => {
    document.querySelectorAll("#tabs-config .tab").forEach((t) => t.classList.remove("active"));
    botaoTab.classList.add("active");
    const aba = botaoTab.dataset.configTab;
    document.querySelectorAll(".config-tab-pane").forEach((pane) => {
      pane.hidden = pane.dataset.configPane !== aba;
    });
  });
});

// Botao "Gerenciar formas de pagamento" -> vai para a view de formas
const btnIrFormas = document.getElementById("btn-config-ir-formas");
if (btnIrFormas) {
  btnIrFormas.addEventListener("click", () => {
    mostrarView("view-formas-pagamento");
  });
}

// ---------------------- TIPOS DE VEICULO ----------------------

const TIPOS_VEICULO_SISTEMA = ["Carro", "Moto", "Carro Grande", "Caminhonete"];
let tiposVeiculoCache = [];

async function carregarTiposVeiculo() {
  try {
    const dados = await chamarApi("/tipos-veiculo");
    tiposVeiculoCache = dados.tipos_veiculo || [];
    renderizarTiposVeiculo(tiposVeiculoCache);
  } catch (erro) {
    // Silencioso: a aba apenas fica vazia se o usuario nao puder ver
    tiposVeiculoCache = [];
    renderizarTiposVeiculo([]);
  }
}

function renderizarTiposVeiculo(tipos) {
  const corpo = document.getElementById("tabela-tipos-veiculo");
  const empty = document.getElementById("tipos-veiculo-empty");
  corpo.innerHTML = "";

  // Quem nao pode editar configuracoes nao ve os botoes de acao
  const podeEditar = !perfilUsuarioAtual || perfilUsuarioAtual === "admin" ||
    ((permissoesMatriz && permissoesMatriz["configuracoes"] && permissoesMatriz["configuracoes"][perfilUsuarioAtual] || []).includes("editar"));

  if (!tipos.length) {
    empty.hidden = false;
  } else {
    empty.hidden = true;
    tipos.forEach((tipo) => {
      const linha = document.createElement("tr");
      const ehSistema = TIPOS_VEICULO_SISTEMA.includes(tipo.nome);
      const origem = ehSistema
        ? '<span class="badge">Sistema</span>'
        : `<span class="badge ${tipo.ativo ? "badge-ativo" : "badge-inativo"}">${tipo.ativo ? "Personalizado" : "Inativo"}</span>`;
      const fmt = (v) => (v && Number(v) > 0 ? `R$ ${Number(v).toFixed(2)}` : '<em style="color:var(--color-text-light)">herda carro</em>');

      const iconeEditar = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
      const iconeAtivar = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M18.36 6.64a9 9 0 1 1-12.72 0" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 2v10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';
      const iconeExcluir = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M10 11v6M14 11v6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';

      let acoes;
      if (!podeEditar) {
        acoes = '<em style="color:var(--color-text-light)">—</em>';
      } else if (ehSistema) {
        acoes = `
          <button type="button" class="btn-acao" data-acao-tipo-veiculo="editar" data-id="${tipo.id}" title="Editar preços (nome e exclusão fixos — tipo do sistema)">
            ${iconeEditar}
          </button>
          <button type="button" class="btn-acao" disabled title="Tipos do sistema não podem ser inativados (alimentam vagas e cobrança)">
            ${iconeAtivar}
          </button>
          <button type="button" class="btn-acao" disabled title="Tipos do sistema não podem ser excluídos">
            ${iconeExcluir}
          </button>
        `;
      } else {
        acoes = `
          <button type="button" class="btn-acao" data-acao-tipo-veiculo="editar" data-id="${tipo.id}" title="Editar">
            ${iconeEditar}
          </button>
          <button type="button" class="btn-acao" data-acao-tipo-veiculo="alternar" data-id="${tipo.id}" data-ativo="${tipo.ativo}" title="${tipo.ativo ? "Inativar" : "Ativar"}">
            ${iconeAtivar}
          </button>
          <button type="button" class="btn-acao btn-acao-danger" data-acao-tipo-veiculo="excluir" data-id="${tipo.id}" data-nome="${escaparHtml(tipo.nome)}" title="Excluir">
            ${iconeExcluir}
          </button>
        `;
      }

      linha.innerHTML = `
        <td><strong>${escaparHtml(tipo.nome)}</strong></td>
        <td>${fmt(tipo.primeira_hora)}</td>
        <td>${fmt(tipo.hora_adicional)}</td>
        <td>${fmt(tipo.diaria)}</td>
        <td>${fmt(tipo.mensal)}</td>
        <td>${origem}</td>
        <td class="col-acoes">${acoes}</td>
      `;
      corpo.appendChild(linha);
    });
  }

  atualizarSelectTiposEntrada(tipos);
}

document.getElementById("tabela-tipos-veiculo").addEventListener("click", async (evento) => {
  const botao = evento.target.closest("[data-acao-tipo-veiculo]");
  if (!botao) return;
  const acao = botao.dataset.acaoTipoVeiculo;
  const { id, nome } = botao.dataset;

  if (acao === "editar") {
    abrirModalTipoVeiculo(Number(id));
    return;
  }

  if (acao === "alternar") {
    const ativo = botao.dataset.ativo === "true";
    try {
      const dados = await chamarApi(`/tipos-veiculo/${id}/alternar-ativo`, { method: "POST" });
      mostrarToast(dados.mensagem || "Status atualizado!", "success");
      await carregarTiposVeiculo();
    } catch (erro) {
      mostrarToast(erro.message, "error");
    }
    return;
  }

  if (acao === "excluir") {
    if (!confirm(`Excluir o tipo de veiculo "${nome}"? Os tickets existentes nao sao afetados.`)) return;
    try {
      const dados = await chamarApi(`/tipos-veiculo/${id}`, { method: "DELETE" });
      mostrarToast(dados.mensagem || "Tipo de veiculo excluido!", "success");
      await carregarTiposVeiculo();
    } catch (erro) {
      mostrarToast(erro.message, "error");
    }
  }
});

// ---------------------- MODAL EDITAR TIPO DE VEICULO ----------------------

function abrirModalTipoVeiculo(id) {
  const tipo = tiposVeiculoCache.find((t) => t.id === id);
  if (!tipo) return;
  const ehSistema = TIPOS_VEICULO_SISTEMA.includes(tipo.nome);
  document.getElementById("modal-tipo-veiculo-titulo").textContent =
    ehSistema ? `Editar preços — ${tipo.nome}` : "Editar tipo de veículo";
  document.getElementById("modal-tipo-veiculo-descricao").textContent = ehSistema
    ? "Consulte ou ajuste os valores cobrados para este tipo de veículo."
    : "Atualize o nome e os valores cobrados para este tipo de veículo.";
  document.getElementById("modal-tipo-veiculo-aviso").hidden = !ehSistema;
  document.getElementById("input-tipo-veiculo-edit-id").value = tipo.id;
  document.getElementById("input-tipo-veiculo-edit-nome").value = tipo.nome;
  document.getElementById("input-tipo-veiculo-edit-nome").disabled = ehSistema;
  document.getElementById("input-tipo-veiculo-edit-primeira").value = tipo.primeira_hora > 0 ? tipo.primeira_hora : "";
  document.getElementById("input-tipo-veiculo-edit-adicional").value = tipo.hora_adicional > 0 ? tipo.hora_adicional : "";
  document.getElementById("input-tipo-veiculo-edit-diaria").value = tipo.diaria > 0 ? tipo.diaria : "";
  document.getElementById("input-tipo-veiculo-edit-mensal").value = tipo.mensal > 0 ? tipo.mensal : "";
  document.getElementById("modal-tipo-veiculo").hidden = false;
}

function fecharModalTipoVeiculo() {
  document.getElementById("modal-tipo-veiculo").hidden = true;
}

document.getElementById("modal-tipo-veiculo-fechar").addEventListener("click", fecharModalTipoVeiculo);
document.getElementById("btn-tipo-veiculo-cancelar").addEventListener("click", fecharModalTipoVeiculo);

document.getElementById("form-tipo-veiculo").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const id = document.getElementById("input-tipo-veiculo-edit-id").value;
  const preco = (idCampo) => {
    const el = document.getElementById(idCampo);
    const v = el && el.value ? Number(el.value) : 0;
    return v > 0 ? v : null;
  };
  const botaoSalvar = document.getElementById("btn-tipo-veiculo-salvar");
  botaoSalvar.disabled = true;
  try {
    const dados = await chamarApi(`/tipos-veiculo/${id}`, {
      method: "PUT",
      body: JSON.stringify({
        nome: document.getElementById("input-tipo-veiculo-edit-nome").value,
        primeira_hora: preco("input-tipo-veiculo-edit-primeira"),
        hora_adicional: preco("input-tipo-veiculo-edit-adicional"),
        diaria: preco("input-tipo-veiculo-edit-diaria"),
        mensal: preco("input-tipo-veiculo-edit-mensal"),
      }),
    });
    mostrarToast(dados.mensagem || "Tipo atualizado!", "success");
    fecharModalTipoVeiculo();
    await carregarTiposVeiculo();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  } finally {
    botaoSalvar.disabled = false;
  }
});

// Popula o select de tipo de veiculo do formulario de entrada (Emitir Ticket)
function atualizarSelectTiposEntrada(tipos) {
  const select = document.getElementById("input-tipo");
  if (!select) return;
  const atual = select.value;
  const personalizados = (tipos || [])
    .filter((t) => t.ativo !== false && !TIPOS_VEICULO_SISTEMA.includes(t.nome))
    .map((t) => t.nome);
  select.innerHTML = TIPOS_VEICULO_SISTEMA
    .filter((n) => n !== "Carro Grande")
    .map((n) => `<option value="${escaparHtml(n)}">${escaparHtml(n)}</option>`)
    .join("") + personalizados
    .map((n) => `<option value="${escaparHtml(n)}">${escaparHtml(n)}</option>`)
    .join("");
  if ([...select.options].some((o) => o.value === atual)) select.value = atual;
}

document.getElementById("btn-adicionar-tipo-veiculo").addEventListener("click", async () => {
  const inputNome = document.getElementById("input-novo-tipo-veiculo");
  const nome = inputNome.value.trim();
  if (!nome) {
    mostrarToast("Informe o nome do tipo de veiculo.", "error");
    return;
  }
  const preco = (id) => {
    const el = document.getElementById(id);
    const v = el && el.value ? Number(el.value) : 0;
    return v > 0 ? v : null;
  };
  const botao = document.getElementById("btn-adicionar-tipo-veiculo");
  botao.disabled = true;
  try {
    const dados = await chamarApi("/tipos-veiculo", {
      method: "POST",
      body: JSON.stringify({
        nome,
        primeira_hora: preco("input-tipo-veiculo-primeira"),
        hora_adicional: preco("input-tipo-veiculo-adicional"),
        diaria: preco("input-tipo-veiculo-diaria"),
        mensal: preco("input-tipo-veiculo-mensal"),
      }),
    });
    mostrarToast(dados.mensagem || "Tipo de veiculo criado!", "success");
    inputNome.value = "";
    ["input-tipo-veiculo-primeira", "input-tipo-veiculo-adicional", "input-tipo-veiculo-diaria", "input-tipo-veiculo-mensal"].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.value = "";
    });
    await carregarTiposVeiculo();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  } finally {
    botao.disabled = false;
  }
});

/// ---------------------- FUNCOES E PERMISSOES (RBAC) ----------------------

let permissoesMatriz = null;
let perfilUsuarioAtual = null;
let permissoesPerfis = [];
let permissoesModulos = [];
let permissoesAcoes = [];
let permissoesCategorias = [];
let permissoesAcoesPorModulo = {};
let permissoesPerfisDetalhes = [];
let perfilSelecionado = null;

// Verifica se o perfil atual tem determinada acao ("ver", "criar", "editar",
// "excluir") em um modulo da matriz de permissoes. Admin sempre tem acesso.
function temPermissaoModulo(modulo, acao = "ver") {
  const perfil = perfilUsuarioAtual;
  if (!perfil || perfil === "admin") return true;
  return Boolean(
    permissoesMatriz &&
    permissoesMatriz[modulo] &&
    permissoesMatriz[modulo][perfil] &&
    permissoesMatriz[modulo][perfil].includes(acao)
  );
}

const PERFIS_BASE = ["admin", "supervisor", "operador"];

function nomePerfil(codigo) {
  const p = permissoesPerfisDetalhes.find((x) => x.codigo === codigo);
  return p ? p.nome : (codigo === "admin" ? "Administrador" : codigo);
}

function descricaoPerfil(codigo) {
  const p = permissoesPerfisDetalhes.find((x) => x.codigo === codigo);
  return p ? p.descricao : "";
}

function perfilEhBase(codigo) {
  return PERFIS_BASE.includes(codigo);
}

async function carregarPerfis() {
  const container = document.getElementById("perfis-container");
  if (!container) return;
  container.innerHTML = '<p class="config-hint">Carregando perfis e catálogo de funcionalidades...</p>';
  try {
    const dados = await chamarApi("/permissoes");
    permissoesMatriz = dados.matriz || {};
    permissoesPerfis = dados.perfis || [];
    permissoesModulos = dados.modulos || [];
    permissoesAcoes = dados.acoes || [];
    permissoesCategorias = dados.categorias || [];
    permissoesAcoesPorModulo = dados.acoes_por_modulo || {};
    permissoesPerfisDetalhes = dados.perfis_detalhes || [];

    renderPerfis();
    atualizarSelectPerfis();

    // Se nenhum perfil editavel estiver selecionado, seleciona o primeiro disponivel
    if (!perfilSelecionado || perfilSelecionado === "admin") {
      const primeiroEditavel = permissoesPerfisDetalhes.find((p) => p.codigo !== "admin" && p.ativo !== false);
      if (primeiroEditavel) {
        selecionarPerfil(primeiroEditavel.codigo);
      }
    } else {
      renderMatrizPerfil(perfilSelecionado);
    }
  } catch (erro) {
    container.innerHTML = `<p class="config-hint">Erro ao carregar perfis: ${erro.message}</p>`;
  }
}

function renderPerfis() {
  const container = document.getElementById("perfis-container");
  if (!container) return;

  const perfis = permissoesPerfisDetalhes.slice();
  if (!perfis.length) {
    container.innerHTML = '<p class="config-hint">Nenhum perfil cadastrado.</p>';
    return;
  }

  let html = '<div class="perfis-grid">';
  perfis.forEach((perfil) => {
    const isBase = perfilEhBase(perfil.codigo);
    const ativo = perfil.ativo !== false;
    const classe = [
      "perfil-card",
      perfilSelecionado === perfil.codigo ? "active" : "",
      ativo ? "" : "inativo",
    ].filter(Boolean).join(" ");
    const badgeClasse = ativo ? "ativo" : "inativo";
    const badgeTexto = isBase ? "Base do Sistema" : (ativo ? "Ativo" : "Inativo");
    const badgeClasseFinal = isBase ? "base" : badgeClasse;

    html += `<div class="${classe}" data-perfil-card="${perfil.codigo}">
      <div class="perfil-card-header">
        <span class="perfil-card-name">
          ${escaparHtml(perfil.nome)}
          <span class="perfil-card-badge ${badgeClasseFinal}">${badgeTexto}</span>
        </span>
      </div>
      <div class="perfil-card-desc">${escaparHtml(perfil.descricao || "Sem descrição")}</div>
      <div class="perfil-card-actions">
        <button type="button" class="btn-mini" data-selecionar-perfil="${perfil.codigo}">Configurar Permissões</button>
        ${!isBase ? `<button type="button" class="btn-mini btn-mini-ghost" data-editar-perfil="${perfil.id}">Editar</button>` : ""}
        ${!isBase ? `<button type="button" class="btn-mini btn-mini-ghost" data-clonar-perfil="${perfil.id}">Clonar</button>` : ""}
        ${!isBase ? `<button type="button" class="btn-mini btn-mini-ghost" data-${ativo ? "inativar" : "ativar"}-perfil="${perfil.id}">${ativo ? "Inativar" : "Ativar"}</button>` : ""}
      </div>
    </div>`;
  });
  html += "</div>";
  container.innerHTML = html;

  container.querySelectorAll("[data-selecionar-perfil]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      selecionarPerfil(btn.dataset.selecionarPerfil);
    });
  });
  container.querySelectorAll(".perfil-card").forEach((card) => {
    card.addEventListener("click", () => {
      const cod = card.dataset.perfilCard;
      if (cod) selecionarPerfil(cod);
    });
  });
  container.querySelectorAll("[data-editar-perfil]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const perfil = permissoesPerfisDetalhes.find((p) => String(p.id) === btn.dataset.editarPerfil);
      if (perfil) abrirModalPerfil(perfil);
    });
  });
  container.querySelectorAll("[data-clonar-perfil]").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      await clonarPerfil(Number(btn.dataset.clonarPerfil));
    });
  });
  container.querySelectorAll("[data-ativar-perfil], [data-inativar-perfil]").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const ativar = !!btn.dataset.ativarPerfil;
      const id = Number(btn.dataset.ativarPerfil || btn.dataset.inativarPerfil);
      await alternarPerfil(id, ativar);
    });
  });
}

function selecionarPerfil(codigo) {
  perfilSelecionado = codigo;
  renderPerfis();
  renderMatrizPerfil(codigo);
}

function renderMatrizPerfil(codigo) {
  const section = document.getElementById("permissoes-matriz-section");
  const container = document.getElementById("permissoes-container");
  const titulo = document.getElementById("permissoes-matriz-titulo");
  if (!section || !container || !titulo) return;

  section.classList.remove("hidden");
  titulo.textContent = `Permissões de Acesso — Perfil: ${nomePerfil(codigo)}`;

  if (codigo === "admin") {
    container.innerHTML = `
      <div class="empty-state" style="padding: 40px; text-align: center; border: 1px dashed var(--color-border); border-radius: var(--radius-sm); background: #f8fafc;">
        <svg width="44" height="44" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin: 0 auto 12px; color: #10b981;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <h4 style="font-size: 16px; margin-bottom: 6px; color: var(--color-text);">Perfil Administrador</h4>
        <p class="config-hint" style="max-width: 540px; margin: 0 auto;">O perfil Administrador possui controle irrestrito a todos os 20 módulos e fluxos do sistema. Por razões de governança e segurança, suas permissões não podem ser limitadas.</p>
      </div>`;
    return;
  }

  const categorias = permissoesCategorias || [];
  const acoesPorModulo = permissoesAcoesPorModulo || {};

  let html = "";

  categorias.forEach((cat) => {
    const modulosCat = cat.modulos.filter((m) => permissoesModulos.includes(m));
    if (!modulosCat.length) return;

    html += `
      <div class="permissoes-categoria-bloco" data-categoria-id="${cat.id}">
        <div class="permissoes-categoria-title" style="display: flex; align-items: center; justify-content: space-between; margin-top: 20px; margin-bottom: 12px;">
          <span>${escaparHtml(cat.nome)}</span>
          <span style="font-size: 11px; font-weight: 500; text-transform: none; color: var(--color-text-light);">${modulosCat.length} módulos</span>
        </div>`;

    modulosCat.forEach((modulo) => {
      const infoMod = acoesPorModulo[modulo] || {
        nome: modulo,
        descricao: "",
        acoes: permissoesAcoes.map((a) => ({ acao: a, nome: a, desc: "" })),
      };

      const acoesPermitidas = (permissoesMatriz[modulo] && permissoesMatriz[modulo][codigo]) || [];
      const moduloLiberado = acoesPermitidas.length > 0;

      html += `
        <div class="permissoes-modulo-card ${moduloLiberado ? '' : 'bloqueado'}" data-modulo-card="${modulo}">
          <div class="permissoes-modulo-header">
            <div class="permissoes-modulo-main-info">
              <div class="permissoes-modulo-title-row">
                <strong>${escaparHtml(infoMod.nome)}</strong>
                <span class="permissoes-modulo-badge ${moduloLiberado ? 'ativo' : 'bloqueado'}" id="badge-modulo-${modulo}">
                  ${moduloLiberado ? 'Liberado' : 'Bloqueado'}
                </span>
              </div>
              <span class="permissoes-modulo-sub">${escaparHtml(infoMod.descricao)}</span>
            </div>
            <div>
              <label class="permissoes-modulo-switch" title="Liberar ou bloquear este módulo para o perfil">
                <input type="checkbox" class="switch-modulo-master" data-modulo="${modulo}" ${moduloLiberado ? 'checked' : ''}>
                <span class="switch-texto-${modulo}">${moduloLiberado ? 'Módulo Liberado' : 'Módulo Bloqueado'}</span>
              </label>
            </div>
          </div>
          <div class="permissoes-modulo-body" id="corpo-modulo-${modulo}">
            ${infoMod.acoes.map((item) => {
              const checado = acoesPermitidas.includes(item.acao);
              return `
                <label class="permissoes-acao-item ${checado ? 'selecionado' : ''}" title="${escaparHtml(item.desc)}">
                  <input type="checkbox" data-modulo="${modulo}" data-perfil="${codigo}" data-acao="${item.acao}" ${checado ? 'checked' : ''}>
                  <div class="permissoes-acao-detalhes">
                    <span class="permissoes-acao-titulo">${escaparHtml(item.nome)}</span>
                    <span class="permissoes-acao-sub">${escaparHtml(item.desc)}</span>
                  </div>
                </label>
              `;
            }).join("")}
          </div>
        </div>
      `;
    });

    html += `</div>`;
  });

  container.innerHTML = html;

  // Interatividade: Switch Mestre de cada Módulo
  container.querySelectorAll(".switch-modulo-master").forEach((sw) => {
    sw.addEventListener("change", () => {
      const modulo = sw.dataset.modulo;
      const card = container.querySelector(`.permissoes-modulo-card[data-modulo-card="${modulo}"]`);
      const badge = document.getElementById(`badge-modulo-${modulo}`);
      const texto = container.querySelector(`.switch-texto-${modulo}`);
      const acaoCheckboxes = card.querySelectorAll(`input[data-modulo="${modulo}"][data-perfil="${codigo}"]`);

      if (sw.checked) {
        card.classList.remove("bloqueado");
        if (badge) {
          badge.className = "permissoes-modulo-badge ativo";
          badge.textContent = "Liberado";
        }
        if (texto) texto.textContent = "Módulo Liberado";
        acaoCheckboxes.forEach((cb) => {
          if (cb.dataset.acao === "ver" || acaoCheckboxes.length <= 2) {
            cb.checked = true;
            cb.closest(".permissoes-acao-item").classList.add("selecionado");
          }
        });
      } else {
        card.classList.add("bloqueado");
        if (badge) {
          badge.className = "permissoes-modulo-badge bloqueado";
          badge.textContent = "Bloqueado";
        }
        if (texto) texto.textContent = "Módulo Bloqueado";
        acaoCheckboxes.forEach((cb) => {
          cb.checked = false;
          cb.closest(".permissoes-acao-item").classList.remove("selecionado");
        });
      }
    });
  });

  // Interatividade: Checkboxes de ações individuais
  container.querySelectorAll(".permissoes-acao-item input[type='checkbox']").forEach((cb) => {
    cb.addEventListener("change", () => {
      const itemLabel = cb.closest(".permissoes-acao-item");
      itemLabel.classList.toggle("selecionado", cb.checked);

      const modulo = cb.dataset.modulo;
      const card = container.querySelector(`.permissoes-modulo-card[data-modulo-card="${modulo}"]`);
      const sw = card.querySelector(".switch-modulo-master");
      const badge = document.getElementById(`badge-modulo-${modulo}`);
      const texto = card.querySelector(`.switch-texto-${modulo}`);

      const qualquerMarcado = Array.from(card.querySelectorAll(`input[data-modulo="${modulo}"][data-perfil="${codigo}"]`)).some((c) => c.checked);

      if (qualquerMarcado && !sw.checked) {
        sw.checked = true;
        card.classList.remove("bloqueado");
        if (badge) {
          badge.className = "permissoes-modulo-badge ativo";
          badge.textContent = "Liberado";
        }
        if (texto) texto.textContent = "Módulo Liberado";
      } else if (!qualquerMarcado && sw.checked) {
        sw.checked = false;
        card.classList.add("bloqueado");
        if (badge) {
          badge.className = "permissoes-modulo-badge bloqueado";
          badge.textContent = "Bloqueado";
        }
        if (texto) texto.textContent = "Módulo Bloqueado";
      }
    });
  });
}

function coletarPermissoes() {
  const novaMatriz = {};
  permissoesModulos.forEach((modulo) => {
    novaMatriz[modulo] = {};
    permissoesPerfis.forEach((perfil) => {
      if (perfil === "admin") {
        novaMatriz[modulo][perfil] = permissoesAcoes.slice();
        return;
      }
      if (perfil === perfilSelecionado) {
        const card = document.querySelector(`.permissoes-modulo-card[data-modulo-card="${modulo}"]`);
        const sw = card ? card.querySelector(".switch-modulo-master") : null;
        if (sw && !sw.checked) {
          novaMatriz[modulo][perfil] = [];
        } else {
          const acoes = [];
          document.querySelectorAll(`input[data-modulo="${modulo}"][data-perfil="${perfil}"]:checked`).forEach((cb) => {
            acoes.push(cb.dataset.acao);
          });
          novaMatriz[modulo][perfil] = acoes;
        }
      } else {
        novaMatriz[modulo][perfil] = (permissoesMatriz[modulo] && permissoesMatriz[modulo][perfil]) || [];
      }
    });
  });
  return novaMatriz;
}

async function salvarPermissoes() {
  const botao = document.getElementById("btn-salvar-permissoes");
  if (!botao) return;
  botao.disabled = true;
  botao.textContent = "Salvando...";
  try {
    const dados = await chamarApi("/permissoes", {
      method: "PUT",
      body: JSON.stringify({ matriz: coletarPermissoes() }),
    });
    permissoesMatriz = dados.matriz || permissoesMatriz;
    mostrarToast(dados.mensagem || "Permissões atualizadas com sucesso!", "success");
    if (perfilSelecionado) renderMatrizPerfil(perfilSelecionado);
  } catch (erro) {
    mostrarToast(erro.message, "error");
  } finally {
    botao.disabled = false;
    botao.textContent = "Salvar permissões";
  }
}

async function restaurarPermissoesPadrao() {
  if (!confirm("Restaurar as permissões padrão de todos os perfis? As alterações não salvas serão perdidas.")) return;
  try {
    const dados = await chamarApi("/permissoes/restaurar", { method: "POST" });
    permissoesMatriz = dados.matriz || permissoesMatriz;
    mostrarToast(dados.mensagem || "Permissões restauradas com sucesso!", "success");
    if (perfilSelecionado) renderMatrizPerfil(perfilSelecionado);
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
}

// ---------------------- MODAL PERFIL ----------------------

let perfilEditandoId = null;

function abrirModalPerfil(perfil = null) {
  const overlay = document.getElementById("modal-perfil");
  if (!overlay) return;
  perfilEditandoId = perfil ? perfil.id : null;
  document.getElementById("input-perfil-id").value = perfil ? perfil.id : "";
  document.getElementById("input-perfil-nome").value = perfil ? perfil.nome : "";
  const campoCod = document.getElementById("campo-perfil-codigo");
  const inputCod = document.getElementById("input-perfil-codigo");
  if (campoCod && inputCod) {
    if (perfil) {
      campoCod.hidden = true;
      inputCod.required = false;
      inputCod.value = perfil.codigo;
    } else {
      campoCod.hidden = false;
      inputCod.required = true;
      inputCod.value = "";
    }
  }
  document.getElementById("input-perfil-descricao").value = perfil ? perfil.descricao : "";
  document.getElementById("modal-perfil-titulo").textContent = perfil ? "Editar perfil" : "Novo perfil de acesso";
  overlay.hidden = false;
  setTimeout(() => document.getElementById("input-perfil-nome").focus(), 50);
}

function fecharModalPerfil() {
  const overlay = document.getElementById("modal-perfil");
  if (overlay) overlay.hidden = true;
  const form = document.getElementById("form-perfil");
  if (form) form.reset();
  document.getElementById("input-perfil-id").value = "";
  perfilEditandoId = null;
}

async function salvarPerfil(evento) {
  evento.preventDefault();
  const id = document.getElementById("input-perfil-id").value;
  const nome = document.getElementById("input-perfil-nome").value.trim();
  const inputCod = document.getElementById("input-perfil-codigo");
  const codigo = inputCod ? inputCod.value.trim().toLowerCase().replace(/\s+/g, "_") : "";
  const descricao = document.getElementById("input-perfil-descricao").value.trim();

  if (!nome || (!id && !codigo)) return;

  const botao = document.getElementById("btn-perfil-salvar") || document.querySelector("#modal-perfil .btn-salvar");
  if (botao) botao.disabled = true;
  try {
    if (id) {
      await chamarApi(`/perfis/${id}`, {
        method: "PUT",
        body: JSON.stringify({ nome, descricao }),
      });
      mostrarToast("Perfil atualizado com sucesso!", "success");
    } else {
      const res = await chamarApi("/perfis", {
        method: "POST",
        body: JSON.stringify({ nome, codigo, descricao }),
      });
      mostrarToast("Perfil criado com sucesso!", "success");
      perfilSelecionado = res.perfil ? res.perfil.codigo : codigo;
    }
    fecharModalPerfil();
    await carregarPerfis();
    if (perfilSelecionado) renderMatrizPerfil(perfilSelecionado);
  } catch (erro) {
    mostrarToast(erro.message, "error");
  } finally {
    if (botao) botao.disabled = false;
  }
}

async function alternarPerfil(id, ativar) {
  try {
    await chamarApi(`/perfis/${id}/${ativar ? "ativar" : "inativar"}`, { method: "POST" });
    mostrarToast(`Perfil ${ativar ? "ativado" : "inativado"} com sucesso!`, "success");
    await carregarPerfis();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
}

async function clonarPerfil(id) {
  const pOrigem = permissoesPerfisDetalhes.find((p) => p.id === id);
  if (!pOrigem) return;

  const nomeNovo = prompt(`Informe o nome do novo perfil clonado de "${pOrigem.nome}":`, `${pOrigem.nome} (Cópia)`);
  if (!nomeNovo || !nomeNovo.trim()) return;

  const codigoSugerido = nomeNovo.trim().toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
  const codigoNovo = prompt("Informe o código identificador único (sem espaços ou acentos):", codigoSugerido);
  if (!codigoNovo || !codigoNovo.trim()) return;

  try {
    const resCriar = await chamarApi("/perfis", {
      method: "POST",
      body: JSON.stringify({
        nome: nomeNovo.trim(),
        codigo: codigoNovo.trim(),
        descricao: `Clonado de ${pOrigem.nome}`,
      }),
    });
    const novoPerfil = resCriar.perfil;

    await chamarApi(`/perfis/${novoPerfil.id}/clonar`, {
      method: "POST",
      body: JSON.stringify({ origem: pOrigem.codigo }),
    });

    mostrarToast(`Perfil "${nomeNovo}" clonado com sucesso!`, "success");
    perfilSelecionado = novoPerfil.codigo;
    await carregarPerfis();
    renderMatrizPerfil(perfilSelecionado);
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
}

function atualizarSelectPerfis() {
  const select = document.getElementById("input-usuario-perfil");
  if (!select) return;
  const atual = select.value;
  select.innerHTML = permissoesPerfisDetalhes
    .filter((p) => p.ativo !== false)
    .map((p) => `<option value="${p.codigo}">${p.nome}</option>`)
    .join("");
  if (atual && permissoesPerfisDetalhes.some((p) => p.codigo === atual && p.ativo !== false)) {
    select.value = atual;
  } else if (permissoesPerfisDetalhes.some((p) => p.codigo === "operador")) {
    select.value = "operador";
  }
}

// Eventos de Permissões
const btnNovoPerfil = document.getElementById("btn-novo-perfil");
if (btnNovoPerfil) btnNovoPerfil.addEventListener("click", () => abrirModalPerfil());

const modalPerfilFechar = document.getElementById("modal-perfil-fechar");
if (modalPerfilFechar) modalPerfilFechar.addEventListener("click", fecharModalPerfil);

const btnPerfilCancelar = document.getElementById("btn-perfil-cancelar");
if (btnPerfilCancelar) btnPerfilCancelar.addEventListener("click", fecharModalPerfil);

const modalPerfilOverlay = document.getElementById("modal-perfil");
if (modalPerfilOverlay) {
  modalPerfilOverlay.addEventListener("click", (evento) => {
    if (evento.target === evento.currentTarget) fecharModalPerfil();
  });
}

const formPerfil = document.getElementById("form-perfil");
if (formPerfil) formPerfil.addEventListener("submit", salvarPerfil);

const btnSalvarPermissoes = document.getElementById("btn-salvar-permissoes");
if (btnSalvarPermissoes) btnSalvarPermissoes.addEventListener("click", salvarPermissoes);

const btnCancelarPermissoes = document.getElementById("btn-cancelar-permissoes");
if (btnCancelarPermissoes) {
  btnCancelarPermissoes.addEventListener("click", () => {
    if (perfilSelecionado) renderMatrizPerfil(perfilSelecionado);
  });
}

const btnRestaurarPermissoes = document.getElementById("btn-restaurar-permissoes");
if (btnRestaurarPermissoes) btnRestaurarPermissoes.addEventListener("click", restaurarPermissoesPadrao);

// Ações rápidas no topo da matriz
const btnMarcarTudo = document.getElementById("btn-marcar-tudo-perfil");
if (btnMarcarTudo) {
  btnMarcarTudo.addEventListener("click", () => {
    const container = document.getElementById("permissoes-container");
    if (!container) return;
    container.querySelectorAll(".switch-modulo-master").forEach((sw) => {
      sw.checked = true;
      const mod = sw.dataset.modulo;
      const card = container.querySelector(`.permissoes-modulo-card[data-modulo-card="${mod}"]`);
      if (card) card.classList.remove("bloqueado");
      const badge = document.getElementById(`badge-modulo-${mod}`);
      if (badge) { badge.className = "permissoes-modulo-badge ativo"; badge.textContent = "Liberado"; }
      const txt = container.querySelector(`.switch-texto-${mod}`);
      if (txt) txt.textContent = "Módulo Liberado";
    });
    container.querySelectorAll(".permissoes-acao-item").forEach((item) => {
      item.classList.add("selecionado");
      const cb = item.querySelector("input[type='checkbox']");
      if (cb) cb.checked = true;
    });
  });
}

const btnDesmarcarTudo = document.getElementById("btn-desmarcar-tudo-perfil");
if (btnDesmarcarTudo) {
  btnDesmarcarTudo.addEventListener("click", () => {
    const container = document.getElementById("permissoes-container");
    if (!container) return;
    container.querySelectorAll(".switch-modulo-master").forEach((sw) => {
      sw.checked = false;
      const mod = sw.dataset.modulo;
      const card = container.querySelector(`.permissoes-modulo-card[data-modulo-card="${mod}"]`);
      if (card) card.classList.add("bloqueado");
      const badge = document.getElementById(`badge-modulo-${mod}`);
      if (badge) { badge.className = "permissoes-modulo-badge bloqueado"; badge.textContent = "Bloqueado"; }
      const txt = container.querySelector(`.switch-texto-${mod}`);
      if (txt) txt.textContent = "Módulo Bloqueado";
    });
    container.querySelectorAll(".permissoes-acao-item").forEach((item) => {
      item.classList.remove("selecionado");
      const cb = item.querySelector("input[type='checkbox']");
      if (cb) cb.checked = false;
    });
  });
}

const btnSomenteLeitura = document.getElementById("btn-somente-leitura-perfil");
if (btnSomenteLeitura) {
  btnSomenteLeitura.addEventListener("click", () => {
    const container = document.getElementById("permissoes-container");
    if (!container) return;
    container.querySelectorAll(".switch-modulo-master").forEach((sw) => {
      sw.checked = true;
      const mod = sw.dataset.modulo;
      const card = container.querySelector(`.permissoes-modulo-card[data-modulo-card="${mod}"]`);
      if (card) card.classList.remove("bloqueado");
      const badge = document.getElementById(`badge-modulo-${mod}`);
      if (badge) { badge.className = "permissoes-modulo-badge ativo"; badge.textContent = "Liberado"; }
      const txt = container.querySelector(`.switch-texto-${mod}`);
      if (txt) txt.textContent = "Módulo Liberado";
    });
    container.querySelectorAll(".permissoes-acao-item").forEach((item) => {
      const cb = item.querySelector("input[type='checkbox']");
      if (cb) {
        const ehVer = cb.dataset.acao === "ver";
        cb.checked = ehVer;
        item.classList.toggle("selecionado", ehVer);
      }
    });
  });
}

// Filtro de busca de módulos
const inputBuscaModulos = document.getElementById("filtro-busca-modulos");
if (inputBuscaModulos) {
  inputBuscaModulos.addEventListener("input", () => {
    const termo = inputBuscaModulos.value.trim().toLowerCase();
    const cards = document.querySelectorAll(".permissoes-modulo-card");
    cards.forEach((card) => {
      const texto = card.textContent.toLowerCase();
      const bate = !termo || texto.includes(termo);
      card.style.display = bate ? "" : "none";
    });
    document.querySelectorAll(".permissoes-categoria-bloco").forEach((bloco) => {
      const temVisivel = Array.from(bloco.querySelectorAll(".permissoes-modulo-card")).some((c) => c.style.display !== "none");
      bloco.style.display = temVisivel ? "" : "none";
    });
  });
}

// Botao na aba de configuracoes para ir a tela dedicada
const btnIrParaPermissoes = document.getElementById("btn-ir-para-permissoes");
if (btnIrParaPermissoes) {
  btnIrParaPermissoes.addEventListener("click", () => {
    mostrarView("view-permissoes");
  });
}

// Carrega as permissoes ao abrir a aba de configuracoes
document.querySelectorAll("#tabs-config .tab").forEach((botaoTab) => {
  botaoTab.addEventListener("click", () => {
    if (botaoTab.dataset.configTab === "permissoes") {
      mostrarView("view-permissoes");
    }
  });
});

// ---------------------- FORMAS DE PAGAMENTO ----------------------

let formaPagamentoEditandoId = null;

async function carregarFormasPagamento() {
  const tbody = document.getElementById("tabela-formas-pagamento");
  const empty = document.getElementById("formas-pagamento-empty");
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="3" class="table-empty">Carregando formas de pagamento...</td></tr>';
  if (empty) empty.hidden = true;
  try {
    const dados = await chamarApi("/formas-pagamento");
    const formas = dados.formas_pagamento || [];
    if (!formas.length) {
      tbody.innerHTML = "";
      if (empty) empty.hidden = false;
      return;
    }
    tbody.innerHTML = formas.map((f) => `
      <tr>
        <td>${f.nome}</td>
        <td>${f.ativo ? '<span class="badge badge-ativo">Ativa</span>' : '<span class="badge badge-inativo">Inativa</span>'}</td>
        <td class="col-acoes">
          <button type="button" class="btn-acao" data-editar-forma="${f.id}" title="Editar">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </td>
      </tr>`).join("");
    tbody.querySelectorAll("[data-editar-forma]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const forma = formas.find((f) => f.id === Number(btn.dataset.editarForma));
        if (forma) abrirModalFormaPagamento(forma);
      });
    });
  } catch (erro) {
    tbody.innerHTML = `<tr><td colspan="3" class="table-empty">Erro: ${erro.message}</td></tr>`;
  }
}

function abrirModalFormaPagamento(forma) {
  formaPagamentoEditandoId = forma ? forma.id : null;
  document.getElementById("modal-forma-pagamento-titulo").textContent = forma ? "Editar forma de pagamento" : "Nova forma de pagamento";
  document.getElementById("input-forma-pagamento-id").value = forma ? forma.id : "";
  document.getElementById("input-forma-pagamento-nome").value = forma ? forma.nome : "";
  document.getElementById("input-forma-pagamento-ativo").checked = forma ? forma.ativo : true;
  document.getElementById("modal-forma-pagamento").hidden = false;
}

function fecharModalFormaPagamento() {
  document.getElementById("modal-forma-pagamento").hidden = true;
  formaPagamentoEditandoId = null;
}

document.getElementById("btn-novo-forma").addEventListener("click", () => abrirModalFormaPagamento(null));
document.getElementById("modal-forma-pagamento-fechar").addEventListener("click", fecharModalFormaPagamento);
document.getElementById("btn-forma-pagamento-cancelar").addEventListener("click", fecharModalFormaPagamento);

document.getElementById("form-forma-pagamento").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const id = formaPagamentoEditandoId;
  const nome = document.getElementById("input-forma-pagamento-nome").value.trim();
  const ativo = document.getElementById("input-forma-pagamento-ativo").checked;
  try {
    if (id) {
      await chamarApi(`/formas-pagamento/${id}`, {
        method: "PUT",
        body: JSON.stringify({ nome, ativo }),
      });
    } else {
      // Codigo interno gerado a partir do nome (nao precisa ser digitado)
      const codigo = nome.normalize("NFD").replace(/[\u0300-\u036f]/g, "")
        .toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
      await chamarApi("/formas-pagamento", {
        method: "POST",
        body: JSON.stringify({ nome, codigo, ativo }),
      });
    }
    fecharModalFormaPagamento();
    carregarFormasPagamento();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});

// ---------------------- APLICAR PERMISSOES NO FRONTEND ----------------------

// Mapeia botoes de acao do frontend para (modulo, acao)
const BOTOES_PERMISSAO = [
  { id: "btn-novo-usuario", modulo: "usuarios", acao: "criar" },
  { id: "btn-novo-cliente", modulo: "mensalistas", acao: "criar" },
  { id: "btn-novo-mensalista", modulo: "mensalistas", acao: "criar" },
  { id: "btn-novo-convenio", modulo: "convenios", acao: "criar" },
  { id: "btn-novo-desconto", modulo: "descontos", acao: "criar" },
  { id: "btn-novo-cortesia", modulo: "cortesias", acao: "criar" },
  { id: "btn-nova-conta", modulo: "contas_receber", acao: "criar" },
  { id: "btn-abrir-caixa", modulo: "caixa", acao: "criar" },
  { id: "btn-config-ir-formas", modulo: "formas_pagamento", acao: "criar" },
  { id: "btn-salvar-configuracoes", modulo: "configuracoes", acao: "editar" },
  { id: "btn-adicionar-tipo-veiculo", modulo: "configuracoes", acao: "editar" },
];

// Mapeia cada item do sidebar (data-view) para o modulo de permissao.
// Itens sem modulo no mapa (ex.: Empresas, apenas master) ficam sempre visiveis.
const MENU_PERMISSAO = {
  "view-visao-geral": "operacao",
  "view-usuarios": "usuarios",
  "view-permissoes": "usuarios",
  "view-clientes": "clientes",
  "view-financeiro": "caixa",
  "view-caixa": "caixa",
  "view-pagamentos": "pagamentos",
  "view-formas-pagamento": "formas_pagamento",
  "view-cortesias": "cortesias",
  "view-mensalistas": "mensalistas",
  "view-convenios": "convenios",
  "view-contas-receber": "contas_receber",
  "view-descontos": "descontos",
  "view-dashboard-financeiro": "dashboard_financeiro",
  "view-relatorios": "relatorios",
  "view-auditoria": "auditoria",
  "view-nfse": "nfse",
  "view-lista-negra": "lista_negra",
  "view-reservas": "reservas",
  "view-ocorrencias": "ocorrencias",
  "view-notificacoes": "notificacoes",
  "view-configuracoes": "configuracoes",
};

// Views do bloco Financeiro do sidebar (para compatibilidade de rotulos)
const VIEWS_FINANCEIRO = [
  "view-financeiro", "view-caixa", "view-pagamentos", "view-formas-pagamento",
  "view-mensalistas", "view-convenios", "view-contas-receber",
  "view-descontos", "view-cortesias", "view-dashboard-financeiro",
  "view-relatorios", "view-auditoria",
];

// Views do bloco Controle do sidebar (para compatibilidade de rotulos)
const VIEWS_CONTROLE = [
  "view-nfse", "view-lista-negra", "view-reservas", "view-ocorrencias",
  "view-notificacoes",
];

// Aplica as permissoes do usuario logado no frontend (oculta acoes nao permitidas)
function aplicarPermissoesFrontend(perfil) {
  if (perfil === "admin") return;

  // Oculta botoes de acao nao permitidos
  BOTOES_PERMISSAO.forEach(({ id, modulo, acao }) => {
    const botao = document.getElementById(id);
    if (botao) {
      const permitido = (permissoesMatriz && permissoesMatriz[modulo] && permissoesMatriz[modulo][perfil] || []).includes(acao);
      botao.style.display = permitido ? "" : "none";
    }
  });

  // Oculta itens do sidebar cujo modulo nao tem permissao "ver"
  Object.entries(MENU_PERMISSAO).forEach(([viewId, modulo]) => {
    const item = document.querySelector(`.menu-item[data-view="${viewId}"]`);
    if (!item) return;
    const permitido = (permissoesMatriz && permissoesMatriz[modulo] && permissoesMatriz[modulo][perfil] || []).includes("ver");
    item.style.display = permitido ? "" : "none";
    item.dataset.permissaoOculto = permitido ? "" : "1";
  });

  // Oculta grupos da sidebar caso todos os seus itens estejam bloqueados por permissao
  document.querySelectorAll(".menu-group").forEach((grupo) => {
    const itens = grupo.querySelectorAll(".menu-item");
    const algumPermitido = Array.from(itens).some(
      (item) => item.dataset.permissaoOculto !== "1"
    );
    grupo.style.display = algumPermitido ? "" : "none";
  });

  // Aba "Funcoes e Permissoes" nas configuracoes: somente quem pode editar usuarios
  const abaPermissoes = document.querySelector('#tabs-config .tab[data-config-tab="permissoes"]');
  if (abaPermissoes) {
    const podeEditar = (permissoesMatriz && permissoesMatriz["usuarios"] && permissoesMatriz["usuarios"][perfil] || []).includes("editar");
    abaPermissoes.style.display = podeEditar ? "" : "none";
    if (!podeEditar) {
      const panePermissoes = document.querySelector('.config-tab-pane[data-config-pane="permissoes"]');
      if (panePermissoes) panePermissoes.hidden = true;
    }
  }

  // Configuracoes do estacionamento: quem nao pode editar tem os campos somente leitura
  const podeEditarConfig = (permissoesMatriz && permissoesMatriz["configuracoes"] && permissoesMatriz["configuracoes"][perfil] || []).includes("editar");
  if (!podeEditarConfig) {
    const formConfig = document.getElementById("form-configuracoes");
    if (formConfig) {
      formConfig.querySelectorAll("input, select, textarea").forEach((campo) => {
        campo.readOnly = true;
        campo.disabled = true;
      });
    }
  }

  // Oculta labels de subgrupo que ficaram sem itens visiveis
  document.querySelectorAll(".menu-subgroup-label").forEach((label) => {
    let proximo = label.nextElementSibling;
    let temVisivel = false;
    while (proximo && !proximo.classList.contains("menu-subgroup-label")) {
      if (proximo.classList.contains("menu-item") && proximo.style.display !== "none") {
        temVisivel = true;
        break;
      }
      proximo = proximo.nextElementSibling;
    }
    label.style.display = temVisivel ? "" : "none";
  });
}

// ---------------------- CAIXA ----------------------

let caixaAberto = null;

async function carregarCaixa() {
  const corpo = document.getElementById("tabela-caixas");
  if (corpo) corpo.innerHTML = "";

  let dados;
  try {
    dados = await chamarApi("/caixa");
  } catch (erro) {
    mostrarToast(erro.message, "error");
    if (corpo) corpo.innerHTML = '<tr><td colspan="8" class="table-empty">Erro ao carregar caixas.</td></tr>';
    return;
  }

  caixaAberto = dados.caixa_aberto;
  const statusBox = document.getElementById("caixa-status");
  const resumoCards = document.getElementById("caixa-resumo-cards");

  // Botoes do topo
  const btnTopoAbrir = document.getElementById("btn-abrir-caixa");
  const btnTopoSangria = document.getElementById("btn-sangria");
  const btnTopoSuprimento = document.getElementById("btn-suprimento");
  const btnTopoFechar = document.getElementById("btn-fechar-caixa");

  if (caixaAberto) {
    if (statusBox) {
      statusBox.innerHTML = `
        <div class="caixa-banner caixa-banner-aberto">
          <div class="caixa-banner-info">
            <div class="caixa-banner-badge">
              <span class="status-indicator-dot"></span>
              <strong>Caixa Aberto • Turno #${caixaAberto.id}</strong>
            </div>
            <div class="caixa-banner-meta">
              <span>👤 Operador: <strong>${caixaAberto.operador}</strong></span>
              <span>🕒 Abertura: <strong>${formatarDataHora(caixaAberto.data_abertura)}</strong></span>
              <span>💵 Fundo Inicial: <strong>${formatarMoeda(caixaAberto.valor_inicial)}</strong></span>
            </div>
          </div>
          <div class="caixa-banner-acoes">
            <button type="button" class="btn-caixa-acao btn-caixa-suprimento" id="btn-suprimento-banner" title="Adicionar troco ao caixa">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
              + Suprimento
            </button>
            <button type="button" class="btn-caixa-acao btn-caixa-sangria" id="btn-sangria-banner" title="Retirar dinheiro do caixa">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/></svg>
              − Sangria
            </button>
            <button type="button" class="btn-caixa-acao btn-caixa-fechar" id="btn-fechar-banner" title="Conferir e fechar caixa">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>
              Encerrar Turno
            </button>
          </div>
        </div>
      `;

      document.getElementById("btn-suprimento-banner")?.addEventListener("click", () => abrirModalMovimento("suprimento"));
      document.getElementById("btn-sangria-banner")?.addEventListener("click", () => abrirModalMovimento("sangria"));
      document.getElementById("btn-fechar-banner")?.addEventListener("click", abrirModalFecharCaixa);
    }

    if (btnTopoAbrir) btnTopoAbrir.hidden = true;
    if (btnTopoSangria) btnTopoSangria.hidden = false;
    if (btnTopoSuprimento) btnTopoSuprimento.hidden = false;
    if (btnTopoFechar) btnTopoFechar.hidden = false;

    // Carrega o resumo discriminado do turno ativo
    try {
      const res = await chamarApi(`/caixa/${caixaAberto.id}/resumo`);
      if (res && res.resumo) {
        document.getElementById("card-caixa-inicial").textContent = formatarMoeda(res.resumo.valor_inicial);
        document.getElementById("card-caixa-entradas").textContent = formatarMoeda(res.resumo.total_entradas);
        document.getElementById("card-caixa-suprimentos").textContent = formatarMoeda(res.resumo.total_suprimentos);
        document.getElementById("card-caixa-sangrias").textContent = formatarMoeda(res.resumo.total_sangrias);
        document.getElementById("card-caixa-estornos").textContent = formatarMoeda(res.resumo.total_estornos);
        document.getElementById("card-caixa-saldo-dinheiro").textContent = formatarMoeda(res.resumo.saldo_dinheiro);
        if (resumoCards) resumoCards.hidden = false;
      }
    } catch (_) {
      if (resumoCards) resumoCards.hidden = true;
    }
  } else {
    if (statusBox) {
      statusBox.innerHTML = `
        <div class="caixa-banner caixa-banner-fechado">
          <div class="caixa-banner-fechado-inner">
            <div class="caixa-banner-fechado-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            </div>
            <div class="caixa-banner-fechado-texto">
              <h4>Nenhum Caixa Aberto no Momento</h4>
              <p>Inicie um novo expediente para registrar movimentações, receber pagamentos e controlar a gaveta de dinheiro.</p>
            </div>
            <button type="button" class="btn-novo btn-abrir-caixa-hero" id="btn-abrir-caixa-hero">
              + Iniciar Expediente (Abrir Caixa)
            </button>
          </div>
        </div>
      `;
      document.getElementById("btn-abrir-caixa-hero")?.addEventListener("click", abrirModalAbrirCaixa);
    }

    if (btnTopoAbrir) btnTopoAbrir.hidden = false;
    if (btnTopoSangria) btnTopoSangria.hidden = true;
    if (btnTopoSuprimento) btnTopoSuprimento.hidden = true;
    if (btnTopoFechar) btnTopoFechar.hidden = true;
    if (resumoCards) resumoCards.hidden = true;
  }

  // Atualiza pagamentos e movimentacoes do turno
  try {
    await carregarPagamentos();
  } catch (_) {}

  try {
    await carregarMovimentacoesCaixaAtivo();
  } catch (_) {}

  if (corpo) {
    (dados.caixas || []).forEach((caixa) => {
      const linha = document.createElement("tr");
      const aberto = caixa.status === "aberto";
      linha.innerHTML = `
        <td class="cell-nome">${caixa.operador}</td>
        <td>${formatarDataHora(caixa.data_abertura)}</td>
        <td>${formatarDataHora(caixa.data_fechamento)}</td>
        <td>${formatarMoeda(caixa.valor_inicial)}</td>
        <td>${formatarMoeda(caixa.valor_esperado)}</td>
        <td>${formatarMoeda(caixa.valor_contado)}</td>
        <td class="${caixa.diferenca >= 0 ? "valor-entrada" : "valor-saida"}">${formatarMoeda(caixa.diferenca)}</td>
        <td><span class="badge ${aberto ? "badge-ativo" : "badge-inativo"}">${aberto ? "Aberto" : "Fechado"}</span></td>
      `;
      corpo.appendChild(linha);
    });
  }

  // Sincroniza liberacao ou bloqueio da tela de Nova Entrada
  atualizarEstadoCaixaNaEntrada(caixaAberto);
}

// Carregar movimentacoes do turno ativo (Sangrias / Suprimentos)
async function carregarMovimentacoesCaixaAtivo() {
  const corpo = document.getElementById("tabela-caixa-movimentacoes");
  const empty = document.getElementById("caixa-movimentacoes-empty");
  const contador = document.getElementById("caixa-qtd-movimentacoes");
  if (!corpo) return;

  if (!caixaAberto) {
    corpo.innerHTML = '<tr><td colspan="5" class="table-empty">Nenhum caixa aberto no momento.</td></tr>';
    if (empty) empty.hidden = true;
    if (contador) contador.textContent = "0";
    return;
  }

  try {
    const dados = await chamarApi(`/caixa/${caixaAberto.id}/movimentacoes`);
    const movs = dados.movimentacoes || [];
    if (contador) contador.textContent = String(movs.length);
    corpo.innerHTML = "";

    if (!movs.length) {
      if (empty) empty.hidden = false;
    } else {
      if (empty) empty.hidden = true;
      movs.forEach((m) => {
        const tr = document.createElement("tr");
        const ehSuprimento = m.tipo === "suprimento";
        tr.innerHTML = `
          <td>${formatarDataHora(m.data)}</td>
          <td><span class="${ehSuprimento ? "badge-tipo-suprimento" : "badge-tipo-sangria"}">${ehSuprimento ? "+ Suprimento" : "− Sangria"}</span></td>
          <td class="cell-nome">${m.motivo || "—"}</td>
          <td>${m.operador || "—"}</td>
          <td style="text-align: right; font-weight: 700;" class="${ehSuprimento ? "valor-entrada" : "valor-saida"}">
            ${ehSuprimento ? "+" : "−"} ${formatarMoeda(m.valor)}
          </td>
        `;
        corpo.appendChild(tr);
      });
    }
  } catch (_) {
    corpo.innerHTML = '<tr><td colspan="5" class="table-empty">Não foi possível carregar movimentações.</td></tr>';
  }
}

// Alternancia entre Abas de Caixa (Pagamentos do Turno, Movimentacoes, Historico)
document.querySelectorAll(".caixa-tabs .tab").forEach((tabBtn) => {
  tabBtn.addEventListener("click", () => {
    document.querySelectorAll(".caixa-tabs .tab").forEach((t) => t.classList.remove("active"));
    tabBtn.classList.add("active");
    const aba = tabBtn.dataset.caixaTab;

    const painelPag = document.getElementById("painel-pagamentos-caixa");
    const painelMov = document.getElementById("painel-movimentacoes-caixa");
    const painelTurnos = document.getElementById("painel-turnos-caixa");

    if (painelPag) painelPag.hidden = aba !== "pagamentos";
    if (painelMov) painelMov.hidden = aba !== "movimentacoes";
    if (painelTurnos) painelTurnos.hidden = aba !== "turnos";

    if (aba === "movimentacoes") {
      carregarMovimentacoesCaixaAtivo();
    }
  });
});

function abrirModalAbrirCaixa() {
  document.getElementById("modal-abrir-caixa").hidden = false;
  setTimeout(() => document.getElementById("input-caixa-operador").focus(), 50);
}
function fecharModalAbrirCaixa() {
  document.getElementById("modal-abrir-caixa").hidden = true;
  document.getElementById("form-abrir-caixa").reset();
}
document.getElementById("btn-abrir-caixa").addEventListener("click", abrirModalAbrirCaixa);
document.getElementById("modal-abrir-caixa-fechar").addEventListener("click", fecharModalAbrirCaixa);
document.getElementById("btn-abrir-caixa-cancelar").addEventListener("click", fecharModalAbrirCaixa);
document.getElementById("modal-abrir-caixa").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) fecharModalAbrirCaixa();
});
document.getElementById("form-abrir-caixa").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    operador: document.getElementById("input-caixa-operador").value.trim(),
    valor_inicial: Number(document.getElementById("input-caixa-valor-inicial").value || 0),
    observacoes: document.getElementById("input-caixa-observacoes").value.trim(),
  };
  try {
    const dados = await chamarApi("/caixa", { method: "POST", body: JSON.stringify(payload) });
    mostrarToast(dados.mensagem, "success");
    fecharModalAbrirCaixa();
    await carregarCaixa();
    await carregarDashboard();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});

// Fechar caixa
async function abrirModalFecharCaixa() {
  if (!caixaAberto) return;
  try {
    const dados = await chamarApi(`/caixa/${caixaAberto.id}/resumo`);
    const resumo = dados.resumo || {};
    const esperado = resumo.saldo_total || 0;
    const totais = resumo.totais_por_forma || {};
    document.getElementById("fechamento-resumo").innerHTML = `
      <div class="fechamento-linha"><span>Valor total esperado</span><strong>${formatarMoeda(esperado)}</strong></div>
      <div class="fechamento-linha"><span>Esperado em dinheiro (gaveta)</span><strong>${formatarMoeda(resumo.saldo_dinheiro || 0)}</strong></div>
      ${Object.entries(totais).map(([forma, valor]) =>
        `<div class="fechamento-linha"><span>${FORMAS_LABEL[forma] || forma}</span><strong>${formatarMoeda(valor)}</strong></div>`
      ).join("")}
    `;
    document.getElementById("modal-fechar-caixa").hidden = false;
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
}
function fecharModalFecharCaixa() {
  document.getElementById("modal-fechar-caixa").hidden = true;
  document.getElementById("form-fechar-caixa").reset();
}
document.getElementById("btn-fechar-caixa").addEventListener("click", abrirModalFecharCaixa);
document.getElementById("modal-fechar-caixa-fechar").addEventListener("click", fecharModalFecharCaixa);
document.getElementById("btn-fechar-caixa-cancelar").addEventListener("click", fecharModalFecharCaixa);
document.getElementById("modal-fechar-caixa").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) fecharModalFecharCaixa();
});
document.getElementById("form-fechar-caixa").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!caixaAberto) return;
  const payload = {
    valor_contado: Number(document.getElementById("input-caixa-valor-contado").value || 0),
    observacoes: document.getElementById("input-caixa-fechar-observacoes").value.trim(),
  };
  try {
    const dados = await chamarApi(`/caixa/${caixaAberto.id}/fechar`, { method: "POST", body: JSON.stringify(payload) });
    mostrarToast(dados.mensagem, "success");
    fecharModalFecharCaixa();
    await carregarCaixa();
    await carregarDashboard();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});

// Sangria / Suprimento
function abrirModalMovimento(tipo) {
  document.getElementById("input-movimento-tipo").value = tipo;
  document.getElementById("modal-movimento-titulo").textContent = tipo === "sangria" ? "Sangria" : "Suprimento";
  document.getElementById("modal-movimento-caixa").hidden = false;
  setTimeout(() => document.getElementById("input-movimento-valor").focus(), 50);
}
function fecharModalMovimento() {
  document.getElementById("modal-movimento-caixa").hidden = true;
  document.getElementById("form-movimento-caixa").reset();
}
document.getElementById("btn-sangria").addEventListener("click", () => abrirModalMovimento("sangria"));
document.getElementById("btn-suprimento").addEventListener("click", () => abrirModalMovimento("suprimento"));
document.getElementById("modal-movimento-fechar").addEventListener("click", fecharModalMovimento);
document.getElementById("btn-movimento-cancelar").addEventListener("click", fecharModalMovimento);
document.getElementById("modal-movimento-caixa").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) fecharModalMovimento();
});
document.getElementById("form-movimento-caixa").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!caixaAberto) return;
  const tipo = document.getElementById("input-movimento-tipo").value;
  const payload = {
    valor: Number(document.getElementById("input-movimento-valor").value),
    motivo: document.getElementById("input-movimento-motivo").value.trim(),
  };
  try {
    const dados = await chamarApi(`/caixa/${caixaAberto.id}/${tipo}`, { method: "POST", body: JSON.stringify(payload) });
    mostrarToast(dados.mensagem, "success");
    fecharModalMovimento();
    await carregarCaixa();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});

// ---------------------- PAGAMENTOS (FRENTE DE CAIXA) ----------------------

let cachePagamentosCaixa = [];

function renderizarTabelaPagamentosCaixa() {
  const corpo = document.getElementById("tabela-pagamentos");
  const empty = document.getElementById("pagamentos-empty");
  const contador = document.getElementById("caixa-qtd-pagamentos");
  const inputBusca = document.getElementById("filtro-caixa-busca");
  const selectForma = document.getElementById("filtro-caixa-forma");

  if (!corpo) return;

  const termo = (inputBusca?.value || "").trim().toLowerCase();
  const formaFiltro = (selectForma?.value || "todas").toLowerCase();

  let lista = cachePagamentosCaixa;

  if (contador) contador.textContent = String(lista.length);

  if (termo) {
    lista = lista.filter((p) => {
      const ticketStr = String(p.ticket_numero || "");
      const opStr = String(p.operador || "").toLowerCase();
      return ticketStr.includes(termo) || opStr.includes(termo);
    });
  }

  if (formaFiltro && formaFiltro !== "todas") {
    lista = lista.filter((p) => (p.forma_pagamento || "").toLowerCase() === formaFiltro);
  }

  corpo.innerHTML = "";
  if (!lista.length) {
    if (empty) empty.hidden = false;
  } else {
    if (empty) empty.hidden = true;
    lista.forEach((pagamento) => {
      const linha = document.createElement("tr");
      const status = pagamento.status;
      const badge = status === "ativo" ? "badge-status-ativo" : status === "cancelado" ? "badge-status-cancelado" : "badge-status-estornado";
      linha.innerHTML = `
        <td><strong>#${pagamento.ticket_numero || "—"}</strong></td>
        <td>${formatarDataHora(pagamento.data)}</td>
        <td class="valor-entrada" style="text-align: right; font-weight: 700;">${formatarMoeda(pagamento.valor)}</td>
        <td><span class="badge-forma badge-forma-${pagamento.forma_pagamento}">${FORMAS_LABEL[pagamento.forma_pagamento] || pagamento.forma_pagamento}</span></td>
        <td>${pagamento.operador || "—"}</td>
        <td style="text-align: center;"><span class="${badge}">${rotuloStatus(status)}</span></td>
        <td class="col-acoes">
          ${status === "ativo" ? `
            <button type="button" class="btn-acao" data-acao-pagamento="cancelar" data-id="${pagamento.id}" title="Cancelar">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
            </button>
            <button type="button" class="btn-acao btn-acao-danger" data-acao-pagamento="estornar" data-id="${pagamento.id}" title="Estornar">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M3 3v5h5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
          ` : ""}
        </td>
      `;
      corpo.appendChild(linha);
    });
  }
}

async function carregarPagamentos() {
  const corpo = document.getElementById("tabela-pagamentos");
  try {
    const dados = await chamarApi("/pagamentos");
    cachePagamentosCaixa = dados.pagamentos || [];
    renderizarTabelaPagamentosCaixa();
  } catch (erro) {
    mostrarToast(erro.message, "error");
    if (corpo) corpo.innerHTML = '<tr><td colspan="7" class="table-empty">Erro ao carregar pagamentos.</td></tr>';
  }
}

// Listeners dos filtros de pagamentos no caixa
document.getElementById("filtro-caixa-busca")?.addEventListener("input", renderizarTabelaPagamentosCaixa);
document.getElementById("filtro-caixa-forma")?.addEventListener("change", renderizarTabelaPagamentosCaixa);
document.getElementById("btn-limpar-busca-caixa")?.addEventListener("click", () => {
  const b = document.getElementById("filtro-caixa-busca");
  const f = document.getElementById("filtro-caixa-forma");
  if (b) b.value = "";
  if (f) f.value = "todas";
  renderizarTabelaPagamentosCaixa();
});

function abrirModalPagamentoAcao(id, tipo) {
  document.getElementById("input-pagamento-acao-id").value = id;
  document.getElementById("input-pagamento-acao-tipo").value = tipo;
  document.getElementById("modal-pagamento-acao-titulo").textContent =
    tipo === "cancelar" ? "Cancelar pagamento" : "Estornar pagamento";
  document.getElementById("modal-pagamento-acao").hidden = false;
  setTimeout(() => document.getElementById("input-pagamento-acao-motivo").focus(), 50);
}
function fecharModalPagamentoAcao() {
  document.getElementById("modal-pagamento-acao").hidden = true;
  document.getElementById("form-pagamento-acao").reset();
}
document.getElementById("modal-pagamento-acao-fechar").addEventListener("click", fecharModalPagamentoAcao);
document.getElementById("btn-pagamento-acao-cancelar").addEventListener("click", fecharModalPagamentoAcao);
document.getElementById("modal-pagamento-acao").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) fecharModalPagamentoAcao();
});
document.getElementById("form-pagamento-acao").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("input-pagamento-acao-id").value;
  const tipo = document.getElementById("input-pagamento-acao-tipo").value;
  const payload = {
    motivo: document.getElementById("input-pagamento-acao-motivo").value.trim(),
    autorizador: document.getElementById("input-pagamento-acao-autorizador").value.trim(),
  };
  try {
    const dados = await chamarApi(`/pagamentos/${id}/${tipo}`, { method: "POST", body: JSON.stringify(payload) });
    mostrarToast(dados.mensagem, "success");
    fecharModalPagamentoAcao();
    await carregarPagamentos();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});
document.getElementById("tabela-pagamentos").addEventListener("click", (evento) => {
  const botao = evento.target.closest("button[data-acao-pagamento]");
  if (!botao) return;
  abrirModalPagamentoAcao(botao.dataset.id, botao.dataset.acaoPagamento);
});

// ---------------------- MENSALISTAS ----------------------

async function carregarMensalistas() {
  const corpo = document.getElementById("tabela-mensalistas");
  const empty = document.getElementById("mensalistas-empty");
  corpo.innerHTML = "";

  let dados;
  try {
    dados = await chamarApi("/mensalistas");
  } catch (erro) {
    mostrarToast(erro.message, "error");
    corpo.innerHTML = '<tr><td colspan="7" class="table-empty">Erro ao carregar mensalistas.</td></tr>';
    return;
  }

  const mensalistas = dados.mensalistas || [];
  empty.hidden = mensalistas.length > 0;

  mensalistas.forEach((m) => {
    const linha = document.createElement("tr");
    const badge = m.status === "ativo" ? "badge-ativo" : m.status === "bloqueado" ? "badge-warn" : "badge-inativo";
    linha.innerHTML = `
      <td class="cell-nome">${m.nome}</td>
      <td>${m.cpf_cnpj || "—"}</td>
      <td>${m.telefone || "—"}</td>
      <td>${formatarMoeda(m.valor_mensal)}</td>
      <td>Dia ${m.dia_vencimento}</td>
      <td><span class="badge ${badge}">${rotuloStatus(m.status)}</span></td>
      <td class="col-acoes">
        <button type="button" class="btn-acao" data-acao-mensalista="editar" data-id="${m.id}" title="Editar">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        ${m.status === "ativo" ? `
          <button type="button" class="btn-acao btn-acao-danger" data-acao-mensalista="bloquear" data-id="${m.id}" title="Bloquear">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="4" y="11" width="16" height="10" rx="2" stroke="currentColor" stroke-width="1.8"/><path d="M8 11V7a4 4 0 0 1 8 0v4" stroke="currentColor" stroke-width="1.8"/></svg>
          </button>
        ` : `
          <button type="button" class="btn-acao" data-acao-mensalista="desbloquear" data-id="${m.id}" title="Desbloquear">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="4" y="11" width="16" height="10" rx="2" stroke="currentColor" stroke-width="1.8"/><path d="M8 11V7a4 4 0 0 1 7.7-1.5" stroke="currentColor" stroke-width="1.8"/></svg>
          </button>
        `}
      </td>
    `;
    corpo.appendChild(linha);
  });
}

function abrirModalMensalista(m = null) {
  document.getElementById("input-mensalista-id").value = m ? m.id : "";
  document.getElementById("input-mensalista-nome").value = m ? m.nome : "";
  document.getElementById("input-mensalista-cpf").value = m ? m.cpf_cnpj : "";
  document.getElementById("input-mensalista-telefone").value = m ? m.telefone : "";
  document.getElementById("input-mensalista-email").value = m ? m.email : "";
  document.getElementById("input-mensalista-valor").value = m ? m.valor_mensal : "";
  document.getElementById("input-mensalista-vencimento").value = m ? m.dia_vencimento : 5;
  document.getElementById("modal-mensalista-titulo").textContent = m ? "Editar mensalista" : "Novo mensalista";
  document.getElementById("modal-mensalista").hidden = false;
  setTimeout(() => document.getElementById("input-mensalista-nome").focus(), 50);
}
function fecharModalMensalista() {
  document.getElementById("modal-mensalista").hidden = true;
  document.getElementById("form-mensalista").reset();
}
document.getElementById("btn-novo-mensalista").addEventListener("click", () => abrirModalMensalista());
document.getElementById("modal-mensalista-fechar").addEventListener("click", fecharModalMensalista);
document.getElementById("btn-mensalista-cancelar").addEventListener("click", fecharModalMensalista);
document.getElementById("modal-mensalista").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) fecharModalMensalista();
});
document.getElementById("form-mensalista").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("input-mensalista-id").value;
  const payload = {
    nome: document.getElementById("input-mensalista-nome").value.trim(),
    cpf_cnpj: document.getElementById("input-mensalista-cpf").value.trim(),
    telefone: document.getElementById("input-mensalista-telefone").value.trim(),
    email: document.getElementById("input-mensalista-email").value.trim(),
    valor_mensal: Number(document.getElementById("input-mensalista-valor").value),
    dia_vencimento: Number(document.getElementById("input-mensalista-vencimento").value),
  };
  try {
    const dados = id
      ? await chamarApi(`/mensalistas/${id}`, { method: "PUT", body: JSON.stringify(payload) })
      : await chamarApi("/mensalistas", { method: "POST", body: JSON.stringify(payload) });
    mostrarToast(dados.mensagem, "success");
    fecharModalMensalista();
    await carregarMensalistas();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});
document.getElementById("tabela-mensalistas").addEventListener("click", async (evento) => {
  const botao = evento.target.closest("button[data-acao-mensalista]");
  if (!botao) return;
  const id = botao.dataset.id;
  const acao = botao.dataset.acaoMensalista;
  if (acao === "editar") {
    try {
      const dados = await chamarApi("/mensalistas");
      const m = (dados.mensalistas || []).find((x) => String(x.id) === String(id));
      if (m) abrirModalMensalista(m);
    } catch (erro) {
      mostrarToast(erro.message, "error");
    }
    return;
  }
  try {
    const dados = await chamarApi(`/mensalistas/${id}/${acao}`, { method: "POST" });
    mostrarToast(dados.mensagem, "success");
    await carregarMensalistas();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});

// ---------------------- CONVENIOS ----------------------

async function carregarConvenios() {
  const corpo = document.getElementById("tabela-convenios");
  const empty = document.getElementById("convenios-empty");
  corpo.innerHTML = "";

  let dados;
  try {
    dados = await chamarApi("/convenios");
  } catch (erro) {
    mostrarToast(erro.message, "error");
    corpo.innerHTML = '<tr><td colspan="5" class="table-empty">Erro ao carregar convênios.</td></tr>';
    return;
  }

  const convenios = dados.convenios || [];
  empty.hidden = convenios.length > 0;

  convenios.forEach((c) => {
    const linha = document.createElement("tr");
    linha.innerHTML = `
      <td class="cell-nome">${c.nome}</td>
      <td>${c.cnpj || "—"}</td>
      <td>${c.contato || "—"}</td>
      <td><span class="badge ${c.ativo ? "badge-ativo" : "badge-inativo"}">${c.ativo ? "Ativo" : "Inativo"}</span></td>
      <td class="col-acoes">
        <button type="button" class="btn-acao" data-acao-convenio="editar" data-id="${c.id}" title="Editar">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
      </td>
    `;
    corpo.appendChild(linha);
  });
}

function abrirModalConvenio(c = null) {
  document.getElementById("input-convenio-id").value = c ? c.id : "";
  document.getElementById("input-convenio-nome").value = c ? c.nome : "";
  document.getElementById("input-convenio-cnpj").value = c ? c.cnpj : "";
  document.getElementById("input-convenio-contato").value = c ? c.contato : "";
  document.getElementById("modal-convenio-titulo").textContent = c ? "Editar convênio" : "Novo convênio";
  document.getElementById("modal-convenio").hidden = false;
  setTimeout(() => document.getElementById("input-convenio-nome").focus(), 50);
}
function fecharModalConvenio() {
  document.getElementById("modal-convenio").hidden = true;
  document.getElementById("form-convenio").reset();
}
document.getElementById("btn-novo-convenio").addEventListener("click", () => abrirModalConvenio());
document.getElementById("modal-convenio-fechar").addEventListener("click", fecharModalConvenio);
document.getElementById("btn-convenio-cancelar").addEventListener("click", fecharModalConvenio);
document.getElementById("modal-convenio").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) fecharModalConvenio();
});
document.getElementById("form-convenio").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("input-convenio-id").value;
  const payload = {
    nome: document.getElementById("input-convenio-nome").value.trim(),
    cnpj: document.getElementById("input-convenio-cnpj").value.trim(),
    contato: document.getElementById("input-convenio-contato").value.trim(),
  };
  try {
    const dados = id
      ? await chamarApi(`/convenios/${id}`, { method: "PUT", body: JSON.stringify(payload) })
      : await chamarApi("/convenios", { method: "POST", body: JSON.stringify(payload) });
    mostrarToast(dados.mensagem, "success");
    fecharModalConvenio();
    await carregarConvenios();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});
document.getElementById("tabela-convenios").addEventListener("click", async (evento) => {
  const botao = evento.target.closest("button[data-acao-convenio]");
  if (!botao) return;
  try {
    const dados = await chamarApi("/convenios");
    const c = (dados.convenios || []).find((x) => String(x.id) === String(botao.dataset.id));
    if (c) abrirModalConvenio(c);
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});

// ---------------------- CONTAS A RECEBER ----------------------

async function carregarContasReceber() {
  const corpo = document.getElementById("tabela-contas-receber");
  const empty = document.getElementById("contas-receber-empty");
  corpo.innerHTML = "";

  let dados;
  try {
    dados = await chamarApi("/contas-receber");
  } catch (erro) {
    mostrarToast(erro.message, "error");
    corpo.innerHTML = '<tr><td colspan="6" class="table-empty">Erro ao carregar contas a receber.</td></tr>';
    return;
  }

  const contas = dados.contas_receber || [];
  empty.hidden = contas.length > 0;

  // Mapa de convenios para exibir o nome
  let conveniosMap = {};
  try {
    const cv = await chamarApi("/convenios");
    (cv.convenios || []).forEach((c) => { conveniosMap[c.id] = c.nome; });
  } catch (erro) { /* ignora */ }

  contas.forEach((conta) => {
    const linha = document.createElement("tr");
    const badge = conta.status === "aberta" ? "badge-warn" : conta.status === "paga" ? "badge-ativo" : "badge-inativo";
    linha.innerHTML = `
      <td>${conveniosMap[conta.convenio_id] || "—"}</td>
      <td>${conta.descricao || "—"}</td>
      <td class="valor-entrada">${formatarMoeda(conta.valor)}</td>
      <td>${formatarDataHora(conta.vencimento)}</td>
      <td><span class="badge ${badge}">${rotuloStatus(conta.status)}</span></td>
      <td class="col-acoes">
        ${conta.status === "aberta" ? `
          <button type="button" class="btn-acao" data-acao-conta="baixar" data-id="${conta.id}" title="Baixar (pagar)">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        ` : ""}
      </td>
    `;
    corpo.appendChild(linha);
  });
}

function abrirModalConta() {
  const select = document.getElementById("input-conta-convenio");
  select.innerHTML = "";
  chamarApi("/convenios").then((dados) => {
    (dados.convenios || []).forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c.id;
      opt.textContent = c.nome;
      select.appendChild(opt);
    });
  }).catch(() => {});
  document.getElementById("modal-conta").hidden = false;
}
function fecharModalConta() {
  document.getElementById("modal-conta").hidden = true;
  document.getElementById("form-conta").reset();
}
document.getElementById("btn-novo-conta").addEventListener("click", abrirModalConta);
document.getElementById("modal-conta-fechar").addEventListener("click", fecharModalConta);
document.getElementById("btn-conta-cancelar").addEventListener("click", fecharModalConta);
document.getElementById("modal-conta").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) fecharModalConta();
});
document.getElementById("form-conta").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    convenio_id: Number(document.getElementById("input-conta-convenio").value),
    descricao: document.getElementById("input-conta-descricao").value.trim(),
    valor: Number(document.getElementById("input-conta-valor").value),
    vencimento: document.getElementById("input-conta-vencimento").value.trim(),
  };
  try {
    const dados = await chamarApi("/contas-receber", { method: "POST", body: JSON.stringify(payload) });
    mostrarToast(dados.mensagem, "success");
    fecharModalConta();
    await carregarContasReceber();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});
document.getElementById("tabela-contas-receber").addEventListener("click", async (evento) => {
  const botao = evento.target.closest("button[data-acao-conta]");
  if (!botao) return;
  if (botao.dataset.acaoConta === "baixar") {
    if (!confirm("Confirmar baixa (pagamento) desta conta a receber?")) return;
    try {
      const dados = await chamarApi(`/contas-receber/${botao.dataset.id}/baixar`, { method: "POST", body: JSON.stringify({}) });
      mostrarToast(dados.mensagem, "success");
      await carregarContasReceber();
    } catch (erro) {
      mostrarToast(erro.message, "error");
    }
  }
});

// ---------------------- DESCONTOS ----------------------

async function carregarDescontos() {
  const corpo = document.getElementById("tabela-descontos");
  const empty = document.getElementById("descontos-empty");
  corpo.innerHTML = "";

  let dados;
  try {
    dados = await chamarApi("/descontos");
  } catch (erro) {
    mostrarToast(erro.message, "error");
    corpo.innerHTML = '<tr><td colspan="7" class="table-empty">Erro ao carregar descontos.</td></tr>';
    return;
  }

  const descontos = dados.descontos || [];
  empty.hidden = descontos.length > 0;

  descontos.forEach((d) => {
    const linha = document.createElement("tr");
    const valor = d.tipo === "percentual" ? `${d.valor}%` : formatarMoeda(d.valor);
    linha.innerHTML = `
      <td class="cell-nome">${d.nome}</td>
      <td><span class="badge">${d.tipo === "percentual" ? "Percentual" : "Fixo"}</span></td>
      <td>${valor}</td>
      <td>${d.motivo || "—"}</td>
      <td>${d.necessita_autorizacao ? "Sim" : "Não"}</td>
      <td><span class="badge ${d.ativo ? "badge-ativo" : "badge-inativo"}">${d.ativo ? "Ativo" : "Inativo"}</span></td>
      <td class="col-acoes">
        <button type="button" class="btn-acao" data-acao-desconto="editar" data-id="${d.id}" title="Editar">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
      </td>
    `;
    corpo.appendChild(linha);
  });
}

function abrirModalDesconto(d = null) {
  document.getElementById("input-desconto-id").value = d ? d.id : "";
  document.getElementById("input-desconto-nome").value = d ? d.nome : "";
  document.getElementById("input-desconto-tipo").value = d ? d.tipo : "percentual";
  document.getElementById("input-desconto-valor").value = d ? d.valor : "";
  document.getElementById("input-desconto-motivo").value = d ? d.motivo : "";
  document.getElementById("input-desconto-autorizacao").checked = d ? d.necessita_autorizacao : false;
  document.getElementById("modal-desconto-titulo").textContent = d ? "Editar desconto" : "Novo desconto";
  document.getElementById("modal-desconto").hidden = false;
  setTimeout(() => document.getElementById("input-desconto-nome").focus(), 50);
}
function fecharModalDesconto() {
  document.getElementById("modal-desconto").hidden = true;
  document.getElementById("form-desconto").reset();
}
document.getElementById("btn-novo-desconto").addEventListener("click", () => abrirModalDesconto());
document.getElementById("modal-desconto-fechar").addEventListener("click", fecharModalDesconto);
document.getElementById("btn-desconto-cancelar").addEventListener("click", fecharModalDesconto);
document.getElementById("modal-desconto").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) fecharModalDesconto();
});
document.getElementById("form-desconto").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("input-desconto-id").value;
  const payload = {
    nome: document.getElementById("input-desconto-nome").value.trim(),
    tipo: document.getElementById("input-desconto-tipo").value,
    valor: Number(document.getElementById("input-desconto-valor").value),
    motivo: document.getElementById("input-desconto-motivo").value.trim(),
    necessita_autorizacao: document.getElementById("input-desconto-autorizacao").checked,
  };
  try {
    const dados = id
      ? await chamarApi(`/descontos/${id}`, { method: "PUT", body: JSON.stringify(payload) })
      : await chamarApi("/descontos", { method: "POST", body: JSON.stringify(payload) });
    mostrarToast(dados.mensagem, "success");
    fecharModalDesconto();
    await carregarDescontos();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});
document.getElementById("tabela-descontos").addEventListener("click", async (evento) => {
  const botao = evento.target.closest("button[data-acao-desconto]");
  if (!botao) return;
  try {
    const dados = await chamarApi("/descontos");
    const d = (dados.descontos || []).find((x) => String(x.id) === String(botao.dataset.id));
    if (d) abrirModalDesconto(d);
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});

// ---------------------- CORTESIAS ----------------------

async function carregarCortesias() {
  const corpo = document.getElementById("tabela-cortesias");
  const empty = document.getElementById("cortesias-empty");
  corpo.innerHTML = "";

  let dados;
  try {
    dados = await chamarApi("/cortesias");
  } catch (erro) {
    mostrarToast(erro.message, "error");
    corpo.innerHTML = '<tr><td colspan="7" class="table-empty">Erro ao carregar cortesias.</td></tr>';
    return;
  }

  const cortesias = dados.cortesias || [];
  empty.hidden = cortesias.length > 0;

  cortesias.forEach((c) => {
    const linha = document.createElement("tr");
    linha.innerHTML = `
      <td>${formatarDataHora(c.data)}</td>
      <td class="cell-nome">${c.motivo}</td>
      <td>${c.usuario || "—"}</td>
      <td>${c.autorizador || "—"}</td>
      <td>${c.ticket_numero || "—"}</td>
      <td><span class="badge ${c.status === "ativo" ? "badge-ativo" : "badge-inativo"}">${c.status}</span></td>
      <td class="col-acoes">
        ${c.status === "ativo" ? `
          <button type="button" class="btn-acao btn-acao-danger" data-acao-cortesia="cancelar" data-id="${c.id}" title="Cancelar">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          </button>
        ` : ""}
      </td>
    `;
    corpo.appendChild(linha);
  });
}

function abrirModalCortesia() {
  document.getElementById("modal-cortesia").hidden = false;
  setTimeout(() => document.getElementById("input-cortesia-motivo").focus(), 50);
}
function fecharModalCortesia() {
  document.getElementById("modal-cortesia").hidden = true;
  document.getElementById("form-cortesia").reset();
}
document.getElementById("btn-novo-cortesia").addEventListener("click", abrirModalCortesia);
document.getElementById("modal-cortesia-fechar").addEventListener("click", fecharModalCortesia);
document.getElementById("btn-cortesia-cancelar").addEventListener("click", fecharModalCortesia);
document.getElementById("modal-cortesia").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) fecharModalCortesia();
});
document.getElementById("form-cortesia").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    motivo: document.getElementById("input-cortesia-motivo").value.trim(),
    ticket_numero: Number(document.getElementById("input-cortesia-ticket").value || 0) || null,
    autorizador: document.getElementById("input-cortesia-autorizador").value.trim(),
  };
  try {
    const dados = await chamarApi("/cortesias", { method: "POST", body: JSON.stringify(payload) });
    mostrarToast(dados.mensagem, "success");
    fecharModalCortesia();
    await carregarCortesias();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});
document.getElementById("tabela-cortesias").addEventListener("click", async (evento) => {
  const botao = evento.target.closest("button[data-acao-cortesia]");
  if (!botao) return;
  if (!confirm("Cancelar esta cortesia?")) return;
  try {
    const dados = await chamarApi(`/cortesias/${botao.dataset.id}/cancelar`, { method: "POST", body: JSON.stringify({}) });
    mostrarToast(dados.mensagem, "success");
    await carregarCortesias();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});

// ---------------------- AUDITORIA ----------------------

const AUDITORIA_PAGE_SIZE = 25;
let auditoriaAlteracoes = [];
let auditoriaAcessos = [];
let auditoriaAbaAtual = "alteracoes";
let auditoriaPagina = 1;

function escaparHtml(texto) {
  return String(texto == null ? "" : texto)
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

function formatarDataAuditoria(data) {
  // Aceita "DD/MM/YYYY HH:MM:SS" ou ISO; devolve "DD/MM HH:MM" quando possivel
  if (!data) return "—";
  const m = String(data).match(/^(\d{2})\/(\d{2})\/(\d{4})[ T](\d{2}):(\d{2})/);
  if (m) return `${m[1]}/${m[2]}/${m[3]} ${m[4]}:${m[5]}`;
  const d = new Date(data);
  if (!isNaN(d)) return d.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
  return String(data);
}

function audDentroDoPeriodo(data) {
  const filtro = document.getElementById("filtro-auditoria-periodo").value;
  if (filtro === "tudo") return true;
  const d = new Date(String(data).replace(" ", "T"));
  if (isNaN(d)) return filtro === "tudo";
  const agora = new Date();
  if (filtro === "hoje") {
    return d.getFullYear() === agora.getFullYear() && d.getMonth() === agora.getMonth() && d.getDate() === agora.getDate();
  }
  const dias = parseInt(filtro, 10);
  return (agora - d) <= dias * 24 * 60 * 60 * 1000;
}

async function carregarAuditoria() {
  try {
    const [alt, logs] = await Promise.all([chamarApi("/auditoria"), chamarApi("/logs-acesso")]);
    auditoriaAlteracoes = (alt.auditoria || []).slice().reverse();
    auditoriaAcessos = (logs.logs_acesso || []).slice().reverse();
  } catch (erro) {
    mostrarToast(erro.message, "error");
    auditoriaAlteracoes = [];
    auditoriaAcessos = [];
  }

  // Resumo
  document.getElementById("aud-total-alteracoes").textContent = auditoriaAlteracoes.length;
  document.getElementById("aud-total-acessos").textContent = auditoriaAcessos.length;
  const ultimo = auditoriaAcessos.find((l) => l.acao === "login") || auditoriaAcessos[0];
  document.getElementById("aud-ultimo-acesso").textContent =
    ultimo ? `${ultimo.usuario || "—"} · ${formatarDataAuditoria(ultimo.data)}` : "—";

  preencherFiltrosAuditoria();
  auditoriaPagina = 1;
  renderizarAuditoria();
}

function preencherFiltrosAuditoria() {
  const selUsuario = document.getElementById("filtro-auditoria-usuario");
  const selTabela = document.getElementById("filtro-auditoria-tabela");
  const usuarioAtual = selUsuario.value;
  const tabelaAtual = selTabela.value;

  const usuarios = new Set();
  auditoriaAlteracoes.forEach((a) => a.usuario && usuarios.add(a.usuario));
  auditoriaAcessos.forEach((l) => l.usuario && usuarios.add(l.usuario));
  const tabelas = new Set(auditoriaAlteracoes.map((a) => a.tabela).filter(Boolean));

  selUsuario.innerHTML = '<option value="">Todos os usuários</option>' +
    [...usuarios].sort().map((u) => `<option value="${escaparHtml(u)}">${escaparHtml(u)}</option>`).join("");
  selTabela.innerHTML = '<option value="">Todas as tabelas</option>' +
    [...tabelas].sort().map((t) => `<option value="${escaparHtml(t)}">${escaparHtml(t)}</option>`).join("");

  selUsuario.value = usuarios.has(usuarioAtual) ? usuarioAtual : "";
  selTabela.value = tabelas.has(tabelaAtual) ? tabelaAtual : "";
}

function audFiltrados() {
  const busca = document.getElementById("filtro-auditoria-busca").value.trim().toLowerCase();
  const usuario = document.getElementById("filtro-auditoria-usuario").value;
  const tabela = document.getElementById("filtro-auditoria-tabela").value;
  const acao = document.getElementById("filtro-auditoria-acao").value;
  const ehAcessos = auditoriaAbaAtual === "acessos";

  const base = ehAcessos ? auditoriaAcessos : auditoriaAlteracoes;
  return base.filter((item) => {
    if (!audDentroDoPeriodo(item.data)) return false;
    if (usuario && (item.usuario || "") !== usuario) return false;
    if (ehAcessos) {
      if (acao && (item.acao || "") !== acao) return false;
    } else if (tabela && (item.tabela || "") !== tabela) {
      return false;
    }
    if (busca) {
      const alvo = ehAcessos
        ? `${item.usuario || ""} ${item.acao || ""} ${item.modulo || ""} ${item.ip || ""}`
        : `${item.tabela || ""} ${item.registro_id || ""} ${item.campo || ""} ${item.valor_antigo || ""} ${item.valor_novo || ""} ${item.usuario || ""}`;
      if (!alvo.toLowerCase().includes(busca)) return false;
    }
    return true;
  });
}

function renderizarAuditoria() {
  const ehAcessos = auditoriaAbaAtual === "acessos";
  const corpo = document.getElementById(ehAcessos ? "tabela-auditoria-acessos" : "tabela-auditoria");
  const empty = document.getElementById(ehAcessos ? "auditoria-acessos-empty" : "auditoria-empty");
  const filtrados = audFiltrados();

  const totalPaginas = Math.max(1, Math.ceil(filtrados.length / AUDITORIA_PAGE_SIZE));
  if (auditoriaPagina > totalPaginas) auditoriaPagina = totalPaginas;
  const inicio = (auditoriaPagina - 1) * AUDITORIA_PAGE_SIZE;
  const pagina = filtrados.slice(inicio, inicio + AUDITORIA_PAGE_SIZE);

  corpo.innerHTML = "";
  if (!pagina.length) {
    empty.hidden = false;
  } else {
    empty.hidden = true;
    pagina.forEach((item) => {
      const linha = document.createElement("tr");
      if (ehAcessos) {
        const corAcao = item.acao === "login" ? "badge-success" : item.acao === "logout" ? "badge-danger" : "";
        linha.innerHTML = `
          <td>${escaparHtml(formatarDataAuditoria(item.data))}</td>
          <td>${escaparHtml(item.usuario || "—")}</td>
          <td><span class="badge ${corAcao}">${escaparHtml(item.acao || "—")}</span></td>
          <td>${escaparHtml(item.modulo || "—")}</td>
          <td>${escaparHtml(item.ip || "—")}</td>
        `;
      } else {
        linha.innerHTML = `
          <td>${escaparHtml(formatarDataAuditoria(item.data))}</td>
          <td><span class="badge">${escaparHtml(item.tabela || "—")}</span></td>
          <td>${escaparHtml(item.registro_id || "—")}</td>
          <td>${escaparHtml(item.campo || "—")}</td>
          <td class="aud-alteracao">
            <span class="aud-valor-antigo">${escaparHtml(item.valor_antigo || "—")}</span>
            <span class="aud-seta">→</span>
            <span class="aud-valor-novo">${escaparHtml(item.valor_novo || "—")}</span>
          </td>
          <td>${escaparHtml(item.usuario || "—")}</td>
          <td>${escaparHtml(item.ip || "—")}</td>
        `;
      }
      corpo.appendChild(linha);
    });
  }

  document.getElementById("aud-pag-info").textContent = `Página ${auditoriaPagina} de ${totalPaginas}`;
  document.getElementById("aud-pag-anterior").disabled = auditoriaPagina <= 1;
  document.getElementById("aud-pag-proxima").disabled = auditoriaPagina >= totalPaginas;
  document.getElementById("aud-contagem").textContent =
    `${filtrados.length} registro${filtrados.length === 1 ? "" : "s"} encontrado${filtrados.length === 1 ? "" : "s"}`;
}

function exportarAuditoriaCSV() {
  const ehAcessos = auditoriaAbaAtual === "acessos";
  const filtrados = audFiltrados();
  let csv;
  if (ehAcessos) {
    csv = "Data;Usuario;Acao;Modulo;IP\n" + filtrados
      .map((l) => [formatarDataAuditoria(l.data), l.usuario, l.acao, l.modulo, l.ip].join(";"))
      .join("\n");
  } else {
    csv = "Data;Tabela;Registro;Campo;ValorAntigo;ValorNovo;Usuario;IP\n" + filtrados
      .map((a) => [formatarDataAuditoria(a.data), a.tabela, a.registro_id, a.campo, a.valor_antigo, a.valor_novo, a.usuario, a.ip].join(";"))
      .join("\n");
  }
  const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = ehAcessos ? "logs_acesso.csv" : "auditoria_alteracoes.csv";
  link.click();
  URL.revokeObjectURL(link.href);
}

// Abas da auditoria
document.querySelectorAll("#tabs-auditoria .tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll("#tabs-auditoria .tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    auditoriaAbaAtual = tab.dataset.auditoriaTab;
    auditoriaPagina = 1;

    document.querySelectorAll("[data-auditoria-pane]").forEach((pane) => {
      pane.hidden = pane.dataset.auditoriaPane !== auditoriaAbaAtual;
    });
    // Filtro especifico de cada aba
    document.getElementById("filtro-auditoria-tabela").hidden = auditoriaAbaAtual === "acessos";
    document.getElementById("filtro-auditoria-acao").hidden = auditoriaAbaAtual !== "acessos";

    renderizarAuditoria();
  });
});

["filtro-auditoria-busca", "filtro-auditoria-periodo", "filtro-auditoria-usuario", "filtro-auditoria-tabela", "filtro-auditoria-acao"].forEach((id) => {
  document.getElementById(id).addEventListener("input", () => {
    auditoriaPagina = 1;
    renderizarAuditoria();
  });
});
document.getElementById("filtro-auditoria-periodo").addEventListener("change", () => {
  auditoriaPagina = 1;
  renderizarAuditoria();
});
["filtro-auditoria-usuario", "filtro-auditoria-tabela", "filtro-auditoria-acao"].forEach((id) => {
  document.getElementById(id).addEventListener("change", () => {
    auditoriaPagina = 1;
    renderizarAuditoria();
  });
});

document.getElementById("btn-exportar-auditoria").addEventListener("click", exportarAuditoriaCSV);
document.getElementById("aud-pag-anterior").addEventListener("click", () => {
  if (auditoriaPagina > 1) { auditoriaPagina--; renderizarAuditoria(); }
});
document.getElementById("aud-pag-proxima").addEventListener("click", () => {
  auditoriaPagina++; renderizarAuditoria();
});

// ---------------------- DASHBOARD FINANCEIRO EXECUTIVO ----------------------

let dashCharts = {};
let cacheDashboardFinanceiro = null;
let periodoEvolucaoAtivo = "diario"; // "diario" | "mensal" | "anual"

function renderGraficoEvolucao() {
  if (!cacheDashboardFinanceiro) return;
  const canvas = document.getElementById("grafico-dash-evolucao");
  if (!canvas) return;

  let labels = [];
  let valores = [];
  let corBorda = "#3b82f6";
  let corFundo = "rgba(59, 130, 246, 0.7)";
  let tituloDataset = "Receita Diária";

  if (periodoEvolucaoAtivo === "mensal") {
    const dados = cacheDashboardFinanceiro.grafico_mensal || { labels: [], valores: [] };
    labels = dados.labels || [];
    valores = dados.valores || [];
    corBorda = "#10b981";
    corFundo = "rgba(16, 185, 129, 0.7)";
    tituloDataset = "Receita Mensal";
  } else if (periodoEvolucaoAtivo === "anual") {
    const dados = cacheDashboardFinanceiro.grafico_anual || { labels: [], valores: [] };
    labels = dados.labels || [];
    valores = dados.valores || [];
    corBorda = "#f59e0b";
    corFundo = "rgba(245, 158, 11, 0.7)";
    tituloDataset = "Receita Anual";
  } else {
    const dados = cacheDashboardFinanceiro.grafico_diario || { labels: [], valores: [] };
    labels = dados.labels || [];
    valores = dados.valores || [];
    corBorda = "#3b82f6";
    corFundo = "rgba(59, 130, 246, 0.7)";
    tituloDataset = "Receita Diária";
  }

  // Calcula pico do periodo ativo
  const picoPeriodo = valores.length > 0 ? Math.max(...valores) : 0;
  const picoEl = document.getElementById("dash-pico-periodo");
  if (picoEl) picoEl.textContent = formatarMoeda(picoPeriodo);

  if (dashCharts["grafico-dash-evolucao"]) {
    dashCharts["grafico-dash-evolucao"].destroy();
  }

  dashCharts["grafico-dash-evolucao"] = new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: tituloDataset,
        data: valores,
        backgroundColor: corFundo,
        borderColor: corBorda,
        borderWidth: 1.5,
        borderRadius: 5,
        maxBarThickness: 36,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${formatarMoeda(ctx.parsed.y)}`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (v) => formatarMoeda(v)
          },
          grid: {
            color: "#f1f5f9"
          }
        },
        x: {
          grid: {
            display: false
          }
        }
      },
    },
  });
}

function renderMixFormasPagamento(porForma) {
  const canvas = document.getElementById("grafico-dash-forma");
  const corpoTabela = document.getElementById("tabela-dash-formas-corpo");
  if (!canvas || !corpoTabela) return;

  const entradas = Object.entries(porForma || {}).filter(([, v]) => v > 0);
  const total = entradas.reduce((acc, [, v]) => acc + v, 0);

  const paletaCores = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#14b8a6", "#ef4444", "#64748b"];

  if (dashCharts["grafico-dash-forma"]) {
    dashCharts["grafico-dash-forma"].destroy();
  }

  if (entradas.length === 0) {
    corpoTabela.innerHTML = '<tr><td colspan="3" class="table-empty" style="padding: 24px; text-align: center; color: var(--color-text-muted);">Nenhum pagamento registrado no mês.</td></tr>';
    // Cria donut vazio cinza
    dashCharts["grafico-dash-forma"] = new Chart(canvas, {
      type: "doughnut",
      data: {
        labels: ["Sem dados"],
        datasets: [{ data: [1], backgroundColor: ["#e2e8f0"] }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        cutout: "70%",
      }
    });
    return;
  }

  // Ordena por maior valor
  entradas.sort((a, b) => b[1] - a[1]);

  const labels = entradas.map(([k]) => FORMAS_LABEL[k] || k);
  const valores = entradas.map(([, v]) => v);
  const cores = entradas.map((_, i) => paletaCores[i % paletaCores.length]);

  dashCharts["grafico-dash-forma"] = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data: valores,
        backgroundColor: cores,
        borderWidth: 2,
        borderColor: "#ffffff",
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const val = ctx.parsed;
              const pct = total > 0 ? Math.round((val / total) * 100) : 0;
              return ` ${ctx.label}: ${formatarMoeda(val)} (${pct}%)`;
            }
          }
        }
      },
      cutout: "68%",
    },
  });

  // Tabela analítica ao lado
  corpoTabela.innerHTML = "";
  entradas.forEach(([k, val], i) => {
    const nome = FORMAS_LABEL[k] || k;
    const cor = cores[i];
    const pct = total > 0 ? Math.round((val / total) * 100) : 0;

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>
        <div class="fin-payment-name">
          <span class="fin-dot" style="background: ${cor};"></span>
          <span>${nome}</span>
        </div>
      </td>
      <td class="fin-payment-val">${formatarMoeda(val)}</td>
      <td class="fin-payment-pct">${pct}%</td>
    `;
    corpoTabela.appendChild(tr);
  });
}

function renderFluxoHorario(porHorario, pico) {
  const canvas = document.getElementById("grafico-dash-horario");
  if (!canvas) return;

  const entradas = Object.entries(porHorario || {});
  const labels = entradas.map(([k]) => k);
  const valores = entradas.map(([, v]) => v);

  // Badge do pico
  const badgePico = document.getElementById("dash-badge-pico");
  if (pico && pico.valor > 0) {
    document.getElementById("dash-hora-pico").textContent = pico.hora;
    document.getElementById("dash-valor-pico").textContent = formatarMoeda(pico.valor);
    if (badgePico) badgePico.hidden = false;
  } else {
    if (badgePico) badgePico.hidden = true;
  }

  if (dashCharts["grafico-dash-horario"]) {
    dashCharts["grafico-dash-horario"].destroy();
  }

  dashCharts["grafico-dash-horario"] = new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Receita",
        data: valores,
        borderColor: "#8b5cf6",
        backgroundColor: "rgba(139, 92, 246, 0.12)",
        fill: true,
        tension: 0.35,
        borderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5,
        pointBackgroundColor: "#8b5cf6",
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `Receita: ${formatarMoeda(ctx.parsed.y)}`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { callback: (v) => formatarMoeda(v) },
          grid: { color: "#f1f5f9" }
        },
        x: {
          grid: { display: false }
        }
      },
    },
  });
}

function renderRankingOperadores(topOperadores) {
  const container = document.getElementById("dash-ranking-operadores");
  const emptyEl = document.getElementById("dash-ranking-empty");
  if (!container) return;

  container.innerHTML = "";
  if (!topOperadores || !topOperadores.length) {
    if (emptyEl) emptyEl.hidden = false;
    return;
  }
  if (emptyEl) emptyEl.hidden = true;

  const maxVal = Math.max(...topOperadores.map((o) => o.valor)) || 1;

  topOperadores.forEach((op, idx) => {
    const posClass = idx === 0 ? "top1" : idx === 1 ? "top2" : idx === 2 ? "top3" : "";
    const pct = Math.max(8, Math.round((op.valor / maxVal) * 100));

    const item = document.createElement("div");
    item.className = "fin-ranking-item";
    item.innerHTML = `
      <div class="fin-ranking-header">
        <span class="fin-ranking-name">
          <span class="fin-rank-pos ${posClass}">${idx + 1}º</span>
          ${op.nome || "Operador"}
        </span>
        <span class="fin-ranking-val">${formatarMoeda(op.valor)}</span>
      </div>
      <div class="fin-ranking-track">
        <div class="fin-ranking-fill" style="width: ${pct}%;"></div>
      </div>
    `;
    container.appendChild(item);
  });
}

function renderComparativoMensal(comp) {
  const c = comp || { mes_atual: 0, mes_anterior: 0, variacao_percentual: 0 };
  const atual = c.mes_atual || 0;
  const anterior = c.mes_anterior || 0;
  const diff = atual - anterior;
  const pct = c.variacao_percentual || 0;

  const elAnt = document.getElementById("dash-comp-anterior");
  const elAtu = document.getElementById("dash-comp-atual");
  const elDiff = document.getElementById("dash-comp-diff");
  const badgeVariacao = document.getElementById("dash-badge-variacao");
  const textoVariacao = document.getElementById("dash-texto-variacao");

  if (elAnt) elAnt.textContent = formatarMoeda(anterior);
  if (elAtu) elAtu.textContent = formatarMoeda(atual);

  if (elDiff) {
    if (diff > 0) {
      elDiff.textContent = `+${formatarMoeda(diff)} (+${pct}%)`;
      elDiff.style.color = "#059669";
    } else if (diff < 0) {
      elDiff.textContent = `${formatarMoeda(diff)} (${pct}%)`;
      elDiff.style.color = "#dc2626";
    } else {
      elDiff.textContent = `R$ 0,00 (0.0%)`;
      elDiff.style.color = "#64748b";
    }
  }

  // Badge do Topo
  if (badgeVariacao && textoVariacao) {
    badgeVariacao.classList.remove("trend-positive", "trend-negative", "trend-neutral");
    if (diff > 0) {
      badgeVariacao.classList.add("trend-positive");
      textoVariacao.textContent = `+${pct}% vs mês anterior`;
    } else if (diff < 0) {
      badgeVariacao.classList.add("trend-negative");
      textoVariacao.textContent = `${pct}% vs mês anterior`;
    } else {
      badgeVariacao.classList.add("trend-neutral");
      textoVariacao.textContent = `0% vs mês anterior`;
    }
  }

  const subMes = document.getElementById("dash-sub-receita-mes");
  if (subMes) {
    if (diff > 0) {
      subMes.innerHTML = `<span style="color: #059669; font-weight: 600;">▲ +${pct}%</span> vs mês anterior`;
    } else if (diff < 0) {
      subMes.innerHTML = `<span style="color: #dc2626; font-weight: 600;">▼ ${pct}%</span> vs mês anterior`;
    } else {
      subMes.textContent = "Acumulado mensal";
    }
  }
}

async function carregarDashboardFinanceiro() {
  try {
    const dados = await chamarApi("/dashboard-financeiro");
    cacheDashboardFinanceiro = dados;

    // 1. Cockpit de Indicadores Chave
    document.getElementById("dash-receita-dia").textContent = formatarMoeda(dados.receita_dia);
    document.getElementById("dash-receita-mes").textContent = formatarMoeda(dados.receita_mes);
    document.getElementById("dash-receita-ano").textContent = formatarMoeda(dados.receita_ano);
    document.getElementById("dash-tickets").textContent = dados.quantidade_tickets;
    document.getElementById("dash-ticket-medio").textContent = formatarMoeda(dados.ticket_medio);
    if (document.getElementById("dash-media-diaria")) {
      document.getElementById("dash-media-diaria").textContent = formatarMoeda(dados.media_diaria_mes || 0);
    }

    // 2. Gráfico de Evolução com abas
    renderGraficoEvolucao();

    // 3. Mix de Pagamentos
    renderMixFormasPagamento(dados.receita_por_forma);

    // 4. Fluxo por Horário
    renderFluxoHorario(dados.receita_por_horario, dados.pico_horario);

    // 5. Ranking dos Operadores
    renderRankingOperadores(dados.top_operadores);

    // 6. Comparativo Mensal
    renderComparativoMensal(dados.comparativo_mensal);

  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
}

// Listeners de alternancia de periodo e botoes do Dashboard Financeiro
document.querySelectorAll("#tabs-periodo-dash-fin .btn-fin-tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#tabs-periodo-dash-fin .btn-fin-tab").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    periodoEvolucaoAtivo = btn.dataset.periodo;
    renderGraficoEvolucao();
  });
});

document.getElementById("btn-refresh-dash-fin")?.addEventListener("click", () => {
  carregarDashboardFinanceiro();
  mostrarToast("Dashboard Financeiro atualizado!", "success");
});

document.getElementById("btn-ir-relatorios-fin")?.addEventListener("click", () => {
  mostrarView("view-relatorios");
});

// ---------------------- RELATORIOS FINANCEIROS (agrupamento + grafico) ----------------------

let relatorioAgrupamento = "dia";
let relatorioChart = null;

async function carregarRelatoriosFinanceiros() {
  try {
    const dados = await chamarApi(`/relatorio-financeiro?agrupamento=${relatorioAgrupamento}`);

    document.getElementById("rel-total-entradas").textContent = dados.total_saidas;
    document.getElementById("rel-total-saidas").textContent = dados.total_saidas;
    document.getElementById("rel-faturamento").textContent = formatarMoeda(dados.faturamento_total);
    document.getElementById("rel-ticket-medio").textContent = formatarMoeda(dados.ticket_medio);

    // Grafico de barras
    const canvas = document.getElementById("grafico-relatorio");
    if (relatorioChart) relatorioChart.destroy();
    relatorioChart = new Chart(canvas, {
      type: "bar",
      data: {
        labels: dados.labels,
        datasets: [{
          label: "Faturamento (R$)",
          data: dados.valores,
          backgroundColor: "rgba(59,130,246,0.7)",
          borderColor: "#3b82f6",
          borderWidth: 1,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } },
      },
    });

    // Faturamento por forma de pagamento
    const formasGrid = document.getElementById("rel-formas-grid");
    const formasEmpty = document.getElementById("rel-formas-empty");
    const formas = Object.entries(dados.formas_pagamento || {}).filter(([, v]) => v > 0);
  if (!formas.length) {
    if (formasGrid) formasGrid.innerHTML = "";
    if (formasEmpty) formasEmpty.hidden = false;
  } else {
    if (formasEmpty) formasEmpty.hidden = true;
      formasGrid.innerHTML = "";
      formas.forEach(([chave, valor]) => {
        const card = document.createElement("div");
        card.className = "forma-card";
        card.innerHTML = `<span class="forma-card-nome">${FORMAS_LABEL[chave] || chave}</span><span class="forma-card-valor">${formatarMoeda(valor)}</span>`;
        formasGrid.appendChild(card);
      });
    }

    // Movimentacoes do periodo
    const corpo = document.getElementById("tabela-rel-movimentacoes");
    const movEmpty = document.getElementById("rel-movimentacoes-empty");
    corpo.innerHTML = "";
    const lancamentos = dados.lancamentos || [];
  if (movEmpty) movEmpty.hidden = lancamentos.length > 0;
    lancamentos.forEach((lancamento) => {
      const linha = document.createElement("tr");
      const tipoEntrada = lancamento.tipo === "entrada";
      linha.innerHTML = `
        <td>${formatarDataHora(lancamento.data)}</td>
        <td class="cell-nome">${lancamento.descricao}</td>
        <td><span class="badge ${tipoEntrada ? "badge-ativo" : "badge-inativo"}">${tipoEntrada ? "Entrada" : "Saída"}</span></td>
        <td><span class="badge">${FORMAS_LABEL[lancamento.forma_pagamento] || lancamento.forma_pagamento}</span></td>
        <td class="${tipoEntrada ? "valor-entrada" : "valor-saida"}">${tipoEntrada ? "+" : "−"} ${formatarMoeda(lancamento.valor)}</td>
      `;
      corpo.appendChild(linha);
    });

    // Ocupacao + DRE (complementares, carregados em paralelo)
    carregarOcupacaoDRE();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
}

document.getElementById("filtro-relatorio-agrupamento").addEventListener("change", (evento) => {
  relatorioAgrupamento = evento.target.value;
  carregarRelatoriosFinanceiros();
});

document.getElementById("btn-exportar-relatorio").addEventListener("click", () => {
  window.open(`/api/relatorio-financeiro/exportar?agrupamento=${relatorioAgrupamento}&formato=csv`, "_blank");
});
document.getElementById("btn-exportar-relatorio-pdf").addEventListener("click", () => {
  window.open(`/api/relatorio-financeiro/exportar?agrupamento=${relatorioAgrupamento}&formato=pdf`, "_blank");
});

// ---------------------- RELATORIOS: PAGAMENTOS POR FORMA DE PAGAMENTO ----------------------

let relatorioPagamentosInicializado = false;

function definirPeriodoRapidoPagamentos(tipo) {
  const agora = new Date();
  const formatarYMD = (d) => {
    const a = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const dia = String(d.getDate()).padStart(2, "0");
    return `${a}-${m}-${dia}`;
  };

  const inputInicio = document.getElementById("filtro-pag-inicio");
  const inputFim = document.getElementById("filtro-pag-fim");

  if (!inputInicio || !inputFim) return;

  if (tipo === "hoje") {
    inputInicio.value = formatarYMD(agora);
    inputFim.value = formatarYMD(agora);
  } else if (tipo === "ontem") {
    const ontem = new Date(agora);
    ontem.setDate(ontem.getDate() - 1);
    inputInicio.value = formatarYMD(ontem);
    inputFim.value = formatarYMD(ontem);
  } else if (tipo === "7d") {
    const d7 = new Date(agora);
    d7.setDate(d7.getDate() - 6);
    inputInicio.value = formatarYMD(d7);
    inputFim.value = formatarYMD(agora);
  } else if (tipo === "30d") {
    const d30 = new Date(agora);
    d30.setDate(d30.getDate() - 29);
    inputInicio.value = formatarYMD(d30);
    inputFim.value = formatarYMD(agora);
  } else if (tipo === "mes_atual") {
    const inicioMes = new Date(agora.getFullYear(), agora.getMonth(), 1);
    inputInicio.value = formatarYMD(inicioMes);
    inputFim.value = formatarYMD(agora);
  } else if (tipo === "mes_anterior") {
    const inicioMesAnt = new Date(agora.getFullYear(), agora.getMonth() - 1, 1);
    const fimMesAnt = new Date(agora.getFullYear(), agora.getMonth(), 0);
    inputInicio.value = formatarYMD(inicioMesAnt);
    inputFim.value = formatarYMD(fimMesAnt);
  } else if (tipo === "tudo") {
    inputInicio.value = "";
    inputFim.value = "";
  }

  document.querySelectorAll(".periodo-atalhos .btn-atalho").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.periodo === tipo);
  });
}

async function carregarFormasPagamentoRelatorio() {
  const select = document.getElementById("filtro-pag-forma");
  if (!select || select.dataset.carregado === "1") return;
  try {
    const dados = await chamarApi("/formas-pagamento");
    const formas = dados.formas_pagamento || [];
    select.innerHTML = '<option value="todas">Todas as formas</option>';
    formas.forEach((f) => {
      const opt = document.createElement("option");
      opt.value = f.codigo;
      opt.textContent = f.nome;
      select.appendChild(opt);
    });
    select.dataset.carregado = "1";
  } catch (e) {
    // fallback silencioso
  }
}

async function carregarRelatorioPagamentos() {
  const inputInicio = document.getElementById("filtro-pag-inicio");
  const inputFim = document.getElementById("filtro-pag-fim");
  const selectForma = document.getElementById("filtro-pag-forma");
  const selectStatus = document.getElementById("filtro-pag-status");

  if (!inputInicio) return;

  const inicio = inputInicio.value;
  const fim = inputFim.value;
  const forma = selectForma ? selectForma.value : "todas";
  const status = selectStatus ? selectStatus.value : "ativo";

  const params = new URLSearchParams();
  if (inicio) params.append("data_inicio", inicio);
  if (fim) params.append("data_fim", fim);
  if (forma && forma !== "todas") params.append("forma_pagamento", forma);
  if (status) params.append("status", status);

  try {
    const dados = await chamarApi(`/relatorio-pagamentos?${params.toString()}`);

    // Cards de resumo
    const elReceita = document.getElementById("card-pag-receita");
    const elQtd = document.getElementById("card-pag-quantidade");
    const elTicketMedio = document.getElementById("card-pag-ticket-medio");

    if (elReceita) elReceita.textContent = formatarMoeda(dados.receita_total);
    if (elQtd) elQtd.textContent = dados.quantidade_total;
    if (elTicketMedio) elTicketMedio.textContent = formatarMoeda(dados.ticket_medio);

    // Tabela consolidada de distribuicao por forma
    const corpoFormas = document.getElementById("tabela-pag-resumo-formas");
    if (corpoFormas) {
      corpoFormas.innerHTML = "";
      const resumoFormas = dados.resumo_formas || [];
      if (!resumoFormas.length) {
        corpoFormas.innerHTML = '<tr><td colspan="5" class="table-empty">Nenhum pagamento registrado no filtro selecionado.</td></tr>';
      } else {
        resumoFormas.forEach((rf) => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>
              <span class="badge-forma badge-forma-${rf.codigo}">${rf.nome}</span>
            </td>
            <td style="text-align: right; font-weight: 600;">${rf.quantidade}</td>
            <td style="text-align: right; font-weight: 700; color: #0f172a;">${formatarMoeda(rf.receita)}</td>
            <td>
              <div class="progresso-container">
                <div class="progresso-barra">
                  <div class="progresso-preenchimento" style="width: ${Math.min(rf.percentual, 100)}%;"></div>
                </div>
                <span class="progresso-pct">${rf.percentual}%</span>
              </div>
            </td>
            <td style="text-align: right; color: var(--color-text-light);">${formatarMoeda(rf.ticket_medio)}</td>
          `;
          corpoFormas.appendChild(tr);
        });
      }
    }

    // Tabela analitica das transacoes
    const corpoTransacoes = document.getElementById("tabela-pag-transacoes");
    const emptyTransacoes = document.getElementById("pag-transacoes-empty");
    const contadorTransacoes = document.getElementById("pag-transacoes-contador");

    if (corpoTransacoes) {
      corpoTransacoes.innerHTML = "";
      const transacoes = dados.transacoes || [];
      if (contadorTransacoes) contadorTransacoes.textContent = `${transacoes.length} transação(ões)`;

      if (!transacoes.length) {
        if (emptyTransacoes) emptyTransacoes.hidden = false;
      } else {
        if (emptyTransacoes) emptyTransacoes.hidden = true;
        transacoes.forEach((t) => {
          const tr = document.createElement("tr");
          const statusClasse = t.status === "ativo" ? "badge-status-ativo" : (t.status === "estornado" ? "badge-status-estornado" : "badge-status-cancelado");
          tr.innerHTML = `
            <td><strong>#${t.ticket_numero || "—"}</strong></td>
            <td>${formatarDataHora(t.data)}</td>
            <td>${t.operador || "—"}</td>
            <td><span class="badge-forma badge-forma-${t.forma_pagamento}">${t.forma_pagamento_nome}</span></td>
            <td style="text-align: right; font-weight: 700; color: #047857;">${formatarMoeda(t.valor)}</td>
            <td style="text-align: center;"><span class="${statusClasse}">${rotuloStatus(t.status)}</span></td>
          `;
          corpoTransacoes.appendChild(tr);
        });
      }
    }
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
}

// Alternancia de abas em Relatorios
document.querySelectorAll(".relatorio-tabs .tab").forEach((tabBtn) => {
  tabBtn.addEventListener("click", () => {
    document.querySelectorAll(".relatorio-tabs .tab").forEach((t) => t.classList.remove("active"));
    tabBtn.classList.add("active");
    const aba = tabBtn.dataset.relatorioTab;
    const painelGeral = document.getElementById("relatorio-tab-geral");
    const painelPagamentos = document.getElementById("relatorio-tab-pagamentos");

    if (aba === "pagamentos") {
      if (painelGeral) painelGeral.hidden = true;
      if (painelPagamentos) painelPagamentos.hidden = false;
      if (!relatorioPagamentosInicializado) {
        definirPeriodoRapidoPagamentos("7d");
        relatorioPagamentosInicializado = true;
      }
      carregarFormasPagamentoRelatorio();
      carregarRelatorioPagamentos();
    } else {
      if (painelGeral) painelGeral.hidden = false;
      if (painelPagamentos) painelPagamentos.hidden = true;
      carregarRelatoriosFinanceiros();
    }
  });
});

// Botoes de atalho de periodo
document.querySelectorAll(".periodo-atalhos .btn-atalho").forEach((btn) => {
  btn.addEventListener("click", () => {
    definirPeriodoRapidoPagamentos(btn.dataset.periodo);
    carregarRelatorioPagamentos();
  });
});

// Acoes de filtrar e limpar
const btnFiltrarPag = document.getElementById("btn-filtrar-pagamentos");
if (btnFiltrarPag) {
  btnFiltrarPag.addEventListener("click", () => {
    document.querySelectorAll(".periodo-atalhos .btn-atalho").forEach((b) => b.classList.remove("active"));
    carregarRelatorioPagamentos();
  });
}

const btnLimparPag = document.getElementById("btn-limpar-filtro-pagamentos");
if (btnLimparPag) {
  btnLimparPag.addEventListener("click", () => {
    definirPeriodoRapidoPagamentos("tudo");
    const sf = document.getElementById("filtro-pag-forma");
    const ss = document.getElementById("filtro-pag-status");
    if (sf) sf.value = "todas";
    if (ss) ss.value = "ativo";
    carregarRelatorioPagamentos();
  });
}

// Exportacao CSV do relatorio de pagamentos por forma
const btnExportarCsvPag = document.getElementById("btn-exportar-pagamentos-csv");
if (btnExportarCsvPag) {
  btnExportarCsvPag.addEventListener("click", () => {
    const inicio = document.getElementById("filtro-pag-inicio")?.value || "";
    const fim = document.getElementById("filtro-pag-fim")?.value || "";
    const forma = document.getElementById("filtro-pag-forma")?.value || "";
    const status = document.getElementById("filtro-pag-status")?.value || "ativo";

    const params = new URLSearchParams();
    if (inicio) params.append("data_inicio", inicio);
    if (fim) params.append("data_fim", fim);
    if (forma && forma !== "todas") params.append("forma_pagamento", forma);
    if (status) params.append("status", status);

    window.open(`/api/relatorio-pagamentos/exportar?${params.toString()}`, "_blank");
  });
}

// ---------------------- SESSAO / LOGOUT / ALTERAR SENHA ----------------------

let sessionEmpresaId = null;
let usuarioMaster = false;

async function carregarSessao() {
  try {
    const dados = await chamarApi("/sessao");
    const usuario = dados.usuario;
    if (!usuario) {
      window.location.href = "/login";
      return;
    }
    document.getElementById("header-usuario-nome").textContent = usuario.nome;
    document.getElementById("header-usuario-perfil").textContent = nomePerfil(usuario.perfil);
    usuarioMaster = !!usuario.master;
    sessionEmpresaId = usuario.empresa_id || null;

    // Header: empresa atual + botao trocar empresa (somente master)
    const headerEmpresa = document.getElementById("header-empresa-nome");
    const btnTrocar = document.getElementById("btn-trocar-empresa");
    if (usuario.empresa) {
      const nomeEstacionamento = (usuario.empresa.nome_fantasia || usuario.empresa.razao_social || "").trim();
      if (nomeEstacionamento) {
        aplicarNomeSistema(nomeEstacionamento);
      }
      if (headerEmpresa) {
        headerEmpresa.textContent = `🏢 ${nomeEstacionamento}`;
        headerEmpresa.hidden = false;
      }
    } else if (headerEmpresa) {
      headerEmpresa.hidden = true;
    }
    if (btnTrocar) btnTrocar.hidden = !usuarioMaster;

    // Menu Empresas: somente master
    const menuEmpresas = document.querySelector('.menu-item[data-view="view-empresas"]');
    if (menuEmpresas) menuEmpresas.classList.toggle("hidden", !usuarioMaster);

    // Master: carrega a lista de empresas para o select do cadastro de usuario
    if (usuarioMaster) {
      try {
        const dadosEmpresas = await chamarApi("/empresas");
        cacheEmpresas = dadosEmpresas.empresas || [];
      } catch (erroEmpresas) {
        cacheEmpresas = [];
      }
    }

    // Aplica as permissoes do usuario no frontend (oculta acoes nao permitidas)
    try {
      const permDados = await chamarApi("/permissoes");
      permissoesMatriz = permDados.matriz || {};
      permissoesPerfis = permDados.perfis || [];
      permissoesModulos = permDados.modulos || [];
      permissoesAcoes = permDados.acoes || [];
      permissoesPerfisDetalhes = permDados.perfis_detalhes || [];
      perfilUsuarioAtual = usuario.perfil;
      atualizarSelectPerfis();
      aplicarPermissoesFrontend(usuario.perfil);

      // Se a view ativa nao tiver permissao "ver", volta para a visao geral
      const viewAtiva = document.querySelector(".view.view-active");
      if (viewAtiva && viewAtiva.id !== "view-visao-geral") {
        const modulo = MENU_PERMISSAO[viewAtiva.id];
        if (modulo) {
          const permitido = (permissoesMatriz[modulo] && permissoesMatriz[modulo][usuario.perfil] || []).includes("ver");
          if (!permitido) mostrarView("view-visao-geral");
        }
      }
    } catch (erro) {
      // se nao conseguir carregar permissoes, nao bloqueia o uso
    }
    // Forca a troca de senha no primeiro acesso, se configurado
    if (usuario.trocar_senha_no_proximo_acesso) {
      abrirModalAlterarSenha(true);
    }
  } catch (erro) {
    window.location.href = "/login";
  }
}

document.getElementById("btn-logout").addEventListener("click", async () => {
  try {
    await fetch("/api/logout", { method: "POST" });
  } catch (erro) {
    // ignora erro de rede no logout
  }
  localStorage.removeItem("estaciona_view");
  localStorage.removeItem("estaciona_aba");
  window.location.href = "/login";
});

// ----- Modal: Alterar senha -----
function abrirModalAlterarSenha(obrigatoria = false) {
  document.getElementById("form-alterar-senha").reset();
  document.getElementById("modal-alterar-senha").hidden = false;
  const titulo = document.getElementById("modal-alterar-senha").querySelector(".modal-title");
  if (titulo) titulo.textContent = obrigatoria ? "Alterar senha (obrigatório)" : "Alterar senha";
  const btnFechar = document.getElementById("modal-alterar-senha-fechar");
  const btnCancelar = document.getElementById("btn-alterar-senha-cancelar");
  if (btnFechar) btnFechar.style.display = obrigatoria ? "none" : "";
  if (btnCancelar) btnCancelar.style.display = obrigatoria ? "none" : "";
  setTimeout(() => document.getElementById("input-senha-atual").focus(), 50);
}

function fecharModalAlterarSenha() {
  document.getElementById("modal-alterar-senha").hidden = true;
}

document.getElementById("btn-alterar-senha").addEventListener("click", () => abrirModalAlterarSenha(false));
document.getElementById("modal-alterar-senha-fechar").addEventListener("click", fecharModalAlterarSenha);
document.getElementById("btn-alterar-senha-cancelar").addEventListener("click", fecharModalAlterarSenha);
document.getElementById("modal-alterar-senha").addEventListener("click", (evento) => {
  if (evento.target === evento.currentTarget) fecharModalAlterarSenha();
});

document.getElementById("form-alterar-senha").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const senhaAtual = document.getElementById("input-senha-atual").value;
  const novaSenha = document.getElementById("input-nova-senha").value;
  const confirmar = document.getElementById("input-confirmar-senha").value;

  if (novaSenha !== confirmar) {
    mostrarToast("A confirmação da nova senha não confere.", "error");
    return;
  }

  const botaoSalvar = document.getElementById("btn-alterar-senha-salvar");
  botaoSalvar.disabled = true;
  try {
    const dados = await chamarApi("/trocar-senha", {
      method: "POST",
      body: JSON.stringify({ senha_atual: senhaAtual, nova_senha: novaSenha }),
    });
    mostrarToast(dados.mensagem, "success");
    fecharModalAlterarSenha();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  } finally {
    botaoSalvar.disabled = false;
  }
});

// ---------------------- NFSE ----------------------

async function carregarNFSE() {
  const corpo = document.getElementById("tabela-nfse");
  const empty = document.getElementById("nfse-empty");
  corpo.innerHTML = "";

  let dados;
  try {
    dados = await chamarApi("/nfse");
  } catch (erro) {
    mostrarToast(erro.message, "error");
    corpo.innerHTML = '<tr><td colspan="8" class="table-empty">Erro ao carregar notas.</td></tr>';
    return;
  }

  const notas = dados.notas || [];
  empty.hidden = notas.length > 0;

  notas.forEach((n) => {
    const linha = document.createElement("tr");
    const tomador = n.razao_social || n.cpf_cnpj || "—";
    const statusCancelada = n.status === "cancelada";
    linha.innerHTML = `
      <td><strong>#${n.numero}</strong></td>
      <td>${formatarDataHora(n.data)}</td>
      <td>${n.ticket_numero || "—"}</td>
      <td>${n.placa || "—"}</td>
      <td class="cell-nome">${tomador}</td>
      <td class="valor-entrada">${formatarMoeda(n.valor)}</td>
      <td><span class="badge ${statusCancelada ? "badge-inativo" : "badge-ativo"}">${statusCancelada ? "Cancelada" : "Emitida"}</span></td>
      <td class="col-acoes">
        ${statusCancelada ? "" : `<button type="button" class="btn-acao btn-acao-danger" data-acao-nfse="cancelar" data-id="${n.id}" title="Cancelar nota">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>`}
      </td>
    `;
    corpo.appendChild(linha);
  });
}

function fecharModalNFSE() {
  document.getElementById("modal-nfse").hidden = true;
  document.getElementById("form-nfse").reset();
}
document.getElementById("btn-nova-nfse").addEventListener("click", () => {
  document.getElementById("modal-nfse").hidden = false;
  setTimeout(() => document.getElementById("input-nfse-valor").focus(), 50);
});
document.getElementById("modal-nfse-fechar").addEventListener("click", fecharModalNFSE);
document.getElementById("btn-nfse-cancelar").addEventListener("click", fecharModalNFSE);
document.getElementById("modal-nfse").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) fecharModalNFSE();
});
document.getElementById("form-nfse").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    valor: Number(document.getElementById("input-nfse-valor").value),
    ticket_numero: document.getElementById("input-nfse-ticket").value || null,
    placa: document.getElementById("input-nfse-placa").value.trim(),
    cpf_cnpj: document.getElementById("input-nfse-cpf-cnpj").value.trim(),
    razao_social: document.getElementById("input-nfse-razao").value.trim(),
    servico: document.getElementById("input-nfse-servico").value.trim() || "Estacionamento de veiculos",
  };
  try {
    const dados = await chamarApi("/nfse", { method: "POST", body: JSON.stringify(payload) });
    mostrarToast(dados.mensagem, "success");
    fecharModalNFSE();
    await carregarNFSE();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});
document.getElementById("tabela-nfse").addEventListener("click", async (evento) => {
  const botao = evento.target.closest("button[data-acao-nfse]");
  if (!botao || botao.dataset.acaoNfse !== "cancelar") return;
  if (!confirm("Deseja cancelar esta nota fiscal?")) return;
  try {
    const dados = await chamarApi(`/nfse/${botao.dataset.id}/cancelar`, { method: "POST" });
    mostrarToast(dados.mensagem, "success");
    await carregarNFSE();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});

// ---------------------- LISTA NEGRA ----------------------

async function carregarListaNegra() {
  const corpo = document.getElementById("tabela-lista-negra");
  const empty = document.getElementById("lista-negra-empty");
  corpo.innerHTML = "";

  let dados;
  try {
    dados = await chamarApi("/lista-negra");
  } catch (erro) {
    mostrarToast(erro.message, "error");
    corpo.innerHTML = '<tr><td colspan="6" class="table-empty">Erro ao carregar lista negra.</td></tr>';
    return;
  }

  const registros = dados.registros || [];
  empty.hidden = registros.length > 0;

  registros.forEach((r) => {
    const linha = document.createElement("tr");
    linha.innerHTML = `
      <td class="cell-nome"><strong>${r.placa}</strong></td>
      <td>${r.motivo || "—"}</td>
      <td><span class="badge ${r.ativo ? "badge-ativo" : "badge-inativo"}">${r.ativo ? "Bloqueado" : "Liberado"}</span></td>
      <td>${r.usuario || "—"}</td>
      <td>${formatarDataHora(r.data)}</td>
      <td class="col-acoes">
        <button type="button" class="btn-acao" data-acao-lista-negra="editar" data-id="${r.id}" title="Editar">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <button type="button" class="btn-acao" data-acao-lista-negra="alternar" data-id="${r.id}" title="${r.ativo ? "Liberar" : "Bloquear"}">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 3v18M5 10l7-7 7 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <button type="button" class="btn-acao btn-acao-danger" data-acao-lista-negra="excluir" data-id="${r.id}" title="Excluir">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
      </td>
    `;
    corpo.appendChild(linha);
  });
}

function abrirModalListaNegra(r = null) {
  document.getElementById("input-lista-negra-id").value = r ? r.id : "";
  document.getElementById("input-lista-negra-placa").value = r ? r.placa : "";
  document.getElementById("input-lista-negra-motivo").value = r ? r.motivo : "";
  document.getElementById("modal-lista-negra").hidden = false;
  setTimeout(() => document.getElementById("input-lista-negra-placa").focus(), 50);
}
function fecharModalListaNegra() {
  document.getElementById("modal-lista-negra").hidden = true;
  document.getElementById("form-lista-negra").reset();
}
document.getElementById("btn-novo-bloqueio").addEventListener("click", () => abrirModalListaNegra());
document.getElementById("modal-lista-negra-fechar").addEventListener("click", fecharModalListaNegra);
document.getElementById("btn-lista-negra-cancelar").addEventListener("click", fecharModalListaNegra);
document.getElementById("modal-lista-negra").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) fecharModalListaNegra();
});
document.getElementById("form-lista-negra").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("input-lista-negra-id").value;
  const payload = {
    placa: document.getElementById("input-lista-negra-placa").value.trim(),
    motivo: document.getElementById("input-lista-negra-motivo").value.trim(),
  };
  try {
    const dados = id
      ? await chamarApi(`/lista-negra/${id}`, { method: "PUT", body: JSON.stringify(payload) })
      : await chamarApi("/lista-negra", { method: "POST", body: JSON.stringify(payload) });
    mostrarToast(dados.mensagem, "success");
    fecharModalListaNegra();
    await carregarListaNegra();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});
document.getElementById("tabela-lista-negra").addEventListener("click", async (evento) => {
  const botao = evento.target.closest("button[data-acao-lista-negra]");
  if (!botao) return;
  const acao = botao.dataset.acaoListaNegra;
  try {
    if (acao === "editar") {
      const dados = await chamarApi("/lista-negra");
      const r = (dados.registros || []).find((x) => String(x.id) === String(botao.dataset.id));
      if (r) abrirModalListaNegra(r);
    } else if (acao === "alternar") {
      const dados = await chamarApi(`/lista-negra/${botao.dataset.id}/alternar-ativo`, { method: "POST" });
      mostrarToast(dados.mensagem, "success");
      await carregarListaNegra();
    } else if (acao === "excluir") {
      if (!confirm("Deseja remover este bloqueio?")) return;
      const dados = await chamarApi(`/lista-negra/${botao.dataset.id}`, { method: "DELETE" });
      mostrarToast(dados.mensagem, "success");
      await carregarListaNegra();
    }
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});

// ---------------------- RESERVAS ----------------------

function paraDatetimeLocal(valor) {
  if (!valor) return "";
  const m = valor.match(/(\d{2})\/(\d{2})\/(\d{4})[ T]?(\d{2}):(\d{2})?/);
  if (m) return `${m[3]}-${m[2]}-${m[1]}T${m[4] || "00"}:${m[5] || "00"}`;
  return valor.replace(" ", "T");
}
function paraDataBR(valor) {
  if (!valor) return "";
  const m = valor.match(/(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/);
  if (m) return `${m[3]}/${m[2]}/${m[1]} ${m[4]}:${m[5]}`;
  return valor;
}

async function carregarReservas() {
  const corpo = document.getElementById("tabela-reservas");
  const empty = document.getElementById("reservas-empty");
  corpo.innerHTML = "";

  let dados;
  try {
    dados = await chamarApi("/reservas");
  } catch (erro) {
    mostrarToast(erro.message, "error");
    corpo.innerHTML = '<tr><td colspan="9" class="table-empty">Erro ao carregar reservas.</td></tr>';
    return;
  }

  const reservas = dados.reservas || [];
  empty.hidden = reservas.length > 0;

  const STATUS_LABEL = { ativa: "Ativa", concluida: "Concluída", cancelada: "Cancelada" };
  reservas.forEach((r) => {
    const linha = document.createElement("tr");
    const statusClass = r.status === "ativa" ? "badge-ativo" : (r.status === "cancelada" ? "badge-inativo" : "");
    linha.innerHTML = `
      <td class="cell-nome">${r.cliente}</td>
      <td>${r.telefone || "—"}</td>
      <td>${r.placa || "—"}</td>
      <td>${r.vaga || "—"}</td>
      <td>${formatarDataHora(r.data_inicio)}</td>
      <td>${formatarDataHora(r.data_fim)}</td>
      <td class="valor-entrada">${formatarMoeda(r.valor)}</td>
      <td><span class="badge ${statusClass}">${STATUS_LABEL[r.status] || r.status}</span></td>
      <td class="col-acoes">
        ${r.status === "ativa" ? `
          <button type="button" class="btn-acao" data-acao-reserva="editar" data-id="${r.id}" title="Editar">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <button type="button" class="btn-acao btn-acao-danger" data-acao-reserva="cancelar" data-id="${r.id}" title="Cancelar reserva">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>` : `<button type="button" class="btn-acao" data-acao-reserva="editar" data-id="${r.id}" title="Editar">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>`}
      </td>
    `;
    corpo.appendChild(linha);
  });
}

function abrirModalReserva(r = null) {
  document.getElementById("input-reserva-id").value = r ? r.id : "";
  document.getElementById("input-reserva-cliente").value = r ? r.cliente : "";
  document.getElementById("input-reserva-telefone").value = r ? r.telefone : "";
  document.getElementById("input-reserva-placa").value = r ? r.placa : "";
  document.getElementById("input-reserva-inicio").value = r ? paraDatetimeLocal(r.data_inicio) : "";
  document.getElementById("input-reserva-fim").value = r ? paraDatetimeLocal(r.data_fim) : "";
  document.getElementById("input-reserva-vaga").value = r && r.vaga ? r.vaga : "";
  document.getElementById("input-reserva-tipo").value = r ? r.tipo_veiculo : "Carro";
  document.getElementById("input-reserva-valor").value = r ? r.valor : "";
  document.getElementById("input-reserva-obs").value = r ? r.observacao : "";
  document.getElementById("modal-reserva-titulo").textContent = r ? "Editar reserva" : "Nova reserva";
  document.getElementById("modal-reserva").hidden = false;
  setTimeout(() => document.getElementById("input-reserva-cliente").focus(), 50);
}
function fecharModalReserva() {
  document.getElementById("modal-reserva").hidden = true;
  document.getElementById("form-reserva").reset();
}
document.getElementById("btn-nova-reserva").addEventListener("click", () => abrirModalReserva());
document.getElementById("modal-reserva-fechar").addEventListener("click", fecharModalReserva);
document.getElementById("btn-reserva-cancelar").addEventListener("click", fecharModalReserva);
document.getElementById("modal-reserva").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) fecharModalReserva();
});
document.getElementById("form-reserva").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("input-reserva-id").value;
  const payload = {
    cliente: document.getElementById("input-reserva-cliente").value.trim(),
    telefone: document.getElementById("input-reserva-telefone").value.trim(),
    placa: document.getElementById("input-reserva-placa").value.trim(),
    data_inicio: paraDataBR(document.getElementById("input-reserva-inicio").value),
    data_fim: paraDataBR(document.getElementById("input-reserva-fim").value),
    vaga: document.getElementById("input-reserva-vaga").value || null,
    tipo_veiculo: document.getElementById("input-reserva-tipo").value,
    valor: Number(document.getElementById("input-reserva-valor").value || 0),
    observacao: document.getElementById("input-reserva-obs").value.trim(),
  };
  try {
    const dados = id
      ? await chamarApi(`/reservas/${id}`, { method: "PUT", body: JSON.stringify(payload) })
      : await chamarApi("/reservas", { method: "POST", body: JSON.stringify(payload) });
    mostrarToast(dados.mensagem, "success");
    fecharModalReserva();
    await carregarReservas();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});
document.getElementById("tabela-reservas").addEventListener("click", async (evento) => {
  const botao = evento.target.closest("button[data-acao-reserva]");
  if (!botao) return;
  const acao = botao.dataset.acaoReserva;
  try {
    if (acao === "editar") {
      const dados = await chamarApi("/reservas");
      const r = (dados.reservas || []).find((x) => String(x.id) === String(botao.dataset.id));
      if (r) abrirModalReserva(r);
    } else if (acao === "cancelar") {
      if (!confirm("Deseja cancelar esta reserva?")) return;
      const dados = await chamarApi(`/reservas/${botao.dataset.id}/cancelar`, { method: "POST" });
      mostrarToast(dados.mensagem, "success");
      await carregarReservas();
    }
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});

// ---------------------- OCORRENCIAS ----------------------

async function carregarOcorrencias() {
  const corpo = document.getElementById("tabela-ocorrencias");
  const empty = document.getElementById("ocorrencias-empty");
  corpo.innerHTML = "";

  let dados;
  try {
    dados = await chamarApi("/ocorrencias");
  } catch (erro) {
    mostrarToast(erro.message, "error");
    corpo.innerHTML = '<tr><td colspan="8" class="table-empty">Erro ao carregar ocorrências.</td></tr>';
    return;
  }

  const ocorrencias = dados.ocorrencias || [];
  empty.hidden = ocorrencias.length > 0;

  const TIPO_LABEL = { avaria: "Avaria", perda: "Perda", outro: "Outro" };
  ocorrencias.forEach((o) => {
    const linha = document.createElement("tr");
    const resolvida = o.status === "resolvida";
    linha.innerHTML = `
      <td>${formatarDataHora(o.data)}</td>
      <td><span class="badge">${TIPO_LABEL[o.tipo] || o.tipo}</span></td>
      <td><strong>${o.placa || "—"}</strong></td>
      <td>${o.ticket_numero || "—"}</td>
      <td class="cell-nome">${o.descricao}</td>
      <td><span class="badge ${resolvida ? "badge-ativo" : "badge-inativo"}">${resolvida ? "Resolvida" : "Aberta"}</span></td>
      <td>${o.usuario || "—"}</td>
      <td class="col-acoes">
        <button type="button" class="btn-acao" data-acao-ocorrencia="editar" data-id="${o.id}" title="Editar">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
      </td>
    `;
    corpo.appendChild(linha);
  });
}

function abrirModalOcorrencia(o = null) {
  document.getElementById("input-ocorrencia-id").value = o ? o.id : "";
  document.getElementById("input-ocorrencia-tipo").value = o ? o.tipo : "avaria";
  document.getElementById("input-ocorrencia-placa").value = o ? o.placa : "";
  document.getElementById("input-ocorrencia-ticket").value = o && o.ticket_numero ? o.ticket_numero : "";
  document.getElementById("input-ocorrencia-descricao").value = o ? o.descricao : "";
  document.getElementById("input-ocorrencia-autorizador").value = o ? o.autorizador : "";
  document.getElementById("modal-ocorrencia").hidden = false;
  setTimeout(() => document.getElementById("input-ocorrencia-descricao").focus(), 50);
}
function fecharModalOcorrencia() {
  document.getElementById("modal-ocorrencia").hidden = true;
  document.getElementById("form-ocorrencia").reset();
}
document.getElementById("btn-nova-ocorrencia").addEventListener("click", () => abrirModalOcorrencia());
document.getElementById("modal-ocorrencia-fechar").addEventListener("click", fecharModalOcorrencia);
document.getElementById("btn-ocorrencia-cancelar").addEventListener("click", fecharModalOcorrencia);
document.getElementById("modal-ocorrencia").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) fecharModalOcorrencia();
});
document.getElementById("form-ocorrencia").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("input-ocorrencia-id").value;
  const payload = {
    tipo: document.getElementById("input-ocorrencia-tipo").value,
    placa: document.getElementById("input-ocorrencia-placa").value.trim(),
    ticket_numero: document.getElementById("input-ocorrencia-ticket").value || null,
    descricao: document.getElementById("input-ocorrencia-descricao").value.trim(),
    autorizador: document.getElementById("input-ocorrencia-autorizador").value.trim(),
  };
  try {
    const dados = id
      ? await chamarApi(`/ocorrencias/${id}`, { method: "PUT", body: JSON.stringify(payload) })
      : await chamarApi("/ocorrencias", { method: "POST", body: JSON.stringify(payload) });
    mostrarToast(dados.mensagem, "success");
    fecharModalOcorrencia();
    await carregarOcorrencias();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});
document.getElementById("tabela-ocorrencias").addEventListener("click", async (evento) => {
  const botao = evento.target.closest("button[data-acao-ocorrencia]");
  if (!botao) return;
  try {
    const dados = await chamarApi("/ocorrencias");
    const o = (dados.ocorrencias || []).find((x) => String(x.id) === String(botao.dataset.id));
    if (o) abrirModalOcorrencia(o);
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});

// ---------------------- AVISOS (NOTIFICACOES) ----------------------

async function carregarAvisos() {
  const corpo = document.getElementById("tabela-avisos");
  const empty = document.getElementById("avisos-empty");
  corpo.innerHTML = "";

  let dados;
  try {
    dados = await chamarApi("/notificacoes-vencimento");
  } catch (erro) {
    mostrarToast(erro.message, "error");
    corpo.innerHTML = '<tr><td colspan="5" class="table-empty">Erro ao carregar avisos.</td></tr>';
    return;
  }

  document.getElementById("aviso-inadimplentes").textContent = dados.inadimplentes || 0;
  document.getElementById("aviso-a-vencer").textContent = dados.a_vencer || 0;
  document.getElementById("aviso-mensagem-geral").textContent = dados.mensagem_geral || "";

  const avisos = dados.avisos || [];
  empty.hidden = avisos.length > 0;

  avisos.forEach((a) => {
    const linha = document.createElement("tr");
    const inadimplente = a.situacao === "inadimplente";
    const contato = [];
    if (a.whatsapp) contato.push(`<a class="link-contato" href="${a.whatsapp}" target="_blank" rel="noopener">WhatsApp</a>`);
    if (a.mailto) contato.push(`<a class="link-contato" href="${a.mailto}">E-mail</a>`);
    linha.innerHTML = `
      <td class="cell-nome">${a.nome}</td>
      <td>${a.competencia || "—"}</td>
      <td class="valor-entrada">${formatarMoeda(a.valor)}</td>
      <td><span class="badge ${inadimplente ? "badge-inativo" : "badge-ativo"}">${inadimplente ? "Inadimplente" : "A vencer"}</span></td>
      <td>${contato.length ? contato.join(" · ") : "—"}</td>
    `;
    corpo.appendChild(linha);
  });
}

// ---------------------- MAPA DE VAGAS ----------------------

const MAPA_TIPO_CLASSE = {
  Carro: "t-carro",
  Moto: "t-moto",
  "Carro Grande": "t-cg",
  Caminhonete: "t-cam",
};

async function abrirMapaVagas() {
  const grid = document.getElementById("mapa-vagas-grid");
  grid.innerHTML = '<p class="empty-state">Carregando vagas...</p>';
  document.getElementById("modal-mapa-vagas").hidden = false;

  let dados;
  try {
    dados = await chamarApi("/vagas");
  } catch (erro) {
    grid.innerHTML = `<p class="empty-state">Erro: ${erro.message}</p>`;
    return;
  }

  document.getElementById("mapa-total-vagas").textContent = dados.total_vagas || 0;
  document.getElementById("mapa-ocupadas").textContent = dados.vagas_ocupadas || 0;
  document.getElementById("mapa-disponiveis").textContent = dados.vagas_livres || 0;
  const total = dados.total_vagas || 0;
  const ocupadas = dados.vagas_ocupadas || 0;
  document.getElementById("mapa-taxa").textContent = total ? `${Math.round((ocupadas / total) * 100)}%` : "0%";

  // Indice das vagas ocupadas: numero da vaga -> dados do veiculo
  const porVaga = {};
  (dados.veiculos || []).forEach((v) => {
    if (v.vaga) porVaga[v.vaga] = v;
  });

  grid.innerHTML = "";
  for (let i = 1; i <= total; i++) {
    const v = porVaga[i];
    const vaga = document.createElement("div");
    if (v) {
      vaga.className = `mapa-vaga ocupada ${MAPA_TIPO_CLASSE[v.tipo_veiculo] || "t-carro"}`;
      vaga.innerHTML = `<span class="mapa-vaga-num">${i}</span><span class="mapa-vaga-placa">${v.placa}</span>`;
      vaga.title = `Vaga ${i} — ${v.placa}\n${v.tipo_veiculo}\nEntrada: ${formatarDataHora(v.entrada)}\nPermanência: ${v.tempo_estacionado || "-"}`;
      vaga.addEventListener("click", () => {
        mostrarToast(`Vaga ${i}: ${v.placa} (${v.tipo_veiculo}) — entrada ${formatarDataHora(v.entrada)}`, "info");
      });
    } else {
      vaga.className = "mapa-vaga livre";
      vaga.innerHTML = `<span class="mapa-vaga-num">${i}</span>`;
      vaga.title = `Vaga ${i} — Livre`;
    }
    grid.appendChild(vaga);
  }
  if (!total) grid.innerHTML = '<p class="empty-state">Nenhuma vaga configurada.</p>';
}
function fecharMapaVagas() {
  document.getElementById("modal-mapa-vagas").hidden = true;
}
document.getElementById("btn-abrir-mapa-vagas").addEventListener("click", abrirMapaVagas);
document.getElementById("btn-mapa-atualizar").addEventListener("click", abrirMapaVagas);
document.getElementById("modal-mapa-vagas-fechar").addEventListener("click", fecharMapaVagas);
document.getElementById("btn-mapa-vagas-fechar").addEventListener("click", fecharMapaVagas);
document.getElementById("modal-mapa-vagas").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) fecharMapaVagas();
});

// ---------------------- TICKET PERDIDO ----------------------

document.getElementById("btn-abrir-ticket-perdido").addEventListener("click", async () => {
  document.getElementById("modal-ticket-perdido").hidden = false;
  const sugerido = document.getElementById("tp-valor-sugerido");
  try {
    const dados = await chamarApi("/tabela-precos");
    const tabela = dados.tabela_precos || dados.tabela || dados.precos || null;
    const valor = tabela && (tabela.valor_ticket_perdido > 0) ? tabela.valor_ticket_perdido : null;
    sugerido.textContent = valor ? `(padrão: ${formatarMoeda(valor)})` : "(configure a tarifa em Configurações)";
  } catch (erro) {
    sugerido.textContent = "";
  }
});
document.getElementById("modal-ticket-perdido-fechar").addEventListener("click", () => {
  document.getElementById("modal-ticket-perdido").hidden = true;
  document.getElementById("form-ticket-perdido").reset();
});
document.getElementById("btn-ticket-perdido-cancelar").addEventListener("click", () => {
  document.getElementById("modal-ticket-perdido").hidden = true;
  document.getElementById("form-ticket-perdido").reset();
});
document.getElementById("modal-ticket-perdido").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) {
    document.getElementById("modal-ticket-perdido").hidden = true;
    document.getElementById("form-ticket-perdido").reset();
  }
});
document.getElementById("form-ticket-perdido").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    placa: document.getElementById("input-tp-placa").value.trim(),
    tipo_veiculo: document.getElementById("input-tp-tipo").value,
    valor: document.getElementById("input-tp-valor").value || null,
    forma_pagamento: document.getElementById("input-tp-forma").value,
    observacoes: document.getElementById("input-tp-obs").value.trim(),
    autorizador: document.getElementById("input-tp-autorizador").value.trim(),
  };
  try {
    const dados = await chamarApi("/ticket-perdido", { method: "POST", body: JSON.stringify(payload) });
    mostrarToast(dados.mensagem, "success");
    if (dados.aviso) mostrarToast(dados.aviso, "warning");
    document.getElementById("modal-ticket-perdido").hidden = true;
    document.getElementById("form-ticket-perdido").reset();
    await carregarDashboard();
    await recarregarAbaAtual();
    if (dados.ticket) {
      mostrarReciboSaida(dados.ticket);
    }
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});

// ---------------------- BACKUP ----------------------

document.getElementById("btn-backup").addEventListener("click", () => {
  window.open("/api/backup", "_blank");
});

// ---------------------- OCUPACAO + DRE (RELATORIOS) ----------------------

async function carregarOcupacaoDRE() {
  try {
    const [ocupacao, dre] = await Promise.all([
      chamarApi("/relatorio-ocupacao"),
      chamarApi("/relatorio-dre"),
    ]);

    document.getElementById("rel-ocu-total").textContent = ocupacao.total_vagas || 0;
    document.getElementById("rel-ocu-ocupadas").textContent = ocupacao.ocupadas || 0;
    document.getElementById("rel-ocu-disponiveis").textContent = ocupacao.disponiveis || 0;
    document.getElementById("rel-ocu-taxa").textContent = `${ocupacao.taxa_ocupacao || 0}%`;

    const porTipo = document.getElementById("rel-ocu-por-tipo");
    porTipo.innerHTML = "";
    const tipos = Object.entries(ocupacao.por_tipo || {});
    if (!tipos.length) {
      porTipo.innerHTML = '<p class="empty-state">Nenhum dado por tipo.</p>';
    } else {
      tipos.forEach(([tipo, valores]) => {
        const item = document.createElement("div");
        item.className = "ocupacao-tipo";
        item.innerHTML = `<span>${tipo}</span><span>${valores.ocupadas}/${valores.vagas || "—"} ocupadas</span>`;
        porTipo.appendChild(item);
      });
    }

    document.getElementById("dre-receita").textContent = formatarMoeda(dre.receita_bruta);
    document.getElementById("dre-descontos").textContent = formatarMoeda(dre.total_descontos);
    document.getElementById("dre-cortesias").textContent = dre.total_cortesias || 0;
    document.getElementById("dre-estornos").textContent = formatarMoeda(dre.total_estornos);
    document.getElementById("dre-resultado").textContent = formatarMoeda(dre.resultado_liquido);
  } catch (erro) {
    // Ocupacao/DRE sao complementares: falha nao bloqueia o relatorio principal
  }
}

// ---------------------- INICIALIZACAO ----------------------

const viewsValidas = [
  "view-visao-geral", "view-empresas", "view-usuarios", "view-clientes", "view-financeiro",
  "view-caixa", "view-pagamentos", "view-formas-pagamento", "view-mensalistas", "view-convenios",
  "view-contas-receber", "view-descontos", "view-cortesias",
  "view-dashboard-financeiro", "view-auditoria", "view-relatorios",
  "view-nfse", "view-lista-negra", "view-reservas", "view-ocorrencias",
  "view-notificacoes", "view-configuracoes", "view-permissoes",
];

async function inicializarApp() {
  atualizarDataHeader();

  const abaSalva = localStorage.getItem("estaciona_aba");
  if (abaSalva && ["patio", "historico", "consultar"].includes(abaSalva)) {
    abaAtual = abaSalva;
    document.querySelectorAll(".tab").forEach((t) => {
      t.classList.toggle("active", t.dataset.tab === abaSalva);
    });
  }

  // 1. Carrega sessao e matriz de permissoes do usuario
  await carregarSessao();

  // 2. Determina a tela inicial garantindo que o usuario possua permissao
  const viewSalva = localStorage.getItem("estaciona_view");
  let viewInicial = "view-visao-geral";

  if (viewSalva && viewsValidas.includes(viewSalva) && viewSalva !== "view-visao-geral") {
    const modulo = MENU_PERMISSAO[viewSalva];
    const permitido = !modulo || perfilUsuarioAtual === "admin" || (
      permissoesMatriz && permissoesMatriz[modulo] && permissoesMatriz[modulo][perfilUsuarioAtual] || []
    ).includes("ver");
    if (permitido) {
      viewInicial = viewSalva;
    }
  }

  mostrarView(viewInicial);
}

inicializarApp();

setInterval(() => {
  const viewAtiva = document.querySelector(".view.view-active");
  if (viewAtiva && viewAtiva.id === "view-visao-geral") {
    carregarDashboard();
    if (!inputBusca.value.trim()) recarregarAbaAtual();
  }
}, 15000);

// ESC fecha o modal visível (reutiliza o proprio botao de fechar, preservando o estado)
document.addEventListener("keydown", (evento) => {
  if (evento.key !== "Escape") return;
  const overlays = document.querySelectorAll(".modal-overlay:not([hidden])");
  if (!overlays.length) return;
  const overlay = overlays[overlays.length - 1];
  const btnFechar = overlay.querySelector(".modal-close");
  if (btnFechar) btnFechar.click();
  else overlay.hidden = true;
});

// ---------------------- ACESSO MOBILE & TERMINAL OPERADOR ----------------------

async function abrirModalAcessoMobile() {
  const modal = document.getElementById("modal-acesso-mobile");
  if (!modal) return;

  modal.hidden = false;
  const inputUrl = document.getElementById("input-mobile-url");
  const linkAbrir = document.getElementById("link-abrir-modo-mobile");
  const qrImg = document.getElementById("mobile-qr-img");
  const qrLoading = document.getElementById("mobile-qr-loading");

  if (qrLoading) qrLoading.style.display = "block";
  if (qrImg) qrImg.style.display = "none";

  let urlFinal = window.location.origin;

  try {
    const dados = await chamarApi("/acesso-mobile");
    if (dados && dados.url_acesso) {
      if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
        urlFinal = dados.url_acesso;
      } else {
        urlFinal = window.location.origin;
      }
    }
  } catch (e) {
    urlFinal = window.location.origin;
  }

  if (inputUrl) inputUrl.value = urlFinal;
  if (linkAbrir) linkAbrir.href = urlFinal;

  // Gera o QR code para acesso instantaneo no celular
  const qrApiUrl = `https://api.qrserver.com/v1/create-qr-code/?size=240x240&margin=4&data=${encodeURIComponent(urlFinal)}`;
  if (qrImg) {
    qrImg.onload = () => {
      if (qrLoading) qrLoading.style.display = "none";
      qrImg.style.display = "block";
    };
    qrImg.onerror = () => {
      if (qrLoading) qrLoading.textContent = "Erro ao carregar QR Code. Utilize o link abaixo.";
    };
    qrImg.src = qrApiUrl;
  }
}

function fecharModalAcessoMobile() {
  const modal = document.getElementById("modal-acesso-mobile");
  if (modal) modal.hidden = true;
}

document.getElementById("btn-abrir-acesso-mobile")?.addEventListener("click", abrirModalAcessoMobile);
document.getElementById("menu-btn-acesso-mobile")?.addEventListener("click", (e) => {
  e.preventDefault();
  abrirModalAcessoMobile();
  fecharSidebar();
});
document.getElementById("modal-acesso-mobile-fechar")?.addEventListener("click", fecharModalAcessoMobile);
document.getElementById("btn-fechar-acesso-mobile")?.addEventListener("click", fecharModalAcessoMobile);
document.getElementById("modal-acesso-mobile")?.addEventListener("click", (e) => {
  if (e.target === e.currentTarget) fecharModalAcessoMobile();
});

document.getElementById("btn-copiar-mobile-url")?.addEventListener("click", async () => {
  const inputUrl = document.getElementById("input-mobile-url");
  if (!inputUrl) return;
  try {
    await navigator.clipboard.writeText(inputUrl.value);
    mostrarToast("Link de acesso copiado com sucesso!", "success");
  } catch (err) {
    inputUrl.select();
    document.execCommand("copy");
    mostrarToast("Link copiado!", "success");
  }
});

// ---------------------- BARRA DE NAVEGAÇÃO INFERIOR MOBILE ----------------------

document.getElementById("btn-mnav-entrada")?.addEventListener("click", () => {
  mostrarView("view-visao-geral");
  document.querySelectorAll(".btn-mobile-nav").forEach(b => b.classList.remove("active"));
  document.getElementById("btn-mnav-entrada")?.classList.add("active");
  const inputPlaca = document.getElementById("input-placa");
  if (inputPlaca) {
    inputPlaca.scrollIntoView({ behavior: "smooth", block: "center" });
    setTimeout(() => inputPlaca.focus(), 300);
  }
});

document.getElementById("btn-mnav-patio")?.addEventListener("click", () => {
  mostrarView("view-visao-geral");
  document.querySelectorAll(".btn-mobile-nav").forEach(b => b.classList.remove("active"));
  document.getElementById("btn-mnav-patio")?.classList.add("active");
  const tabPatio = document.getElementById("tab-count-patio");
  if (tabPatio) tabPatio.click();
  const vehicleList = document.getElementById("vehicle-list");
  if (vehicleList) vehicleList.scrollIntoView({ behavior: "smooth", block: "start" });
});

document.getElementById("btn-mnav-saida")?.addEventListener("click", () => {
  mostrarView("view-visao-geral");
  document.querySelectorAll(".btn-mobile-nav").forEach(b => b.classList.remove("active"));
  document.getElementById("btn-mnav-saida")?.classList.add("active");
  const inputBusca = document.getElementById("input-busca");
  if (inputBusca) {
    inputBusca.scrollIntoView({ behavior: "smooth", block: "center" });
    setTimeout(() => inputBusca.focus(), 300);
    mostrarToast("Digite a placa ou ticket para registrar a saída", "info");
  }
});

document.getElementById("btn-mnav-vagas")?.addEventListener("click", () => {
  document.querySelectorAll(".btn-mobile-nav").forEach(b => b.classList.remove("active"));
  document.getElementById("btn-mnav-vagas")?.classList.add("active");
  abrirMapaVagas();
});

document.getElementById("btn-mnav-menu")?.addEventListener("click", () => {
  abrirSidebar();
});
