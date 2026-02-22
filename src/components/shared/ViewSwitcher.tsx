"use client";

import { SHIFT_DEFINITIONS, SHIFT_ORDER } from "@/lib/shift-definitions";
import { LayerId } from "@/lib/types";
import { useResearchState } from "@/state/research-state";

const VIEW_LABELS: Array<{ id: LayerId; label: string; subtitle: string }> = [
  { id: "chronicle", label: "Database View", subtitle: "Complete archive cards" },
  { id: "opinion_shift", label: "Opinion Shift", subtitle: "Deep analysis" },
];

export function ViewSwitcher() {
  const { state, dispatch } = useResearchState();

  return (
    <section className="switchPanel">
      <section className="switchSection">
        <h2>Views</h2>
        <div className="switchList">
          {VIEW_LABELS.map((view) => (
            <button
              key={view.id}
              type="button"
              className={`switchCard ${state.activeView === view.id ? "active" : ""}`}
              onClick={() => dispatch({ type: "set-view", view: view.id })}
            >
              <span className="switchTitle">{view.label}</span>
              <span className="switchSubtitle">{view.subtitle}</span>
            </button>
          ))}
        </div>
      </section>

      {state.activeView === "opinion_shift" ? (
        <section className="switchSection">
          <h2>Shift Focus</h2>
          <div className="switchList">
            {SHIFT_ORDER.map((shiftId) => {
              const shift = SHIFT_DEFINITIONS[shiftId];
              const enabled = shift.id === "republic_shift";
              return (
                <button
                  key={shift.id}
                  type="button"
                  disabled={!enabled}
                  className={`switchCard ${state.activeShift === shift.id ? "active" : ""} ${!enabled ? "disabled" : ""}`}
                  onClick={() => dispatch({ type: "set-shift", shift: shift.id })}
                >
                  <span className="switchTitle">{shift.label}</span>
                  <span className="switchSubtitle">
                    Milestone {shift.milestoneYear} {enabled ? "| Active in v1" : "| Queued"}
                  </span>
                </button>
              );
            })}
          </div>
        </section>
      ) : null}
    </section>
  );
}
