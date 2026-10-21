"""Evidence ledger and Dempster-Shafer fusion over the frame {F (fraud), L (legitimate)}.

Each source contributes a mass function m = (m_F, m_L, m_Theta). Conflict between
sources is not hidden: when the combined belief in neither hypothesis clears its
threshold the system abstains and routes to out-of-band verification.
"""
from __future__ import annotations

# source reliabilities (set on the DEV split, see experiments/tune.py)
MASS = {
    "violation_hard": 0.92,
    "violation_soft": 0.45,
    "consistent": 0.60,
    "forensic_rel": 0.75,  # reliability of a positive forensic flag
    "forensic_clean": 0.15,  # weak support for L when media look clean
    "context_rel": 0.55,
}
TAU_F, TAU_L = 0.60, 0.50


def combine(m1, m2):
    f1, l1, t1 = m1
    f2, l2, t2 = m2
    k = f1 * l2 + l1 * f2  # conflict
    if k >= 0.999:
        return (0.0, 0.0, 1.0), k
    f = (f1 * f2 + f1 * t2 + t1 * f2) / (1 - k)
    l = (l1 * l2 + l1 * t2 + t1 * l2) / (1 - k)
    return (f, l, 1 - f - l), k


class Ledger:
    def __init__(self, mass=None):
        self.mass = dict(MASS, **(mass or {}))
        self.items = []  # (source, m, note)
        self.state = (0.0, 0.0, 1.0)
        self.max_conflict = 0.0

    def add(self, source, m, note=""):
        self.items.append((source, tuple(round(x, 4) for x in m), note))
        self.state, k = combine(self.state, m)
        self.max_conflict = max(self.max_conflict, k)

    # ---- source adapters
    def add_procedure(self, findings):
        for f in findings:
            if f["type"] == "violation":
                v = self.mass["violation_hard"] if f["strength"] == "hard" else self.mass["violation_soft"]
                self.add("procedure:" + f["id"], (v, 0.0, 1 - v), f["title"])
            else:
                c = self.mass["consistent"]
                self.add("procedure:" + f["id"], (0.0, c, 1 - c), f["title"])

    def add_forensic(self, name, score):
        if score >= 0.5:
            r = self.mass["forensic_rel"] * score
            self.add("forensic:" + name, (r, 0.0, 1 - r), f"manipulation score {score:.2f}")
        else:
            c = self.mass["forensic_clean"] * (1 - score)
            self.add("forensic:" + name, (0.0, c, 1 - c), f"no strong manipulation evidence ({score:.2f})")

    def add_context(self, p):
        r = self.mass["context_rel"]
        self.add("context:ccs", (r * p, r * (1 - p) * 0.5, 1 - r * p - r * (1 - p) * 0.5), f"CCS stage-risk {p:.2f}")

    # ---- decisions
    @property
    def bel_f(self):
        return self.state[0]

    @property
    def bel_l(self):
        return self.state[1]

    def p_fraud(self):
        f, l, t = self.state
        return f + t / 2  # pignistic transform

    def decision(self, tau_f=TAU_F, tau_l=TAU_L):
        if self.bel_f >= tau_f:
            return "FRAUD"
        if self.bel_l >= tau_l:
            return "LEGITIMATE"
        return "ABSTAIN_VERIFY"

    def decisive(self, tau_f=TAU_F, tau_l=TAU_L):
        return self.decision(tau_f, tau_l) != "ABSTAIN_VERIFY"
