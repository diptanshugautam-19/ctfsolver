import { Banner } from "@/components/site/banner";
import { MagicalImage } from "@/components/site/magical-image";
import { Button } from "@/components/ui/button";
import Link from "next/link";

const professors = [
  {
    name: "Minerva McGonagall",
    subject: "Transfiguration",
    img: "/professor-portrait-mcgonagall-style.jpg",
  },
  {
    name: "Severus Snape",
    subject: "Potions",
    img: "/snape.png",
  },
  {
    name: "Filius Flitwick",
    subject: "Charms",
    img: "/filus.png",
  },
  {
    name: "Albus Dumbledore",
    subject: "Headmaster",
    img: "/dumbledore.png",
  },
];

export default function FacultyPage() {
  return (
    <>
      <Banner
        title="Faculty"
        subtitle="Our esteemed professors guide students through the arcane arts."
        imgAlt="Staff table at the Great Hall"
        imgUrl="https://images.unsplash.com/photo-1517841905240-472988babdf9"
      />
      <div className="mx-auto max-w-6xl px-4 md:px-6 py-10 md:py-16">
        <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-6">
          {professors.map((p) => (
            <article key={p.name} className="scroll-paper p-4 text-center">
              <MagicalImage
                src={p.img}
                alt={`${p.name} portrait`}
                width={400}
                height={400}
              />
              <h3 className="font-serif text-xl mt-3">{p.name}</h3>
              <p className="opacity-80">{p.subject}</p>
              {p.name === "Albus Dumbledore" && (
                <div className="mt-3">
                  <Button
                    asChild
                    variant="outline"
                    size="sm"
                    className="bg-gradient-to-r from-amber-100 to-yellow-100 border-amber-300 text-amber-800 hover:from-amber-200 hover:to-yellow-200 hover:border-amber-400 transition-all duration-300 shadow-md hover:shadow-lg"
                  >
                    <Link href="/forbidden/dumbledore-office">
                      🏰 Visit Office
                    </Link>
                  </Button>
                </div>
              )}
            </article>
          ))}
        </div>
      </div>
    </>
  );
}
