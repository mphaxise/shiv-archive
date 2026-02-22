const DEFAULT_TONE_COLOR = "#6B7280";

const TONE_COLORS: Record<string, string> = {
  tribute: "#D4AF37",
  critique: "#DC2626",
  proposal: "#10B981",
};

export function toneColor(tone: string | null | undefined): string {
  if (!tone) {
    return DEFAULT_TONE_COLOR;
  }
  return TONE_COLORS[tone.trim().toLowerCase()] ?? DEFAULT_TONE_COLOR;
}

