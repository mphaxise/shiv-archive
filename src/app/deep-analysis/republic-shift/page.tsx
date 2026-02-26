import type { Metadata } from "next";

import {
  RepublicShiftNarrative,
  RepublicShiftStoryPayload,
} from "@/components/story/RepublicShiftNarrative";
import republicShiftStory from "@/data/republic_shift_story_2026-02-26.json";

export const metadata: Metadata = {
  title: "Deep Analysis | Republic Shift | Shiv Archive",
  description:
    "Interactive narrative article tracing the Republic Shift across Shiv Visvanathan's archive.",
};

export default function RepublicShiftNarrativePage() {
  return (
    <RepublicShiftNarrative
      story={republicShiftStory as unknown as RepublicShiftStoryPayload}
    />
  );
}
