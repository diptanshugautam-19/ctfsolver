"use client";

import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function ForbiddenForestPage() {
  const [creatureEncounter, setCreatureEncounter] = useState<string | null>(
    null
  );
  const [moonPhase, setMoonPhase] = useState(false);
  const [showCentaurWisdom, setShowCentaurWisdom] = useState(false);
  const [forestSounds, setForestSounds] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setMoonPhase(!moonPhase);
      setForestSounds(true);
      setTimeout(() => setForestSounds(false), 3000);
    }, 8000);
    return () => clearInterval(interval);
  }, [moonPhase]);

  const creatures = [
    {
      name: "Unicorn",
      emoji: "🦄",
      danger: "Safe",
      description: "Pure magical beings that only approach the pure of heart",
    },
    {
      name: "Centaur",
      emoji: "🏹",
      danger: "Neutral",
      description: "Proud beings skilled in divination and archery",
    },
    {
      name: "Acromantula",
      emoji: "🕷️",
      danger: "Deadly",
      description: "Giant spiders led by Aragog, dangerous to all humans",
    },
    {
      name: "Hippogriff",
      emoji: "🦅",
      danger: "Dangerous",
      description: "Proud creatures requiring proper respect and approach",
    },
    {
      name: "Thestral",
      emoji: "🦇",
      danger: "Safe",
      description:
        "Winged skeletal horses visible only to those who've witnessed death",
    },
    {
      name: "Werewolf",
      emoji: "🐺",
      danger: "Deadly",
      description: "Transformed humans during full moon nights",
    },
  ];

  const centaurWisdom = [
    "The stars have been read wrongly before now, even by centaurs. I hope this is one of those times.",
    "We are sworn not to set ourselves against the heavens. Have we not read that the signs say this is to be?",
    "Mars is bright tonight. Unusually bright.",
    "The forest is not safe at this time — especially for you.",
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-green-950 via-gray-900 to-black relative overflow-hidden">
      {/* Forest atmosphere effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Floating forest particles */}
        {[...Array(40)].map((_, i) => (
          <div
            key={i}
            className={`absolute w-1 h-1 rounded-full opacity-60 ${
              forestSounds
                ? "bg-yellow-400 animate-ping"
                : "bg-green-400 animate-pulse"
            }`}
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${2 + Math.random() * 3}s`,
            }}
          />
        ))}
        {/* Moonlight effect */}
        <div
          className={`absolute top-10 right-10 w-20 h-20 rounded-full transition-all duration-2000 ${
            moonPhase
              ? "bg-yellow-200 opacity-80 shadow-lg shadow-yellow-200/50"
              : "bg-gray-300 opacity-50"
          }`}
        />
        {/* Dark forest shadows */}
        <div className="absolute inset-0 bg-gradient-radial from-transparent via-black/40 to-black/70" />
      </div>

      <div className="container mx-auto px-4 py-12 relative z-10">
        {/* Header with Warning */}
        <div className="text-center mb-8">
          <div className="mb-4">
            <Badge
              variant="destructive"
              className="bg-red-900 text-red-200 mb-4"
            >
              🚫 STRICTLY FORBIDDEN TO STUDENTS 🚫
            </Badge>
          </div>
          <h1 className="text-6xl font-serif text-green-400 mb-4 font-cinzel tracking-wide drop-shadow-lg">
            🌲 The Forbidden Forest 🌲
          </h1>
          <p className="text-xl text-green-300 font-eb-garamond italic mb-4">
            "The forest hides many secrets. Many have entered... not all have
            returned."
          </p>

          <Alert className="max-w-2xl mx-auto bg-amber-950/50 border-amber-700">
            <AlertDescription className="text-amber-200">
              <strong>Hagrid's Warning:</strong> "The forest is strictly
              off-limits to students. There are dangerous creatures in there
              that would not hesitate to tear you apart."
            </AlertDescription>
          </Alert>
        </div>

        {/* Forest Guardians - Hagrid & Keepers */}
        <Card className="bg-gradient-to-br from-brown-950/70 to-amber-950/70 border-amber-700 backdrop-blur-sm mb-8">
          <CardContent className="p-8">
            <h2 className="text-4xl font-serif text-amber-300 text-center mb-6">
              Keepers of the Forest
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="text-center">
                <div className="text-6xl mb-4">🧔‍♂️🏠</div>
                <h3 className="text-2xl font-serif text-amber-300 mb-3">
                  Rubeus Hagrid
                </h3>
                <p className="text-amber-200 text-sm leading-relaxed">
                  Keeper of Keys and Grounds at Hogwarts, and lover of dangerous
                  creatures. Hagrid knows the forest better than anyone and
                  maintains relationships with its inhabitants.
                </p>
                <div className="mt-4 space-y-1 text-xs text-amber-300">
                  <div>🏠 Lives in hut on forest edge</div>
                  <div>🐾 Befriends dangerous creatures</div>
                  <div>🔑 Keeper of Hogwarts secrets</div>
                </div>
              </div>

              <div className="text-center">
                <div className="text-6xl mb-4">🏹👥</div>
                <h3 className="text-2xl font-serif text-amber-300 mb-3">
                  The Centaur Herd
                </h3>
                <p className="text-amber-200 text-sm leading-relaxed">
                  Ancient beings who consider themselves guardians of the
                  forest. They are skilled in divination, reading the stars and
                  planets to divine the future.
                </p>
                <div className="mt-4 space-y-1 text-xs text-amber-300">
                  <div>⭐ Masters of Divination</div>
                  <div>🏹 Expert archers and warriors</div>
                  <div>🌙 Follow celestial wisdom</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Magical Creatures */}
        <Card className="bg-gradient-to-br from-purple-950/50 to-indigo-950/50 border-purple-700 backdrop-blur-sm mb-8">
          <CardContent className="p-8">
            <h2 className="text-4xl font-serif text-purple-300 text-center mb-6">
              Inhabitants of the Dark Wood
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              {creatures.map((creature, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-lg border cursor-pointer transition-all hover:scale-105 ${
                    creature.danger === "Deadly"
                      ? "bg-red-950/30 border-red-700"
                      : creature.danger === "Dangerous"
                      ? "bg-orange-950/30 border-orange-700"
                      : creature.danger === "Neutral"
                      ? "bg-yellow-950/30 border-yellow-700"
                      : "bg-green-950/30 border-green-700"
                  }`}
                  onClick={() => setCreatureEncounter(creature.name)}
                >
                  <div className="text-center">
                    <div className="text-4xl mb-2">{creature.emoji}</div>
                    <h4 className="font-semibold mb-1">{creature.name}</h4>
                    <Badge
                      variant={
                        creature.danger === "Deadly"
                          ? "destructive"
                          : "secondary"
                      }
                      className="text-xs mb-2"
                    >
                      {creature.danger}
                    </Badge>
                    <p className="text-xs opacity-80">{creature.description}</p>
                  </div>
                </div>
              ))}
            </div>

            {creatureEncounter && (
              <Alert className="bg-indigo-950/50 border-indigo-700">
                <AlertDescription className="text-indigo-200">
                  <strong>Creature Spotted:</strong> You have encountered a{" "}
                  {creatureEncounter} in the depths of the forest.
                  {creatureEncounter === "Acromantula" &&
                    " Back away slowly and do not make sudden movements!"}
                  {creatureEncounter === "Unicorn" &&
                    " You must be pure of heart to approach this magnificent being."}
                  {creatureEncounter === "Centaur" &&
                    " Show respect - they do not appreciate being treated as common beasts."}
                  {creatureEncounter === "Thestral" &&
                    " Only visible to those who have witnessed death."}
                  {creatureEncounter === "Hippogriff" &&
                    " Bow and wait for it to bow back before approaching."}
                  {creatureEncounter === "Werewolf" &&
                    " Extremely dangerous during full moon - flee immediately!"}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Centaur Wisdom */}
        <Card className="bg-gradient-to-br from-blue-950/50 to-cyan-950/50 border-cyan-700 backdrop-blur-sm mb-8">
          <CardContent className="p-8">
            <div className="text-center">
              <div className="text-6xl mb-4">🏹⭐</div>
              <h2 className="text-3xl font-serif text-cyan-300 mb-4">
                Words of the Centaurs
              </h2>
              <p className="text-cyan-200 mb-6">
                The centaurs of the Forbidden Forest are ancient beings who read
                the future in the stars. Their wisdom spans millennia, though
                they rarely share it with wizardkind.
              </p>

              <Button
                onClick={() => setShowCentaurWisdom(!showCentaurWisdom)}
                className="bg-cyan-700 hover:bg-cyan-600 text-white mb-6"
              >
                {showCentaurWisdom ? "Hide" : "Seek"} Centaur Wisdom
              </Button>

              {showCentaurWisdom && (
                <div className="space-y-4">
                  {centaurWisdom.map((wisdom, index) => (
                    <div
                      key={index}
                      className="p-4 bg-cyan-900/20 rounded border border-cyan-600"
                    >
                      <p className="text-cyan-100 italic font-serif">
                        "{wisdom}"
                      </p>
                    </div>
                  ))}
                  <div className="text-xs text-cyan-300 mt-4">
                    <em>
                      - Spoken by Firenze, Bane, and Ronan of the Forbidden
                      Forest
                    </em>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Dark History & Hogwarts Connection */}
        <Card className="bg-gradient-to-br from-gray-950/50 to-slate-950/50 border-gray-700 backdrop-blur-sm mb-8">
          <CardContent className="p-8">
            <h2 className="text-4xl font-serif text-gray-300 text-center mb-6">
              Forest Chronicles
            </h2>

            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-xl font-serif text-gray-300 mb-3 flex items-center">
                    <span className="text-2xl mr-2">🏰</span>
                    Ancient Hogwarts Boundary
                  </h3>
                  <p className="text-gray-400 text-sm">
                    The Forbidden Forest has served as Hogwarts' natural
                    boundary for over 1,000 years. The founders chose this
                    location knowing the forest would provide both protection
                    and a source of magical creatures for study.
                  </p>
                </div>

                <div>
                  <h3 className="text-xl font-serif text-gray-300 mb-3 flex items-center">
                    <span className="text-2xl mr-2">📚</span>
                    Care of Magical Creatures
                  </h3>
                  <p className="text-gray-400 text-sm">
                    Many of Hogwarts' Care of Magical Creatures lessons take
                    place at the forest's edge. Students learn about the
                    creatures that inhabit these ancient woods under strict
                    supervision.
                  </p>
                </div>
              </div>

              <Separator className="bg-gray-600" />

              <div className="space-y-4">
                <h3 className="text-2xl font-serif text-gray-300 text-center">
                  Notable Events in Forest History
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-red-950/20 rounded border border-red-800">
                    <h4 className="text-red-300 font-semibold mb-2">🕐 1991</h4>
                    <p className="text-red-200 text-sm">
                      Harry's first detention with Hagrid - encounters Voldemort
                      drinking unicorn blood
                    </p>
                  </div>

                  <div className="p-4 bg-green-950/20 rounded border border-green-800">
                    <h4 className="text-green-300 font-semibold mb-2">
                      🕐 1992
                    </h4>
                    <p className="text-green-200 text-sm">
                      Harry and Ron follow spiders to Aragog's lair in the heart
                      of the forest
                    </p>
                  </div>

                  <div className="p-4 bg-blue-950/20 rounded border border-blue-800">
                    <h4 className="text-blue-300 font-semibold mb-2">
                      🕐 1995
                    </h4>
                    <p className="text-blue-200 text-sm">
                      Umbridge's encounter with centaurs after insulting their
                      intelligence
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Aragog's Domain */}
        <Card className="bg-gradient-to-br from-gray-900/70 to-black/70 border-gray-600 backdrop-blur-sm mb-8">
          <CardContent className="p-8">
            <div className="text-center">
              <div className="text-8xl mb-4">🕷️🕸️</div>
              <h2 className="text-3xl font-serif text-gray-300 mb-4">
                Aragog's Colony
              </h2>
              <p className="text-gray-400 mb-6 max-w-3xl mx-auto">
                Deep in the heart of the Forbidden Forest lies the domain of
                Aragog, an ancient Acromantula raised by Hagrid. His children
                have multiplied over the decades, creating one of the most
                dangerous areas in the entire forest.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                <div className="p-4 bg-gray-950/40 rounded border border-gray-700">
                  <h4 className="text-gray-300 font-semibold mb-2">
                    🕷️ Aragog (Deceased)
                  </h4>
                  <p className="text-gray-400 text-sm">
                    Ancient Acromantula, friend to Hagrid since his school days.
                    Though blind, he commanded respect from his massive
                    offspring.
                  </p>
                </div>

                <div className="p-4 bg-gray-950/40 rounded border border-gray-700">
                  <h4 className="text-gray-300 font-semibold mb-2">
                    🕸️ The Colony
                  </h4>
                  <p className="text-gray-400 text-sm">
                    Hundreds of Acromantulas now inhabit the deep forest, making
                    it extremely dangerous for any human who ventures too far.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Forest Rules & Safety */}
        <Card className="bg-gradient-to-br from-orange-950/50 to-red-950/50 border-orange-700 backdrop-blur-sm">
          <CardContent className="p-8">
            <h2 className="text-4xl font-serif text-orange-300 text-center mb-6">
              Forest Laws & Safety
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-xl font-serif text-orange-300 mb-4">
                  ⚠️ Hogwarts Rules
                </h3>
                <ul className="space-y-2 text-orange-200 text-sm">
                  <li>• Students are STRICTLY forbidden from entering alone</li>
                  <li>• Only supervised visits with staff are permitted</li>
                  <li>• Detention in the forest requires adult supervision</li>
                  <li>• Emergency flares must be carried at all times</li>
                  <li>• Never venture beyond the marked pathways</li>
                </ul>
              </div>

              <div>
                <h3 className="text-xl font-serif text-orange-300 mb-4">
                  🛡️ Survival Tips
                </h3>
                <ul className="space-y-2 text-orange-200 text-sm">
                  <li>• Never run from predators - move slowly and calmly</li>
                  <li>• Respect centaurs - they are not beasts to be tamed</li>
                  <li>
                    • Avoid areas with thick webbing (Acromantula territory)
                  </li>
                  <li>• Full moon nights are especially dangerous</li>
                  <li>• Trust Hagrid's guidance above all else</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center mt-12">
          <blockquote className="text-2xl font-serif text-green-300 italic font-eb-garamond mb-4">
            "What we may be within the dark, we should fear to be within the
            light."
          </blockquote>
          <cite className="text-gray-400">— Ancient Centaur Proverb</cite>

          <div className="mt-6 p-4 bg-green-950/20 rounded border border-green-800">
            <p className="text-green-200 text-sm">
              🌲 <strong>Remember:</strong> The Forbidden Forest represents the
              wild, untamed magical world that exists beyond human control. It
              teaches us respect for nature and the creatures that call it home,
              while reminding us that some boundaries exist for our own
              protection.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
