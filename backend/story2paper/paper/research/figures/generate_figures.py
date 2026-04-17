#!/usr/bin/env python3
"""
Generate paper figures from benchmark_results.json
Usage: python generate_figures.py
Requires: matplotlib, numpy (pip install if missing)
"""
import json, os, sys

os.makedirs(os.path.dirname(__file__), exist_ok=True)

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("ERROR: matplotlib not installed. Run: pip install matplotlib numpy")
    sys.exit(1)

BASE = os.path.dirname(__file__)
with open(f"{BASE}/../experiments/benchmark_results.json") as f:
    data = json.load(f)

AGG = data["AGGREGATE"]
SYSTEMS = ["DirectChat", "Story2Proposal", "Story2Paper_NoContract", "Story2Paper_NoRefiner", "Story2Paper"]
COLORS = ["#94a3b8", "#60a5fa", "#a78bfa", "#fb923c", "#34d399"]

# ── Figure 1: Main Results Bar Chart ──────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(SYSTEMS))
width = 0.35

eval_scores = [AGG[s]["avg_eval"] for s in SYSTEMS]
kw_recalls = [AGG[s]["avg_kw"] for s in SYSTEMS]

bars1 = ax.bar(x - width/2, eval_scores, width, label="Evaluator Score (0–10)",
               color=COLORS, edgecolor="none", rounded=2)
bars2 = ax.bar(x + width/2, kw_recalls, width, label="Keyword Recall (0–1)",
               color=COLORS, alpha=0.55, edgecolor="none", rounded=2)

labels = []
for s in SYSTEMS:
    if s == "DirectChat":
        labels.append("DirectChat")
    elif s == "Story2Proposal":
        labels.append("Story2Proposal")
    elif s == "Story2Paper":
        labels.append("Story2Paper")
    else:
        labels.append(s.replace("Story2Paper_", "S2P\n−").replace("Story2Paper", ""))

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9)
ax.set_ylabel("Score")
ax.set_ylim(0, 7)
ax.set_title("Main Results: Story2Paper vs. Baselines", fontweight="bold", pad=12)
ax.legend(loc="upper left")
ax.yaxis.grid(True, linestyle="--", alpha=0.4)
ax.set_axisbelow(True)

for bar, score in zip(bars1, eval_scores):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.08,
            f"{score:.2f}", ha="center", va="bottom", fontsize=8)

plt.tight_layout()
plt.savefig(f"{BASE}/fig_main_results.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ fig_main_results.png")

# ── Figure 2: Ablation — Contract Effect ─────────────────────────────────────
fig, ax = plt.subplots(figsize=(5.5, 4))
ab_systems = ["Story2Paper_NoContract", "Story2Paper"]
ab_scores = [AGG[s]["avg_eval"] for s in ab_systems]
ab_kw = [AGG[s]["avg_kw"] for s in ab_systems]

x = np.arange(2)
width = 0.28
bars1 = ax.bar(x - width, ab_scores, width, label="Eval Score",
               color=["#a78bfa", "#34d399"], edgecolor="none", rounded=2)
bars2 = ax.bar(x, ab_kw, width, label="Keyword Recall",
               color=["#a78bfa", "#34d399"], alpha=0.6, edgecolor="none", rounded=2)

ax.set_xticks(x)
ax.set_xticklabels(["S2P −Contract", "S2P +Contract"], fontsize=10)
ax.set_ylabel("Score")
ax.set_ylim(0, 7)
ax.set_title("Effect of Visual Contract", fontweight="bold", pad=10)
ax.legend(fontsize=9)
ax.yaxis.grid(True, linestyle="--", alpha=0.4)
ax.set_axisbelow(True)

delta_eval = ab_scores[1] - ab_scores[0]
delta_kw = ab_kw[1] - ab_kw[0]
ax.annotate(f"+{delta_eval:.2f}", xy=(0.5 + width/2, ab_scores[1] + 0.1),
            ha="center", fontsize=10, color="#059669", fontweight="bold")
ax.annotate(f"+{delta_kw:.3f}", xy=(0.5, ab_kw[1] + 0.05),
            ha="center", fontsize=10, color="#059669", fontweight="bold")

plt.tight_layout()
plt.savefig(f"{BASE}/fig_ablation_contract.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ fig_ablation_contract.png")

# ── Figure 3: Per-entry Breakdown ─────────────────────────────────────────────
entry_ids = [f"jc_{str(i).zfill(3)}" for i in range(1, 11)]
eval_dc = [data["RESULTS"]["DirectChat"][eid]["evaluator_score"] for eid in entry_ids]
eval_s2p = [data["RESULTS"]["Story2Paper"][eid]["evaluator_score"] for eid in entry_ids]

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

axes[0].plot(entry_ids, eval_dc, "o-", color="#94a3b8", label="DirectChat", linewidth=1.8, markersize=6)
axes[0].plot(entry_ids, eval_s2p, "s-", color="#34d399", label="Story2Paper", linewidth=1.8, markersize=6)
axes[0].fill_between(entry_ids, eval_dc, alpha=0.12, color="#94a3b8")
axes[0].set_title("Evaluator Score per Entry", fontweight="bold", pad=8)
axes[0].set_xlabel("Entry ID")
axes[0].set_ylabel("Score (0–10)")
axes[0].legend()
axes[0].tick_params(axis="x", rotation=45)
axes[0].grid(True, linestyle="--", alpha=0.4)

sec_data = np.array([
    [data["RESULTS"][s][eid]["section_recall"] for eid in entry_ids]
    for s in ["DirectChat", "Story2Proposal", "Story2Paper"]
])
im = axes[1].imshow(sec_data, aspect="auto", cmap="Greens", vmin=0.6, vmax=1.0)
axes[1].set_yticks(range(3))
axes[1].set_yticklabels(["DirectChat", "Story2Proposal", "Story2Paper"])
axes[1].set_xticks(range(10))
axes[1].set_xticklabels(entry_ids, rotation=45)
axes[1].set_title("Section Recall Heatmap", fontweight="bold", pad=8)
cbar = plt.colorbar(im, ax=axes[1])
cbar.set_label("Recall")

plt.tight_layout()
plt.savefig(f"{BASE}/fig_per_entry_breakdown.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ fig_per_entry_breakdown.png")

print(f"\nAll figures → {BASE}/")
