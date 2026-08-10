/* ==========================================================================
   Estaciona - Controle por ticket - Frontend JS
   Consome a API Flask (/api/...) e controla toda a interatividade da SPA.
   ========================================================================== */

const API_BASE = "/api";

let abaAtual = "patio";
let cacheVeiculosPatio = [];

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
  document.querySelectorAll(".view").forEach((view) => view.classList.remove("view-active"));
  const view = document.getElementById(viewId);
  if (view) view.classList.add("view-active");

  document.querySelectorAll(".menu-item").forEach((item) => item.classList.remove("active"));
  const menuItem = document.querySelector(`.menu-item[data-view="${viewId}"]`);
  if (menuItem) menuItem.classList.add("active");

  // Fecha sidebar em mobile apos selecao
  document.getElementById("app-sidebar").classList.remove("open");
  document.getElementById("sidebar-backdrop").classList.remove("open");

  if (viewId === "view-visao-geral") {
    carregarDashboard();
    if (abaAtual === "patio") carregarPatio();
    else if (abaAtual === "historico") carregarHistorico();
    else if (abaAtual === "consultar") consultar("");
  }
}

document.querySelectorAll(".menu-item").forEach((item) => {
  item.addEventListener("click", (evento) => {
    evento.preventDefault();
    mostrarView(item.dataset.view);
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
  } catch (erro) {
    mostrarToast(erro.message, "error");
  } finally {
    botao.disabled = false;
  }
});

// ---------------------- SAIDA ----------------------

async function registrarSaida(identificador) {
  try {
    const dados = await chamarApi("/saida", {
      method: "POST",
      body: JSON.stringify({ identificador }),
    });
    mostrarToast(dados.mensagem, "success");
    await carregarDashboard();
    await recarregarAbaAtual();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
}

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
    mostrarToast(`Ticket #${botao.dataset.numero} enviado para impressão.`, "success");
    window.print();
  }
});

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

// ---------------------- RELATORIOS ----------------------

document.getElementById("form-relatorio-modal").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const data = document.getElementById("input-data-relatorio").value.trim();

  try {
    const query = data ? `?data=${encodeURIComponent(data)}` : "";
    const dados = await chamarApi(`/relatorio${query}`);

    document.getElementById("modal-stats").hidden = false;
    document.getElementById("rel-total-entradas").textContent = dados.total_entradas;
    document.getElementById("rel-total-saidas").textContent = dados.total_saidas;
    document.getElementById("rel-faturamento").textContent = formatarMoeda(dados.faturamento_total);
  } catch (erro) {
    mostrarToast(erro.message, "error");
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

    const perfil = usuario.perfil === "admin" ? "Administrador" : "Operador";
    const statusAtivo = usuario.ativo;
    const dataCadastro = (usuario.data_cadastro || "").split(" ")[0] || "—";

    linha.innerHTML = `
      <td class="cell-nome">${usuario.nome}</td>
      <td>${usuario.email}</td>
      <td>
        <span class="badge ${statusAtivo ? "badge-perfil-admin" : ""}">${perfil}</span>
      </td>
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
  document.getElementById("input-usuario-perfil").value = usuario ? usuario.perfil : "operador";
  document.getElementById("input-usuario-ativo").value = usuario ? String(usuario.ativo) : "true";
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
  const perfil = document.getElementById("input-usuario-perfil").value;
  const ativo = document.getElementById("input-usuario-ativo").value === "true";

  if (!nome || !email) return;

  const botaoSalvar = document.getElementById("btn-usuario-salvar");
  botaoSalvar.disabled = true;
  try {
    if (id) {
      const dados = await chamarApi(`/usuarios/${id}`, {
        method: "PUT",
        body: JSON.stringify({ nome, email, perfil, ativo }),
      });
      mostrarToast(dados.mensagem, "success");
    } else {
      const dados = await chamarApi("/usuarios", {
        method: "POST",
        body: JSON.stringify({ nome, email, perfil, ativo }),
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
      ? `${cliente.data_inicio} – ${cliente.data_fim}`
      : "—";

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

async function carregarConfiguracoes() {
  try {
    const dados = await chamarApi("/configuracoes");
    document.getElementById("input-config-primeira-hora").value = dados.valor_primeira_hora;
    document.getElementById("input-config-hora-adicional").value = dados.valor_hora_adicional;
    document.getElementById("input-config-valor-mensal").value = dados.valor_mensal;
    document.getElementById("input-config-total-vagas").value = dados.total_vagas;
  } catch (erro) {
    mostrarToast(erro.message, "error");
  }
}

document.getElementById("form-configuracoes").addEventListener("submit", async (evento) => {
  evento.preventDefault();

  const botaoSalvar = evento.target.querySelector(".btn-salvar-config");
  botaoSalvar.disabled = true;

  const payload = {
    valor_primeira_hora: Number(document.getElementById("input-config-primeira-hora").value),
    valor_hora_adicional: Number(document.getElementById("input-config-hora-adicional").value),
    valor_mensal: Number(document.getElementById("input-config-valor-mensal").value),
    total_vagas: Number(document.getElementById("input-config-total-vagas").value),
  };

  try {
    const dados = await chamarApi("/configuracoes", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    mostrarToast(dados.mensagem, "success");
    await carregarConfiguracoes();
  } catch (erro) {
    mostrarToast(erro.message, "error");
  } finally {
    botaoSalvar.disabled = false;
  }
});

// ---------------------- INICIALIZACAO ----------------------

atualizarDataHeader();
carregarDashboard();
carregarPatio();
carregarUsuarios();
carregarClientes();
carregarConfiguracoes();

setInterval(() => {
  carregarDashboard();
  if (!inputBusca.value.trim()) recarregarAbaAtual();
}, 15000);
