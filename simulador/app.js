// Simulador "ChatGPT 2024" — TP4 IA y Neurociencias (UTDT)
// La API key vive solo en esta variable. No se escribe en disco ni en el navegador.
let apiKey = null;

const API = "https://api.openai.com/v1";
const ANIOS = { "gpt-4o-mini": "2024", "gpt-4o": "2024", "vicuna": "2023", "llava": "2023", "chatgpt": "2026" };

const ajustes = { modelo: "gpt-4o-mini", temperatura: 1, sistema: "" };
let guiones = [];
let conversaciones = [];
let actual = null;
let imagenPendiente = null; // {dataUrl, nombre}
let ocupado = false;
let loteDetener = false;

const $ = (id) => document.getElementById(id);

// ---------- utilidades ----------
function anioDe(modelo) {
  const m = (modelo || "").toLowerCase();
  for (const k of Object.keys(ANIOS)) if (m.includes(k)) return ANIOS[k];
  return "";
}
function marcaTiempo() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}`;
}
function descargar(nombre, texto) {
  const url = URL.createObjectURL(new Blob([texto], { type: "application/x-ndjson" }));
  const a = Object.assign(document.createElement("a"), { href: url, download: nombre });
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}
const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
function escapar(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ---------- markdown mínimo ----------
function inline(s) {
  return s
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<em>$2</em>");
}
function markdown(src) {
  // las fórmulas \[ ... \] pueden ocupar varias líneas: se juntan en una para que KaTeX las encuentre
  src = (src || "").replace(/\\\[([\s\S]*?)\\\]/g, (m) => "\n" + m.replace(/\n/g, " ") + "\n");
  const lineas = escapar(src).split("\n");
  let html = "", lista = null, enCodigo = false, codigo = [], tabla = [];
  const cerrarLista = () => { if (lista) { html += `</${lista}>`; lista = null; } };
  const cerrarTabla = () => {
    if (!tabla.length) return;
    const filas = tabla.filter((f) => !/^\|?\s*:?-{2,}/.test(f.replace(/\|/g, "|").trim()));
    html += "<table>" + filas.map((f, i) => {
      const celdas = f.trim().replace(/^\||\|$/g, "").split("|").map((c) => inline(c.trim()));
      const t = i === 0 ? "th" : "td";
      return "<tr>" + celdas.map((c) => `<${t}>${c}</${t}>`).join("") + "</tr>";
    }).join("") + "</table>";
    tabla = [];
  };
  for (const l of lineas) {
    if (l.trim().startsWith("```")) {
      if (enCodigo) { html += `<pre><code>${codigo.join("\n")}</code></pre>`; codigo = []; enCodigo = false; }
      else { cerrarLista(); cerrarTabla(); enCodigo = true; }
      continue;
    }
    if (enCodigo) { codigo.push(l); continue; }
    if (/^\s*\|.*\|\s*$/.test(l)) { cerrarLista(); tabla.push(l); continue; } else cerrarTabla();
    let m;
    if ((m = l.match(/^(#{1,6})\s+(.*)$/))) { cerrarLista(); const n = Math.min(3, m[1].length); html += `<h${n}>${inline(m[2])}</h${n}>`; continue; }
    if (/^\s*(-{3,}|\*{3,})\s*$/.test(l)) { cerrarLista(); html += "<hr>"; continue; }
    if ((m = l.match(/^\s*[-*•]\s+(.*)$/))) { if (lista !== "ul") { cerrarLista(); html += "<ul>"; lista = "ul"; } html += `<li>${inline(m[1])}</li>`; continue; }
    if ((m = l.match(/^\s*(\d+)[.)]\s+(.*)$/))) { if (lista !== "ol") { cerrarLista(); html += `<ol start="${m[1]}">`; lista = "ol"; } html += `<li>${inline(m[2])}</li>`; continue; }
    if (!l.trim()) { cerrarLista(); continue; }
    cerrarLista();
    html += `<p>${inline(l)}</p>`;
  }
  cerrarLista(); cerrarTabla();
  if (enCodigo) html += `<pre><code>${codigo.join("\n")}</code></pre>`;
  return html;
}

// ---------- API ----------
async function llamarOpenAI(mensajes, { modelo, temperatura }) {
  let espera = 1500;
  for (let intento = 0; intento < 6; intento++) {
    let r;
    try {
      r = await fetch(`${API}/chat/completions`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiKey}` },
        body: JSON.stringify({ model: modelo, temperature: temperatura, messages: mensajes }),
      });
    } catch (e) {
      await dormir(espera); espera *= 2; continue;
    }
    if (r.ok) {
      const j = await r.json();
      return {
        texto: j.choices[0].message.content || "",
        fin: j.choices[0].finish_reason,
        modelo_api: j.model,
        tokens: j.usage,
      };
    }
    if (r.status === 429 || r.status >= 500) { await dormir(espera); espera *= 2; continue; }
    const err = await r.json().catch(() => ({}));
    throw new Error((err.error && err.error.message) || `HTTP ${r.status}`);
  }
  throw new Error("La API no respondió después de varios intentos.");
}

function mensajesParaApi(conv) {
  const out = [];
  if (conv.sistema) out.push({ role: "system", content: conv.sistema });
  for (const m of conv.mensajes) {
    if (m.rol === "user" && m.imagen) {
      out.push({ role: "user", content: [
        { type: "text", text: m.texto },
        { type: "image_url", image_url: { url: m.imagen } },
      ] });
    } else {
      out.push({ role: m.rol, content: m.texto });
    }
  }
  return out;
}

// ---------- conversaciones ----------
function nuevaConversacion({ estrategia = null, modelo = ajustes.modelo, fuente = "en vivo" } = {}) {
  const conv = {
    id: crypto.randomUUID(),
    titulo: estrategia ? `${estrategia.id} · ${estrategia.nombre}` : "Nuevo chat",
    estrategia: estrategia ? estrategia.id : null,
    rep: null,
    modelo,
    temperatura: ajustes.temperatura,
    sistema: ajustes.sistema,
    fecha: new Date().toISOString(),
    fuente,
    mensajes: [],
  };
  conversaciones.unshift(conv);
  return conv;
}
function turnosUsuario(conv) { return conv.mensajes.filter((m) => m.rol === "user").length; }
function guionDe(conv) { return guiones.find((g) => g.id === conv.estrategia); }

function aJsonl(conv) {
  const turnos = [];
  let n = 0;
  for (let i = 0; i < conv.mensajes.length; i++) {
    const m = conv.mensajes[i];
    if (m.rol !== "user") continue;
    n++;
    const resp = conv.mensajes[i + 1] && conv.mensajes[i + 1].rol === "assistant" ? conv.mensajes[i + 1] : null;
    turnos.push({
      turno: n,
      usuario: m.texto,
      imagen: m.imagenNombre || null,
      modelo: resp ? resp.texto : null,
      finish_reason: resp ? resp.fin || null : null,
      modelo_api: resp ? resp.modelo_api || null : null,
      tokens: resp ? resp.tokens || null : null,
    });
  }
  return JSON.stringify({
    id: conv.id, modelo: conv.modelo, anio: anioDe(conv.modelo), estrategia: conv.estrategia,
    rep: conv.rep, temperatura: conv.temperatura, sistema: conv.sistema || null,
    fecha: conv.fecha, fuente: conv.fuente, turnos,
  });
}

// ---------- render ----------
function render() {
  const chat = $("chat");
  chat.innerHTML = "";
  const conv = actual;
  const modelo = conv ? conv.modelo : ajustes.modelo;
  $("modelLabel").textContent = modelo;
  const anio = anioDe(modelo);
  $("modelYear").textContent = anio ? `· ${anio}` : "";
  $("input").placeholder = `Enviar un mensaje a ${modelo}`;

  if (!conv || conv.mensajes.length === 0) {
    chat.innerHTML = `<div class="empty"><h1>¿En qué puedo ayudarte?</h1><p class="empty-sub">${
      conv && conv.estrategia ? "El primer turno del guion ya está en el cuadro de texto." : "Elegí un guion a la izquierda o escribí libremente."
    }</p></div>`;
  } else {
    let n = conv.turnoInicial || 0;
    for (const m of conv.mensajes) {
      const div = document.createElement("div");
      if (m.rol === "user") {
        n++;
        div.className = "msg user";
        div.innerHTML = `<div class="user-col">${conv.estrategia ? `<div class="turn-tag">${conv.estrategia} · turno ${n}</div>` : ""}<div class="bubble">${
          m.imagen ? `<img src="${m.imagen}" alt="">` : ""}${escapar(m.texto)}</div></div>`;
      } else {
        div.className = "msg bot" + (m.error ? " err" : "");
        div.innerHTML = `<div class="content">${m.pensando ? '<div class="typing"><span></span></div>' : markdown(m.texto)}</div>`;
      }
      chat.appendChild(div);
    }
  }
  if (window.renderMathInElement) {
    renderMathInElement(chat, {
      delimiters: [{ left: "\\[", right: "\\]", display: true }, { left: "\\(", right: "\\)", display: false }],
      throwOnError: false,
    });
  }
  chat.scrollTop = chat.scrollHeight;

  const g = conv && guionDe(conv);
  const chip = $("guionChip");
  if (g) {
    const hechos = turnosUsuario(conv);
    chip.hidden = false;
    chip.textContent = conv.turnoInicial != null
      ? `${g.id} · ${g.nombre} · turno ${conv.turnoInicial + 1} de ${g.turnos.length}`
      : `${g.id} · ${g.nombre} · ${Math.min(hechos + 1, g.turnos.length)}/${g.turnos.length}` + (hechos >= g.turnos.length ? " · completo" : "");
    $("btnAuto").hidden = hechos >= g.turnos.length || conv.fuente !== "en vivo";
  } else {
    chip.hidden = true;
    $("btnAuto").hidden = true;
  }
  renderHistorial();
}

function renderHistorial() {
  const h = $("historial");
  h.innerHTML = "";
  for (const c of conversaciones.slice(0, 60)) {
    const d = document.createElement("div");
    d.className = "side-item" + (c === actual ? " active" : "");
    const extra = c.fuente !== "en vivo" ? `<small>${escapar(c.modelo)}</small>` : "";
    d.innerHTML = `${escapar(c.titulo)}${c.rep ? ` · r${String(c.rep).padStart(2, "0")}` : ""}${extra}`;
    d.onclick = () => { actual = c; prepararSiguienteTurno(); render(); };
    h.appendChild(d);
  }
}

function prepararSiguienteTurno() {
  const g = actual && guionDe(actual);
  const inp = $("input");
  if (g && actual.fuente === "en vivo") {
    const n = turnosUsuario(actual);
    inp.value = n < g.turnos.length ? g.turnos[n] : "";
  } else {
    inp.value = "";
  }
  autoAltura();
}
function autoAltura() {
  const t = $("input");
  t.style.height = "auto";
  t.style.height = Math.min(t.scrollHeight, 220) + "px";
}

// ---------- enviar ----------
async function enviar(texto) {
  if (ocupado) return;
  if (!apiKey) { abrirKey(); return; }
  texto = (texto || "").trim();
  if (!texto && !imagenPendiente) return;
  if (!actual) actual = nuevaConversacion();
  if (actual.fuente !== "en vivo") actual = nuevaConversacion();
  if (actual.titulo === "Nuevo chat" && texto) actual.titulo = texto.slice(0, 40);

  const msg = { rol: "user", texto };
  if (imagenPendiente) { msg.imagen = imagenPendiente.dataUrl; msg.imagenNombre = imagenPendiente.nombre; }
  actual.mensajes.push(msg);
  limpiarImagen();
  const placeholder = { rol: "assistant", texto: "", pensando: true };
  actual.mensajes.push(placeholder);
  $("input").value = ""; autoAltura();
  ocupado = true; $("btnEnviar").disabled = true;
  render();

  const conv = actual;
  try {
    const historial = mensajesParaApi({ ...conv, mensajes: conv.mensajes.slice(0, -1) });
    const r = await llamarOpenAI(historial, { modelo: conv.modelo, temperatura: conv.temperatura });
    Object.assign(placeholder, { texto: r.texto, fin: r.fin, modelo_api: r.modelo_api, tokens: r.tokens, pensando: false });
  } catch (e) {
    Object.assign(placeholder, { texto: `Error: ${e.message}`, error: true, pensando: false });
  }
  ocupado = false; $("btnEnviar").disabled = false;
  if (conv === actual) { prepararSiguienteTurno(); render(); }
}

async function enviarRestantes() {
  const g = actual && guionDe(actual);
  if (!g) return;
  while (turnosUsuario(actual) < g.turnos.length) {
    await enviar(g.turnos[turnosUsuario(actual)]);
    const ultimo = actual.mensajes[actual.mensajes.length - 1];
    if (ultimo && ultimo.error) break;
  }
}

// ---------- imagen ----------
function limpiarImagen() {
  imagenPendiente = null;
  $("attachPreview").hidden = true;
  $("attachPreview").innerHTML = "";
}
function cargarImagen(file) {
  const fr = new FileReader();
  fr.onload = () => {
    imagenPendiente = { dataUrl: fr.result, nombre: file.name };
    const p = $("attachPreview");
    p.hidden = false;
    p.innerHTML = `<img src="${fr.result}" alt=""><span>${escapar(file.name)}</span><button type="button" title="Quitar">✕</button>`;
    p.querySelector("button").onclick = limpiarImagen;
    if (!$("input").value) $("input").value = "¿Qué hay en esta imagen? Respondé con una palabra.";
  };
  fr.readAsDataURL(file);
}

// ---------- API key ----------
function abrirKey() { $("keyErr").textContent = ""; $("inpKey").value = ""; $("dlgKey").showModal(); }
async function validarKey(k) {
  const r = await fetch(`${API}/models/${encodeURIComponent(ajustes.modelo)}`, { headers: { Authorization: `Bearer ${k}` } });
  if (!r.ok) {
    const e = await r.json().catch(() => ({}));
    throw new Error((e.error && e.error.message) || `HTTP ${r.status}`);
  }
}
$("formKey").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const k = $("inpKey").value.trim();
  if (!k) return;
  $("btnKeyOk").disabled = true; $("keyErr").textContent = "Verificando…";
  try {
    await validarKey(k);
    apiKey = k;
    $("inpKey").value = "";
    $("keyState").textContent = `API key cargada · ${ajustes.modelo} disponible`;
    $("keyState").classList.add("ok");
    $("dlgKey").close();
  } catch (e) {
    $("keyErr").textContent = `No funcionó: ${e.message}`;
  }
  $("btnKeyOk").disabled = false;
});
$("btnKeyLuego").onclick = () => $("dlgKey").close();

// ---------- lote ----------
function abrirLote() {
  const c = $("loteChecks");
  c.innerHTML = guiones.map((g) => `<label><input type="checkbox" value="${g.id}" checked> ${g.id} · ${escapar(g.nombre)}</label>`).join("");
  $("loteErr").textContent = "";
  $("dlgLote").showModal();
}
async function correrLote() {
  if (!apiKey) { $("dlgLote").close(); abrirKey(); return; }
  const n = +$("loteN").value, temp = +$("loteT").value, par = +$("loteP").value;
  const modelo = $("loteModelo").value.trim() || "gpt-4o-mini";
  const ids = [...$("loteChecks").querySelectorAll("input:checked")].map((i) => i.value);
  if (!ids.length) return;
  const trabajos = [];
  for (const id of ids) for (let r = 1; r <= n; r++) trabajos.push({ g: guiones.find((x) => x.id === id), rep: r });
  const totalTurnos = trabajos.reduce((s, t) => s + t.g.turnos.length, 0);
  let hechos = 0, errores = 0;
  const resultados = [];
  loteDetener = false;
  $("loteProg").hidden = false; $("btnLoteGo").disabled = true; $("btnLoteParar").hidden = false;
  const actualizar = () => {
    $("loteBar").style.width = `${(100 * hechos) / totalTurnos}%`;
    $("loteTxt").textContent = `${hechos}/${totalTurnos} turnos · ${resultados.length}/${trabajos.length} conversaciones${errores ? ` · ${errores} con error` : ""}`;
  };
  actualizar();

  const cola = trabajos.slice();
  async function trabajador() {
    while (cola.length && !loteDetener) {
      const { g, rep } = cola.shift();
      const conv = {
        id: crypto.randomUUID(), titulo: `${g.id} · ${g.nombre}`, estrategia: g.id, rep,
        modelo, temperatura: temp, sistema: "", fecha: new Date().toISOString(), fuente: "lote", mensajes: [],
      };
      for (const t of g.turnos) {
        if (loteDetener) break;
        conv.mensajes.push({ rol: "user", texto: t });
        try {
          const r = await llamarOpenAI(mensajesParaApi(conv), { modelo, temperatura: temp });
          conv.mensajes.push({ rol: "assistant", texto: r.texto, fin: r.fin, modelo_api: r.modelo_api, tokens: r.tokens });
        } catch (e) {
          conv.mensajes.push({ rol: "assistant", texto: `Error: ${e.message}`, error: true });
          errores++;
          break;
        }
        hechos++; actualizar();
      }
      resultados.push(conv);
      actualizar();
    }
  }
  await Promise.all(Array.from({ length: Math.max(1, par) }, trabajador));

  resultados.sort((a, b) => (a.estrategia + String(a.rep).padStart(3, "0")).localeCompare(b.estrategia + String(b.rep).padStart(3, "0")));
  for (const c of resultados.slice().reverse()) conversaciones.unshift(c);
  descargar(`lote_${modelo}_${marcaTiempo()}.jsonl`, resultados.map(aJsonl).join("\n") + "\n");
  $("btnLoteGo").disabled = false; $("btnLoteParar").hidden = true;
  $("loteTxt").textContent += loteDetener ? " · detenido, se descargó lo hecho" : " · listo, JSONL descargado";
  renderHistorial();
}

// ---------- prueba de visión (ataque adversarial) ----------
// la lista de imágenes a probar se lee de ataque_adversarial/prueba.json en cada clic,
// así se puede cambiar sin recargar la página (y sin volver a pegar la key)
async function imagenesAProbar() {
  const r = await fetch("../ataque_adversarial/prueba.json", { cache: "no-store" });
  const j = await r.json();
  return j.imagenes.map((f) => `../ataque_adversarial/${f}`);
}
const PREGUNTA_IMAGEN = "¿Qué hay en esta imagen? Respondé con una palabra.";

async function aDataUrl(ruta) {
  const b = await (await fetch(ruta, { cache: "no-store" })).blob();
  return await new Promise((ok) => { const fr = new FileReader(); fr.onload = () => ok(fr.result); fr.readAsDataURL(b); });
}
async function probarImagenes() {
  if (!apiKey) { abrirKey(); return; }
  if (ocupado) return;
  ocupado = true;
  const resultados = [];
  for (const ruta of await imagenesAProbar()) {
    const nombre = ruta.split("/").pop().replace(".png", "");
    const conv = {
      id: crypto.randomUUID(), titulo: `Imagen · ${nombre}`, estrategia: null, rep: 1,
      modelo: ajustes.modelo, temperatura: 0, sistema: "", fecha: new Date().toISOString(), fuente: "visión", mensajes: [],
    };
    conv.mensajes.push({ rol: "user", texto: PREGUNTA_IMAGEN, imagen: await aDataUrl(ruta), imagenNombre: ruta });
    conv.mensajes.push({ rol: "assistant", texto: "", pensando: true });
    conversaciones.unshift(conv); actual = conv; render();
    try {
      const r = await llamarOpenAI(mensajesParaApi({ ...conv, mensajes: conv.mensajes.slice(0, 1) }), { modelo: conv.modelo, temperatura: 0 });
      conv.mensajes[1] = { rol: "assistant", texto: r.texto, fin: r.fin, modelo_api: r.modelo_api, tokens: r.tokens };
    } catch (e) {
      conv.mensajes[1] = { rol: "assistant", texto: `Error: ${e.message}`, error: true };
    }
    render();
    resultados.push(conv);
  }
  ocupado = false;
  descargar(`vision_${ajustes.modelo}_${marcaTiempo()}.jsonl`, resultados.map(aJsonl).join("\n") + "\n");
}

// ---------- reproducir ----------
function cargarJsonl(texto, nombreArchivo) {
  const cargadas = [];
  for (const linea of texto.split("\n")) {
    if (!linea.trim()) continue;
    let o;
    try { o = JSON.parse(linea); } catch { continue; }
    const g = guiones.find((x) => x.id === o.estrategia);
    const conv = {
      id: o.id || crypto.randomUUID(),
      titulo: g ? `${g.id} · ${g.nombre}` : (o.turnos && o.turnos[0] && o.turnos[0].imagen ? `Imagen · ${o.turnos[0].imagen.split("/").pop().replace(".png", "")}` : (o.estrategia || "Conversación")),
      estrategia: o.estrategia || null, rep: o.rep || null,
      modelo: o.modelo || "modelo", temperatura: o.temperatura, sistema: o.sistema || "",
      fecha: o.fecha || "", fuente: "reproducida", mensajes: [],
    };
    for (const t of o.turnos || []) {
      conv.mensajes.push({ rol: "user", texto: t.usuario || "", imagen: t.imagen && t.imagen.includes("/") ? t.imagen : null });
      if (t.modelo != null) conv.mensajes.push({ rol: "assistant", texto: t.modelo });
    }
    cargadas.push(conv);
  }
  $("reproInfo").textContent = `${cargadas.length} conversaciones de ${nombreArchivo}. Hacé clic en una para verla con el formato del simulador.`;
  const lista = $("reproList");
  lista.innerHTML = "";
  for (const c of cargadas) {
    conversaciones.push(c);
    const d = document.createElement("div");
    d.className = "side-item";
    d.textContent = `${c.titulo}${c.rep ? ` · r${String(c.rep).padStart(2, "0")}` : ""} · ${c.modelo}`;
    d.onclick = () => { actual = c; $("dlgRepro").close(); prepararSiguienteTurno(); render(); };
    lista.appendChild(d);
  }
  $("dlgRepro").showModal();
  renderHistorial();
}

// ---------- eventos ----------
$("composer").addEventListener("submit", (e) => { e.preventDefault(); enviar($("input").value); });
$("input").addEventListener("input", autoAltura);
$("input").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); enviar($("input").value); }
});
$("btnAuto").onclick = enviarRestantes;
$("btnNuevo").onclick = () => { actual = nuevaConversacion(); prepararSiguienteTurno(); render(); };
$("btnAdjuntar").onclick = () => $("fileImg").click();
$("fileImg").onchange = (e) => { if (e.target.files[0]) cargarImagen(e.target.files[0]); e.target.value = ""; };
$("btnLote").onclick = abrirLote;
$("btnLoteGo").onclick = correrLote;
$("btnLoteParar").onclick = () => { loteDetener = true; };
$("btnLoteCerrar").onclick = () => $("dlgLote").close();
$("btnReproducir").onclick = () => $("fileJsonl").click();
$("btnVision").onclick = probarImagenes;
$("fileJsonl").onchange = async (e) => {
  const f = e.target.files[0];
  if (f) cargarJsonl(await f.text(), f.name);
  e.target.value = "";
};
$("btnExportar").onclick = () => {
  if (!actual || !actual.mensajes.length) return;
  const nombre = `${actual.modelo}_${actual.estrategia || "libre"}_${marcaTiempo()}.jsonl`;
  descargar(nombre, aJsonl(actual) + "\n");
};
$("btnAjustes").onclick = () => {
  $("ajModelo").value = ajustes.modelo; $("ajT").value = ajustes.temperatura; $("ajSystem").value = ajustes.sistema;
  $("dlgAjustes").showModal();
};
$("formAjustes").addEventListener("submit", () => {
  ajustes.modelo = $("ajModelo").value.trim() || "gpt-4o-mini";
  ajustes.temperatura = +$("ajT").value;
  ajustes.sistema = $("ajSystem").value.trim();
  if (actual && actual.fuente === "en vivo" && actual.mensajes.length === 0) {
    actual.modelo = ajustes.modelo; actual.temperatura = ajustes.temperatura; actual.sistema = ajustes.sistema;
  }
  render();
});
$("btnCambiarKey").onclick = () => { $("dlgAjustes").close(); abrirKey(); };
$("modelPill").onclick = () => $("btnAjustes").click();

// ---------- inicio ----------
(async function iniciar() {
  try {
    const r = await fetch("../guiones/estrategias.json", { cache: "no-store" });
    guiones = (await r.json()).estrategias;
  } catch {
    guiones = [];
  }
  const lista = $("listaGuiones");
  for (const g of guiones) {
    const d = document.createElement("div");
    d.className = "side-item";
    d.textContent = `${g.id} · ${g.nombre}`;
    d.title = g.idea;
    d.onclick = () => { actual = nuevaConversacion({ estrategia: g }); prepararSiguienteTurno(); render(); };
    lista.appendChild(d);
  }
  const q = new URLSearchParams(location.search);
  if (q.get("captura")) {
    document.body.classList.add("captura");
    const texto = await (await fetch(q.get("captura"), { cache: "no-store" })).text();
    const lineas = texto.split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));
    let o = q.has("n") ? lineas[+q.get("n")] : lineas.find((x) => x.estrategia === q.get("e") && String(x.rep) === q.get("r"));
    if (o) {
      cargarJsonl(JSON.stringify(o), "captura");
      $("dlgRepro").close();
      actual = conversaciones[conversaciones.length - 1];
      // &turno=N: sólo ese turno (la pregunta y la respuesta), para capturas por turno
      if (q.has("turno")) {
        const k = +q.get("turno");
        const usuarios = actual.mensajes.map((m, i) => (m.rol === "user" ? i : -1)).filter((i) => i >= 0);
        const ini = usuarios[k - 1], fin = usuarios[k] ?? actual.mensajes.length;
        actual.mensajes = actual.mensajes.slice(ini, fin);
        actual.turnoInicial = k - 1;
      }
    }
    render();
    document.body.dataset.listo = "1";
    return;
  }
  render();
  abrirKey();
})();
