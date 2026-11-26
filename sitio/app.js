"use strict";
/* Lee data/articulos.csv (generado por el notebook) y pinta tarjetas, resumen y tabla. */

const COP = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
let articulos = [];

/* Analizador CSV mínimo con soporte de comillas, comas y saltos de línea dentro de campos. */
function parsearCSV(texto) {
  texto = texto.replace(/^﻿/, "");
  const filas = []; let fila = [], campo = "", comillas = false;
  for (let i = 0; i < texto.length; i++) {
    const c = texto[i];
    if (comillas) {
      if (c === '"' && texto[i + 1] === '"') { campo += '"'; i++; }
      else if (c === '"') comillas = false;
      else campo += c;
    } else if (c === '"') comillas = true;
    else if (c === ",") { fila.push(campo); campo = ""; }
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && texto[i + 1] === "\n") i++;
      fila.push(campo); campo = "";
      if (fila.length > 1 || fila[0] !== "") filas.push(fila);
      fila = [];
    } else campo += c;
  }
  if (campo !== "" || fila.length) { fila.push(campo); filas.push(fila); }
  const [cab, ...datos] = filas;
  return datos.map(f => Object.fromEntries(cab.map((k, i) => [k, f[i] ?? ""])));
}

const num = v => Number(v);
const el = id => document.getElementById(id);
function esc(s) { const d = document.createElement("div"); d.textContent = s ?? ""; return d.innerHTML; }

function filtrados() {
  const q = el("buscar").value.trim().toLowerCase();
  let lista = articulos.filter(a => a.nombre.toLowerCase().includes(q));
  if (el("solo-descuento").checked) lista = lista.filter(a => a.descuento_total_cop > 0);
  const ord = el("orden").value;
  const claves = {
    "posicion": (a, b) => a.posicion - b.posicion,
    "precio-asc": (a, b) => a.precio_con_descuento - b.precio_con_descuento,
    "precio-desc": (a, b) => b.precio_con_descuento - a.precio_con_descuento,
    "descuento-desc": (a, b) => b.descuento_pct_sitio - a.descuento_pct_sitio,
  };
  return lista.sort(claves[ord]);
}

function tarjeta(a) {
  const con = a.descuento_total_cop > 0;
  return `<article class="articulo">
    <div class="foto"><span class="pos">#${a.posicion}</span>
      <img src="${esc(a.imagen)}" alt="${esc(a.nombre)}" loading="lazy" referrerpolicy="no-referrer"></div>
    <div class="cuerpo">
      <h3>${esc(a.nombre)}</h3>
      <div class="precio-previo">${con ? COP.format(a.precio_sin_descuento) : ""}</div>
      <div class="precio">${COP.format(a.precio_con_descuento)}</div>
      <div>${con ? `<span class="insignia">${a.descuento_pct_sitio}% OFF · ahorro ${COP.format(a.descuento_total_cop)}</span>`
                 : `<span class="insignia sin">Sin descuento</span>`}</div>
      <div class="meta">${esc(a.cuotas)}</div>
      <div class="meta">${esc(a.envio)}${a.vendedor ? " · Vende: " + esc(a.vendedor) : ""}</div>
      <a class="enlace" href="${esc(a.url)}" target="_blank" rel="noopener noreferrer">Ver publicación en MercadoLibre ↗</a>
    </div></article>`;
}

function pintar() {
  const lista = filtrados();
  el("rejilla").innerHTML = lista.map(tarjeta).join("");
  el("estado").textContent = lista.length ? `Mostrando ${lista.length} de ${articulos.length} artículos.` : "Ningún artículo coincide con los filtros.";
}

function pintarResumen() {
  const con = articulos.filter(a => a.descuento_total_cop > 0);
  const barato = articulos.reduce((m, a) => a.precio_con_descuento < m.precio_con_descuento ? a : m);
  const mayor = con.length ? con.reduce((m, a) => a.descuento_pct_sitio > m.descuento_pct_sitio ? a : m) : null;
  const prom = con.length ? con.reduce((s, a) => s + a.descuento_pct_sitio, 0) / con.length : 0;
  const datos = [
    [articulos.length, "artículos analizados"],
    [`${con.length} de ${articulos.length}`, "tienen precio con descuento"],
    [mayor ? `${mayor.descuento_pct_sitio}%` : "—", mayor ? `mayor descuento (#${mayor.posicion})` : "mayor descuento"],
    [`${prom.toFixed(1)}%`, "descuento promedio (solo los que tienen)"],
    [COP.format(barato.precio_con_descuento), `precio más bajo (#${barato.posicion})`],
  ];
  el("resumen").innerHTML = datos.map(([v, r]) => `<div class="dato"><span class="valor">${esc(String(v))}</span><span class="rotulo">${esc(r)}</span></div>`).join("");
}

function pintarTabla() {
  el("tabla").querySelector("tbody").innerHTML = [...articulos].sort((a, b) => a.posicion - b.posicion).map(a =>
    `<tr><td>${a.posicion}</td><td>${esc(a.nombre)}</td>
     <td class="num">${COP.format(a.precio_sin_descuento)}</td><td class="num">${COP.format(a.precio_con_descuento)}</td>
     <td class="num">${a.descuento_pct_sitio ? a.descuento_pct_sitio + "%" : "—"}</td><td>${esc(a.origen_datos)}</td></tr>`).join("");
}

async function iniciar() {
  try {
    const r = await fetch("data/articulos.csv", { cache: "no-store" });
    if (!r.ok) throw new Error("HTTP " + r.status);
    articulos = parsearCSV(await r.text()).map(a => ({
      ...a, posicion: num(a.posicion), precio_sin_descuento: num(a.precio_sin_descuento),
      precio_con_descuento: num(a.precio_con_descuento), descuento_total_cop: num(a.descuento_total_cop),
      descuento_pct_sitio: num(a.descuento_pct_sitio),
    }));
    el("fecha-captura").textContent = "Captura de datos: " + articulos[0].fecha_extraccion;
    pintarResumen(); pintarTabla(); pintar();
    ["buscar", "orden", "solo-descuento"].forEach(id => el(id).addEventListener("input", pintar));
  } catch (e) {
    el("estado").innerHTML = `<span class="error">No se pudo cargar data/articulos.csv (${esc(e.message)}). Si abres el archivo directamente, usa un servidor local: <code>python -m http.server</code>.</span>`;
  }
}
iniciar();
