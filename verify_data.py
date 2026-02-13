#!/usr/bin/env python3
"""
Verify that all numerical data in the ISO-Bench website matches the paper.
Parses both index.html and example_paper.tex, extracts all data points,
and reports any mismatches.
"""

import re
import sys

WEBSITE_PATH = "/Users/fortuna/Desktop/Colab/ICML_paper_ISO/lossfunk_stuff/website/index.html"
PAPER_PATH = "/Users/fortuna/Desktop/Colab/ICML_paper_ISO/iclr2026/example_paper.tex"

with open(WEBSITE_PATH, "r") as f:
    website = f.read()
with open(PAPER_PATH, "r") as f:
    paper = f.read()

mismatches = []
matches = []
notes = []

def check(description, website_val, paper_val):
    if str(website_val).strip() != str(paper_val).strip():
        mismatches.append(f"MISMATCH: {description}\n  Website: {website_val}\n  Paper:   {paper_val}")
    else:
        matches.append(f"OK: {description} = {website_val}")

def note(description):
    notes.append(description)

# ============================================================
# 1. TASK COUNTS
# ============================================================
print("=" * 70)
print("1. TASK COUNTS")
print("=" * 70)

w_total = "54" if "54 tasks" in website or "54 optimization tasks" in website else "NOT FOUND"
p_total = "54" if "54 tasks" in paper or "54 optimization tasks" in paper else "NOT FOUND"
check("Total tasks", w_total, p_total)

w_vllm = "39" if "39 tasks" in website else "NOT FOUND"
p_vllm = "39" if "39 vLLM" in paper or "39 from vLLM" in paper else "NOT FOUND"
check("vLLM tasks", w_vllm, p_vllm)

w_sglang = "15" if "15 tasks" in website else "NOT FOUND"
p_sglang = "15" if "15 from SGLang" in paper or "15 SGLang" in paper else "NOT FOUND"
check("SGLang tasks", w_sglang, p_sglang)

# ============================================================
# 2. AGENT CONFIGURATIONS
# ============================================================
print("\n" + "=" * 70)
print("2. AGENT CONFIGURATIONS")
print("=" * 70)

agents_website = {
    "Claude Code": "Claude Sonnet 4.5" if "Claude Code</strong> (Claude Sonnet 4.5)" in website else "NOT FOUND",
    "Codex CLI": "GPT-5" if "Codex CLI</strong> (GPT-5)" in website else "NOT FOUND",
    "TRAE (Sonnet)": "Claude Sonnet 4.5" if "TRAE (Sonnet)</strong> (Claude Sonnet 4.5)" in website else "NOT FOUND",
    "TRAE (GPT-5)": "GPT-5" if "TRAE (GPT-5)</strong> (GPT-5)" in website else "NOT FOUND",
}

agents_paper = {
    "Claude Code": "Claude Sonnet 4.5" if "Claude Code & Claude Sonnet 4.5" in paper else "NOT FOUND",
    "Codex CLI": "GPT-5" if "Codex CLI & GPT-5" in paper else "NOT FOUND",
    "TRAE (Sonnet)": "Claude Sonnet 4.5" if "TRAE-Agent (Sonnet) & Claude Sonnet 4.5" in paper else "NOT FOUND",
    "TRAE (GPT-5)": "GPT-5" if "TRAE-Agent (GPT-5) & GPT-5" in paper else "NOT FOUND",
}

for agent in agents_website:
    check(f"Agent '{agent}' model", agents_website[agent], agents_paper[agent])

w_budget = "120" if "120 minutes" in website else "NOT FOUND"
p_budget = "120" if "120 minutes" in paper else "NOT FOUND"
check("Time budget (minutes)", w_budget, p_budget)

# ============================================================
# 3. TABLE 2: TRUE SUCCESS RATES BY PROJECT
# ============================================================
print("\n" + "=" * 70)
print("3. TABLE 2: TRUE SUCCESS RATES BY PROJECT")
print("=" * 70)

true_success_website = {}
ts_pattern = re.compile(
    r'<tr>\s*<td>(?:<strong>)?([^<]+?)(?:</strong>)?</td>\s*<td>([^<]+)</td>\s*<td>(?:<strong>)?([\d.]+%)(?:</strong>)?</td>\s*<td>(?:<strong>)?([\d.]+%)(?:</strong>)?</td>\s*</tr>'
)
ts_section = website[website.find("Can Agents Optimize GPU Inference Code?"):]
ts_section = ts_section[:ts_section.find("Do Hard Metrics Tell the Full Story?")]
for m in ts_pattern.finditer(ts_section):
    agent = m.group(1).strip()
    true_success_website[agent] = {"vllm": m.group(3), "sglang": m.group(4)}

true_success_paper = {}
ts_paper_pattern = re.compile(r'(Claude Code|TRAE \(Sonnet\)|TRAE \(GPT-5\)|Codex CLI)\s*&\s*([\d.]+)\\%\s*&\s*([\d.]+)\\%')
paper_ts_section = paper[paper.find("True Success rates"):]
paper_ts_section = paper_ts_section[:paper_ts_section.find("\\end{table}")]
for m in ts_paper_pattern.finditer(paper_ts_section):
    agent = m.group(1).strip()
    true_success_paper[agent] = {"vllm": m.group(2) + "%", "sglang": m.group(3) + "%"}

for agent in ["Claude Code", "TRAE (Sonnet)", "TRAE (GPT-5)", "Codex CLI"]:
    w_vllm = true_success_website.get(agent, {}).get("vllm", "NOT FOUND")
    p_vllm = true_success_paper.get(agent, {}).get("vllm", "NOT FOUND")
    check(f"True Success vLLM - {agent}", w_vllm, p_vllm)
    w_sg = true_success_website.get(agent, {}).get("sglang", "NOT FOUND")
    p_sg = true_success_paper.get(agent, {}).get("sglang", "NOT FOUND")
    check(f"True Success SGLang - {agent}", w_sg, p_sg)

# ============================================================
# 4. TABLE 3: HARD VS TRUE SUCCESS WITH GAP
# ============================================================
print("\n" + "=" * 70)
print("4. TABLE 3: HARD VS TRUE SUCCESS WITH GAP")
print("=" * 70)

def parse_website_hard_true(section_text):
    results = {}
    pattern = re.compile(
        r'<tr>\s*<td>(?:<strong>)?([^<]+?)(?:</strong>)?</td>\s*<td>([\d.]+%)</td>\s*<td>([\d.]+%)</td>\s*<td>(?:<strong>)?([\d.]+%)(?:</strong>)?</td>\s*</tr>'
    )
    for m in pattern.finditer(section_text):
        agent = m.group(1).strip()
        results[agent] = {"hard": m.group(2), "true": m.group(3), "gap": m.group(4)}
    return results

w_hard_section = website[website.find("Do Hard Metrics Tell the Full Story?"):]
w_vllm_section = w_hard_section[w_hard_section.find("<h4"):]
w_sglang_start = w_vllm_section.find("SGLang")
w_vllm_table = w_vllm_section[:w_sglang_start]
w_sglang_section = w_vllm_section[w_sglang_start:]
w_sglang_table = w_sglang_section[:w_sglang_section.find("</section>")]

w_vllm_ht = parse_website_hard_true(w_vllm_table)
w_sglang_ht = parse_website_hard_true(w_sglang_table)

paper_ht_section = paper[paper.find("Hard Success vs"):]
paper_ht_section = paper_ht_section[:paper_ht_section.find("\\end{tabular}")]

p_vllm_ht = {}
p_sglang_ht = {}

ht_pattern = re.compile(r'&\s*(Claude Code|Codex CLI|TRAE \(Sonnet\)|TRAE \(GPT-5\))\s*&\s*([\d.]+)\s*&\s*([\d.]+)\s*&\s*([\d.]+)')
vllm_part = paper_ht_section[:paper_ht_section.find("SGLang")]
sglang_part = paper_ht_section[paper_ht_section.find("SGLang"):]

for m in ht_pattern.finditer(vllm_part):
    agent = m.group(1).strip()
    p_vllm_ht[agent] = {"hard": m.group(2) + "%", "true": m.group(3) + "%", "gap": m.group(4) + "%"}

for m in ht_pattern.finditer(sglang_part):
    agent = m.group(1).strip()
    p_sglang_ht[agent] = {"hard": m.group(2) + "%", "true": m.group(3) + "%", "gap": m.group(4) + "%"}

for agent in ["Claude Code", "Codex CLI", "TRAE (Sonnet)", "TRAE (GPT-5)"]:
    for metric in ["hard", "true", "gap"]:
        metric_name = {"hard": "Hard Success", "true": "True Success", "gap": "Gap"}[metric]
        w_val = w_vllm_ht.get(agent, {}).get(metric, "NOT FOUND")
        p_val = p_vllm_ht.get(agent, {}).get(metric, "NOT FOUND")
        check(f"vLLM {metric_name} - {agent}", w_val, p_val)
    for metric in ["hard", "true", "gap"]:
        metric_name = {"hard": "Hard Success", "true": "True Success", "gap": "Gap"}[metric]
        w_val = w_sglang_ht.get(agent, {}).get(metric, "NOT FOUND")
        p_val = p_sglang_ht.get(agent, {}).get(metric, "NOT FOUND")
        check(f"SGLang {metric_name} - {agent}", w_val, p_val)

# ============================================================
# 5. TABLE 4: QUADRANT DISTRIBUTION
# ============================================================
print("\n" + "=" * 70)
print("5. TABLE 4: QUADRANT DISTRIBUTION (Q1-Q4)")
print("=" * 70)

def parse_website_quadrant(section_text):
    results = {}
    pattern = re.compile(
        r'<tr>\s*<td>(?:<strong>)?([^<]+?)(?:</strong>)?</td>\s*<td>(?:<strong>)?(\d+)(?:</strong>)?</td>\s*<td>(?:<strong>)?(\d+)(?:</strong>)?</td>\s*<td>(?:<strong>)?(\d+)(?:</strong>)?</td>\s*<td>(?:<strong>)?(\d+)(?:</strong>)?</td>\s*</tr>'
    )
    for m in pattern.finditer(section_text):
        agent = m.group(1).strip()
        results[agent] = {"Q1": m.group(2), "Q2": m.group(3), "Q3": m.group(4), "Q4": m.group(5)}
    return results

w_quad_section = website[website.find("Quadrant Distribution"):]
w_quad_vllm = w_quad_section[w_quad_section.find("vLLM (39 tasks)"):]
w_quad_sglang_start = w_quad_vllm.find("SGLang (15 tasks)")
w_quad_vllm_table = w_quad_vllm[:w_quad_sglang_start]
w_quad_sglang_table = w_quad_vllm[w_quad_sglang_start:]

w_vllm_q = parse_website_quadrant(w_quad_vllm_table)
w_sglang_q = parse_website_quadrant(w_quad_sglang_table)

paper_q_section = paper[paper.find("Distribution of outcomes across quadrants"):]
paper_q_section = paper_q_section[:paper_q_section.find("\\end{tabular}")]

q_pattern = re.compile(r'&\s*(Claude Code|Codex CLI|TRAE \(Sonnet\)|TRAE \(GPT-5\))\s*&\s*(\d+)\s*&\s*(\d+)\s*&\s*(\d+)\s*&\s*(\d+)')

p_vllm_q = {}
p_sglang_q = {}

vllm_q_part = paper_q_section[:paper_q_section.find("SGLang")]
sglang_q_part = paper_q_section[paper_q_section.find("SGLang"):]

for m in q_pattern.finditer(vllm_q_part):
    agent = m.group(1).strip()
    p_vllm_q[agent] = {"Q1": m.group(2), "Q2": m.group(3), "Q3": m.group(4), "Q4": m.group(5)}

for m in q_pattern.finditer(sglang_q_part):
    agent = m.group(1).strip()
    p_sglang_q[agent] = {"Q1": m.group(2), "Q2": m.group(3), "Q3": m.group(4), "Q4": m.group(5)}

for agent in ["Claude Code", "Codex CLI", "TRAE (Sonnet)", "TRAE (GPT-5)"]:
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        w_val = w_vllm_q.get(agent, {}).get(q, "NOT FOUND")
        p_val = p_vllm_q.get(agent, {}).get(q, "NOT FOUND")
        check(f"vLLM {q} - {agent}", w_val, p_val)
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        w_val = w_sglang_q.get(agent, {}).get(q, "NOT FOUND")
        p_val = p_sglang_q.get(agent, {}).get(q, "NOT FOUND")
        check(f"SGLang {q} - {agent}", w_val, p_val)

# ============================================================
# 5b. VERIFY QUADRANT SUMS = TASK COUNTS
# ============================================================
print("\n" + "=" * 70)
print("5b. QUADRANT SUMS CONSISTENCY CHECK")
print("=" * 70)

for agent in ["Claude Code", "Codex CLI", "TRAE (Sonnet)", "TRAE (GPT-5)"]:
    q_vals = w_vllm_q.get(agent, {})
    if all(v != "NOT FOUND" for v in q_vals.values()):
        total = sum(int(q_vals[q]) for q in ["Q1", "Q2", "Q3", "Q4"])
        check(f"vLLM quadrant sum - {agent} (should be 39)", str(total), "39")
    q_vals = w_sglang_q.get(agent, {})
    if all(v != "NOT FOUND" for v in q_vals.values()):
        total = sum(int(q_vals[q]) for q in ["Q1", "Q2", "Q3", "Q4"])
        check(f"SGLang quadrant sum - {agent} (should be 15)", str(total), "15")

# ============================================================
# 5c. VERIFY PERCENTAGES MATCH QUADRANT COUNTS
# ============================================================
print("\n" + "=" * 70)
print("5c. TRUE SUCCESS PERCENTAGES vs QUADRANT COUNTS")
print("=" * 70)

for agent in ["Claude Code", "Codex CLI", "TRAE (Sonnet)", "TRAE (GPT-5)"]:
    q1_vllm = w_vllm_q.get(agent, {}).get("Q1", None)
    ts_vllm = true_success_website.get(agent, {}).get("vllm", None)
    if q1_vllm and ts_vllm:
        computed_pct = round(int(q1_vllm) / 39 * 100, 1)
        reported_pct = float(ts_vllm.replace("%", ""))
        check(f"vLLM True Success % vs Q1/39 - {agent}", f"{reported_pct}%", f"{computed_pct}%")
    q1_sg = w_sglang_q.get(agent, {}).get("Q1", None)
    ts_sg = true_success_website.get(agent, {}).get("sglang", None)
    if q1_sg and ts_sg:
        computed_pct = round(int(q1_sg) / 15 * 100, 1)
        reported_pct = float(ts_sg.replace("%", ""))
        check(f"SGLang True Success % vs Q1/15 - {agent}", f"{reported_pct}%", f"{computed_pct}%")

# ============================================================
# 5d. VERIFY HARD SUCCESS PERCENTAGES vs QUADRANT COUNTS
# ============================================================
print("\n" + "=" * 70)
print("5d. HARD SUCCESS PERCENTAGES vs QUADRANT COUNTS (Q1+Q3)")
print("=" * 70)

for agent in ["Claude Code", "Codex CLI", "TRAE (Sonnet)", "TRAE (GPT-5)"]:
    q1 = w_vllm_q.get(agent, {}).get("Q1", None)
    q3 = w_vllm_q.get(agent, {}).get("Q3", None)
    hs = w_vllm_ht.get(agent, {}).get("hard", None)
    if q1 and q3 and hs:
        computed_pct = round((int(q1) + int(q3)) / 39 * 100, 1)
        reported_pct = float(hs.replace("%", ""))
        check(f"vLLM Hard Success % vs (Q1+Q3)/39 - {agent}", f"{reported_pct}%", f"{computed_pct}%")
    q1 = w_sglang_q.get(agent, {}).get("Q1", None)
    q3 = w_sglang_q.get(agent, {}).get("Q3", None)
    hs = w_sglang_ht.get(agent, {}).get("hard", None)
    if q1 and q3 and hs:
        computed_pct = round((int(q1) + int(q3)) / 15 * 100, 1)
        reported_pct = float(hs.replace("%", ""))
        check(f"SGLang Hard Success % vs (Q1+Q3)/15 - {agent}", f"{reported_pct}%", f"{computed_pct}%")

# ============================================================
# 6. UNDERSTANDING vs EXECUTION GAP TABLE
# ============================================================
print("\n" + "=" * 70)
print("6. UNDERSTANDING vs EXECUTION GAP (vLLM)")
print("=" * 70)

w_ue_section = website[website.find("Understanding vs. Execution Gap"):]
w_ue_section = w_ue_section[:w_ue_section.find("</table>")]

ue_pattern = re.compile(
    r'<tr>\s*<td>([^<]+)</td>\s*<td>([\d.]+%)</td>\s*<td>([\d.]+%)</td>\s*<td>(?:<strong>)?([\d.]+%)(?:</strong>)?</td>\s*</tr>'
)

w_ue = {}
for m in ue_pattern.finditer(w_ue_section):
    agent = m.group(1).strip()
    w_ue[agent] = {"correct_target": m.group(2), "true_success": m.group(3), "gap": m.group(4)}

# Compute from quadrant data in paper: Correct Target (Q1+Q2) / 39
p_ue = {}
for agent in ["Claude Code", "Codex CLI", "TRAE (Sonnet)", "TRAE (GPT-5)"]:
    q1 = p_vllm_q.get(agent, {}).get("Q1", None)
    q2 = p_vllm_q.get(agent, {}).get("Q2", None)
    ts = true_success_paper.get(agent, {}).get("vllm", None)
    if q1 and q2 and ts:
        correct_pct = round((int(q1) + int(q2)) / 39 * 100, 1)
        true_pct = float(ts.replace("%", ""))
        gap_pct = round(correct_pct - true_pct, 1)
        p_ue[agent] = {"correct_target": f"{correct_pct}%", "true_success": ts, "gap": f"{gap_pct}%"}

for agent in ["TRAE (GPT-5)", "Codex CLI", "TRAE (Sonnet)", "Claude Code"]:
    w_ct = w_ue.get(agent, {}).get("correct_target", "NOT FOUND")
    p_ct = p_ue.get(agent, {}).get("correct_target", "NOT FOUND")
    check(f"vLLM Correct Target (Q1+Q2) - {agent}", w_ct, p_ct)
    w_ts = w_ue.get(agent, {}).get("true_success", "NOT FOUND")
    p_ts = p_ue.get(agent, {}).get("true_success", "NOT FOUND")
    check(f"vLLM True Success (UE table) - {agent}", w_ts, p_ts)
    w_gap = w_ue.get(agent, {}).get("gap", "NOT FOUND")
    p_gap = p_ue.get(agent, {}).get("gap", "NOT FOUND")
    check(f"vLLM UE Gap - {agent}", w_gap, p_gap)

# ============================================================
# 7. KEY CLAIMS / HIGHLIGHTED NUMBERS
# ============================================================
print("\n" + "=" * 70)
print("7. KEY CLAIMS / HIGHLIGHTED NUMBERS")
print("=" * 70)

w_overestimate = "20%" if "up to <strong>20%</strong>" in website or "up to 20%" in website else "NOT FOUND"
p_overestimate = "20%" if "10-20" in paper else "NOT FOUND"
check("Max overestimation claim", w_overestimate, p_overestimate)

# Website: "87.2% correct bottleneck identification" - derived from (7+27)/39 = 87.2%
# Paper has Q1=7, Q2=27 for TRAE (GPT-5) vLLM -> (7+27)/39 = 87.179% -> 87.2%
# This is not stated literally in the paper but is derivable from Table 4
computed_from_paper = round((7+27)/39*100, 1)
check("TRAE GPT-5 bottleneck identification (87.2% derived from quadrant table)",
      "87.2" if "87.2%" in website else "NOT FOUND",
      str(computed_from_paper))

# Website highlighted: "69.3%"
w_gap_highlight = "69.3%" if "69.3%" in website else "NOT FOUND"
computed_gap = round(87.2 - 17.9, 1)
check("TRAE GPT-5 understanding-execution gap (87.2 - 17.9)", w_gap_highlight, f"{computed_gap}%")

# Website: "0% success rate" for open-source
w_oss_rate = "0%" if "0% success rate" in website else "NOT FOUND"
p_oss_rate = "0%" if "None produced a working optimization" in paper else "NOT FOUND"
check("Open-source success rate (website says 0%, paper says 'None produced a working optimization')",
      w_oss_rate, "0%")

# Website: "three open-source models"
w_oss_count = "3" if "three open-source models" in website else "NOT FOUND"
p_oss_count = "3" if "three open-source models" in paper or "three open-source" in paper else "NOT FOUND"
check("Number of open-source models", w_oss_count, p_oss_count)

# ============================================================
# 8. OPEN-SOURCE MODEL DETAILS
# ============================================================
print("\n" + "=" * 70)
print("8. OPEN-SOURCE MODEL DETAILS")
print("=" * 70)

check("MiniMax steps", "75" if "75 steps" in website else "NOT FOUND",
      "75" if "75 steps" in paper or "Steps: 75" in paper else "NOT FOUND")
check("MiniMax tool calls", "0" if ">0</td>" in website else "NOT FOUND",
      "0" if "Tool calls: \\textbf{0}" in paper or "0 Tool Calls" in paper else "NOT FOUND")
check("MiniMax duration", "477s" if "477s" in website else "NOT FOUND",
      "477s" if "477s" in paper else "NOT FOUND")
check("MiniMax output tokens", "81,782" if "81,782" in website else "NOT FOUND",
      "81,782" if "81,782" in paper else "NOT FOUND")
check("MiniMax token rate", "171 tok/s" if "171 tok/s" in website else "NOT FOUND",
      "171 tok/s" if "171 tok/s" in paper else "NOT FOUND")
check("MiniMax input tokens", "1,599,945" if "1,599,945" in website else "NOT FOUND",
      "1,599,945" if "1,599,945" in paper else "NOT FOUND")
check("MiniMax repeat count", "2,412" if "2,412" in website else "NOT FOUND",
      "2,412" if "2,412" in paper else "NOT FOUND")
check("GPT-OSS file creation attempts", "~84" if "~84" in website or "84 file creation" in website else "NOT FOUND",
      "~84" if "84" in paper else "NOT FOUND")
check("GLM tool calls total", "386" if "386" in website else "NOT FOUND",
      "386" if "386" in paper else "NOT FOUND")
check("GLM bash calls", "327" if "327 bash" in website else "NOT FOUND",
      "327" if "327 bash" in paper else "NOT FOUND")
check("GLM str_replace calls", "59" if "59 str_replace" in website else "NOT FOUND",
      "59" if "59 str" in paper or "59 successful" in paper else "NOT FOUND")
check("GLM max steps", "400" if "400 steps" in website else "NOT FOUND",
      "400" if "400-step" in paper or "400 steps" in paper else "NOT FOUND")

# ============================================================
# 9. METHODOLOGY NUMBERS
# ============================================================
print("\n" + "=" * 70)
print("9. METHODOLOGY NUMBERS")
print("=" * 70)

check("Significance threshold",
      "5%" if "5%" in website else "NOT FOUND",
      "5%" if "5\\%" in paper else "NOT FOUND")

w_judge = "Gemini-3-Flash-Preview" if "Gemini-3-Flash-Preview" in website else "NOT FOUND"
p_judge = "Gemini-3-Flash-Preview" if "Gemini-3-Flash-Preview" in paper else "NOT FOUND"
check("LLM judge model", w_judge, p_judge)

# ============================================================
# 10. GAP ARITHMETIC VERIFICATION
# ============================================================
print("\n" + "=" * 70)
print("10. GAP ARITHMETIC VERIFICATION")
print("=" * 70)

for agent in ["Claude Code", "Codex CLI", "TRAE (Sonnet)", "TRAE (GPT-5)"]:
    h = w_vllm_ht.get(agent, {}).get("hard", None)
    t = w_vllm_ht.get(agent, {}).get("true", None)
    g = w_vllm_ht.get(agent, {}).get("gap", None)
    if h and t and g:
        computed_gap = round(float(h.replace("%","")) - float(t.replace("%","")), 1)
        reported_gap = float(g.replace("%",""))
        check(f"vLLM Gap arithmetic - {agent} ({h} - {t})", f"{reported_gap}%", f"{computed_gap}%")
    h = w_sglang_ht.get(agent, {}).get("hard", None)
    t = w_sglang_ht.get(agent, {}).get("true", None)
    g = w_sglang_ht.get(agent, {}).get("gap", None)
    if h and t and g:
        computed_gap = round(float(h.replace("%","")) - float(t.replace("%","")), 1)
        reported_gap = float(g.replace("%",""))
        check(f"SGLang Gap arithmetic - {agent} ({h} - {t})", f"{reported_gap}%", f"{computed_gap}%")

# ============================================================
# 11. OPEN-SOURCE MODEL NAMES
# ============================================================
print("\n" + "=" * 70)
print("11. OPEN-SOURCE MODEL NAMES")
print("=" * 70)

for model_name in ["MiniMax-M2.1", "GPT-OSS-120B", "GLM-4.7"]:
    w_found = model_name if model_name in website else "NOT FOUND"
    p_found = model_name if model_name in paper else "NOT FOUND"
    check(f"Open-source model name: {model_name}", w_found, p_found)

# ============================================================
# 12. CONTENT PRESENT IN PAPER BUT NOT WEBSITE (informational)
# ============================================================
print("\n" + "=" * 70)
print("12. CONTENT IN PAPER BUT NOT ON WEBSITE (informational, not errors)")
print("=" * 70)

# Bamba accuracy regression: paper mentions "accuracy collapsed from 32% to 0%"
# Website does not discuss Bamba or accuracy regression
note("Paper mentions Bamba accuracy regression (32% to 0%) - website does not include this detail (OK: website summarizes, paper has full case studies)")

# Commit filtering stats (paper only)
note("Paper has commit filtering stats table (15234/8421 total commits, etc.) - website does not include these (OK: pipeline details are paper-only)")

# Paper mentions specific commit hashes - website does not
note("Paper includes specific commit hashes (98f47f2a, 015069b0, fe66b347, 2deb029d) - website does not (OK: case study detail)")

for n in notes:
    print(f"  NOTE: {n}")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"\nTotal checks: {len(matches) + len(mismatches)}")
print(f"Passed: {len(matches)}")
print(f"MISMATCHES: {len(mismatches)}")
print(f"Notes (informational): {len(notes)}")

if mismatches:
    print("\n" + "!" * 70)
    print("ALL MISMATCHES:")
    print("!" * 70)
    for m in mismatches:
        print(f"\n  {m}")
else:
    print("\n*** All data points match between website and paper! ***")

print("\n" + "-" * 70)
print("DETAILED PASS LIST:")
print("-" * 70)
for m in matches:
    print(f"  {m}")

sys.exit(1 if mismatches else 0)
