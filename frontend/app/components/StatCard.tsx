export default function StatCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string | number;
  icon: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand/10 text-brand">
        {icon}
      </div>
      <p className="font-display mt-4 text-3xl font-semibold text-foreground">
        {value}
      </p>
      <p className="mt-1 text-sm text-muted">{label}</p>
    </div>
  );
}
