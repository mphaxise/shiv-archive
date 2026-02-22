import { DatasetPayload } from "@/lib/types";

function formatUtcStamp(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(parsed);
}

export function SiteFooter({
  generatedAtUtc,
  citationsLabel = "archive",
}: {
  generatedAtUtc: DatasetPayload["metadata"]["generated_at_utc"];
  citationsLabel?: string;
}) {
  const lastUpdated = formatUtcStamp(generatedAtUtc);

  return (
    <footer className="siteFooter">
      <p>
        Last updated: <strong>{lastUpdated}</strong>
      </p>
      <p>
        Contact: <a href="mailto:praneet.koppula@gmail.com">praneet.koppula@gmail.com</a> |
        GitHub:{" "}
        <a href="https://github.com/mphaxise/shiv-archive" target="_blank" rel="noreferrer">
          github.com/mphaxise/shiv-archive
        </a>
      </p>
      <p>
        Citation guidance: cite the original publication URL for each article, and cite this{" "}
        {citationsLabel} with the snapshot timestamp above.
      </p>
    </footer>
  );
}
