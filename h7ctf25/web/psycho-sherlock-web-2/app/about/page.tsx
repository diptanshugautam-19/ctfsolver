import { Banner } from "@/components/site/banner"
import { MagicalImage } from "@/components/site/magical-image"

export default function AboutPage() {
  return (
    <>
      <Banner
        title="About Hogwarts"
        subtitle="Founded over a thousand years ago by Godric Gryffindor, Salazar Slytherin, Rowena Ravenclaw, and Helga Hufflepuff."
        imgAlt="Ancient stone corridors of Hogwarts with torches"
        imgUrl="/hogwarts-stone-corridor-torches-ancient.jpg"
      />
      <div className="mx-auto max-w-6xl px-4 md:px-6 py-10 md:py-16 space-y-10">
        <section className="grid md:grid-cols-2 gap-8 items-start">
          <div className="space-y-4">
            <h2 className="font-serif text-2xl">History & Founders</h2>
            <p className="leading-relaxed">
              Hogwarts was established as a sanctuary for magical education, shielding students from the eyes of the
              Muggle world and fostering their talents in safety.
            </p>
            <p className="leading-relaxed">
              The Founders imbued the castle with enchantments, living portraits, and concealed chambers—each reflecting
              their distinct values and visions for future generations.
            </p>
          </div>
          <MagicalImage
            src="/hogwarts-founders-tapestry-medieval-style.jpg"
            alt="Tapestry depicting the four founders"
            width={900}
            height={600}
          />
        </section>

        <section className="grid md:grid-cols-2 gap-8 items-start">
          <MagicalImage
            src="/hogwarts-crest-vintage-parchment.jpg"
            alt="Hogwarts crest in vintage style"
            width={900}
            height={600}
          />
          <div className="space-y-4">
            <h2 className="font-serif text-2xl">The Crest & Motto</h2>
            <p className="leading-relaxed">
              The Hogwarts crest symbolizes unity among Houses and bears the motto: “Draco Dormiens Nunquam
              Titillandus.” Let wisdom guide power.
            </p>
          </div>
        </section>
      </div>
    </>
  )
}
