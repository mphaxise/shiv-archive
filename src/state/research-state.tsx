"use client";

import {
  Dispatch,
  PropsWithChildren,
  createContext,
  useContext,
  useMemo,
  useReducer,
} from "react";

import { EngineState, LayerId, ShiftId } from "@/lib/types";

type ResearchAction =
  | { type: "set-view"; view: LayerId }
  | { type: "set-shift"; shift: ShiftId }
  | { type: "set-search"; searchTerm: string }
  | { type: "set-year"; year: "all" | number }
  | { type: "reset-filters" };

interface ResearchContextValue {
  state: EngineState;
  dispatch: Dispatch<ResearchAction>;
}

const INITIAL_STATE: EngineState = {
  activeView: "chronicle",
  activeShift: "republic_shift",
  activeFilter: {
    searchTerm: "",
    year: "all",
  },
};

const ResearchStateContext = createContext<ResearchContextValue | null>(null);

function reducer(state: EngineState, action: ResearchAction): EngineState {
  switch (action.type) {
    case "set-view":
      return {
        ...state,
        activeView: action.view,
        activeShift:
          action.view === "opinion_shift" && state.activeShift !== "republic_shift"
            ? "republic_shift"
            : state.activeShift,
      };
    case "set-shift":
      return {
        ...state,
        activeShift: action.shift,
      };
    case "set-search":
      return {
        ...state,
        activeFilter: {
          ...state.activeFilter,
          searchTerm: action.searchTerm,
        },
      };
    case "set-year":
      return {
        ...state,
        activeFilter: {
          ...state.activeFilter,
          year: action.year,
        },
      };
    case "reset-filters":
      return {
        ...state,
        activeFilter: INITIAL_STATE.activeFilter,
      };
    default:
      return state;
  }
}

export function ResearchStateProvider({ children }: PropsWithChildren) {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);
  const value = useMemo(() => ({ state, dispatch }), [state]);
  return <ResearchStateContext.Provider value={value}>{children}</ResearchStateContext.Provider>;
}

export function useResearchState() {
  const context = useContext(ResearchStateContext);
  if (!context) {
    throw new Error("useResearchState must be used within ResearchStateProvider.");
  }
  return context;
}
