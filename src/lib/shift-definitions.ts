import { ShiftDefinition, ShiftId } from "@/lib/types";

export const SHIFT_ORDER: ShiftId[] = [
  "republic_shift",
  "ecological_shift",
  "science_shift",
  "political_shift",
];

export const SHIFT_DEFINITIONS: Record<ShiftId, ShiftDefinition> = {
  republic_shift: {
    id: "republic_shift",
    label: "The Republic Shift",
    milestoneYear: 2024,
    fromStatement:
      "First Republic constitutional formalism: faith in Nehruvian institutions and procedural legitimacy.",
    toStatement:
      "Second Republic turbulence: zombie institutions, digital-populist churn, and improvised democratic publics.",
    changeSummary:
      "From the death and mourning of the First Republic to the morning of a messy, improvisational Second Republic.",
    keywords: [
      "republic",
      "constitution",
      "citizen",
      "democracy",
      "institution",
      "left",
      "right",
      "formalism",
      "nehru",
      "public sphere",
    ],
    preferredTagSlugs: [
      "democracy",
      "law-and-justice",
      "public-institutions",
      "public-sphere",
      "nationalism",
    ],
    beforeNarrative:
      "Phase 1 traces the grammar and erosion of the First Republic, where constitutional form struggled to hold social trust.",
    afterNarrative:
      "Phase 2 tracks the arrival of the Second Republic through populist publics, digital mediation, and new civic improvisations.",
  },
  ecological_shift: {
    id: "ecological_shift",
    label: "The Ecological Shift",
    milestoneYear: 2021,
    fromStatement:
      "Resource-management environmentalism and development-with-a-human-face state conservation.",
    toStatement:
      "Anthropocene consciousness: ecocide, right to survive, and shamanic ecological lifeworlds.",
    changeSummary:
      "The archive pivots from resource-management discourse to ecological plurality, vulnerability, and the right to survive.",
    keywords: [
      "ecology",
      "anthropocene",
      "ecocide",
      "aravallis",
      "green",
      "nature",
      "environment",
      "survival",
      "climate",
      "shaman",
    ],
    preferredTagSlugs: [
      "ecology",
      "technology-and-society",
      "development",
      "knowledge-systems",
      "pluralism",
    ],
    beforeNarrative:
      "Phase 1 captures policy-oriented environmental management and development compromises.",
    afterNarrative:
      "Phase 2 foregrounds Anthropocene rupture, ecological violence, and alternative ways of knowing nature.",
  },
  science_shift: {
    id: "science_shift",
    label: "The Science Shift",
    milestoneYear: 2023,
    fromStatement:
      "Institutional Big Science and monopolies of certified expertise.",
    toStatement:
      "Knowledge Panchayats and cognitive justice across housewife, tribal, and marginal knowledges.",
    changeSummary:
      "This shift maps the move from centralized expertise to distributed and playful knowledge democracies.",
    keywords: [
      "science",
      "big science",
      "expert",
      "knowledge",
      "panchayat",
      "cognitive justice",
      "university",
      "playfulness",
      "innovation",
      "dialogue",
    ],
    preferredTagSlugs: [
      "science-policy",
      "knowledge-systems",
      "education-policy",
      "culture-and-modernity",
      "technology-and-society",
    ],
    beforeNarrative:
      "Phase 1 critiques institutional science and technocratic closure around expertise.",
    afterNarrative:
      "Phase 2 expands science into public play, plural knowledge, and cognitive justice.",
  },
  political_shift: {
    id: "political_shift",
    label: "The Political Shift",
    milestoneYear: 2022,
    fromStatement:
      "Strategic dissent and civil-society lobbying within conventional oppositional scripts.",
    toStatement:
      "Body politics: yatras, political theatre, and playful moral satyagraha.",
    changeSummary:
      "The shift marks a transition from petitionary dissent to embodied politics, affect, and public ethics.",
    keywords: [
      "dissent",
      "civil society",
      "yatra",
      "rahul",
      "satyagraha",
      "body politics",
      "theatre",
      "violence",
      "peace",
      "ethics",
    ],
    preferredTagSlugs: [
      "social-movements",
      "pluralism",
      "ethics",
      "democracy",
      "law-and-justice",
    ],
    beforeNarrative:
      "Phase 1 maps strategic critique, lobbying, and rights-based democratic contention.",
    afterNarrative:
      "Phase 2 emphasizes embodied politics, moral imagination, and performative democratic acts.",
  },
};
