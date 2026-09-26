/* Site Julia Monteiro — menu, aviso de cookies (Consent Mode v2),
   Google Ads (conversão "Contato") e botão flutuante de WhatsApp.

   Dados vêm do <body> (preenchidos pelo app.py):
   - data-ads-id / data-ads-label: IDs do Google Ads, VAZIOS fora do domínio
     de produção (localhost, previews e *.vercel.app não medem nada).
   - data-modo-consentimento: "avancado" ou "basico" (páginas de saúde).
   - data-pagina-saude: "1" quando o endereço revela um tema de saúde.
   - data-paginas-saude: caminhos de saúde (para o referenciador genérico).
*/
(function () {
  "use strict";

  var body = document.body;
  var d = body.dataset;
  var CHAVE = "consentimento";

  /* ---------------- menu mobile ---------------- */
  var navToggle = document.getElementById("navToggle");
  var mainNav = document.getElementById("mainNav");

  function fecharMenu() {
    if (!navToggle || !mainNav) return;
    mainNav.classList.remove("open");
    navToggle.classList.remove("open");
    navToggle.setAttribute("aria-expanded", "false");
    navToggle.setAttribute("aria-label", "Abrir menu");
  }

  if (navToggle && mainNav) {
    navToggle.addEventListener("click", function () {
      var aberto = mainNav.classList.toggle("open");
      navToggle.classList.toggle("open", aberto);
      navToggle.setAttribute("aria-expanded", String(aberto));
      navToggle.setAttribute("aria-label", aberto ? "Fechar menu" : "Abrir menu");
    });
    mainNav.addEventListener("click", function (e) {
      if (e.target.closest("a")) fecharMenu();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") fecharMenu();
    });
  }

  /* ---------------- consentimento ---------------- */
  var escolhaNaPagina = null;

  function escolhaSalva() {
    try {
      var v = window.localStorage.getItem(CHAVE);
      return v === "granted" || v === "denied" ? v : null;
    } catch (e) {
      return null; // sem acesso ao armazenamento: vale "denied"
    }
  }

  // "granted" só com aceite explícito; qualquer falha = "denied"
  window.consentimentoAtual = function () {
    return (escolhaNaPagina || escolhaSalva()) === "granted" ? "granted" : "denied";
  };

  function salvarEscolha(valor) {
    escolhaNaPagina = valor;
    try {
      window.localStorage.setItem(CHAVE, valor);
    } catch (e) {
      /* o aviso volta na próxima visita */
    }
  }

  /* ---------------- Google Ads ---------------- */
  var saude = (d.paginasSaude || "").split(" ").filter(Boolean);
  var gtagConfigurado = false;
  var gtagInjetado = false;

  function ehCaminhoSaude(caminho) {
    return saude.some(function (p) {
      return caminho === p || caminho.indexOf(p + "/") === 0;
    });
  }

  function paginaAtualEhSaude() {
    return d.paginaSaude === "1" || ehCaminhoSaude(location.pathname);
  }

  // Só os identificadores de clique do anúncio seguem para o Google (o lance
  // usa o gclid). utm_term e afins podem conter o termo buscado: ficam fora.
  function parametrosDeClique() {
    var atual = new URLSearchParams(location.search);
    var manter = new URLSearchParams();
    ["gclid", "gbraid", "wbraid"].forEach(function (k) {
      if (atual.has(k)) manter.set(k, atual.get(k));
    });
    var qs = manter.toString();
    return qs ? "?" + qs : "";
  }

  // Endereço genérico das páginas de saúde: base + "/tema" + gclid/gbraid/wbraid
  function urlGenerica() {
    return d.baseUrl + "/tema" + parametrosDeClique();
  }

  function urlDaPagina() {
    return location.protocol + "//" + location.host + location.pathname + parametrosDeClique();
  }

  function referenciadorSeguro() {
    var ref = document.referrer;
    if (!ref) return "";
    try {
      var u = new URL(ref);
      var mesmoSite =
        u.hostname.replace(/^www\./, "") === location.hostname.replace(/^www\./, "");
      if (!mesmoSite) return u.protocol + "//" + u.host + "/";
      if (ehCaminhoSaude(u.pathname)) return d.baseUrl + "/tema";
      return u.protocol + "//" + u.host + u.pathname;
    } catch (e) {
      return "";
    }
  }

  function parametrosDaPagina() {
    var p = {
      allow_ad_personalization_signals: false,
      page_location: urlDaPagina(),
      page_referrer: referenciadorSeguro()
    };
    if (paginaAtualEhSaude()) {
      p.page_location = urlGenerica();
      p.page_title = "Tema";
    }
    return p;
  }

  function configurarGtag() {
    if (gtagConfigurado || typeof window.gtag !== "function" || !d.adsId) return;
    gtagConfigurado = true;
    window.gtag("js", new Date());
    window.gtag("config", d.adsId, parametrosDaPagina());
  }

  // Modo básico: o gtag.js só é injetado DEPOIS do aceite.
  function injetarGtagSeAceito() {
    if (gtagInjetado || !d.adsId) return;
    if (window.consentimentoAtual() !== "granted") return;
    gtagInjetado = true;
    configurarGtag();
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(d.adsId);
    document.head.appendChild(s);
  }

  if (d.adsId) {
    if (d.modoConsentimento === "basico") {
      injetarGtagSeAceito(); // só carrega se já houver aceite salvo
    } else {
      configurarGtag(); // modo avançado: o gtag.js já está no HTML
    }
  }

  // Conversão "Contato": um listener delegado cobre todos os botões
  // .js-whatsapp-cta (header, menu, hero, meio, contato e flutuante).
  window.trackWhatsAppConversion = function (origem) {
    if (typeof window.gtag !== "function" || !d.adsId || !d.adsLabel) return;
    if (d.modoConsentimento === "basico" && window.consentimentoAtual() !== "granted") return;
    var params = { send_to: d.adsId + "/" + d.adsLabel };
    if (paginaAtualEhSaude()) {
      params.page_location = urlGenerica();
      params.page_title = "Tema";
    }
    window.gtag("event", "conversion", params);
  };

  document.addEventListener("click", function (e) {
    var link = e.target.closest ? e.target.closest(".js-whatsapp-cta") : null;
    if (link) window.trackWhatsAppConversion(link.getAttribute("data-cta-origem") || "");
  });

  /* ---------------- aviso de cookies ---------------- */
  var aviso = document.getElementById("avisoCookies");
  var raiz = document.documentElement;

  function ajustarAlturaAviso() {
    if (aviso && !aviso.hidden) raiz.style.setProperty("--aviso-h", aviso.offsetHeight + "px");
  }

  function mostrarAviso() {
    if (!aviso) return;
    aviso.hidden = false;
    body.classList.add("aviso-aberto");
    ajustarAlturaAviso();
  }

  function esconderAviso() {
    if (!aviso) return;
    aviso.hidden = true;
    body.classList.remove("aviso-aberto");
    raiz.style.setProperty("--aviso-h", "0px");
  }

  function aplicarEscolha(valor) {
    salvarEscolha(valor);
    if (typeof window.gtag === "function" && d.adsId) {
      window.gtag("consent", "update", valor === "granted"
        ? { ad_storage: "granted", ad_user_data: "granted" }
        : { ad_storage: "denied", ad_user_data: "denied" });
    }
    if (valor === "granted" && d.modoConsentimento === "basico") injetarGtagSeAceito();
    esconderAviso();
  }

  if (aviso) {
    aviso.addEventListener("click", function (e) {
      var botao = e.target.closest("[data-consentimento]");
      if (botao) aplicarEscolha(botao.getAttribute("data-consentimento"));
    });
    if (!escolhaSalva()) mostrarAviso();
    window.addEventListener("resize", ajustarAlturaAviso);
  }

  document.addEventListener("click", function (e) {
    var pref = e.target.closest ? e.target.closest(".js-preferencias-cookies") : null;
    if (!pref || !aviso) return;
    e.preventDefault();
    mostrarAviso();
    var primeiro = aviso.querySelector("button");
    if (primeiro) primeiro.focus();
  });

  /* ---------------- botão flutuante ---------------- */
  // Some quando o CTA de contato ou o rodapé aparecem na tela.
  var flutuante = document.querySelector(".wa-float");
  if (flutuante && "IntersectionObserver" in window) {
    var alvos = document.querySelectorAll(".js-cta-final, .site-footer");
    var visiveis = [];
    var ioFlutuante = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (en) {
        var i = visiveis.indexOf(en.target);
        if (en.isIntersecting && i === -1) visiveis.push(en.target);
        if (!en.isIntersecting && i !== -1) visiveis.splice(i, 1);
      });
      var ocultar = visiveis.length > 0;
      flutuante.classList.toggle("wa-float--oculto", ocultar);
      if (ocultar) flutuante.setAttribute("tabindex", "-1");
      else flutuante.removeAttribute("tabindex");
    }, { threshold: 0.1 });
    alvos.forEach(function (el) { ioFlutuante.observe(el); });
  }

  /* ---------------- menu da home ---------------- */
  // Destaca o link do menu da seção visível (só na home).
  if (d.pagina === "home" && "IntersectionObserver" in window) {
    var linksSecao = document.querySelectorAll(".nav a[data-secao]");
    var ioMenu = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (en) {
        if (!en.isIntersecting) return;
        linksSecao.forEach(function (a) {
          a.classList.toggle("ativo", a.getAttribute("data-secao") === en.target.id);
        });
      });
    }, { rootMargin: "-45% 0px -45% 0px" });
    document.querySelectorAll("main section[id]").forEach(function (s) { ioMenu.observe(s); });
  }
})();
