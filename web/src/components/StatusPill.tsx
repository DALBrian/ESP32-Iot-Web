type Props = { online?: boolean };
export default function StatusPill({ online }: Props) {
  const color = online ? "#16a34a" : "#dc2626";
  const text = online ? "ONLINE" : "OFFLINE";
  return (
    <span
      style={{
        backgroundColor: color,
        color: "white",
        padding: "4px 10px",
        borderRadius: 999,
        fontWeight: 600,
        fontSize: 12,
      }}
    >
      {text}
    </span>
  );
}
