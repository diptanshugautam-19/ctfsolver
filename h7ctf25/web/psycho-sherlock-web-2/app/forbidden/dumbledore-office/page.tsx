"use client";

import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import Link from "next/link";

export default function DumbledoreOfficePage() {
  const [phoenixAnimation, setPhoenixAnimation] = useState(false);
  const [revealSecret, setRevealSecret] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setPhoenixAnimation(true);
      setTimeout(() => setPhoenixAnimation(false), 3000);
    }, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-950 via-indigo-950 to-slate-900 relative overflow-hidden">
      {/* Floating magical particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(30)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-yellow-400 rounded-full opacity-60 animate-pulse"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${2 + Math.random() * 3}s`,
            }}
          />
        ))}
      </div>

      <div className="container mx-auto px-4 py-12 relative z-10">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-6xl font-serif text-amber-300 mb-4 font-cinzel tracking-wide">
            🧙‍♂️ Dumbledore's Office 🧙‍♂️
          </h1>
          <p className="text-xl text-purple-300 font-eb-garamond italic">
            "It is our choices, Harry, that show what we truly are, far more
            than our abilities."
          </p>
          <Badge
            variant="outline"
            className="mt-4 text-amber-400 border-amber-400"
          >
            Headmaster's Private Chambers
          </Badge>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          {/* Fawkes the Phoenix */}
          <Card className="bg-gradient-to-br from-red-950/50 to-orange-950/50 border-orange-700 backdrop-blur-sm">
            <CardContent className="p-8">
              <div className="text-center">
                <div
                  className={`text-8xl mb-6 transition-all duration-3000 ${
                    phoenixAnimation ? "animate-bounce scale-110" : "scale-100"
                  }`}
                >
                  🔥🦅
                </div>
                <h2 className="text-3xl font-serif text-orange-300 mb-4">
                  Fawkes the Phoenix
                </h2>
                <p className="text-orange-200 mb-4 leading-relaxed">
                  The magnificent phoenix perches gracefully, his scarlet and
                  gold plumage shimmering in the magical light. Fawkes's healing
                  tears and tail feathers have saved many lives throughout
                  Hogwarts' history.
                </p>
                <div className="space-y-2 text-sm text-orange-300">
                  <div>
                    🎵 <em>Phoenix song echoes through the office...</em>
                  </div>
                  <div>
                    💧 <em>Tears that can heal any wound</em>
                  </div>
                  <div>
                    🪶{" "}
                    <em>Tail feathers core the Elder Wand and Harry's wand</em>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Pensieve */}
          <Card className="bg-gradient-to-br from-blue-950/50 to-cyan-950/50 border-cyan-700 backdrop-blur-sm">
            <CardContent className="p-8">
              <div className="text-center">
                <div className="text-8xl mb-6">🌀💭</div>
                <h2 className="text-3xl font-serif text-cyan-300 mb-4">
                  The Pensieve
                </h2>
                <p className="text-cyan-200 mb-4 leading-relaxed">
                  A shallow stone basin carved with ancient runes, filled with a
                  silvery substance that holds memories and thoughts. Here, one
                  can review the past with perfect clarity.
                </p>
                <Button
                  onClick={() => setRevealSecret(!revealSecret)}
                  className="bg-cyan-700 hover:bg-cyan-600 text-white"
                >
                  Peer into Memory
                </Button>
                {revealSecret && (
                  <div className="mt-4 p-4 bg-cyan-900/30 rounded border border-cyan-600">
                    <p className="text-cyan-100 text-sm italic">
                      "You see, Harry, memory is a curious thing... What lies
                      within the depths of the Pensieve may hold the key to
                      understanding Tom Riddle's past..."
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Hogwarts Artifacts */}
        <Card className="bg-gradient-to-br from-purple-950/50 to-indigo-950/50 border-purple-700 backdrop-blur-sm mb-8">
          <CardContent className="p-8">
            <h2 className="text-4xl font-serif text-purple-300 text-center mb-8">
              Sacred Hogwarts Artifacts
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Sorting Hat */}
              <div className="text-center p-6 bg-amber-950/30 rounded-lg border border-amber-700">
                <div className="text-6xl mb-4">🎩</div>
                <h3 className="text-xl font-serif text-amber-300 mb-2">
                  The Sorting Hat
                </h3>
                <p className="text-amber-200 text-sm">
                  The ancient hat that sorts students into their houses,
                  containing the wisdom of the four founders of Hogwarts.
                </p>
              </div>

              {/* Sword of Gryffindor */}
              <div className="text-center p-6 bg-red-950/30 rounded-lg border border-red-700">
                <div className="text-6xl mb-4">⚔️</div>
                <h3 className="text-xl font-serif text-red-300 mb-2">
                  Sword of Gryffindor
                </h3>
                <p className="text-red-200 text-sm">
                  Forged by goblins with goblin silver, it absorbs only that
                  which strengthens it. Impregnated with basilisk venom.
                </p>
              </div>

              {/* Elder Wand */}
              <div className="text-center p-6 bg-gray-950/30 rounded-lg border border-gray-700">
                <div className="text-6xl mb-4">🪄</div>
                <h3 className="text-xl font-serif text-gray-300 mb-2">
                  The Elder Wand
                </h3>
                <p className="text-gray-200 text-sm">
                  The most powerful wand ever created, with a core of Thestral
                  tail hair, fifteen inches long.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Secret Passages */}
        <Card className="bg-gradient-to-br from-slate-950/50 to-gray-950/50 border-slate-700 backdrop-blur-sm mb-8">
          <CardContent className="p-8">
            <h2 className="text-4xl font-serif text-slate-300 text-center mb-8">
              🗝️ Secret Passages 🗝️
            </h2>
            <p className="text-slate-400 text-center mb-6 italic">
              "The castle holds many secrets, Harry. Some are meant to be
              discovered..."
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Forbidden Forest */}
              <div className="text-center p-6 bg-green-950/30 rounded-lg border border-green-700 hover:border-green-500 transition-all duration-300">
                <div className="text-6xl mb-4">🌲🦄</div>
                <h3 className="text-xl font-serif text-green-300 mb-4">
                  The Forbidden Forest
                </h3>
                <p className="text-green-200 text-sm mb-4">
                  A dark and dangerous forest on the grounds of Hogwarts, home
                  to many magical creatures including centaurs, unicorns, and
                  Acromantulas.
                </p>
                <Button
                  asChild
                  className="bg-green-800 hover:bg-green-700 text-white border-green-600"
                >
                  <Link href="/forbidden/forbidden-forest">
                    🌿 Enter the Forest
                  </Link>
                </Button>
              </div>

              {/* Chamber of Secrets */}
              <div className="text-center p-6 bg-emerald-950/30 rounded-lg border border-emerald-700 hover:border-emerald-500 transition-all duration-300">
                <div className="text-6xl mb-4">🐍🗝️</div>
                <h3 className="text-xl font-serif text-emerald-300 mb-4">
                  The Chamber of Secrets
                </h3>
                <p className="text-emerald-200 text-sm mb-4">
                  Hidden deep beneath the school, created by Salazar Slytherin.
                  Only the heir of Slytherin can open its doors.
                </p>
                <Button
                  asChild
                  className="bg-emerald-800 hover:bg-emerald-700 text-white border-emerald-600"
                >
                  <Link href="/forbidden/chamber-of-secrets">
                    🐍 Open the Chamber
                  </Link>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Hogwarts History */}
        <Card className="bg-gradient-to-br from-emerald-950/50 to-teal-950/50 border-emerald-700 backdrop-blur-sm">
          <CardContent className="p-8">
            <h2 className="text-4xl font-serif text-emerald-300 text-center mb-6">
              Chronicles of Hogwarts
            </h2>

            <div className="space-y-6">
              <div className="flex items-start space-x-4">
                <div className="text-3xl">🏰</div>
                <div>
                  <h3 className="text-xl font-serif text-emerald-300 mb-2">
                    Foundation (c. 990 AD)
                  </h3>
                  <p className="text-emerald-200">
                    Founded by Godric Gryffindor, Helga Hufflepuff, Rowena
                    Ravenclaw, and Salazar Slytherin. Each founder valued
                    different qualities and established the four houses.
                  </p>
                </div>
              </div>

              <Separator className="bg-emerald-700" />

              <div className="flex items-start space-x-4">
                <div className="text-3xl">📚</div>
                <div>
                  <h3 className="text-xl font-serif text-emerald-300 mb-2">
                    The Great Library
                  </h3>
                  <p className="text-emerald-200">
                    Contains thousands of spellbooks, including the powerful
                    tome of advanced magic. The Restricted Section holds the
                    most dangerous magical knowledge.
                  </p>
                </div>
              </div>

              <Separator className="bg-emerald-700" />

              <div className="flex items-start space-x-4">
                <div className="text-3xl">🔮</div>
                <div>
                  <h3 className="text-xl font-serif text-emerald-300 mb-2">
                    Magical Protections
                  </h3>
                  <p className="text-emerald-200">
                    The castle is protected by numerous enchantments:
                    Anti-Apparition charms, defensive spells, and the ancient
                    magic woven into its very foundations.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer Quote */}
        <div className="text-center mt-12">
          <blockquote className="text-2xl font-serif text-amber-300 italic font-eb-garamond">
            "Happiness can be found even in the darkest of times, if one only
            remembers to turn on the light."
          </blockquote>
          <cite className="text-purple-300 mt-2 block">
            — Albus Percival Wulfric Brian Dumbledore
          </cite>
        </div>
      </div>
    </div>
  );
}
