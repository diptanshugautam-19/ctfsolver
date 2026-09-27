import { Banner } from "@/components/site/banner"
import { MagicalImage } from "@/components/site/magical-image"

const houses = [
  {
    name: "Gryffindor",
    desc: "Home to the brave and chivalrous. Their emblem is the lion, and their colors are scarlet and gold.",
    img: "/gryffindor-common-room-warm-scarlet-gold.jpg",
  },
  {
    name: "Slytherin",
    desc: "Cunning, ambitious, and resourceful. Their emblem is the serpent, in silver and emerald.",
    img: "/slytherin-common-room-emerald-stone.jpg",
  },
  {
    name: "Ravenclaw",
    desc: "For those of wit and learning. The eagle soars in bronze and blue.",
    img: "/ravenclaw-common-room-airy-library.jpg",
  },
  {
    name: "Hufflepuff",
    desc: "Dedicated, patient, and loyal. The badger stands proudly in black and yellow.",
    img: "/hufflepuff-common-room-cozy-warm.jpg",
  },
]

export default function HousesPage() {
  return (
    <>
      <Banner
        title="The Four Houses"
        subtitle="Each House fosters unique virtues. Discover where you belong."
        imgAlt="House banners in an ancient hall"
        imgUrl="/hogwarts-house-banners-hall.jpg"
      />
      <div className="mx-auto max-w-6xl px-4 md:px-6 py-10 md:py-16 space-y-10">
        {houses.map((h, i) => (
          <section key={h.name} className="grid md:grid-cols-2 gap-8 items-start">
            {i % 2 === 0 ? (
              <>
                <div className="space-y-4">
                  <h2 className="font-serif text-2xl">{h.name}</h2>
                  <p className="leading-relaxed">{h.desc}</p>
                </div>
                <MagicalImage src={h.img} alt={`${h.name} common room`} width={900} height={600} />
              </>
            ) : (
              <>
                <MagicalImage src={h.img} alt={`${h.name} common room`} width={900} height={600} />
                <div className="space-y-4">
                  <h2 className="font-serif text-2xl">{h.name}</h2>
                  <p className="leading-relaxed">{h.desc}</p>
                </div>
              </>
            )}
          </section>
        ))}
      </div>
    </>
  )
}
