export function Footer() {
  return (
    <footer role="contentinfo" className="mt-16 border-t border-border">
      <div className="mx-auto max-w-6xl px-4 md:px-6 py-10 scroll-paper">
        <div className="text-center space-y-3">
          <p className="font-serif text-xl">“Draco Dormiens Nunquam Titillandus.”</p>
          <p className="text-sm opacity-80">© {new Date().getFullYear()} Hogwarts School of Witchcraft and Wizardry</p>
        </div>
      </div>
    </footer>
  )
}
