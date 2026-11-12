const LINKS = [
  { href: "#/", label: "Queue" },
  { href: "#/instructions", label: "Agent instructions" },
];

export function Header({ route }: Readonly<{ route: string }>) {
  return (
    <header className="header">
      <a className="brand" href="#/">
        UnderCover <span className="tagline">Claims desk</span>
      </a>
      <nav aria-label="Main">
        {LINKS.map((link) => (
          <a
            key={link.href}
            href={link.href}
            aria-current={`#${route}` === link.href ? "page" : undefined}
          >
            {link.label}
          </a>
        ))}
      </nav>
    </header>
  );
}
