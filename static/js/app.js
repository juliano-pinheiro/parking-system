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
  document.getElementById("app-sidebar").classList.remove("open");
  document.getElementById("sidebar-backdrop").classList.remove("open");

  if (viewId === "view-visao-geral") {
    carregarDashboard();
    if (abaAtual === "patio") carregarPatio();
    else if (abaAtual === "historico") carregarHistorico();
    else if (abaAtual === "consultar") consultar("");
  } else if (viewId === "view-empresas") {
    carregarEmpresas();
  } else if (viewId === "view-financeiro") {
    carregarFinanceiro();
  } else if (viewId === "view-relatorios") {
    carregarRelatoriosFinanceiros();
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
  } else if (viewId === "view-auditoria") {
    carregarAuditoria();
  }
}

document.querySelectorAll(".menu-item").forEach((item) => {
  item.addEventListener("click", (evento) => {
    evento.preventDefault();
    mostrarView(item.dataset.view);
  });
});

// Toggle dos grupos de menu (submenus expansiveis)
document.querySelectorAll(".menu-group-toggle").forEach((toggle) => {
  toggle.addEventListener("click", () => {
    const grupo = toggle.closest(".menu-group");
    if (grupo) grupo.classList.toggle("open");
  });
});

// Pesquisa do menu: filtra itens
const inputPesquisaMenu = document.getElementById("sidebar-input-pesquisa");
if (inputPesquisaMenu) {
  inputPesquisaMenu.addEventListener("input", () => {
    const termo = inputPesquisaMenu.value.trim().toLowerCase();
    document.querySelectorAll(".menu-item").forEach((item) => {
      const texto = item.textContent.toLowerCase();
      item.style.display = texto.includes(termo) ? "flex" : "none";
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
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
}

// ---------------------- NOVA ENTRADA ----------------------

document.getElementById("form-entrada").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const placaInput = document.getElementById("input-placa");
  const tipoInput = document.getElementById("input-tipo");
  const obsInput = document.getElementById("input-observacoes");
  const botao = evento.target.querySelector(".btn-emitir");

  const placa = placaInput.value.trim();
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
    tipoInput.value = "Carro";

    await carregarDashboard();
    if (abaAtual === "patio") await carregarPatio();

    // Exibe o modelo do ticket emitido para impressao
    mostrarTicket(dados.ticket);
  } catch (erro) {
    mostrarToast(erro.message, "error");
  } finally {
    botao.disabled = false;
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
});

// ---------------------- SAIDA ----------------------

let saidaPendente = null; // identificador aguardando escolha da forma de pagamento

async function registrarSaida(identificador) {
  // Abre o modal de forma de pagamento antes de confirmar a saida
  saidaPendente = identificador;
  document.getElementById("modal-forma-pagamento").hidden = false;
}

async function confirmarSaida(identificador, formaPagamento) {
  try {
    const dados = await chamarApi("/saida", {
      method: "POST",
      body: JSON.stringify({ identificador, forma_pagamento: formaPagamento }),
    });
    mostrarToast(dados.mensagem, "success");
    await carregarDashboard();
    await recarregarAbaAtual();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
}

function fecharModalForma() {
  document.getElementById("modal-forma-pagamento").hidden = true;
  saidaPendente = null;
}

document.getElementById("modal-forma-fechar").addEventListener("click", fecharModalForma);
document.getElementById("btn-forma-cancelar").addEventListener("click", fecharModalForma);
document.getElementById("modal-forma-pagamento").addEventListener("click", (evento) => {
  if (evento.target === evento.currentTarget) fecharModalForma();
});

document.getElementById("forma-opcoes").addEventListener("click", (evento) => {
  const botao = evento.target.closest(".forma-opcao");
  if (!botao) return;
  const forma = botao.dataset.forma;
  const identificador = saidaPendente;
  fecharModalForma();
  if (identificador) confirmarSaida(identificador, forma);
});

document.addEventListener("keydown", (evento) => {
  if (evento.key === "Escape" && !document.getElementById("modal-forma-pagamento").hidden) fecharModalForma();
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

    const dataEntrada = ticket.entrada.split(" ")[0].slice(0, 5);
    const horaEntrada = ticket.entrada.split(" ")[1] ? ticket.entrada.split(" ")[1].slice(0, 5) : "";

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

    item.innerHTML = `
      <div class="vehicle-icon">${iconeVeiculo(ticket.tipo_veiculo)}</div>
      <div class="vehicle-main">
        <div class="vehicle-plate-row">
          <span class="vehicle-plate">${ticket.placa}</span>
          <span class="vehicle-type">${ticket.tipo_veiculo}</span>
        </div>
        <div class="vehicle-meta">
          ${ICON_CLOCK} ${ticket.tempo_estacionado} &middot; ${dataEntrada}, ${horaEntrada}
        </div>
        ${obsHtml}
      </div>
      <div class="vehicle-right">
        ${statusHtml}
        <span class="vehicle-value">${formatarMoeda(ticket.valor)}</span>
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

// ---------------------- BUSCA (CAMPO DE TEXTO) ----------------------

const inputBusca = document.getElementById("input-busca");

async function executarBuscaAtual() {
  const termo = inputBusca.value.trim();

  if (abaAtual === "patio") {
    if (!termo) return carregarPatio();
    const filtrados = cacheVeiculosPatio.filter((t) =>
      t.placa.toUpperCase().includes(termo.toUpperCase()) || String(t.numero).includes(termo)
    );
    renderListaVeiculos(filtrados, { permitirSaida: true });
  } else if (abaAtual === "historico") {
    if (!termo) return carregarHistorico();
    const dados = await chamarApi(`/historico`);
    const filtrados = dados.veiculos.filter((t) =>
      t.placa.toUpperCase().includes(termo.toUpperCase()) || String(t.numero).includes(termo)
    );
    renderListaVeiculos(filtrados, { permitirSaida: false });
  } else if (abaAtual === "consultar") {
    await consultar(termo);
  }
}

let debounceBusca = null;
inputBusca.addEventListener("input", () => {
  clearTimeout(debounceBusca);
  debounceBusca = setTimeout(executarBuscaAtual, 200);
});

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

  mostrarTicket(ticket);
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

  lancamentos.forEach((lancamento) => {
    const linha = document.createElement("tr");
    const tipoEntrada = lancamento.tipo === "entrada";
    const forma = FORMAS_LABEL[lancamento.forma_pagamento] || lancamento.forma_pagamento;
    const origem = lancamento.origem === "ticket" ? " (ticket)" : "";

    linha.innerHTML = `
      <td>${lancamento.data || "—"}</td>
      <td class="cell-nome">${lancamento.descricao}${origem}</td>
      <td>
        <span class="badge ${tipoEntrada ? "badge-ativo" : "badge-inativo"}">${tipoEntrada ? "Entrada" : "Saída"}</span>
      </td>
      <td><span class="badge">${forma}</span></td>
      <td class="${tipoEntrada ? "valor-entrada" : "valor-saida"}">${tipoEntrada ? "+" : "−"} ${formatarMoeda(lancamento.valor)}</td>
      <td class="col-acoes">
        <button type="button" class="btn-acao" data-acao-lancamento="editar" data-id="${lancamento.id}" title="Editar">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <button type="button" class="btn-acao btn-acao-danger" data-acao-lancamento="excluir" data-id="${lancamento.id}" title="Excluir">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M10 11v6M14 11v6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
        </button>
      </td>
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
    mostrarToast(erro.message, "error");
    corpo.innerHTML = '<tr><td colspan="6" class="table-empty">Erro ao carregar usuários.</td></tr>';
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
    const dataCadastro = (usuario.data_cadastro || "").split(" ")[0] || "—";
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
        await carregarSessao();
        await carregarEmpresas();
        await carregarDashboard();
        await carregarPatio();
        await carregarUsuarios();
        await carregarConfiguracoes();
        recarregarAbaAtual();
      } catch (erro) {
        mostrarToast(erro.message, "error");
      }
    });
  });
}

document.getElementById("btn-trocar-empresa").addEventListener("click", abrirModalTrocarEmpresa);
document.getElementById("modal-trocar-empresa-fechar").addEventListener("click", () => {
  document.getElementById("modal-trocar-empresa").hidden = true;
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

// ---------------------- CONFIGURACOES ----------------------

function aplicarNomeSistema(nome) {
  const nomeFinal = (nome || "").trim() || "Estaciona Parking";
  const elSidebar = document.getElementById("nome-sistema");
  const elRodape = document.getElementById("nome-sistema-rodape");
  const elTitulo = document.getElementById("titulo-sistema");
  if (elSidebar) elSidebar.textContent = nomeFinal;
  if (elRodape) elRodape.textContent = nomeFinal;
  if (elTitulo) elTitulo.textContent = `${nomeFinal} - Controle por ticket`;
}

async function carregarConfiguracoes() {
  try {
    const dados = await chamarApi("/configuracoes");
    cacheConfiguracoes = dados;
    // Identificacao
    document.getElementById("input-config-nome").value = dados.nome_estacionamento || "";
    document.getElementById("input-config-cnpj").value = dados.cnpj || "";
    document.getElementById("input-config-telefone").value = dados.telefone || "";
    document.getElementById("input-config-endereco").value = dados.endereco || "";
    document.getElementById("input-config-cidade").value = dados.cidade || "";
    document.getElementById("input-config-estado").value = dados.estado || "";
    document.getElementById("input-config-cep").value = dados.cep || "";

    // Funcionamento
    document.getElementById("input-config-horario-abertura").value = dados.horario_abertura || "";
    document.getElementById("input-config-horario-fechamento").value = dados.horario_fechamento || "";

    // Vagas
    document.getElementById("input-config-total-vagas").value = dados.total_vagas;
    document.getElementById("input-config-vagas-carro").value = dados.vagas_carro ?? 0;
    document.getElementById("input-config-vagas-moto").value = dados.vagas_moto ?? 0;
    document.getElementById("input-config-vagas-carro-grande").value = dados.vagas_carro_grande ?? 0;
    document.getElementById("input-config-vagas-caminhonete").value = dados.vagas_caminhonete ?? 0;

    // Precos
    document.getElementById("input-config-primeira-hora").value = dados.valor_primeira_hora;
    document.getElementById("input-config-hora-adicional").value = dados.valor_hora_adicional;
    document.getElementById("input-config-valor-mensal").value = dados.valor_mensal;

    // Ticket
    document.getElementById("input-config-cabecalho-ticket").value = dados.cabecalho_ticket || "";
    document.getElementById("input-config-rodape-ticket").value = dados.rodape_ticket || "";

    // Regras
    document.getElementById("input-config-bloquear-sem-vaga").checked = !!dados.bloquear_sem_vaga;
    document.getElementById("input-config-exigir-observacao").checked = dados.exigir_observacao !== false;

    // PIX
    document.getElementById("input-config-pix-tipo").value = dados.pix_tipo || "";
    document.getElementById("input-config-pix-chave").value = dados.pix_chave || "";

    aplicarNomeSistema(dados.nome_estacionamento);
    atualizarPreviewTicket();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }

  // Carrega a tabela de precos (regras avancadas)
  try {
    const dadosTabela = await chamarApi("/tabela-precos");
    const tp = dadosTabela.tabela_precos || {};
    document.getElementById("input-config-tp-fracionamento").value = tp.fracionamento_minutos ?? 60;
    document.getElementById("input-config-tp-tarifa-minima").value = tp.tarifa_minima ?? "";
    document.getElementById("input-config-tp-meia-min").value = tp.meia_estadia_minutos ?? "";
    document.getElementById("input-config-tp-meia-valor").value = tp.meia_estadia_valor ?? "";
    document.getElementById("input-config-tp-tolerancia").value = tp.tolerancia_minutos ?? "";
    document.getElementById("input-config-tp-noturno").value = tp.valor_noturno ?? "";
    document.getElementById("input-config-tp-fim-semana").value = tp.fim_semana ?? "";
    document.getElementById("input-config-tp-feriados").value = tp.feriados ?? "";

    // Precos por tipo de veiculo
    document.getElementById("input-config-tp-carro-primeira").value = tp.primeira_hora ?? "";
    document.getElementById("input-config-tp-carro-adicional").value = tp.hora_adicional ?? "";
    document.getElementById("input-config-tp-carro-diaria").value = tp.diaria ?? "";
    document.getElementById("input-config-tp-carro-minuto").value = tp.valor_minuto ?? "";
    document.getElementById("input-config-tp-carro-max").value = tp.valor_maximo_diario ?? "";
    document.getElementById("input-config-tp-carro-mensal").value = tp.mensal ?? "";

    document.getElementById("input-config-tp-moto-primeira").value = tp.moto_primeira_hora ?? "";
    document.getElementById("input-config-tp-moto-adicional").value = tp.moto_hora_adicional ?? "";
    document.getElementById("input-config-tp-moto-diaria").value = tp.moto_diaria ?? "";
    document.getElementById("input-config-tp-moto-minuto").value = tp.moto_valor_minuto ?? "";
    document.getElementById("input-config-tp-moto-max").value = tp.moto_valor_maximo_diario ?? "";
    document.getElementById("input-config-tp-moto-mensal").value = tp.moto_mensal ?? "";

    document.getElementById("input-config-tp-cg-primeira").value = tp.carro_grande_primeira_hora ?? "";
    document.getElementById("input-config-tp-cg-adicional").value = tp.carro_grande_hora_adicional ?? "";
    document.getElementById("input-config-tp-cg-diaria").value = tp.carro_grande_diaria ?? "";
    document.getElementById("input-config-tp-cg-minuto").value = tp.carro_grande_valor_minuto ?? "";
    document.getElementById("input-config-tp-cg-max").value = tp.carro_grande_valor_maximo_diario ?? "";
    document.getElementById("input-config-tp-cg-mensal").value = tp.carro_grande_mensal ?? "";

    document.getElementById("input-config-tp-cam-primeira").value = tp.caminhonete_primeira_hora ?? "";
    document.getElementById("input-config-tp-cam-adicional").value = tp.caminhonete_hora_adicional ?? "";
    document.getElementById("input-config-tp-cam-diaria").value = tp.caminhonete_diaria ?? "";
    document.getElementById("input-config-tp-cam-minuto").value = tp.caminhonete_valor_minuto ?? "";
    document.getElementById("input-config-tp-cam-max").value = tp.caminhonete_valor_maximo_diario ?? "";
    document.getElementById("input-config-tp-cam-mensal").value = tp.caminhonete_mensal ?? "";
  } catch (erro) {
    // tabela de precos pode nao existir ainda; ignora
  }
}

function atualizarPreviewTicket() {
  const nome = document.getElementById("input-config-nome").value.trim() || "Estaciona Parking";
  const endereco = document.getElementById("input-config-endereco").value.trim();
  const telefone = document.getElementById("input-config-telefone").value.trim();
  const cabecalho = document.getElementById("input-config-cabecalho-ticket").value.trim();
  const rodape = document.getElementById("input-config-rodape-ticket").value.trim();

  document.getElementById("ticket-preview-nome").textContent = nome;
  document.getElementById("ticket-preview-endereco").textContent = endereco;
  document.getElementById("ticket-preview-telefone").textContent = telefone;

  const headerEl = document.querySelector(".ticket-preview-header");
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

  document.getElementById("ticket-preview-rodape").textContent = rodape;
}

// Atualiza a preview do ticket enquanto o usuario digita
["input-config-nome", "input-config-endereco", "input-config-telefone",
 "input-config-cabecalho-ticket", "input-config-rodape-ticket"].forEach((id) => {
  const el = document.getElementById(id);
  if (el) el.addEventListener("input", atualizarPreviewTicket);
});

document.getElementById("form-configuracoes").addEventListener("submit", async (evento) => {
  evento.preventDefault();

  const botaoSalvar = evento.target.querySelector(".btn-salvar-config");
  botaoSalvar.disabled = true;

  const payload = {
    nome_estacionamento: document.getElementById("input-config-nome").value.trim(),
    cnpj: document.getElementById("input-config-cnpj").value.trim(),
    telefone: document.getElementById("input-config-telefone").value.trim(),
    endereco: document.getElementById("input-config-endereco").value.trim(),
    cidade: document.getElementById("input-config-cidade").value.trim(),
    estado: document.getElementById("input-config-estado").value.trim(),
    cep: document.getElementById("input-config-cep").value.trim(),
    horario_abertura: document.getElementById("input-config-horario-abertura").value.trim(),
    horario_fechamento: document.getElementById("input-config-horario-fechamento").value.trim(),
    total_vagas: Number(document.getElementById("input-config-total-vagas").value),
    vagas_carro: Number(document.getElementById("input-config-vagas-carro").value || 0),
    vagas_moto: Number(document.getElementById("input-config-vagas-moto").value || 0),
    vagas_carro_grande: Number(document.getElementById("input-config-vagas-carro-grande").value || 0),
    vagas_caminhonete: Number(document.getElementById("input-config-vagas-caminhonete").value || 0),
    valor_primeira_hora: Number(document.getElementById("input-config-primeira-hora").value),
    valor_hora_adicional: Number(document.getElementById("input-config-hora-adicional").value),
    valor_mensal: Number(document.getElementById("input-config-valor-mensal").value),
    cabecalho_ticket: document.getElementById("input-config-cabecalho-ticket").value.trim(),
    rodape_ticket: document.getElementById("input-config-rodape-ticket").value.trim(),
    bloquear_sem_vaga: document.getElementById("input-config-bloquear-sem-vaga").checked,
    exigir_observacao: document.getElementById("input-config-exigir-observacao").checked,
    pix_tipo: document.getElementById("input-config-pix-tipo").value.trim(),
    pix_chave: document.getElementById("input-config-pix-chave").value.trim(),
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
    botaoSalvar.disabled = false;
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
document.getElementById("btn-config-ir-formas").addEventListener("click", () => {
  mostrarView("view-formas-pagamento");
});

// ---------------------- FUNCOES E PERMISSOES ----------------------

let permissoesMatriz = null;
let permissoesPerfis = [];
let permissoesModulos = [];
let permissoesAcoes = [];
let permissoesPerfisDetalhes = [];
let perfilSelecionado = null;

const PERFIS_BASE = ["admin", "supervisor", "operador"];

const PERMISSOES_ACAO_LABEL = {
  ver: "Ver",
  criar: "Criar",
  editar: "Editar",
  excluir: "Excluir",
  autorizar: "Autorizar",
  fechar_caixa: "Fechar caixa",
  estornar: "Estornar",
  cancelar: "Cancelar",
};

const PERMISSOES_ACAO_ICON = {
  ver: "O",
  criar: "+",
  editar: "E",
  excluir: "X",
  autorizar: "A",
  fechar_caixa: "F",
  estornar: "R",
  cancelar: "C",
};

const PERMISSOES_MODULO_LABEL = {
  caixa: "Caixa",
  pagamentos: "Pagamentos",
  formas_pagamento: "Formas de Pagamento",
  tabela_precos: "Tabela de Preços",
  descontos: "Descontos",
  cortesias: "Cortesias",
  mensalistas: "Mensalistas",
  convenios: "Convênios",
  contas_receber: "Contas a Receber",
  estornos: "Estornos",
  auditoria: "Auditoria",
  dashboard_financeiro: "Dashboard Financeiro",
  relatorios: "Relatórios",
  usuarios: "Usuários",
};

const PERMISSOES_MODULO_DESC = {
  caixa: "Abertura, fechamento, sangria e suprimento de caixa",
  pagamentos: "Registro, cancelamento e estorno de pagamentos",
  formas_pagamento: "Cadastro das formas de pagamento aceitas",
  tabela_precos: "Valores e regras de cobrança dos tickets",
  descontos: "Cadastro e autorização de descontos",
  cortesias: "Emissão e autorização de cortesias",
  mensalistas: "Cadastro, pagamento e bloqueio de mensalistas",
  convenios: "Cadastro de empresas conveniadas",
  contas_receber: "Contas a receber e baixas de convênios",
  estornos: "Registro de estornos de pagamentos",
  auditoria: "Consulta de logs de alteração e acesso",
  dashboard_financeiro: "Indicadores e gráficos financeiros",
  relatorios: "Relatórios e exportações",
  usuarios: "Cadastro e gestão de usuários do sistema",
};

// Agrupa os modulos por categoria para melhor organizacao
const PERMISSOES_CATEGORIAS = [
  {
    nome: "Operacional",
    modulos: ["caixa", "pagamentos", "tabela_precos", "descontos", "cortesias", "estornos"],
  },
  {
    nome: "Financeiro",
    modulos: ["dashboard_financeiro", "relatorios", "formas_pagamento", "contas_receber"],
  },
  {
    nome: "Cadastros",
    modulos: ["mensalistas", "convenios"],
  },
  {
    nome: "Administrativo",
    modulos: ["usuarios", "auditoria"],
  },
];

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
  container.innerHTML = '<p class="config-hint">Carregando perfis...</p>';
  try {
    const dados = await chamarApi("/permissoes");
    permissoesMatriz = dados.matriz || {};
    permissoesPerfis = dados.perfis || [];
    permissoesModulos = dados.modulos || [];
    permissoesAcoes = dados.acoes || [];
    permissoesPerfisDetalhes = dados.perfis_detalhes || [];
    renderPerfis();
    atualizarSelectPerfis();
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
    const badgeTexto = isBase ? "Base" : (ativo ? "Ativo" : "Inativo");
    const badgeClasseFinal = isBase ? "base" : badgeClasse;

    html += `<div class="${classe}" data-perfil-card="${perfil.codigo}">
      <div class="perfil-card-header">
        <span class="perfil-card-name">
          ${perfil.nome}
          <span class="perfil-card-badge ${badgeClasseFinal}">${badgeTexto}</span>
        </span>
      </div>
      <div class="perfil-card-desc">${perfil.descricao || "Sem descricao"}</div>
      <div class="perfil-card-actions">
        <button type="button" class="btn-mini" data-selecionar-perfil="${perfil.codigo}">Permissoes</button>
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
  titulo.textContent = `Permissoes - ${nomePerfil(codigo)}`;

  if (codigo === "admin") {
    container.innerHTML = '<p class="config-hint">O perfil Administrador tem acesso total e nao pode ser alterado.</p>';
    return;
  }

  let html = '<div class="permissoes-card">';
  html += `<div class="permissoes-card-body">
    <div class="permissoes-card-actions" style="margin-bottom: 12px;">
      <button type="button" class="btn-mini" id="btn-marcar-tudo-perfil">Marcar tudo</button>
      <button type="button" class="btn-mini btn-mini-ghost" id="btn-desmarcar-tudo-perfil">Desmarcar tudo</button>
    </div>`;

  PERMISSOES_CATEGORIAS.forEach((cat) => {
    const modulosCat = cat.modulos.filter((m) => permissoesModulos.includes(m));
    if (!modulosCat.length) return;
    html += `<div class="permissoes-categoria">
      <div class="permissoes-categoria-title">${cat.nome}</div>
      ${modulosCat.map((modulo) => {
        const acoes = (permissoesMatriz[modulo] && permissoesMatriz[modulo][codigo]) || [];
        return `<div class="permissoes-modulo">
          <div class="permissoes-modulo-info">
            <span class="permissoes-modulo-nome">${PERMISSOES_MODULO_LABEL[modulo] || modulo}</span>
            <span class="permissoes-modulo-desc">${PERMISSOES_MODULO_DESC[modulo] || ""}</span>
          </div>
          <div class="permissoes-acoes">
            ${permissoesAcoes.map((acao) => {
              const marcado = acoes.includes(acao) ? "checked" : "";
              return `<label class="permissoes-acao" title="${PERMISSOES_ACAO_LABEL[acao] || acao}">
                <input type="checkbox" data-modulo="${modulo}" data-perfil="${codigo}" data-acao="${acao}" ${marcado}>
                <span class="permissoes-acao-icon">${PERMISSOES_ACAO_ICON[acao] || ""}</span>
                <span class="permissoes-acao-label">${PERMISSOES_ACAO_LABEL[acao] || acao}</span>
              </label>`;
            }).join("")}
          </div>
        </div>`;
      }).join("")}
    </div>`;
  });

  html += "</div></div>";
  container.innerHTML = html;

  document.getElementById("btn-marcar-tudo-perfil").addEventListener("click", () => {
    container.querySelectorAll(`input[data-perfil="${codigo}"]`).forEach((cb) => { cb.checked = true; });
  });
  document.getElementById("btn-desmarcar-tudo-perfil").addEventListener("click", () => {
    container.querySelectorAll(`input[data-perfil="${codigo}"]`).forEach((cb) => { cb.checked = false; });
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
      const acoes = [];
      document.querySelectorAll(`input[data-modulo="${modulo}"][data-perfil="${perfil}"]:checked`).forEach((cb) => {
        acoes.push(cb.dataset.acao);
      });
      novaMatriz[modulo][perfil] = acoes;
    });
  });
  return novaMatriz;
}

async function salvarPermissoes() {
  const botao = document.getElementById("btn-salvar-permissoes");
  botao.disabled = true;
  try {
    const dados = await chamarApi("/permissoes", {
      method: "PUT",
      body: JSON.stringify({ matriz: coletarPermissoes() }),
    });
    permissoesMatriz = dados.matriz || permissoesMatriz;
    mostrarToast(dados.mensagem, "success");
    if (perfilSelecionado) renderMatrizPerfil(perfilSelecionado);
  } catch (erro) {
    mostrarToast(erro.message, "error");
  } finally {
    botao.disabled = false;
  }
}

async function restaurarPermissoesPadrao() {
  if (!confirm("Restaurar as permissoes padrao de todos os perfis? As alteracoes nao salvas serao perdidas.")) return;
  try {
    const dados = await chamarApi("/permissoes/restaurar", { method: "POST" });
    permissoesMatriz = dados.matriz || permissoesMatriz;
    mostrarToast(dados.mensagem, "success");
    if (perfilSelecionado) renderMatrizPerfil(perfilSelecionado);
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
}

// ---------------------- MODAL PERFIL ----------------------

let perfilEditandoId = null;

function abrirModalPerfil(perfil = null) {
  const overlay = document.getElementById("modal-perfil");
  perfilEditandoId = perfil ? perfil.id : null;
  document.getElementById("input-perfil-id").value = perfil ? perfil.id : "";
  document.getElementById("input-perfil-nome").value = perfil ? perfil.nome : "";
  document.getElementById("input-perfil-codigo").value = perfil ? perfil.codigo : "";
  document.getElementById("input-perfil-codigo").disabled = !!perfil;
  document.getElementById("input-perfil-descricao").value = perfil ? perfil.descricao : "";
  document.getElementById("modal-perfil-titulo").textContent = perfil ? "Editar perfil" : "Novo perfil";
  overlay.hidden = false;
  setTimeout(() => document.getElementById("input-perfil-nome").focus(), 50);
}

function fecharModalPerfil() {
  document.getElementById("modal-perfil").hidden = true;
  document.getElementById("form-perfil").reset();
  document.getElementById("input-perfil-id").value = "";
  document.getElementById("input-perfil-codigo").disabled = false;
  perfilEditandoId = null;
}

async function salvarPerfil(evento) {
  evento.preventDefault();
  const id = document.getElementById("input-perfil-id").value;
  const nome = document.getElementById("input-perfil-nome").value.trim();
  const codigo = document.getElementById("input-perfil-codigo").value.trim().toLowerCase().replace(/\\s+/g, "_");
  const descricao = document.getElementById("input-perfil-descricao").value.trim();

  if (!nome || !codigo) return;

  const botao = document.getElementById("btn-perfil-salvar");
  botao.disabled = true;
  try {
    if (id) {
      await chamarApi(`/perfis/${id}`, {
        method: "PUT",
        body: JSON.stringify({ nome, descricao }),
      });
      mostrarToast("Perfil atualizado com sucesso!", "success");
    } else {
      await chamarApi("/perfis", {
        method: "POST",
        body: JSON.stringify({ nome, codigo, descricao }),
      });
      mostrarToast("Perfil criado com sucesso!", "success");
    }
    fecharModalPerfil();
    await carregarPerfis();
    if (perfilSelecionado) renderMatrizPerfil(perfilSelecionado);
  } catch (erro) {
    mostrarToast(erro.message, "error");
  } finally {
    botao.disabled = false;
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
  const origem = prompt("Informe o codigo do perfil de origem (ex: operador, supervisor):");
  if (!origem) return;
  try {
    await chamarApi(`/perfis/${id}/clonar`, {
      method: "POST",
      body: JSON.stringify({ origem }),
    });
    mostrarToast("Permissoes clonadas com sucesso!", "success");
    await carregarPerfis();
    if (perfilSelecionado) renderMatrizPerfil(perfilSelecionado);
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

// Eventos
document.getElementById("btn-novo-perfil").addEventListener("click", () => abrirModalPerfil());
document.getElementById("modal-perfil-fechar").addEventListener("click", fecharModalPerfil);
document.getElementById("btn-perfil-cancelar").addEventListener("click", fecharModalPerfil);
document.getElementById("modal-perfil").addEventListener("click", (evento) => {
  if (evento.target === evento.currentTarget) fecharModalPerfil();
});
document.getElementById("form-perfil").addEventListener("submit", salvarPerfil);
document.addEventListener("keydown", (evento) => {
  if (evento.key === "Escape" && !document.getElementById("modal-perfil").hidden) fecharModalPerfil();
});

document.getElementById("btn-salvar-permissoes").addEventListener("click", salvarPermissoes);
document.getElementById("btn-cancelar-permissoes").addEventListener("click", () => {
  if (perfilSelecionado) renderMatrizPerfil(perfilSelecionado);
});
document.getElementById("btn-restaurar-permissoes").addEventListener("click", restaurarPermissoesPadrao);

// Carrega as permissoes ao abrir a aba de configuracoes
document.querySelectorAll("#tabs-config .tab").forEach((botaoTab) => {
  botaoTab.addEventListener("click", () => {
    if (botaoTab.dataset.configTab === "permissoes") {
      perfilSelecionado = null;
      carregarPerfis();
    }
  });
});

// ---------------------- FORMAS DE PAGAMENTO ----------------------

let formaPagamentoEditandoId = null;

async function carregarFormasPagamento() {
  const tbody = document.getElementById("tabela-formas-pagamento");
  const empty = document.getElementById("formas-pagamento-empty");
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="4" class="table-empty">Carregando formas de pagamento...</td></tr>';
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
        <td><code>${f.codigo}</code></td>
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
    tbody.innerHTML = `<tr><td colspan="4" class="table-empty">Erro: ${erro.message}</td></tr>`;
  }
}

function abrirModalFormaPagamento(forma) {
  formaPagamentoEditandoId = forma ? forma.id : null;
  document.getElementById("modal-forma-pagamento-titulo").textContent = forma ? "Editar forma de pagamento" : "Nova forma de pagamento";
  document.getElementById("input-forma-pagamento-id").value = forma ? forma.id : "";
  document.getElementById("input-forma-pagamento-nome").value = forma ? forma.nome : "";
  document.getElementById("input-forma-pagamento-codigo").value = forma ? forma.codigo : "";
  document.getElementById("input-forma-pagamento-codigo").disabled = !!forma;
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
  const codigo = document.getElementById("input-forma-pagamento-codigo").value.trim();
  const ativo = document.getElementById("input-forma-pagamento-ativo").checked;
  try {
    if (id) {
      await chamarApi(`/formas-pagamento/${id}`, {
        method: "PUT",
        body: JSON.stringify({ nome, ativo }),
      });
    } else {
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
];

// Mapeia cada item do sidebar (data-view) para o modulo de permissao.
// Itens sem modulo (ex.: visao-geral) ficam sempre visiveis.
const MENU_PERMISSAO = {
  "view-usuarios": "usuarios",
  "view-clientes": "mensalistas",
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
  "view-configuracoes": "usuarios",
};

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
  corpo.innerHTML = "";

  let dados;
  try {
    dados = await chamarApi("/caixa");
  } catch (erro) {
    mostrarToast(erro.message, "error");
    corpo.innerHTML = '<tr><td colspan="8" class="table-empty">Erro ao carregar caixas.</td></tr>';
    return;
  }

  caixaAberto = dados.caixa_aberto;
  const statusBox = document.getElementById("caixa-status");

  if (caixaAberto) {
    statusBox.innerHTML = `
      <div class="caixa-aberto">
        <span class="badge badge-ativo">Caixa aberto</span>
        <span>Operador: <strong>${caixaAberto.operador}</strong></span>
        <span>Abertura: <strong>${caixaAberto.data_abertura}</strong></span>
        <span>Valor inicial: <strong>${formatarMoeda(caixaAberto.valor_inicial)}</strong></span>
      </div>
    `;
    document.getElementById("btn-abrir-caixa").hidden = true;
    document.getElementById("btn-sangria").hidden = false;
    document.getElementById("btn-suprimento").hidden = false;
    document.getElementById("btn-fechar-caixa").hidden = false;
  } else {
    statusBox.innerHTML = '<p class="empty-state">Nenhum caixa aberto. Clique em "Abrir caixa" para iniciar o expediente.</p>';
    document.getElementById("btn-abrir-caixa").hidden = false;
    document.getElementById("btn-sangria").hidden = true;
    document.getElementById("btn-suprimento").hidden = true;
    document.getElementById("btn-fechar-caixa").hidden = true;
  }

  (dados.caixas || []).forEach((caixa) => {
    const linha = document.createElement("tr");
    const aberto = caixa.status === "aberto";
    linha.innerHTML = `
      <td class="cell-nome">${caixa.operador}</td>
      <td>${caixa.data_abertura}</td>
      <td>${caixa.data_fechamento || "—"}</td>
      <td>${formatarMoeda(caixa.valor_inicial)}</td>
      <td>${formatarMoeda(caixa.valor_esperado)}</td>
      <td>${formatarMoeda(caixa.valor_contado)}</td>
      <td class="${caixa.diferenca >= 0 ? "valor-entrada" : "valor-saida"}">${formatarMoeda(caixa.diferenca)}</td>
      <td><span class="badge ${aberto ? "badge-ativo" : "badge-inativo"}">${aberto ? "Aberto" : "Fechado"}</span></td>
    `;
    corpo.appendChild(linha);
  });
}

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
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
});

// Fechar caixa
async function abrirModalFecharCaixa() {
  if (!caixaAberto) return;
  try {
    const dados = await chamarApi(`/caixa/${caixaAberto.id}/movimentacoes`);
    const totais = {};
    (dados.movimentacoes || []).forEach((m) => {
      if (m.tipo === "entrada") {
        const forma = m.forma_pagamento || "dinheiro";
        totais[forma] = (totais[forma] || 0) + m.valor;
      }
    });
    const esperado = Object.values(totais).reduce((a, b) => a + b, 0);
    document.getElementById("fechamento-resumo").innerHTML = `
      <div class="fechamento-linha"><span>Valor esperado</span><strong>${formatarMoeda(esperado)}</strong></div>
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

// ---------------------- PAGAMENTOS ----------------------

async function carregarPagamentos() {
  const corpo = document.getElementById("tabela-pagamentos");
  const empty = document.getElementById("pagamentos-empty");
  corpo.innerHTML = "";

  let dados;
  try {
    dados = await chamarApi("/pagamentos");
  } catch (erro) {
    mostrarToast(erro.message, "error");
    corpo.innerHTML = '<tr><td colspan="7" class="table-empty">Erro ao carregar pagamentos.</td></tr>';
    return;
  }

  const pagamentos = dados.pagamentos || [];
  empty.hidden = pagamentos.length > 0;

  pagamentos.forEach((pagamento) => {
    const linha = document.createElement("tr");
    const status = pagamento.status;
    const badge = status === "ativo" ? "badge-ativo" : status === "cancelado" ? "badge-inativo" : "badge-warn";
    linha.innerHTML = `
      <td>${pagamento.ticket_numero || "—"}</td>
      <td>${pagamento.data}</td>
      <td class="valor-entrada">${formatarMoeda(pagamento.valor)}</td>
      <td><span class="badge">${FORMAS_LABEL[pagamento.forma_pagamento] || pagamento.forma_pagamento}</span></td>
      <td>${pagamento.operador || "—"}</td>
      <td><span class="badge ${badge}">${status}</span></td>
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
      <td><span class="badge ${badge}">${m.status}</span></td>
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
      <td>${conta.vencimento || "—"}</td>
      <td><span class="badge ${badge}">${conta.status}</span></td>
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
      <td>${c.data}</td>
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

async function carregarAuditoria() {
  const corpo = document.getElementById("tabela-auditoria");
  const empty = document.getElementById("auditoria-empty");
  corpo.innerHTML = "";

  let dados;
  try {
    dados = await chamarApi("/auditoria");
  } catch (erro) {
    mostrarToast(erro.message, "error");
    corpo.innerHTML = '<tr><td colspan="7" class="table-empty">Erro ao carregar auditoria.</td></tr>';
    return;
  }

  const registros = dados.auditoria || [];
  empty.hidden = registros.length > 0;

  registros.slice().reverse().forEach((a) => {
    const linha = document.createElement("tr");
    linha.innerHTML = `
      <td>${a.data}</td>
      <td><span class="badge">${a.tabela}</span></td>
      <td>${a.registro_id || "—"}</td>
      <td>${a.campo || "—"}</td>
      <td>${a.valor_antigo || "—"}</td>
      <td>${a.valor_novo || "—"}</td>
      <td>${a.usuario || "—"}</td>
    `;
    corpo.appendChild(linha);
  });
}

// ---------------------- DASHBOARD FINANCEIRO ----------------------

let dashCharts = {};

function criarGrafico(canvasId, tipo, labels, valores, cor) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  if (dashCharts[canvasId]) dashCharts[canvasId].destroy();
  dashCharts[canvasId] = new Chart(canvas, {
    type: tipo,
    data: {
      labels,
      datasets: [{
        label: "R$",
        data: valores,
        backgroundColor: cor,
        borderColor: cor,
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
}

async function carregarDashboardFinanceiro() {
  let dados;
  try {
    dados = await chamarApi("/dashboard-financeiro");
  } catch (erro) {
    mostrarToast(erro.message, "error");
    return;
  }

  document.getElementById("dash-receita-dia").textContent = formatarMoeda(dados.receita_dia);
  document.getElementById("dash-receita-mes").textContent = formatarMoeda(dados.receita_mes);
  document.getElementById("dash-receita-ano").textContent = formatarMoeda(dados.receita_ano);
  document.getElementById("dash-tickets").textContent = dados.quantidade_tickets;
  document.getElementById("dash-ticket-medio").textContent = formatarMoeda(dados.ticket_medio);

  criarGrafico("grafico-dash-diario", "bar", dados.grafico_diario.labels, dados.grafico_diario.valores, "rgba(59,130,246,0.7)");
  criarGrafico("grafico-dash-mensal", "bar", dados.grafico_mensal.labels, dados.grafico_mensal.valores, "rgba(16,185,129,0.7)");

  const formas = Object.entries(dados.receita_por_forma || {});
  criarGrafico(
    "grafico-dash-forma",
    "doughnut",
    formas.map(([k]) => FORMAS_LABEL[k] || k),
    formas.map(([, v]) => v),
    ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#14b8a6", "#ec4899"]
  );

  const horarios = Object.entries(dados.receita_por_horario || {});
  criarGrafico("grafico-dash-horario", "line", horarios.map(([k]) => k), horarios.map(([, v]) => v), "rgba(139,92,246,0.7)");
}

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
      formasGrid.innerHTML = "";
      formasEmpty.hidden = false;
    } else {
      formasEmpty.hidden = true;
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
    movEmpty.hidden = lancamentos.length > 0;
    lancamentos.forEach((lancamento) => {
      const linha = document.createElement("tr");
      const tipoEntrada = lancamento.tipo === "entrada";
      linha.innerHTML = `
        <td>${lancamento.data || "—"}</td>
        <td class="cell-nome">${lancamento.descricao}</td>
        <td><span class="badge ${tipoEntrada ? "badge-ativo" : "badge-inativo"}">${tipoEntrada ? "Entrada" : "Saída"}</span></td>
        <td><span class="badge">${FORMAS_LABEL[lancamento.forma_pagamento] || lancamento.forma_pagamento}</span></td>
        <td class="${tipoEntrada ? "valor-entrada" : "valor-saida"}">${tipoEntrada ? "+" : "−"} ${formatarMoeda(lancamento.valor)}</td>
      `;
      corpo.appendChild(linha);
    });
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
    if (usuario.empresa && headerEmpresa) {
      headerEmpresa.textContent = `🏢 ${usuario.empresa.nome_fantasia}`;
      headerEmpresa.hidden = false;
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
      atualizarSelectPerfis();
      aplicarPermissoesFrontend(usuario.perfil);

      // Se a view ativa nao tiver permissao "ver", volta para a visao geral
      const viewAtiva = document.querySelector(".view.view-active");
      if (viewAtiva) {
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

// ---------------------- INICIALIZACAO ----------------------

// Restaura a view e a aba em que o usuario estava (mantem a pagina ao F5/atualizar)
const viewSalva = localStorage.getItem("estaciona_view");
const viewsValidas = [
  "view-visao-geral", "view-empresas", "view-usuarios", "view-clientes", "view-financeiro",
  "view-caixa", "view-pagamentos", "view-mensalistas", "view-convenios",
  "view-contas-receber", "view-descontos", "view-cortesias",
  "view-dashboard-financeiro", "view-auditoria", "view-relatorios",
  "view-configuracoes",
];
if (viewSalva && viewsValidas.includes(viewSalva)) {
  mostrarView(viewSalva);
}

const abaSalva = localStorage.getItem("estaciona_aba");
if (abaSalva && ["patio", "historico", "consultar"].includes(abaSalva)) {
  abaAtual = abaSalva;
  document.querySelectorAll(".tab").forEach((t) => {
    t.classList.toggle("active", t.dataset.tab === abaSalva);
  });
}

atualizarDataHeader();
carregarSessao();
carregarEmpresas();
carregarDashboard();
carregarPatio();
carregarUsuarios();
carregarClientes();
carregarConfiguracoes();

setInterval(() => {
  carregarDashboard();
  if (!inputBusca.value.trim()) recarregarAbaAtual();
}, 15000);
