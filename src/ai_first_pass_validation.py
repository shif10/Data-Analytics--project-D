"""Record the AI first-pass labels on the two validation samples.

Reads data/processed/clustering/final/{screen_audit_sample,cluster_label_sample}.csv,
adds `ai_pass_*` columns (the human rater columns stay blank) and writes
ai_first_pass_validation.csv with the resulting rates.

These labels come from one AI reader judging TITLES ONLY. They are a
first-pass estimate, not an independent human validation.
Row numbers refer to the row order of the sample files (0-based).
"""

from pathlib import Path

import pandas as pd

D = Path("data/processed/clustering/final")

# ---- Audit sample: rows 0-49 health rule, 50-99 no-education rule,
# ---- 100-149 kept records with >=5 health words.
EXCLUDED_IN_SCOPE = {28, 77}
EXCLUDED_UNSURE = {61, 73, 94}
KEPT_OFF_TOPIC = {102, 105, 113, 115, 124, 127, 139, 140, 142, 149}
KEPT_UNSURE = {106, 117, 144}

# ---- Cluster sample: rows 20*c .. 20*c+19 belong to cluster c.
NOT_IN_SCOPE = {22, 27, 29, 31, 39, 57, 60, 70, 72}
SCOPE_UNSURE = {18}
THEME_PARTIAL = {18, 20, 23, 24, 28, 30, 35, 37, 40, 49, 61, 63, 65, 68, 75}


def audit():
    a = pd.read_csv(D / "screen_audit_sample.csv")
    labels = []
    for i, g in enumerate(a["audit_group"]):
        if g.startswith("excluded"):
            labels.append("yes" if i in EXCLUDED_IN_SCOPE
                          else "unsure" if i in EXCLUDED_UNSURE else "no")
        else:
            labels.append("no" if i in KEPT_OFF_TOPIC
                          else "unsure" if i in KEPT_UNSURE else "yes")
    a["ai_pass_in_scope"] = labels
    a.to_csv(D / "screen_audit_sample.csv", index=False)
    rows = []
    for g, d in a.groupby("audit_group"):
        n = len(d)
        vc = d["ai_pass_in_scope"].value_counts()
        if g.startswith("excluded"):
            wrong = int(vc.get("yes", 0))
            unsure = int(vc.get("unsure", 0))
            rows.append({
                "sample": g, "n": n,
                "in_scope_wrongly_excluded": wrong, "unsure": unsure,
                "rule_precision_low": round(1 - (wrong + unsure) / n, 3),
                "rule_precision_high": round(1 - wrong / n, 3),
            })
        else:
            off = int(vc.get("no", 0))
            unsure = int(vc.get("unsure", 0))
            rows.append({
                "sample": g, "n": n,
                "off_topic_kept": off, "unsure": unsure,
                "off_topic_share_low": round(off / n, 3),
                "off_topic_share_high": round((off + unsure) / n, 3),
            })
    return rows


def clusters():
    c = pd.read_csv(D / "cluster_label_sample.csv")
    scope, fit = [], []
    for i in range(len(c)):
        if i in NOT_IN_SCOPE:
            scope.append("no")
            fit.append("n/a")
        else:
            scope.append("unsure" if i in SCOPE_UNSURE else "yes")
            fit.append("partial" if i in THEME_PARTIAL else "yes")
    c["ai_pass_in_scope"] = scope
    c["ai_pass_theme_fit"] = fit
    c.to_csv(D / "cluster_label_sample.csv", index=False)
    rows = []
    for k, d in c.groupby("cluster"):
        n = len(d)
        insc = d[d["ai_pass_in_scope"] != "no"]
        rows.append({
            "sample": f"cluster_{k}", "n": n,
            "off_topic": int((d["ai_pass_in_scope"] == "no").sum()),
            "off_topic_share": round((d["ai_pass_in_scope"] == "no").mean(), 3),
            "theme_fit_yes": int((insc["ai_pass_theme_fit"] == "yes").sum()),
            "theme_fit_partial": int((insc["ai_pass_theme_fit"] == "partial").sum()),
            "theme_fit_yes_share_of_in_scope": round(
                (insc["ai_pass_theme_fit"] == "yes").mean(), 3
            ),
        })
    return rows


if __name__ == "__main__":
    out = pd.DataFrame(audit() + clusters())
    out["note"] = "One AI reader, titles only. Not independent human validation."
    out.to_csv(D / "ai_first_pass_validation.csv", index=False)
    print(out.to_string(index=False))
