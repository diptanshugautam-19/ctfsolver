import { Banner } from "@/components/site/banner"
import { MagicalImage } from "@/components/site/magical-image"
import Link from "next/link"

export default function Page() {
  return (
    <>
      <Banner
        title="Welcome to Hogwarts"
        subtitle="A castle of secrets, a library of mysteries, and a future brimming with magic. Term begins September 1st."
        imgAlt="Hogwarts castle at dusk, glowing windows and mist"
        imgUrl="/hogwarts-castle-at-dusk-mist-glowing-windows.jpg"
      />
      <div className="mx-auto max-w-6xl px-4 md:px-6 py-10 md:py-16 space-y-10">
        <section className="grid md:grid-cols-2 gap-8 items-start">
          <div className="space-y-4">
            <h2 className="font-serif text-2xl">A Magical Welcome</h2>
            <p className="leading-relaxed text-pretty">
              Nestled in the Scottish Highlands, Hogwarts School of Witchcraft and Wizardry stands as a beacon for young
              witches and wizards seeking knowledge, friendship, and courage. From the Great Hall’s enchanted ceiling to
              secret passages that whisper of legends, the castle invites you to discover your place in a world of
              magic.
            </p>
            <p className="leading-relaxed text-pretty">
              First-years will be sorted into one of four Houses, each with its own history, traditions, and common
              room. Your adventure awaits beyond these ancient doors.
            </p>
            <div className="flex flex-wrap gap-3 pt-2">
              <Link href="/about" className="px-4 py-2 rounded-md bg-accent/20 hover:bg-accent/30 transition">
                Learn About Hogwarts
              </Link>
              <Link href="/admissions" className="px-4 py-2 rounded-md bg-primary/30 hover:bg-primary/40 transition">
                Apply by Owl Post
              </Link>
            </div>
          </div>
          <MagicalImage
            src="/great-hall-floating-candles-long-tables.jpg"
            alt="The Great Hall with floating candles"
            width={900}
            height={600}
          />
        </section>

        <section className="grid md:grid-cols-3 gap-6">
          {[
            {
              title: "Gryffindor",
              img: "/gryffindor-lion-banner-vintage.jpg",
              desc: "Daring, nerve, and chivalry light the path of the lion-hearted.",
              href: "/houses",
            },
            {
              title: "Slytherin",
              img: "/slytherin-serpent-crest-emerald.jpg",
              desc: "Cunning and ambition guide those who seize destiny.",
              href: "/houses",
            },
            {
              title: "Ravenclaw",
              img: "/ravenclaw-eagle-crest-bronze.jpg",
              desc: "Wit and learning for curious minds and soaring ideals.",
              href: "/houses",
            },
          ].map((card) => (
            <article key={card.title} className="scroll-paper p-4">
              <MagicalImage src={card.img} alt={`${card.title} emblem`} width={600} height={360} />
              <h3 className="font-serif text-xl mt-4">{card.title}</h3>
              <p className="leading-relaxed mt-2 opacity-90">{card.desc}</p>
              <Link href={card.href} className="inline-block mt-3 text-foreground/90 underline underline-offset-4">
                Explore Houses
              </Link>
            </article>
          ))}
        </section>
      </div>
    </>
  )
}
