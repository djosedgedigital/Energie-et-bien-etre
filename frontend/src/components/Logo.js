export default function Logo({ className = "h-12" }) {
  return (
    <div className={`${className} flex items-center justify-center bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-secondary)] text-white font-bold text-xl rounded-lg px-4`}>
      E&B™
    </div>
  );
}