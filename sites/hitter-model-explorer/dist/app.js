(() => {
  "use strict";

  const payload = window.UBM_EXPLORER_DATA;
  if (!payload || !Array.isArray(payload.players)) {
    document.body.innerHTML = '<p class="empty-state">The forecast data could not be loaded.</p>';
    return;
  }

  const players = payload.players;
  const state = {
    query: "",
    team: "all",
    stage: "all",
    gap: "all",
    sort: "overall_rank",
    ascending: true,
    page: 1,
    pageSize: 30,
    selectedId: players[0]?.player_id ?? null,
  };

  const els = {
    rows: document.getElementById("playerRows"),
    resultCount: document.getElementById("resultCount"),
    empty: document.getElementById("emptyState"),
    pageLabel: document.getElementById("pageLabel"),
    prev: document.getElementById("prevPage"),
    next: document.getElementById("nextPage"),
    detail: document.getElementById("detailPanel"),
    search: document.getElementById("searchInput"),
    team: document.getElementById("teamFilter"),
    stage: document.getElementById("stageFilter"),
    gap: document.getElementById("gapFilter"),
  };

  const stageLabel = value => ({
    current_mlb: "Current MLB",
    upper_minors: "Upper minors",
    lower_minors: "Lower minors",
    no_2025_record: "No 2025 record",
  })[value] || value || "Unknown";

  const fmt = (value, digits = 1) => value == null ? "—" : Number(value).toFixed(digits);
  const pct = value => value == null ? "—" : `${Math.round(Number(value) * 100)}%`;
  const signed = (value, digits = 2) => {
    if (value == null) return "—";
    const number = Number(value);
    return `${number > 0 ? "+" : ""}${number.toFixed(digits)}`;
  };
  const escapeHtml = value => String(value ?? "").replace(/[&<>'"]/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[char]);

  function matchesGap(player) {
    if (state.gap === "all") return true;
    if (state.gap === "flagged") return player.gap_count > 0;
    if (state.gap === "model") return player.flag_model_disagreement || player.flag_routing_sensitive;
    if (state.gap === "playingTime") return player.flag_opportunity_disagreement;
    if (state.gap === "contact") return player.flag_no_current_contact;
    if (state.gap === "prior") return player.flag_population_prior;
    return true;
  }

  function filteredPlayers() {
    const query = state.query.trim().toLocaleLowerCase();
    const result = players.filter(player => {
      const matchesSearch = !query
        || player.player_name.toLocaleLowerCase().includes(query)
        || String(player.player_id).includes(query);
      const matchesStage = state.stage === "all" || player.player_stage === state.stage;
      const matchesTeam = state.team === "all" || player.organization_name === state.team;
      return matchesSearch && matchesTeam && matchesStage && matchesGap(player);
    });
    return result.sort((a, b) => {
      const av = a[state.sort];
      const bv = b[state.sort];
      if (typeof av === "string") {
        return (state.ascending ? 1 : -1) * av.localeCompare(bv || "");
      }
      const left = av == null ? (state.ascending ? Infinity : -Infinity) : av;
      const right = bv == null ? (state.ascending ? Infinity : -Infinity) : bv;
      return (state.ascending ? 1 : -1) * (left - right);
    });
  }

  function renderTable() {
    const filtered = filteredPlayers();
    const pages = Math.max(1, Math.ceil(filtered.length / state.pageSize));
    state.page = Math.min(state.page, pages);
    const start = (state.page - 1) * state.pageSize;
    const visible = filtered.slice(start, start + state.pageSize);
    els.resultCount.textContent = `${filtered.length.toLocaleString()} hitters`;
    els.pageLabel.textContent = `Page ${state.page} of ${pages}`;
    els.prev.disabled = state.page <= 1;
    els.next.disabled = state.page >= pages;
    els.empty.hidden = filtered.length !== 0;
    els.rows.innerHTML = visible.map(player => {
      const warClass = player.prediction_selected_partial_war >= 0 ? "war-positive" : "war-negative";
      return `<tr data-id="${player.player_id}" class="${player.player_id === state.selectedId ? "selected" : ""}">
        <td class="number">${player.overall_rank}</td>
        <td><span class="player-cell"><span class="player-name">${escapeHtml(player.player_name)}</span><span class="player-id">${player.primary_position || "—"} · ${player.player_id}</span></span></td>
        <td><span class="stage-chip">${stageLabel(player.player_stage)}</span></td>
        <td class="number">${fmt(player.prediction_expected_mlb_pa, 0)}</td>
        <td class="number">${pct(player.prediction_mlb_active_probability)}</td>
        <td class="number">${signed(player.prediction_hitting_war_per_600)}</td>
        <td class="number ${warClass}">${signed(player.prediction_selected_partial_war)}</td>
        <td class="number"><span class="flag-chip ${player.gap_count ? "has-flags" : ""}">${player.gap_count}</span></td>
      </tr>`;
    }).join("");
    els.rows.querySelectorAll("tr").forEach(row => {
      row.addEventListener("click", () => selectPlayer(Number(row.dataset.id), true));
    });
  }

  function flagLabels(player) {
    const flags = [];
    if (player.flag_population_prior) flags.push("No 2025 batting line — population prior used");
    if (player.flag_no_current_contact) flags.push("No 2025 detailed-contact evidence; the frozen 2025 contact source contains MiLB only");
    if (player.flag_no_position_profile) flags.push("No usable 2025 position profile");
    if (player.flag_model_disagreement) flags.push("Batting models disagree more than 90% of players");
    if (player.flag_opportunity_disagreement) flags.push("Playing-time models disagree more than 90% of players");
    if (player.flag_wide_interval) flags.push("Forecast interval is among the widest 10%");
    if (player.flag_routing_sensitive) flags.push("Forecast is sensitive to the arrival-model routing choice");
    return flags;
  }

  function modelRead(player) {
    const pieces = [];
    if (player.flag_population_prior) {
      pieces.push("There was no 2025 batting record, so skill is not player-specific; value is a population rate scaled by expected playing time.");
    } else {
      pieces.push(`The batting ensemble projects ${signed(player.prediction_batting_replacement_war)} batting-plus-replacement WAR.`);
    }
    if (player.prediction_hitting_war_per_600 != null) {
      pieces.push(`At equal playing time, the conditional hitting model projects ${signed(player.prediction_hitting_war_per_600)} batting-plus-replacement WAR per 600 MLB PA.`);
    }
    if (player.prediction_expected_mlb_pa < 100) {
      pieces.push("Most of the uncertainty comes from whether he receives meaningful MLB playing time.");
    } else if (player.opportunity_spread >= payload.meta.thresholds.opportunity_spread) {
      pieces.push("The playing-time systems disagree substantially, so the final value is sensitive to opportunity.");
    }
    if (player.model_member_spread >= payload.meta.thresholds.model_member_spread) {
      pieces.push("The five batting models also disagree, which is a useful case to review rather than treat as one precise number.");
    }
    if (!player.flag_population_prior && player.gap_count === 0) {
      pieces.push("Evidence coverage and model agreement are comparatively strong for this forecast.");
    }
    return pieces.join(" ");
  }

  function componentRows(player) {
    const components = [
      ["Batting + repl.", player.prediction_batting_replacement_war],
      ["Position", player.prediction_position_war],
      ["Baserunning", player.prediction_baserunning_war],
      ["Catcher defense", player.prediction_catcher_defense_war],
      ["General defense", player.prediction_general_defense_war],
    ];
    const scale = Math.max(1, ...components.map(([, value]) => Math.abs(Number(value || 0))));
    return components.map(([label, value]) => {
      const width = Math.min(50, Math.abs(Number(value || 0)) / scale * 50);
      const className = value < 0 ? "negative" : "positive";
      return `<div class="bar-row"><span>${label}</span><div class="bar-track"><i class="${className}" style="width:${width}%"></i></div><span class="bar-value">${signed(value)}</span></div>`;
    }).join("");
  }

  function memberRows(player) {
    const members = [
      ["Direct LGBM", player.prediction_member__direct_lightgbm],
      ["3-part LGBM", player.prediction_member__three_part_lightgbm],
      ["2-part XGB", player.prediction_member__two_part_xgboost],
      ["2-part EBM", player.prediction_member__two_part_ebm],
      ["2-part Ridge", player.prediction_member__two_part_ridge],
    ];
    const min = Math.min(0, ...members.map(([, value]) => Number(value || 0)));
    const max = Math.max(0.01, ...members.map(([, value]) => Number(value || 0)));
    const range = max - min || 1;
    return members.map(([label, value]) => {
      const position = ((0 - min) / range) * 100;
      const width = Math.abs(Number(value || 0)) / range * 100;
      const style = value < 0
        ? `right:${100 - position}%;width:${width}%`
        : `left:${position}%;width:${width}%`;
      return `<div class="bar-row"><span>${label}</span><div class="bar-track"><i class="${value < 0 ? "negative" : "positive"}" style="${style}"></i></div><span class="bar-value">${signed(value)}</span></div>`;
    }).join("");
  }

  function historyCards(player) {
    return [0, 1, 2].map(lag => {
      const season = 2025 - lag;
      const key = name => player[`lag${lag}__${name}`];
      if (!key("season_available")) {
        return `<div class="season-card"><h4>${season}</h4><p class="fine-print">No record</p></div>`;
      }
      const contactText = key("contact_feature_available") ? fmt(key("contact_events"), 0) : "Not covered";
      return `<div class="season-card"><h4>${season} · ${escapeHtml(key("highest_level") || "—")}</h4><dl>
        <dt>PA</dt><dd>${fmt(key("plate_appearances"), 0)}</dd>
        <dt>Age</dt><dd>${fmt(key("age") ?? key("reported_age"), 1)}</dd>
        <dt>BB%</dt><dd>${pct(key("ubb_rate"))}</dd>
        <dt>K%</dt><dd>${pct(key("strikeout_rate"))}</dd>
        <dt>HR%</dt><dd>${pct(key("home_run_rate"))}</dd>
        <dt>Contact events</dt><dd>${contactText}</dd>
      </dl></div>`;
    }).join("");
  }

  function intervalRail(player) {
    const low = player.selected_lower_90;
    const high = player.selected_upper_90;
    const point = player.prediction_selected_partial_war;
    const padding = Math.max(0.25, (high - low) * 0.08);
    const min = low - padding;
    const max = high + padding;
    const at = value => Math.max(0, Math.min(100, (value - min) / (max - min) * 100));
    return `<div class="interval-rail"><div class="interval-line"></div><div class="interval-band" style="left:${at(low)}%;width:${at(high) - at(low)}%"></div><div class="interval-point" style="left:${at(point)}%"></div></div><div class="interval-labels"><span>${signed(low)} low</span><span>${signed(high)} high</span></div>`;
  }

  function renderDetail(player) {
    const flags = flagLabels(player);
    els.detail.innerHTML = `
      <div class="detail-header">
        <div><div class="eyebrow">${stageLabel(player.player_stage)} · ${player.primary_position || "No position"}</div><h2>${escapeHtml(player.player_name)}</h2><p>${escapeHtml(player.organization_name)} · MLBAM ${player.player_id} · ${player.history_seasons} season${player.history_seasons === 1 ? "" : "s"} of model history</p></div>
        <div class="rank-badge"><strong>#${player.overall_rank}</strong><span>partial WAR</span></div>
      </div>
      <div class="hero-metrics">
        <div class="metric"><strong>${signed(player.prediction_selected_partial_war)}</strong><span>projected partial WAR</span></div>
        <div class="metric"><strong>${fmt(player.prediction_expected_mlb_pa, 0)}</strong><span>expected MLB PA</span></div>
        <div class="metric"><strong>${pct(player.prediction_mlb_active_probability)}</strong><span>chance of MLB PA</span></div>
      </div>
      <div class="model-read">${modelRead(player)}</div>

      <section class="detail-section"><div class="section-heading"><h3>Value build</h3><span>WAR components</span></div><div class="component-list">${componentRows(player)}</div></section>
      <section class="detail-section"><div class="section-heading"><h3>Uncertainty</h3><span>90% historical-error range</span></div>${intervalRail(player)}</section>
      <section class="detail-section"><div class="section-heading"><h3>Batting model votes</h3><span>spread ${fmt(player.model_member_spread, 2)} WAR</span></div><div class="model-bars">${memberRows(player)}</div></section>
      <section class="detail-section"><div class="section-heading"><h3>Playing-time comparison</h3><span>expected MLB PA</span></div><div class="comparison-grid">
        <div class="comparison-card selected-model"><span>Selected</span><strong>${fmt(player.prediction_expected_mlb_pa, 0)} PA · ${pct(player.prediction_mlb_active_probability)}</strong></div>
        <div class="comparison-card"><span>Older cohort</span><strong>${fmt(player.benchmark_incumbent_expected_mlb_pa, 0)} PA · ${pct(player.benchmark_incumbent_active_probability)}</strong></div>
        <div class="comparison-card"><span>Level baseline</span><strong>${fmt(player.benchmark_parametric_expected_mlb_pa, 0)} PA · ${pct(player.benchmark_parametric_active_probability)}</strong></div>
      </div></section>
      <section class="detail-section"><div class="section-heading"><h3>Recent record</h3><span>inputs, newest first</span></div><div class="history-grid">${historyCards(player)}</div></section>
      <section class="detail-section"><div class="section-heading"><h3>Review flags</h3><span>${flags.length} found</span></div><div class="flags">${flags.length ? flags.map(flag => `<span class="review-flag">${flag}</span>`).join("") : '<span class="review-clear">No high-priority evidence or disagreement flags.</span>'}</div></section>
      <p class="fine-print">Hit/600 isolates projected batting plus replacement value at 600 MLB plate appearances, conditional on playing; it excludes opportunity, position, baserunning, and defense. Partial WAR includes batting plus replacement, position, baserunning, and catcher defense. General defense is held at zero. The forecast is frozen and has not been evaluated against 2026 results.</p>`;
  }

  function selectPlayer(id, scrollOnMobile = false) {
    const player = players.find(item => item.player_id === id);
    if (!player) return false;
    state.selectedId = id;
    renderTable();
    renderDetail(player);
    if (scrollOnMobile && window.innerWidth <= 1080) {
      els.detail.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    return true;
  }

  function updateFilters() {
    state.query = els.search.value;
    state.team = els.team.value;
    state.stage = els.stage.value;
    state.gap = els.gap.value;
    state.page = 1;
    renderTable();
  }

  els.search.addEventListener("input", updateFilters);
  els.team.addEventListener("change", updateFilters);
  els.stage.addEventListener("change", updateFilters);
  els.gap.addEventListener("change", updateFilters);
  els.prev.addEventListener("click", () => { state.page -= 1; renderTable(); });
  els.next.addEventListener("click", () => { state.page += 1; renderTable(); });
  document.querySelectorAll("th button[data-sort]").forEach(button => {
    button.addEventListener("click", () => {
      const key = button.dataset.sort;
      if (state.sort === key) state.ascending = !state.ascending;
      else {
        state.sort = key;
        state.ascending = key === "player_name" || key === "overall_rank";
      }
      state.page = 1;
      renderTable();
    });
  });

  const organizations = [...new Set(players.map(player => player.organization_name))]
    .sort((a, b) => {
      if (a === "Unassigned / inactive") return 1;
      if (b === "Unassigned / inactive") return -1;
      return a.localeCompare(b);
    });
  els.team.insertAdjacentHTML(
    "beforeend",
    organizations.map(name => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join(""),
  );

  document.getElementById("summaryPlayers").textContent = players.length.toLocaleString();
  document.getElementById("summaryMlb").textContent = players.filter(p => p.player_stage === "current_mlb").length.toLocaleString();
  document.getElementById("summaryMlbContact").textContent = `${players.filter(p => p.player_stage === "current_mlb" && !p.flag_no_current_contact).length}/667`;
  document.getElementById("summaryPrior").textContent = players.filter(p => p.flag_population_prior).length.toLocaleString();
  document.getElementById("summaryFlagged").textContent = players.filter(p => p.gap_count > 0).length.toLocaleString();

  function registerWebMcp() {
    const context = document.modelContext;
    if (!context?.registerTool) return;
    const report = error => console.warn("WebMCP registration failed", error);
    const tools = [
      {
        name: "find_hitter",
        title: "Find hitter",
        description: "Select a hitter in the explorer by exact MLBAM player ID or a name fragment.",
        inputSchema: {
          type: "object",
          properties: { query: { type: "string", minLength: 1 } },
          required: ["query"],
          additionalProperties: false,
        },
        annotations: { readOnlyHint: true, untrustedContentHint: false },
        execute(input) {
          if (!input || typeof input.query !== "string" || !input.query.trim()) throw new Error("query is required");
          const query = input.query.trim().toLocaleLowerCase();
          const player = players.find(p => String(p.player_id) === query)
            || players.find(p => p.player_name.toLocaleLowerCase().includes(query));
          if (!player) throw new Error("no matching hitter");
          els.search.value = player.player_name;
          updateFilters();
          selectPlayer(player.player_id);
          return { player_id: player.player_id, player_name: player.player_name, partial_war: player.prediction_selected_partial_war };
        },
      },
      {
        name: "show_review_cases",
        title: "Show review cases",
        description: "Filter the visible table to hitters with any model-data or disagreement review flag.",
        inputSchema: { type: "object", properties: {}, additionalProperties: false },
        annotations: { readOnlyHint: true, untrustedContentHint: false },
        execute() {
          els.gap.value = "flagged";
          updateFilters();
          return { matching_players: filteredPlayers().length };
        },
      },
    ];
    tools.forEach(tool => {
      try { void Promise.resolve(context.registerTool(tool)).catch(report); } catch (error) { report(error); }
    });
  }

  renderTable();
  if (players[0]) renderDetail(players[0]);
  registerWebMcp();
})();
