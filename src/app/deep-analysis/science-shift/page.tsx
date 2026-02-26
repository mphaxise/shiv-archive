import type { Metadata } from "next";

import {
  ScienceShiftNarrative,
  ScienceShiftStoryPayload,
} from "@/components/story/ScienceShiftNarrative";
import scienceShiftStory from "@/data/science_shift_story_2026-02-26.json";

export const metadata: Metadata = {
  title: "Deep Analysis | Science Shift | Shiv Archive",
  description:
    "Interactive narrative article tracing the Science Shift across Shiv Visvanathan's archive.",
};

export default function ScienceShiftNarrativePage() {
  return (
    <ScienceShiftNarrative story={scienceShiftStory as unknown as ScienceShiftStoryPayload} />
  );
}
