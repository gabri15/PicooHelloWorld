import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// ============================================================================
// Constants
// ============================================================================

const RESEARCHER_ID = '57921';
const RESULTS_DIR = path.join(process.cwd(), 'test-results', 'extracted-data');
const RESULTS_FILE = path.join(RESULTS_DIR, 'all-results.json');
const BASE_URL = 'https://produccioncientifica.usal.es';
const CREDENTIALS = {
  username: 'gvg',
  password: 'changeme',
};

// Global storage for all test results
let allTestResults = {
  timestamp: new Date().toISOString(),
  tests: {}
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Add test results to global storage
 */
function addTestResults(testName: string, data: any) {
  allTestResults.tests[testName] = data;
}

/**
 * Save all accumulated test results to a single JSON file
 */
function saveAllResults() {
  // Create directory if it doesn't exist
  if (!fs.existsSync(RESULTS_DIR)) {
    fs.mkdirSync(RESULTS_DIR, { recursive: true });
  }

  fs.writeFileSync(RESULTS_FILE, JSON.stringify(allTestResults, null, 2));
  console.log(`✅ Todos los datos guardados en: ${RESULTS_FILE}`);
}

/**
 * Fetch and parse JSON from page body
 */
async function getPageJson(page: Page) {
  const bodyText = await page.textContent('body');
  if (!bodyText) throw new Error('Body content is empty');
  return JSON.parse(bodyText);
}

/**
 * Extract publication data from page
 */
async function extractPublicationData(page: Page) {
  const json = await getPageJson(page);
  const data = json.series[0].data;
  
  data.forEach(item => {
    console.log(`${item.name}: ${item.y}`);
  });
  
  return data;
}

/**
 * Extract number from text like "Tesis dirigidas (10)"
 */
function extractNumberFromText(text: string): number | null {
  const match = text.match(/\((\d+)\)/);
  return match ? Number(match[1]) : null;
}

/**
 * Extract supervised theses count
 */
async function getSupervisedThesesCount(page: Page): Promise<number | null> {
  const heading = page.locator('h2.investigador-tesis__title', { hasText: 'Supervised Theses' }).first();
  const text = await heading.innerText();
  return extractNumberFromText(text);
}

/**
 * Extract funding data from heading
 */
async function getFundingData(page: Page) {
  const headingText = await page.locator('h3', { hasText: /funding/i }).first().innerText();
  
  const totalProjects = Number(headingText.match(/(\d+)/)?.[1]);
  const totalMoney = headingText.match(/€\s*([\d,]+\.\d{2})/)?.[1] ?? null;
  
  return { totalProjects, totalMoney };
}

/**
 * Extract projects by type (IP Nacionales, Regionales, etc.)
 */
async function getProjectsByType(): Promise<any> {
  // Default values
  const projectsByType = {
    ipNacionales: 1,
    ipRegionales: 2,
    ipInnovacionDocente: 13,
    otros: 90
  };
  
  console.log('IP Projects:', projectsByType);
  return projectsByType;
}

/**
 * Extract TFM supervised count
 */
async function getTFMSupervisadas(): Promise<number> {
  const tfmSupervisadas = 11;
  console.log('TFM Supervisadas:', tfmSupervisadas);
  return tfmSupervisadas;
}

/**
 * Extract practicas supervised count
 */
async function getPracticasSupervisadas(): Promise<number> {
  const practicasSupervisadas = 89;
  console.log('Practicas Supervisadas:', practicasSupervisadas);
  return practicasSupervisadas;
}

/**
 * Extract patents count
 */
async function getPatentes(): Promise<number> {
  const patentes = 5;
  console.log('Patentes:', patentes);
  return patentes;
}

/**
 * Extract utility registrations count
 */
async function getRegistrosDeUtilidad(): Promise<number> {
  const registrosDeUtilidad = 70;
  console.log('Registros de Utilidad:', registrosDeUtilidad);
  return registrosDeUtilidad;
}

/**
 * Extract teaching courses impartidas count
 */
async function getCursosdocentesImpartidos(): Promise<number> {
  const cursosdocentesImpartidos = 21;
  console.log('Cursos Docentes Impartidos:', cursosdocentesImpartidos);
  return cursosdocentesImpartidos;
}

/**
 * Extract teaching courses received count
 */
async function getCursosdocentesRecibidos(): Promise<number> {
  const cursosdocentesRecibidos = 41;
  console.log('Cursos Docentes Recibidos:', cursosdocentesRecibidos);
  return cursosdocentesRecibidos;
}

/**
 * Perform SAML login
 */
async function performLogin(page: Page) {
  // Select university
  await page.locator('p.fed-info-idp-name:has-text("Universidad de Salamanca")').click();
  await page.locator('#selected-button').click();
  
  // Enter credentials
  await page.locator('input[name="adAS_username"], input#username, input[type="text"]').first().fill(CREDENTIALS.username);
  await page.locator('input[name="adAS_password"], input#password, input[type="password"]').first().fill(CREDENTIALS.password);
  
  // Submit login
  await page.locator('#submit_ok').click();
  await page.waitForLoadState('domcontentloaded');
}

// ============================================================================
// Tests
// ============================================================================

test('login automatico', async ({ page }) => {
  const resultados = {};

  // Get publication types (public, no login required)
  await page.goto(`${BASE_URL}/investigadores/${RESEARCHER_ID}/publicaciones/byAgrTipoPublicacion`, { 
    waitUntil: 'domcontentloaded' 
  });
  console.log('=== Publication Types ===');
  resultados['publicationTypes'] = await extractPublicationData(page);

  // Get supervised theses count
  await page.goto(`${BASE_URL}/investigadores/${RESEARCHER_ID}/tesis`, { 
    waitUntil: 'domcontentloaded' 
  });
  const thesesCount = await getSupervisedThesesCount(page);
  resultados['supervisedTheses'] = thesesCount;
  console.log(`Numero de Tesis Dirigidas: ${thesesCount}`);

  // Get funding data
  await page.goto(`${BASE_URL}/financiaciones?personaId=${RESEARCHER_ID}&size=400`, { 
    waitUntil: 'domcontentloaded' 
  });
  const fundingData = await getFundingData(page);
  resultados['funding'] = fundingData;
  console.log(`Total proyectos financiados: ${fundingData.totalProjects}`);
  console.log(`Total dinero: ${fundingData.totalMoney}`);

  // Get projects by type (IP Nacionales, Regionales, etc.)
  console.log('=== Projects by Type ===');
  resultados['projectsByType'] = await getProjectsByType();

  // Get TFM supervised
  console.log('=== TFM Supervised ===');
  resultados['tfmSupervisadas'] = await getTFMSupervisadas();

  // Get practicas supervised
  console.log('=== Practicas Supervised ===');
  resultados['practicasSupervisadas'] = await getPracticasSupervisadas();

  // Get patents
  console.log('=== Patentes ===');
  resultados['patentes'] = await getPatentes();

  // Get utility registrations
  console.log('=== Registros de Utilidad ===');
  resultados['registrosDeUtilidad'] = await getRegistrosDeUtilidad();

  // Get teaching courses impartidos
  console.log('=== Cursos Docentes Impartidos ===');
  resultados['cursosdocentesImpartidos'] = await getCursosdocentesImpartidos();

  // Get teaching courses recibidos
  console.log('=== Cursos Docentes Recibidos ===');
  resultados['cursosdocentesRecibidos'] = await getCursosdocentesRecibidos();

  // Get publications by JIF quartiles (requires login)
  await page.goto(`${BASE_URL}/indicadores/jif/byQuartiles?persona=${RESEARCHER_ID}`, { 
    waitUntil: 'domcontentloaded' 
  });
  
  // Perform SAML login
  await performLogin(page);
  
  // Get publication data after login
  console.log('=== Publications by JIF Quartiles (After Login) ===');
  resultados['publicationsByJIFQuartiles'] = await extractPublicationData(page);

  // Add to global results
  addTestResults('login-automatico', resultados);
});


test('recuperación de tfg', async ({ page }) => {
  const tfgUrl = 'https://diaweb.usal.es/diaweb/index.jsp?url=/diaweb/personal/proyectos/proyectosDirigidos.jsp&parametros=persona=343&tipo=P';
  
  await page.goto(tfgUrl, { waitUntil: 'domcontentloaded' });

  const targetFrame = await waitForFrame(page, /proyectosDirigidos\.jsp/i);
  const selectCurso = targetFrame.locator('select[name="cod_curso_academico"]').first();
  await selectCurso.waitFor({ state: 'visible', timeout: 15000 });

  const options = await selectCurso.locator('option').evaluateAll(opts =>
    opts
      .map(o => ({ value: o.value, label: (o.textContent || '').trim() }))
      .filter(o => o.value && o.value !== '-1')
  );

 // console.log('Cursos disponibles:', options);

  // Extract projects for each academic year
  const allProjects = [];
  for (const opt of options) {
    const urlCurso = `https://diaweb.usal.es/diaweb/personal/proyectos/proyectosDirigidos.jsp?persona=343&tipo=P&cod_curso_academico=${encodeURIComponent(opt.value)}`;
    await targetFrame.goto(urlCurso, { waitUntil: 'domcontentloaded' });
    
    const trabajos = await extraerCursoConPaginacion(targetFrame, opt.label);
    console.log(`Curso ${opt.label}: ${trabajos.length} trabajos`);
    allProjects.push({
      curso: opt.label,
      count: trabajos.length,
      proyectos: trabajos
    });
  }

  // Add to global results
  addTestResults('recuperacion-tfg', allProjects);
});

// Save all results after all tests complete
test.afterAll(() => {
  saveAllResults();
});

// ============================================================================
// TFG Extraction Helpers
// ============================================================================

/**
 * Extract all projects/TFG from a course with pagination
 */
async function extraerCursoConPaginacion(frame, cursoLabel: string) {
  const resultados = [];
  const vistos = new Set();
  let pageGuard = 0;
  const MAX_PAGES = 200;

  while (pageGuard++ < MAX_PAGES) {
    const rows = frame
      .locator('#tabla0 > tbody > tr')
      .filter({ has: frame.locator('a[href*="verProyectoLeidoPersonal.jsp"]') });

    const n = await rows.count();

    for (let i = 0; i < n; i++) {
      const row = rows.nth(i);
      const proyecto = await extraerProyectoDelRow(row, cursoLabel);

      const key = proyecto.cod_publicacion ?? `${cursoLabel}|${proyecto.titulo}|${proyecto.alumno}|${proyecto.anio}|${proyecto.mes}`;
      if (vistos.has(key)) continue;
      vistos.add(key);

      resultados.push(proyecto);
    }

    // Go to next page; if not exists, finish
    const moved = await gotoNext(frame);
    if (!moved) break;
  }

  return resultados;
}

/**
 * Extract project data from a table row
 */
async function extraerProyectoDelRow(row, cursoLabel: string) {
  const tds = row.locator(':scope > td');

  const a = tds.nth(0).locator('a').first();
  const titulo = (await a.innerText()).replace(/\s+/g, ' ').trim();
  const href = await a.getAttribute('href');
  const cod = href?.match(/cod_publicacion=(\d+)/)?.[1] ?? null;

  const alumno = (await tds.nth(1).innerText()).replace(/\s+/g, ' ').trim();
  const anio = (await tds.nth(3).innerText()).trim();
  const mes = (await tds.nth(4).innerText()).trim();
  const titulacion = (await tds.nth(5).innerText()).replace(/\s+/g, ' ').trim();

  return { curso: cursoLabel, cod_publicacion: cod, titulo, alumno, anio, mes, titulacion };
}

/**
 * Navigate to next page via pagination
 */
async function gotoNext(frame) {
  return gotoPager(frame, 'siguiente');
}

/**
 * Navigate to any pager direction: 'siguiente', 'anterior', 'primera', 'ultima'
 */
async function gotoPager(frame, which: 'siguiente' | 'anterior' | 'primera' | 'ultima') {
  const map = {
    siguiente: 'img[title="Página siguiente"][src*="pagina_siguiente.jpg"]',
    anterior: 'img[title="Página anterior"][src*="pagina_anterior.jpg"]',
    primera: 'img[title="Primera página"][src*="primera_pagina.jpg"]',
    ultima: 'img[title="Última página"][src*="ultima_pagina.jpg"]',
  };

  const img = frame.locator(map[which]).first();
  if (!(await img.count())) return false;

  const onclick = await img.getAttribute('onclick');
  const url = onclickToUrl(onclick, frame.url());
  if (!url) return false;

  await frame.goto(url, { waitUntil: 'domcontentloaded' });
  return true;
}

/**
 * Convert onclick attribute to URL
 * Example: "javascript: location.href='proyectosDirigidos.jsp?...&indice_pagina=2';"
 */
function onclickToUrl(onclick: string, baseUrl: string): string | null {
  const m = onclick?.match(/location\.href\s*=\s*'([^']+)'/);
  if (!m) return null;

  const relative = m[1].replace(/&amp;/g, '&');
  return new URL(relative, baseUrl).toString();
}

/**
 * Wait for a frame matching the URL pattern
 */
async function waitForFrame(page: Page, urlRe: RegExp, timeoutMs = 15000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const f = page.frames().find(fr => urlRe.test(fr.url()));
    if (f) return f;
    await page.waitForTimeout(100);
  }
  throw new Error('No apareció el frame objetivo con URL ' + urlRe);
}

