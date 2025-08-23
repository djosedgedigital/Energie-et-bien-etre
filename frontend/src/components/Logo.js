export default function Logo({ className = "h-12", showFullName = false }) {
  if (showFullName) {
    return (
      <div className={`${className} flex items-center justify-center space-x-3`}>
        <div className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-secondary)] text-white font-bold text-lg lg:text-xl rounded-lg px-3 py-2">
          E&B™
        </div>
        <div className="text-[var(--color-primary)] font-bold text-lg lg:text-2xl">
          Énergie & Bien-être
        </div>
      </div>
    );
  }
  
  return (
    <div className={`${className} flex items-center justify-center bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-secondary)] text-white font-bold text-xl rounded-lg px-4`}>
      E&B™
    </div>
  );
}